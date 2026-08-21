"""
Re-sincronizar APENAS as requisições com a nova lógica de dados completos
"""
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.sync_service import SyncService
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    try:
        print("=" * 100)
        print("RE-SINCRONIZACAO DE REQUISICOES COM DADOS COMPLETOS")
        print("=" * 100)

        # Criar engine e session
        engine = create_engine(
            f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@"
            f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Inicializar sync service
            sync_service = SyncService(session)

            print("\n>>> Iniciando sincronização de requisições...")
            print("Estratégia:")
            print("  1. Buscar lista de requisições via endpoint paginado (rápido)")
            print("  2. Para CADA requisição, buscar dados completos via /requisitions/{id}")
            print("  3. Salvar com name, description, positions, approvalWorkflow, etc.")
            print()

            # Sincronizar requisições
            stats = sync_service._sync_requisicoes()

            print("\n" + "=" * 100)
            print("RESULTADO DA SINCRONIZACAO")
            print("=" * 100)
            print(f"Total processado:  {stats['processed']}")
            print(f"Criadas:           {stats['created']}")
            print(f"Atualizadas:       {stats['updated']}")
            print(f"Ignoradas:         {stats['skipped']}")
            print(f"Falharam:          {stats['failed']}")
            print(f"Enriquecidas:      {stats.get('enriched', 0)}")

            session.close()

            print("\n" + "=" * 100)
            print("SINCRONIZACAO CONCLUIDA COM SUCESSO!")
            print("=" * 100)

        except Exception as e:
            session.rollback()
            session.close()
            raise e

    except Exception as e:
        logger.error(f"ERRO na sincronização: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
