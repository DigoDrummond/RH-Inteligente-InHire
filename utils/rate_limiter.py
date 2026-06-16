"""
Sistema Avançado de Rate Limiting
Implementa limitação inteligente de taxa com múltiplas estratégias
"""
import time
import threading
from collections import deque
from datetime import datetime, timedelta
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# ENUMS E DATACLASSES
# ============================================================================

class RateLimitStrategy(Enum):
    """Estratégias de rate limiting"""
    TOKEN_BUCKET = "token_bucket"      # Token bucket algorithm
    SLIDING_WINDOW = "sliding_window"  # Sliding window counter
    FIXED_WINDOW = "fixed_window"      # Fixed window counter
    ADAPTIVE = "adaptive"              # Adaptive based on response times


class RateLimitExceeded(Exception):
    """Exceção lançada quando rate limit é excedido"""
    pass


@dataclass
class RateLimitConfig:
    """Configuração de rate limiting"""
    max_requests: int                    # Máximo de requisições
    time_window_seconds: float           # Janela de tempo em segundos
    strategy: RateLimitStrategy          # Estratégia a usar
    burst_size: Optional[int] = None     # Tamanho do burst (token bucket)
    backoff_factor: float = 1.5          # Fator de backoff exponencial
    max_backoff_seconds: float = 300.0   # Máximo tempo de backoff (5 min)
    adaptive_threshold_ms: float = 1000.0  # Threshold para modo adaptativo


@dataclass
class RequestRecord:
    """Registro de uma requisição"""
    timestamp: float
    duration_ms: float = 0.0
    success: bool = True


# ============================================================================
# TOKEN BUCKET RATE LIMITER
# ============================================================================

class TokenBucketLimiter:
    """
    Implementa algoritmo Token Bucket

    Permite bursts controlados enquanto mantém taxa média constante.
    Ideal para APIs que permitem bursts ocasionais.
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.capacity = config.burst_size or config.max_requests
        self.tokens = float(self.capacity)
        self.refill_rate = config.max_requests / config.time_window_seconds
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def _refill(self):
        """Reabastece tokens baseado no tempo decorrido"""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate

        with self.lock:
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now

    def acquire(self, tokens: float = 1.0) -> bool:
        """
        Tenta adquirir tokens

        Args:
            tokens: Número de tokens a adquirir

        Returns:
            True se tokens foram adquiridos, False caso contrário
        """
        self._refill()

        with self.lock:
            if self.tokens >= tokens:
                self.tokens -= tokens
                logger.debug(f"Tokens adquiridos: {tokens:.2f}, restantes: {self.tokens:.2f}")
                return True
            else:
                logger.warning(f"Tokens insuficientes: {self.tokens:.2f} < {tokens:.2f}")
                return False

    def wait_time(self) -> float:
        """Retorna tempo de espera em segundos até próximo token"""
        self._refill()

        with self.lock:
            if self.tokens >= 1.0:
                return 0.0

            tokens_needed = 1.0 - self.tokens
            return tokens_needed / self.refill_rate

    def get_status(self) -> dict:
        """Retorna status atual do limiter"""
        self._refill()
        return {
            'tokens_available': self.tokens,
            'capacity': self.capacity,
            'refill_rate': self.refill_rate,
            'utilization_pct': (1 - self.tokens / self.capacity) * 100
        }


# ============================================================================
# SLIDING WINDOW RATE LIMITER
# ============================================================================

class SlidingWindowLimiter:
    """
    Implementa algoritmo Sliding Window Counter

    Mais preciso que fixed window, evita edge cases.
    Ideal para limites rígidos e precisos.
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests: deque[RequestRecord] = deque()
        self.lock = threading.Lock()

    def _cleanup_old_requests(self):
        """Remove requisições fora da janela de tempo"""
        cutoff = time.time() - self.config.time_window_seconds

        with self.lock:
            while self.requests and self.requests[0].timestamp < cutoff:
                self.requests.popleft()

    def acquire(self) -> bool:
        """
        Tenta registrar uma nova requisição

        Returns:
            True se requisição foi permitida, False caso contrário
        """
        self._cleanup_old_requests()

        with self.lock:
            if len(self.requests) < self.config.max_requests:
                self.requests.append(RequestRecord(timestamp=time.time()))
                logger.debug(f"Requisição permitida: {len(self.requests)}/{self.config.max_requests}")
                return True
            else:
                logger.warning(f"Rate limit excedido: {len(self.requests)}/{self.config.max_requests}")
                return False

    def record_duration(self, duration_ms: float, success: bool = True):
        """Registra duração da última requisição"""
        with self.lock:
            if self.requests:
                self.requests[-1].duration_ms = duration_ms
                self.requests[-1].success = success

    def wait_time(self) -> float:
        """Retorna tempo de espera até próxima janela"""
        self._cleanup_old_requests()

        with self.lock:
            if len(self.requests) < self.config.max_requests:
                return 0.0

            # Tempo até a requisição mais antiga sair da janela
            oldest_timestamp = self.requests[0].timestamp
            time_until_slot = (
                oldest_timestamp +
                self.config.time_window_seconds -
                time.time()
            )
            return max(0.0, time_until_slot)

    def get_status(self) -> dict:
        """Retorna status atual do limiter"""
        self._cleanup_old_requests()

        with self.lock:
            current_count = len(self.requests)
            avg_duration = (
                sum(r.duration_ms for r in self.requests) / current_count
                if current_count > 0 else 0.0
            )

            return {
                'current_requests': current_count,
                'max_requests': self.config.max_requests,
                'utilization_pct': (current_count / self.config.max_requests) * 100,
                'avg_duration_ms': avg_duration
            }


# ============================================================================
# ADAPTIVE RATE LIMITER
# ============================================================================

class AdaptiveRateLimiter:
    """
    Implementa rate limiting adaptativo baseado em performance

    Ajusta automaticamente a taxa baseado nos tempos de resposta.
    Ideal para APIs com capacidade variável.
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.base_limiter = SlidingWindowLimiter(config)
        self.current_limit = config.max_requests
        self.adjustment_factor = 1.0
        self.consecutive_slow = 0
        self.consecutive_fast = 0
        self.lock = threading.Lock()

    def _adjust_limit(self, duration_ms: float):
        """Ajusta limite baseado na performance"""
        with self.lock:
            # Se resposta muito lenta, reduzir limite
            if duration_ms > self.config.adaptive_threshold_ms:
                self.consecutive_slow += 1
                self.consecutive_fast = 0

                if self.consecutive_slow >= 3:
                    self.adjustment_factor = max(0.5, self.adjustment_factor * 0.9)
                    self.consecutive_slow = 0
                    logger.warning(
                        f"Reduzindo rate limit: fator={self.adjustment_factor:.2f}, "
                        f"duration={duration_ms:.0f}ms"
                    )

            # Se respostas rápidas, aumentar limite
            elif duration_ms < self.config.adaptive_threshold_ms * 0.5:
                self.consecutive_fast += 1
                self.consecutive_slow = 0

                if self.consecutive_fast >= 5:
                    self.adjustment_factor = min(1.0, self.adjustment_factor * 1.1)
                    self.consecutive_fast = 0
                    logger.info(
                        f"Aumentando rate limit: fator={self.adjustment_factor:.2f}, "
                        f"duration={duration_ms:.0f}ms"
                    )

            # Atualizar limite atual
            new_limit = int(self.config.max_requests * self.adjustment_factor)
            if new_limit != self.current_limit:
                self.current_limit = new_limit
                logger.info(f"Novo rate limit: {self.current_limit} req/{self.config.time_window_seconds}s")

    def acquire(self) -> bool:
        """Tenta adquirir permissão para requisição"""
        # Usar limite ajustado
        original_limit = self.base_limiter.config.max_requests
        self.base_limiter.config.max_requests = self.current_limit

        result = self.base_limiter.acquire()

        self.base_limiter.config.max_requests = original_limit
        return result

    def record_duration(self, duration_ms: float, success: bool = True):
        """Registra duração e ajusta limite"""
        self.base_limiter.record_duration(duration_ms, success)
        if success:
            self._adjust_limit(duration_ms)

    def wait_time(self) -> float:
        """Retorna tempo de espera"""
        return self.base_limiter.wait_time()

    def get_status(self) -> dict:
        """Retorna status incluindo ajustes adaptativos"""
        status = self.base_limiter.get_status()
        status.update({
            'adjustment_factor': self.adjustment_factor,
            'current_limit': self.current_limit,
            'base_limit': self.config.max_requests
        })
        return status


# ============================================================================
# RATE LIMITER FACTORY
# ============================================================================

class RateLimiter:
    """
    Factory e wrapper para diferentes estratégias de rate limiting
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.backoff_until: Optional[float] = None
        self.backoff_count = 0

        # Criar limiter baseado na estratégia
        if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            self.limiter = TokenBucketLimiter(config)
        elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            self.limiter = SlidingWindowLimiter(config)
        elif config.strategy == RateLimitStrategy.ADAPTIVE:
            self.limiter = AdaptiveRateLimiter(config)
        else:
            raise ValueError(f"Estratégia não suportada: {config.strategy}")

        logger.info(
            f"Rate limiter inicializado: {config.strategy.value}, "
            f"{config.max_requests} req/{config.time_window_seconds}s"
        )

    def acquire(self, wait: bool = True) -> bool:
        """
        Tenta adquirir permissão para fazer requisição

        Args:
            wait: Se True, aguarda até conseguir permissão

        Returns:
            True se permissão foi concedida

        Raises:
            RateLimitExceeded: Se wait=False e limite foi excedido
        """
        # Verificar se está em backoff
        if self.backoff_until and time.time() < self.backoff_until:
            if not wait:
                raise RateLimitExceeded("Em período de backoff")

            wait_time = self.backoff_until - time.time()
            logger.info(f"Aguardando backoff: {wait_time:.1f}s")
            time.sleep(wait_time)
            self.backoff_until = None

        # Tentar adquirir
        if self.limiter.acquire():
            self.backoff_count = 0
            return True

        if not wait:
            raise RateLimitExceeded("Rate limit excedido")

        # Aguardar e aplicar backoff exponencial
        wait_time = self.limiter.wait_time()

        if wait_time > 0:
            # Aplicar backoff exponencial
            backoff = min(
                wait_time * (self.config.backoff_factor ** self.backoff_count),
                self.config.max_backoff_seconds
            )

            logger.info(f"Rate limit excedido, aguardando {backoff:.1f}s (backoff #{self.backoff_count})")
            time.sleep(backoff)

            self.backoff_count += 1
            self.backoff_until = time.time() + backoff

        return self.acquire(wait=wait)

    def record_request(self, duration_ms: float, success: bool = True):
        """Registra estatísticas da requisição"""
        if hasattr(self.limiter, 'record_duration'):
            self.limiter.record_duration(duration_ms, success)

    def get_status(self) -> dict:
        """Retorna status detalhado do limiter"""
        status = self.limiter.get_status()
        status.update({
            'strategy': self.config.strategy.value,
            'backoff_count': self.backoff_count,
            'in_backoff': self.backoff_until is not None and time.time() < self.backoff_until
        })
        return status


# ============================================================================
# DECORATOR PARA RATE LIMITING
# ============================================================================

def rate_limited(limiter: RateLimiter, track_duration: bool = True):
    """
    Decorator para aplicar rate limiting a funções

    Args:
        limiter: Instância de RateLimiter
        track_duration: Se True, registra duração da chamada

    Example:
        limiter = RateLimiter(RateLimitConfig(
            max_requests=100,
            time_window_seconds=60,
            strategy=RateLimitStrategy.TOKEN_BUCKET
        ))

        @rate_limited(limiter)
        def api_call():
            return requests.get('...')
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Adquirir permissão
            limiter.acquire(wait=True)

            # Executar função
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                success = False
                raise
            finally:
                # Registrar duração se configurado
                if track_duration:
                    duration_ms = (time.time() - start_time) * 1000
                    limiter.record_request(duration_ms, success)

        return wrapper
    return decorator


# ============================================================================
# RATE LIMITERS PRÉ-CONFIGURADOS
# ============================================================================

# InHire API (limite máximo)
INHIRE_API_LIMITER = RateLimiter(RateLimitConfig(
    max_requests=200,             # 200 requisições
    time_window_seconds=60,       # Por minuto
    strategy=RateLimitStrategy.ADAPTIVE,
    burst_size=50,                # Permitir burst de 50
    adaptive_threshold_ms=2000.0  # 2s threshold
))

# Database operations (mais permissivo)
DATABASE_LIMITER = RateLimiter(RateLimitConfig(
    max_requests=100,
    time_window_seconds=10,
    strategy=RateLimitStrategy.TOKEN_BUCKET,
    burst_size=50
))

# Exports e relatórios (muito restritivo)
EXPORT_LIMITER = RateLimiter(RateLimitConfig(
    max_requests=5,
    time_window_seconds=60,
    strategy=RateLimitStrategy.SLIDING_WINDOW
))
