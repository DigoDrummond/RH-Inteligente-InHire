"""
Sistema de logs estruturados para o sistema de sincronização Inhire
Suporta logs em JSON e texto, com rotação de arquivos
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
from pythonjsonlogger import jsonlogger
from logging.handlers import RotatingFileHandler
from config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Formatter customizado para logs em JSON"""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # Adicionar timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()

        # Adicionar nível de log
        log_record['level'] = record.levelname

        # Adicionar nome do logger
        log_record['logger'] = record.name

        # Adicionar informações do processo
        log_record['pid'] = os.getpid()

        # Adicionar ambiente
        log_record['environment'] = settings.ENVIRONMENT

        # Remover campos redundantes se existirem
        for field in ['levelname', 'name', 'processName']:
            log_record.pop(field, None)


class ColoredFormatter(logging.Formatter):
    """Formatter com cores para console"""

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Formatar a mensagem
        record.levelname = f"{log_color}{record.levelname}{reset}"
        return super().format(record)


def setup_logging(
    name: str = "inhire_sync",
    level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configura sistema de logging

    Args:
        name: Nome do logger
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Formato de log ('json' ou 'text')
        log_file: Caminho do arquivo de log

    Returns:
        Logger configurado
    """
    # Usar configurações padrão se não fornecidas
    level = level or settings.LOG_LEVEL
    log_format = log_format or settings.LOG_FORMAT
    log_file = log_file or settings.LOG_FILE_PATH if settings.LOG_FILE_ENABLED else None

    # Criar logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remover handlers existentes para evitar duplicação
    logger.handlers = []

    # ========================================
    # Handler para Console
    # ========================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    if log_format == "json":
        console_formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(logger)s %(message)s'
        )
    else:
        # Formato texto com cores
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # ========================================
    # Handler para Arquivo (com rotação)
    # ========================================
    if log_file:
        # Criar diretório de logs se não existir
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=settings.LOG_FILE_MAX_BYTES,
            backupCount=settings.LOG_FILE_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level.upper()))

        if log_format == "json":
            file_formatter = CustomJsonFormatter(
                '%(timestamp)s %(level)s %(logger)s %(message)s'
            )
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Evitar propagação para o logger raiz
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado

    Args:
        name: Nome do logger (geralmente __name__ do módulo)

    Returns:
        Logger configurado
    """
    # Se o logger já existe e está configurado, retornar
    logger = logging.getLogger(name)

    # Se não tem handlers, configurar
    if not logger.handlers:
        return setup_logging(name)

    return logger


# ========================================
# Funções de Conveniência
# ========================================

def log_sync_start(logger: logging.Logger, sync_type: str, entity: str, tenant_id: str = None):
    """Log de início de sincronização"""
    extra = {
        'sync_type': sync_type,
        'entity': entity,
        'tenant_id': tenant_id or settings.INHIRE_TENANT,
        'event': 'sync_start'
    }
    logger.info(
        f"Iniciando sincronização {sync_type} de {entity}",
        extra=extra
    )


def log_sync_end(
    logger: logging.Logger,
    sync_type: str,
    entity: str,
    status: str,
    stats: dict,
    duration_ms: int = None,
    tenant_id: str = None
):
    """Log de fim de sincronização"""
    extra = {
        'sync_type': sync_type,
        'entity': entity,
        'status': status,
        'tenant_id': tenant_id or settings.INHIRE_TENANT,
        'event': 'sync_end',
        'duration_ms': duration_ms,
        **stats
    }

    if status == "SUCCESS":
        logger.info(
            f"Sincronização {sync_type} de {entity} concluída com sucesso",
            extra=extra
        )
    elif status == "PARTIAL":
        logger.warning(
            f"Sincronização {sync_type} de {entity} concluída parcialmente",
            extra=extra
        )
    else:
        logger.error(
            f"Sincronização {sync_type} de {entity} falhou",
            extra=extra
        )


def log_api_request(
    logger: logging.Logger,
    method: str,
    url: str,
    status_code: int = None,
    duration_ms: int = None,
    error: str = None
):
    """Log de requisição à API"""
    extra = {
        'event': 'api_request',
        'method': method,
        'url': url,
        'status_code': status_code,
        'duration_ms': duration_ms
    }

    if error:
        extra['error'] = error
        logger.error(f"Erro na requisição {method} {url}: {error}", extra=extra)
    elif status_code and status_code >= 400:
        logger.warning(f"Requisição {method} {url} retornou {status_code}", extra=extra)
    else:
        logger.debug(f"Requisição {method} {url} concluída", extra=extra)


def log_database_operation(
    logger: logging.Logger,
    operation: str,
    table: str,
    records: int = 1,
    error: str = None
):
    """Log de operação no banco de dados"""
    extra = {
        'event': 'database_operation',
        'operation': operation,
        'table': table,
        'records': records
    }

    if error:
        extra['error'] = error
        logger.error(f"Erro na operação {operation} em {table}: {error}", extra=extra)
    else:
        logger.debug(f"Operação {operation} em {table}: {records} registros", extra=extra)


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: dict = None
):
    """Log de erro com contexto adicional"""
    extra = {
        'event': 'error',
        'error_type': type(error).__name__,
        'error_message': str(error)
    }

    if context:
        extra.update(context)

    logger.error(
        f"Erro: {str(error)}",
        extra=extra,
        exc_info=True  # Incluir stack trace
    )


# ========================================
# Logger Global
# ========================================

# Criar logger principal do sistema
main_logger = setup_logging("inhire_sync")


if __name__ == "__main__":
    """Teste do sistema de logging"""

    # Configurar logger de teste
    test_logger = setup_logging("test", level="DEBUG")

    # Testar diferentes níveis
    test_logger.debug("Mensagem de DEBUG")
    test_logger.info("Mensagem de INFO")
    test_logger.warning("Mensagem de WARNING")
    test_logger.error("Mensagem de ERROR")
    test_logger.critical("Mensagem de CRITICAL")

    # Testar funções de conveniência
    log_sync_start(test_logger, "FULL", "VAGAS", "test-tenant")

    log_sync_end(
        test_logger,
        "FULL",
        "VAGAS",
        "SUCCESS",
        {"processed": 100, "created": 50, "updated": 30, "skipped": 20},
        duration_ms=5000,
        tenant_id="test-tenant"
    )

    log_api_request(
        test_logger,
        "POST",
        "https://api.inhire.app/jobs/paginated/lean",
        status_code=200,
        duration_ms=1500
    )

    log_database_operation(
        test_logger,
        "INSERT",
        "vagas",
        records=50
    )

    # Testar log de erro
    try:
        raise ValueError("Erro de teste")
    except Exception as e:
        log_error_with_context(
            test_logger,
            e,
            context={"operation": "test", "data": "exemplo"}
        )

    print("\n✓ Testes de logging concluídos!")
