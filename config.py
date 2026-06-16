"""
Configurações do Sistema de Sincronização Inhire
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações centralizadas do sistema"""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    # ========================================
    # Configurações da API Inhire
    # ========================================
    INHIRE_BASE_URL: str = "https://api.inhire.app/"
    INHIRE_AUTH_URL: str = "https://auth.inhire.app/"
    INHIRE_EMAIL: str = ""  # Configurar no .env
    INHIRE_PASSWORD: str = ""  # Configurar no .env
    INHIRE_TENANT: str = ""  # Configurar no .env

    # Timeouts (em segundos)
    INHIRE_TIMEOUT_CONNECT: int = 15
    INHIRE_TIMEOUT_READ: int = 45
    INHIRE_TIMEOUT_WRITE: int = 45
    INHIRE_TIMEOUT_TOTAL: int = 90

    # Timeouts estendidos para sincronização incremental completa
    SYNC_INCREMENTAL_TIMEOUT_CONNECT: int = 30
    SYNC_INCREMENTAL_TIMEOUT_READ: int = 120  # 2 minutos para endpoints pesados
    SYNC_INCREMENTAL_TIMEOUT_TOTAL: int = 180  # 3 minutos total

    # Rate Limiting
    INHIRE_MAX_REQUESTS_PER_MINUTE: int = 1000
    INHIRE_RETRY_ATTEMPTS: int = 3
    INHIRE_RETRY_BACKOFF_FACTOR: float = 2.0

    # ========================================
    # Configurações do Banco de Dados PostgreSQL
    # ========================================
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "inhire_sync"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_SCHEMA: str = "public"

    # Pool de conexões
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # SSL
    DB_SSL_MODE: str = "prefer"  # disable, allow, prefer, require

    @property
    def DATABASE_URL(self) -> str:
        """Gera URL de conexão do banco de dados"""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?client_encoding=utf8"
        )

    # ========================================
    # Configurações de Sincronização
    # ========================================

    # Habilitar/Desabilitar Sincronização
    SYNC_ENABLED: bool = True
    SYNC_VAGAS_ENABLED: bool = True
    SYNC_POSICOES_ENABLED: bool = True
    SYNC_CANDIDATURAS_ENABLED: bool = True
    SYNC_TALENTOS_ENABLED: bool = True

    # Frequências de Sincronização
    SYNC_INCREMENTAL_FREQUENCY_MINUTES: int = 60  # 1 hora
    SYNC_FULL_FREQUENCY_HOURS: int = 24  # 1 dia

    # Paginação
    SYNC_BATCH_SIZE: int = 50  # Registros por página
    SYNC_MAX_PAGES: Optional[int] = None  # None = sem limite

    # Controle de Concorrência
    SYNC_MAX_CONCURRENT_SYNCS: int = 3
    SYNC_MAX_WORKERS: int = 5

    # Configurações específicas para Sincronização Incremental Completa
    SYNC_INCREMENTAL_COMMIT_BATCH: int = 50  # Commit a cada N registros (evita timeout BD)
    SYNC_INCREMENTAL_LOG_PROGRESS_EVERY: int = 100  # Log de progresso a cada N registros
    SYNC_INCREMENTAL_FAIL_ON_ERROR: bool = True  # Interromper em caso de erro crítico
    SYNC_INCREMENTAL_VALIDATE_INTEGRITY: bool = True  # Validar integridade pós-sync
    SYNC_INCREMENTAL_MAX_ERRORS_PER_ENTITY: int = 5  # Máximo de erros por entidade antes de parar

    # ========================================
    # Otimizações de Timeline (08/01/2026)
    # ========================================

    # Fallback para primeira sincronização (quando não há timeline no BD)
    # Após primeira sync, o sistema usa a última data de sincronização automaticamente
    TIMELINE_DAYS_LOOKBACK: int = 30  # Dias para buscar candidaturas (fallback)

    # Threads paralelas para processamento de timeline (10x mais rápido)
    # Recomendado: 10 threads para balance entre performance e carga no servidor
    # Valores válidos: 5-20 (ajustar conforme CPU disponível)
    TIMELINE_MAX_WORKERS: int = 10  # Threads paralelas (10x mais rápido)

    # ========================================
    # Configurações do Scheduler
    # ========================================
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_TIMEZONE: str = "America/Sao_Paulo"

    # Horário da sincronização completa diária (cron)
    SCHEDULER_FULL_SYNC_HOUR: int = 2  # 02:00 AM
    SCHEDULER_FULL_SYNC_MINUTE: int = 0

    # ========================================
    # Configurações de Logging
    # ========================================
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "json"  # json, text
    LOG_FILE_ENABLED: bool = True
    LOG_FILE_PATH: str = "logs/inhire_sync.log"
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
    LOG_FILE_BACKUP_COUNT: int = 5

    # ========================================
    # Configurações de Notificações
    # ========================================
    NOTIFICATIONS_ENABLED: bool = False
    NOTIFICATION_EMAIL: Optional[str] = None
    NOTIFICATION_WEBHOOK_URL: Optional[str] = None

    # ========================================
    # Ambiente
    # ========================================
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False

    # ========================================
    # Configurações de Métricas (Prometheus)
    # ========================================
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 8000
    METRICS_UPDATE_INTERVAL_SECONDS: int = 30

    @property
    def is_production(self) -> bool:
        """Verifica se está em produção"""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Verifica se está em desenvolvimento"""
        return self.ENVIRONMENT.lower() == "development"


# Instância global de configurações
settings = Settings()


# ========================================
# Constantes do Sistema
# ========================================

class SyncType:
    """Tipos de sincronização"""
    FULL = "FULL"
    INCREMENTAL = "INCREMENTAL"
    EXPRESS = "EXPRESS"
    MANUAL = "MANUAL"


class SyncStatus:
    """Status de sincronização"""
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    PARTIAL = "PARTIAL"


class SyncEntity:
    """Entidades sincronizáveis"""
    VAGA = "VAGA"
    POSICAO = "POSICAO"
    CANDIDATURA = "CANDIDATURA"
    TALENTO = "TALENTO"
    ALL = "ALL"


class InhireEndpoints:
    """Endpoints da API Inhire"""

    # Autenticação
    LOGIN = "/login"
    REFRESH = "/refresh"

    # Vagas
    JOBS_PAGINATED_LEAN = "/jobs/paginated/lean"
    JOB_BY_ID = "/jobs/{job_id}"

    # Posições
    POSITIONS_PAGINATED = "/jobs/positions/paginated/{job_id}"  # Lista posições da vaga + histórico de status

    # Candidaturas
    APPLICATIONS_PAGINATED = "/job-talents/{job_id}/talents/paginated/lean"

    # Talentos
    TALENTS_PAGINATED = "/talents/paginated"
    TALENT_BY_ID = "/talents/{talent_id}"

    # Requisições
    REQUISITIONS_PAGINATED = "/requisitions/paginated"  # NOVO: endpoint paginado
    REQUISITIONS_BY_JOB = "/requisitions/job/{job_id}"


# ========================================
# Headers HTTP Padrão
# ========================================

def get_default_headers(token: Optional[str] = None, tenant: Optional[str] = None) -> dict:
    """Retorna headers HTTP padrão para requisições"""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Tenant": tenant or settings.INHIRE_TENANT
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


# ========================================
# Validações de Inicialização
# ========================================

def validate_settings() -> bool:
    """Valida configurações essenciais"""
    errors = []

    # Validar credenciais Inhire
    if not settings.INHIRE_EMAIL or not settings.INHIRE_PASSWORD:
        errors.append("Credenciais Inhire não configuradas (INHIRE_EMAIL, INHIRE_PASSWORD)")

    # Validar conexão banco
    if not all([settings.DB_HOST, settings.DB_NAME, settings.DB_USER, settings.DB_PASSWORD]):
        errors.append("Configurações de banco de dados incompletas")

    # Validar frequências
    if settings.SYNC_INCREMENTAL_FREQUENCY_MINUTES <= 0:
        errors.append("SYNC_INCREMENTAL_FREQUENCY_MINUTES deve ser maior que 0")

    if settings.SYNC_FULL_FREQUENCY_HOURS <= 0:
        errors.append("SYNC_FULL_FREQUENCY_HOURS deve ser maior que 0")

    # Validar batch size
    if settings.SYNC_BATCH_SIZE < 1 or settings.SYNC_BATCH_SIZE > 200:
        errors.append("SYNC_BATCH_SIZE deve estar entre 1 e 200")

    if errors:
        for error in errors:
            print(f"[ERRO DE CONFIGURAÇÃO] {error}")
        return False

    return True


if __name__ == "__main__":
    """Testa configurações"""
    print("=== Configurações do Sistema ===\n")
    print(f"Ambiente: {settings.ENVIRONMENT}")
    print(f"Debug: {settings.DEBUG}")
    print(f"\n=== API Inhire ===")
    print(f"Base URL: {settings.INHIRE_BASE_URL}")
    print(f"Tenant: {settings.INHIRE_TENANT}")
    print(f"Email: {settings.INHIRE_EMAIL}")
    print(f"\n=== Banco de Dados ===")
    print(f"Host: {settings.DB_HOST}:{settings.DB_PORT}")
    print(f"Database: {settings.DB_NAME}")
    print(f"Schema: {settings.DB_SCHEMA}")
    print(f"\n=== Sincronização ===")
    print(f"Habilitada: {settings.SYNC_ENABLED}")
    print(f"Batch Size: {settings.SYNC_BATCH_SIZE}")
    print(f"Freq. Incremental: {settings.SYNC_INCREMENTAL_FREQUENCY_MINUTES} min")
    print(f"Freq. Completa: {settings.SYNC_FULL_FREQUENCY_HOURS} horas")
    print(f"\n=== Validação ===")
    if validate_settings():
        print("✓ Configurações válidas!")
    else:
        print("✗ Configurações inválidas!")
