"""
Sistema de métricas de performance usando Prometheus
Fornece observabilidade detalhada do sistema de sincronização
"""
from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
from functools import wraps
import time
from typing import Callable
from utils.logger import get_logger

logger = get_logger(__name__)


# ========================================
# Métricas de Sincronização
# ========================================

# Contadores de registros processados
sync_records_total = Counter(
    'inhire_sync_records_total',
    'Total de registros processados na sincronização',
    ['entity', 'operation']  # Labels: entity (vaga, talento, etc), operation (created, updated, skipped, failed)
)

# Tempo de execução de sincronizações
sync_duration_seconds = Histogram(
    'inhire_sync_duration_seconds',
    'Duração das sincronizações em segundos',
    ['entity', 'sync_type'],  # Labels: entity, sync_type (full, incremental, manual)
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600]  # Buckets de 1s até 1h
)

# Contador de sincronizações
sync_executions_total = Counter(
    'inhire_sync_executions_total',
    'Total de execuções de sincronização',
    ['entity', 'sync_type', 'status']  # Labels: entity, sync_type, status (success, error, partial)
)

# Gauge de registros no banco
database_records_count = Gauge(
    'inhire_database_records_count',
    'Número atual de registros no banco',
    ['entity']  # Labels: entity
)


# ========================================
# Métricas de API
# ========================================

# Contador de chamadas à API
api_requests_total = Counter(
    'inhire_api_requests_total',
    'Total de requisições à API Inhire',
    ['endpoint', 'method', 'status_code']
)

# Tempo de resposta da API
api_request_duration_seconds = Histogram(
    'inhire_api_request_duration_seconds',
    'Duração das requisições à API em segundos',
    ['endpoint', 'method'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30]
)

# Contador de erros da API
api_errors_total = Counter(
    'inhire_api_errors_total',
    'Total de erros nas requisições à API',
    ['endpoint', 'error_type']
)


# ========================================
# Métricas de Autenticação
# ========================================

# Contador de autenticações
auth_attempts_total = Counter(
    'inhire_auth_attempts_total',
    'Total de tentativas de autenticação',
    ['result']  # Labels: result (success, failure)
)

# Contador de refresh de tokens
token_refresh_total = Counter(
    'inhire_token_refresh_total',
    'Total de refreshes de token',
    ['result']
)


# ========================================
# Métricas de Banco de Dados
# ========================================

# Tempo de operações no banco
database_operation_duration_seconds = Histogram(
    'inhire_database_operation_duration_seconds',
    'Duração das operações de banco em segundos',
    ['operation'],  # Labels: operation (upsert_vaga, upsert_talento, etc)
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5]
)

# Contador de erros de banco
database_errors_total = Counter(
    'inhire_database_errors_total',
    'Total de erros nas operações de banco',
    ['operation', 'error_type']
)


# ========================================
# Métricas de Candidatos Declined
# ========================================

declined_candidates_total = Gauge(
    'inhire_declined_candidates_total',
    'Total de candidatos com status declined'
)

declined_rate_by_job = Gauge(
    'inhire_declined_rate_by_job',
    'Taxa de declínio por vaga',
    ['job_id', 'job_name']
)


# ========================================
# Informações do Sistema
# ========================================

system_info = Info(
    'inhire_sync_system',
    'Informações sobre o sistema de sincronização'
)


# ========================================
# Decoradores para Métricas
# ========================================

def track_sync_duration(entity: str, sync_type: str):
    """
    Decorator para rastrear duração de sincronizações

    Args:
        entity: Nome da entidade (vaga, talento, etc)
        sync_type: Tipo de sincronização (full, incremental, manual)

    Example:
        @track_sync_duration('vaga', 'full')
        def sync_vagas():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                sync_duration_seconds.labels(entity=entity, sync_type=sync_type).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                sync_duration_seconds.labels(entity=entity, sync_type=sync_type).observe(duration)
                raise
        return wrapper
    return decorator


def track_api_request(endpoint: str, method: str):
    """
    Decorator para rastrear requisições à API

    Args:
        endpoint: Nome do endpoint
        method: Método HTTP (GET, POST, etc)

    Example:
        @track_api_request('/jobs', 'POST')
        def get_jobs():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = None
            try:
                result = func(*args, **kwargs)
                status_code = 200
                api_requests_total.labels(
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code
                ).inc()
                duration = time.time() - start_time
                api_request_duration_seconds.labels(endpoint=endpoint, method=method).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                api_request_duration_seconds.labels(endpoint=endpoint, method=method).observe(duration)
                api_errors_total.labels(endpoint=endpoint, error_type=type(e).__name__).inc()
                raise
        return wrapper
    return decorator


def track_database_operation(operation: str):
    """
    Decorator para rastrear operações de banco

    Args:
        operation: Nome da operação (upsert_vaga, etc)

    Example:
        @track_database_operation('upsert_vaga')
        def upsert_vaga(data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                database_operation_duration_seconds.labels(operation=operation).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                database_operation_duration_seconds.labels(operation=operation).observe(duration)
                database_errors_total.labels(operation=operation, error_type=type(e).__name__).inc()
                raise
        return wrapper
    return decorator


# ========================================
# Funções Auxiliares
# ========================================

def record_sync_stats(entity: str, stats: dict):
    """
    Registra estatísticas de sincronização nas métricas

    Args:
        entity: Nome da entidade
        stats: Dicionário com estatísticas (processed, created, updated, skipped, failed)
    """
    sync_records_total.labels(entity=entity, operation='created').inc(stats.get('created', 0))
    sync_records_total.labels(entity=entity, operation='updated').inc(stats.get('updated', 0))
    sync_records_total.labels(entity=entity, operation='skipped').inc(stats.get('skipped', 0))
    sync_records_total.labels(entity=entity, operation='failed').inc(stats.get('failed', 0))


def record_sync_execution(entity: str, sync_type: str, status: str):
    """
    Registra execução de sincronização

    Args:
        entity: Nome da entidade
        sync_type: Tipo de sincronização
        status: Status da execução (success, error, partial)
    """
    sync_executions_total.labels(entity=entity, sync_type=sync_type, status=status).inc()


def update_database_counts(session):
    """
    Atualiza contadores de registros no banco

    Args:
        session: Sessão SQLAlchemy
    """
    from models.database import Vaga, Posicao, Candidatura, Talento

    try:
        database_records_count.labels(entity='vaga').set(session.query(Vaga).count())
        database_records_count.labels(entity='posicao').set(session.query(Posicao).count())
        database_records_count.labels(entity='candidatura').set(session.query(Candidatura).count())
        database_records_count.labels(entity='talento').set(session.query(Talento).count())
    except Exception as e:
        logger.error(f"Erro ao atualizar contadores de banco: {str(e)}")


def update_declined_metrics(session):
    """
    Atualiza métricas de candidatos declined

    Args:
        session: Sessão SQLAlchemy
    """
    from models.database import Candidatura, Vaga, CandidaturaStatusEnum
    from sqlalchemy import func

    try:
        # Total de declined
        total_declined = session.query(Candidatura).filter(
            Candidatura.status == CandidaturaStatusEnum.DECLINED
        ).count()
        declined_candidates_total.set(total_declined)

        # Taxa por vaga
        rates = (
            session.query(
                Vaga.inhire_id,
                Vaga.name,
                func.count(Candidatura.id).label('total'),
                func.sum(
                    (Candidatura.status == CandidaturaStatusEnum.DECLINED).cast(int)
                ).label('declined')
            )
            .join(Candidatura, Candidatura.vaga_id == Vaga.id)
            .group_by(Vaga.id, Vaga.inhire_id, Vaga.name)
            .all()
        )

        for rate in rates:
            if rate.total > 0:
                decline_rate = (rate.declined or 0) / rate.total * 100
                declined_rate_by_job.labels(
                    job_id=rate.inhire_id,
                    job_name=rate.name
                ).set(decline_rate)

    except Exception as e:
        logger.error(f"Erro ao atualizar métricas de declined: {str(e)}")


def set_system_info(version: str, environment: str, tenant: str):
    """
    Define informações do sistema

    Args:
        version: Versão do sistema
        environment: Ambiente (dev, staging, production)
        tenant: ID do tenant
    """
    system_info.info({
        'version': version,
        'environment': environment,
        'tenant': tenant
    })


def start_metrics_server(port: int = 8000):
    """
    Inicia servidor HTTP para exposição de métricas Prometheus

    Args:
        port: Porta para o servidor (padrão: 8000)
    """
    try:
        start_http_server(port)
        logger.info(f"Servidor de métricas iniciado na porta {port}")
        logger.info(f"Métricas disponíveis em: http://localhost:{port}/metrics")
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor de métricas: {str(e)}")
        raise


# ========================================
# Classe para Contexto de Métricas
# ========================================

class MetricsContext:
    """
    Context manager para rastreamento automático de métricas

    Example:
        with MetricsContext('vaga', 'full') as ctx:
            # Código de sincronização
            ctx.record_stats({'created': 10, 'updated': 5})
    """

    def __init__(self, entity: str, sync_type: str):
        self.entity = entity
        self.sync_type = sync_type
        self.start_time = None
        self.status = 'success'

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        if exc_type is not None:
            self.status = 'error'

        sync_duration_seconds.labels(
            entity=self.entity,
            sync_type=self.sync_type
        ).observe(duration)

        sync_executions_total.labels(
            entity=self.entity,
            sync_type=self.sync_type,
            status=self.status
        ).inc()

        return False  # Propagar exceções

    def record_stats(self, stats: dict):
        """Registra estatísticas durante a execução"""
        record_sync_stats(self.entity, stats)

    def set_partial(self):
        """Marca sincronização como parcial"""
        self.status = 'partial'
