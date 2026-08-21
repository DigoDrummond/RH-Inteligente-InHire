"""
Servidor de Métricas Prometheus
Expõe métricas do sistema de sincronização para coleta pelo Prometheus
"""
import sys
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from utils.metrics import (
    start_metrics_server,
    set_system_info,
    update_database_counts,
    update_declined_metrics
)
from utils.advanced_metrics import collect_all_advanced_metrics
from utils.logger import get_logger, setup_logging


def main():
    """Inicia servidor de métricas e atualiza periodicamente"""
    setup_logging()
    logger = get_logger(__name__)

    # Porta configurável via variável de ambiente
    port = getattr(settings, 'METRICS_PORT', 8000)

    print("=" * 70)
    print("SERVIDOR DE MÉTRICAS PROMETHEUS")
    print("=" * 70)
    print(f"\nPorta: {port}")
    print(f"Endpoint: http://localhost:{port}/metrics")
    print(f"Tenant: {settings.INHIRE_TENANT}")
    print(f"Ambiente: {settings.ENVIRONMENT}")
    print("\nPressione Ctrl+C para parar")
    print("=" * 70)

    try:
        # Iniciar servidor HTTP
        start_metrics_server(port)
        logger.info("Servidor de métricas iniciado com sucesso")

        # Definir informações do sistema
        set_system_info(
            version='1.0.0',
            environment=settings.ENVIRONMENT,
            tenant=settings.INHIRE_TENANT
        )

        # Conectar ao banco para atualizar métricas
        db_url = (
            f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
        engine = create_engine(db_url, echo=False, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=engine)

        # Loop de atualização de métricas
        update_interval_basic = 30      # Métricas básicas a cada 30s
        update_interval_advanced = 120  # Métricas avançadas a cada 2min
        last_advanced_update = 0

        print(f"\nAtualizando métricas básicas a cada {update_interval_basic}s")
        print(f"Atualizando métricas avançadas a cada {update_interval_advanced}s")

        while True:
            try:
                session = SessionLocal()
                current_time = time.time()

                # Atualizar métricas básicas (sempre)
                update_database_counts(session)
                update_declined_metrics(session)

                # Atualizar métricas avançadas (periodicamente)
                if current_time - last_advanced_update >= update_interval_advanced:
                    logger.info("Coletando métricas avançadas...")
                    collect_all_advanced_metrics(session)
                    last_advanced_update = current_time

                session.close()

                logger.debug(f"Métricas atualizadas com sucesso")

            except Exception as e:
                logger.error(f"Erro ao atualizar métricas: {str(e)}", exc_info=True)

            # Aguardar próxima atualização
            time.sleep(update_interval_basic)

    except KeyboardInterrupt:
        print("\n\nServidor de métricas interrompido pelo usuário")
        logger.info("Servidor de métricas finalizado")
        return 0

    except Exception as e:
        logger.error(f"Erro fatal no servidor de métricas: {str(e)}", exc_info=True)
        print(f"\n❌ ERRO: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
