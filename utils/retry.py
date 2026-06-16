"""
Mecanismos de retry com backoff exponencial
Usado para lidar com falhas temporárias de rede e API
"""
import time
import functools
from typing import Callable, Any, Type, Tuple
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
import logging
from requests.exceptions import RequestException, Timeout, ConnectionError
from config import settings


# ========================================
# Exceções Personalizadas
# ========================================

class TokenExpiredException(Exception):
    """Exceção quando o token JWT expirou"""
    pass


class RateLimitException(Exception):
    """Exceção quando rate limit foi atingido"""
    pass


class APIException(Exception):
    """Exceção genérica de API"""
    pass


# ========================================
# Decoradores de Retry
# ========================================

def retry_with_backoff(
    max_attempts: int = None,
    max_wait: int = 60,
    exceptions: Tuple[Type[Exception], ...] = (RequestException, ConnectionError, Timeout),
    logger: logging.Logger = None
):
    """
    Decorator para retry com backoff exponencial

    Args:
        max_attempts: Número máximo de tentativas (default: config.INHIRE_RETRY_ATTEMPTS)
        max_wait: Tempo máximo de espera entre tentativas em segundos
        exceptions: Tupla de exceções que devem triggerar retry
        logger: Logger para registrar tentativas

    Returns:
        Decorator function

    Example:
        @retry_with_backoff(max_attempts=3)
        def fetch_data():
            return requests.get(url)
    """
    max_attempts = max_attempts or settings.INHIRE_RETRY_ATTEMPTS
    logger = logger or logging.getLogger(__name__)

    def decorator(func):
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=settings.INHIRE_RETRY_BACKOFF_FACTOR,
                min=1,
                max=max_wait
            ),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.DEBUG)
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def retry_on_rate_limit(
    max_attempts: int = 5,
    base_wait: int = 60,
    logger: logging.Logger = None
):
    """
    Decorator específico para rate limiting (HTTP 429)

    Args:
        max_attempts: Número máximo de tentativas
        base_wait: Tempo base de espera em segundos
        logger: Logger para registrar tentativas

    Returns:
        Decorator function

    Example:
        @retry_on_rate_limit()
        def api_call():
            return requests.post(url, data=data)
    """
    logger = logger or logging.getLogger(__name__)

    def decorator(func):
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=2,
                min=base_wait,
                max=300  # Máximo 5 minutos
            ),
            retry=retry_if_exception_type(RateLimitException),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.DEBUG)
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def retry_on_token_expired(
    max_attempts: int = 2,
    refresh_callback: Callable = None,
    logger: logging.Logger = None
):
    """
    Decorator para retry quando token expira (HTTP 401)

    Args:
        max_attempts: Número máximo de tentativas
        refresh_callback: Função para renovar o token
        logger: Logger para registrar tentativas

    Returns:
        Decorator function

    Example:
        @retry_on_token_expired(refresh_callback=auth_service.refresh_token)
        def fetch_jobs():
            return api_client.get_jobs()
    """
    logger = logger or logging.getLogger(__name__)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0

            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)

                except TokenExpiredException as e:
                    attempts += 1

                    if attempts >= max_attempts:
                        logger.error(f"Token expirou após {max_attempts} tentativas")
                        raise

                    logger.warning(f"Token expirado (tentativa {attempts}/{max_attempts})")

                    # Tentar renovar token se callback fornecido
                    if refresh_callback:
                        try:
                            logger.info("Tentando renovar token...")
                            refresh_callback()
                            logger.info("Token renovado com sucesso")
                        except Exception as refresh_error:
                            logger.error(f"Falha ao renovar token: {refresh_error}")
                            raise
                    else:
                        logger.warning("Nenhum callback de renovação fornecido")
                        raise

            return None

        return wrapper

    return decorator


# ========================================
# Classe de Retry Customizado
# ========================================

class RetryManager:
    """
    Gerenciador de retry com lógica customizada
    """

    def __init__(
        self,
        max_attempts: int = None,
        backoff_factor: float = None,
        max_wait: int = 60,
        logger: logging.Logger = None
    ):
        """
        Inicializa o gerenciador de retry

        Args:
            max_attempts: Número máximo de tentativas
            backoff_factor: Fator de multiplicação para backoff exponencial
            max_wait: Tempo máximo de espera entre tentativas
            logger: Logger para registrar tentativas
        """
        self.max_attempts = max_attempts or settings.INHIRE_RETRY_ATTEMPTS
        self.backoff_factor = backoff_factor or settings.INHIRE_RETRY_BACKOFF_FACTOR
        self.max_wait = max_wait
        self.logger = logger or logging.getLogger(__name__)

    def execute_with_retry(
        self,
        func: Callable,
        *args,
        retry_on: Tuple[Type[Exception], ...] = (Exception,),
        **kwargs
    ) -> Any:
        """
        Executa uma função com retry

        Args:
            func: Função a ser executada
            *args: Argumentos posicionais para a função
            retry_on: Tupla de exceções que devem triggerar retry
            **kwargs: Argumentos nomeados para a função

        Returns:
            Resultado da função

        Raises:
            Última exceção se todas as tentativas falharem
        """
        last_exception = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                self.logger.debug(f"Tentativa {attempt}/{self.max_attempts} de {func.__name__}")
                result = func(*args, **kwargs)

                if attempt > 1:
                    self.logger.info(f"Sucesso na tentativa {attempt}/{self.max_attempts}")

                return result

            except retry_on as e:
                last_exception = e
                self.logger.warning(
                    f"Tentativa {attempt}/{self.max_attempts} falhou: {str(e)}"
                )

                if attempt < self.max_attempts:
                    # Calcular tempo de espera com backoff exponencial
                    wait_time = min(
                        self.backoff_factor ** (attempt - 1),
                        self.max_wait
                    )

                    self.logger.info(f"Aguardando {wait_time}s antes da próxima tentativa...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(
                        f"Todas as {self.max_attempts} tentativas falharam"
                    )

            except Exception as e:
                # Exceções não esperadas não devem triggerar retry
                self.logger.error(f"Erro não recuperável: {str(e)}")
                raise

        # Se chegou aqui, todas as tentativas falharam
        raise last_exception

    def execute_with_rate_limit_handling(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Executa uma função com tratamento especial de rate limiting

        Args:
            func: Função a ser executada
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados

        Returns:
            Resultado da função
        """
        return self.execute_with_retry(
            func,
            *args,
            retry_on=(RateLimitException, ConnectionError, Timeout),
            **kwargs
        )


# ========================================
# Funções Utilitárias
# ========================================

def calculate_backoff_time(attempt: int, base: float = 1.0, factor: float = 2.0, max_wait: int = 60) -> float:
    """
    Calcula tempo de espera com backoff exponencial

    Args:
        attempt: Número da tentativa atual
        base: Tempo base em segundos
        factor: Fator de multiplicação
        max_wait: Tempo máximo de espera

    Returns:
        Tempo de espera em segundos
    """
    wait_time = base * (factor ** (attempt - 1))
    return min(wait_time, max_wait)


def is_retriable_error(exception: Exception) -> bool:
    """
    Verifica se um erro é recuperável e deve triggerar retry

    Args:
        exception: Exceção a ser verificada

    Returns:
        True se deve fazer retry, False caso contrário
    """
    # Erros de rede são retriáveis
    if isinstance(exception, (ConnectionError, Timeout, RequestException)):
        return True

    # Rate limiting é retriável
    if isinstance(exception, RateLimitException):
        return True

    # Token expirado é retriável
    if isinstance(exception, TokenExpiredException):
        return True

    # Outros erros não são retriáveis por padrão
    return False


# ========================================
# Instância Global
# ========================================

# Gerenciador de retry padrão
default_retry_manager = RetryManager()


if __name__ == "__main__":
    """Testes do mecanismo de retry"""
    import random

    # Configurar logging para testes
    logging.basicConfig(level=logging.DEBUG)
    test_logger = logging.getLogger("test_retry")

    # Teste 1: Função que falha algumas vezes e depois sucede
    attempt_count = 0

    @retry_with_backoff(max_attempts=5, logger=test_logger)
    def flaky_function():
        global attempt_count
        attempt_count += 1

        if attempt_count < 3:
            raise ConnectionError(f"Falha na tentativa {attempt_count}")

        return f"Sucesso na tentativa {attempt_count}!"

    print("=== Teste 1: Função com falhas intermitentes ===")
    try:
        result = flaky_function()
        print(f"Resultado: {result}\n")
    except Exception as e:
        print(f"Erro: {e}\n")

    # Teste 2: Rate limiting
    @retry_on_rate_limit(max_attempts=3, base_wait=2, logger=test_logger)
    def rate_limited_function():
        if random.random() < 0.7:
            raise RateLimitException("Rate limit atingido")
        return "Requisição bem-sucedida!"

    print("=== Teste 2: Rate limiting ===")
    try:
        result = rate_limited_function()
        print(f"Resultado: {result}\n")
    except Exception as e:
        print(f"Erro: {e}\n")

    # Teste 3: Usando RetryManager
    print("=== Teste 3: RetryManager ===")
    retry_manager = RetryManager(max_attempts=3, backoff_factor=1.5, logger=test_logger)

    def sometimes_fails():
        if random.random() < 0.5:
            raise ValueError("Falha aleatória")
        return "Sucesso!"

    try:
        result = retry_manager.execute_with_retry(
            sometimes_fails,
            retry_on=(ValueError,)
        )
        print(f"Resultado: {result}\n")
    except Exception as e:
        print(f"Erro após todas as tentativas: {e}\n")

    # Teste 4: Backoff calculation
    print("=== Teste 4: Cálculo de backoff ===")
    for i in range(1, 6):
        wait_time = calculate_backoff_time(i, base=1.0, factor=2.0, max_wait=30)
        print(f"Tentativa {i}: aguardar {wait_time:.2f}s")

    print("\n✓ Testes de retry concluídos!")
