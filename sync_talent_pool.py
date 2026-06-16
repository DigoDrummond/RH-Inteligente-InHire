"""
Script para Sincronizar Talent Pool (Talentos SEM Candidaturas)

OBJETIVO:
    Sincronizar talentos que NAO possuem candidaturas (talent pool).

PROBLEMA:
    - Banco de dados: 61.915 talentos (todos COM candidaturas)
    - Pagina Inhire: 85.562 talentos
    - Divergencia: ~23.650 talentos SEM candidaturas (nunca sincronizados)

LIMITACAO CONHECIDA:
    A API /talents/paginated retorna apenas ~473 talentos (modificados recentemente).
    Este script sincroniza esses talentos, mas nao cobre os 23.650 restantes.

    Para 100% de cobertura, contactar suporte Inhire solicitando:
    - Endpoint que retorne TODOS os talentos do tenant
    - Ou parametro para incluir talentos sem candidaturas

QUANDO USAR:
    - Apos sync_full() ou sync incremental
    - 1x por semana para capturar novos talentos do pool
    - Quando detectar divergencia entre BD e pagina Inhire

TEMPO ESTIMADO: 2-3 minutos
COBERTURA: ~470 talentos do pool (~2% dos 23.650)

USO:
    python sync_talent_pool.py

Data: 2026-03-19
"""

import sys
import os
from pathlib import Path
import time

# Fix de encoding
os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ['TZ'] = 'America/Sao_Paulo'

# Adicionar root ao path
sys.path.insert(0, str(Path(__file__).parent))

from services.sync_service import SyncService
from services.api_client import InhireAPIClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from utils.logger import get_logger
from models.database import Candidatura, Talento
import traceback

logger = get_logger(__name__)


def print_banner():
    """Exibe banner informativo"""
    print()
    print("=" * 80)
    print("SINCRONIZACAO: TALENT POOL (Talentos SEM Candidaturas)")
    print("=" * 80)
    print()
    print("Este script sincroniza talentos que NAO tem candidaturas.")
    print()
    print("PROBLEMA IDENTIFICADO:")
    print("  - Banco de dados:  61.915 talentos (todos COM candidaturas)")
    print("  - Pagina Inhire:   85.562 talentos")
    print("  - Divergencia:     ~23.650 talentos SEM candidaturas")
    print()
    print("LIMITACAO DA API:")
    print("  - API /talents/paginated retorna apenas ~473 talentos")
    print("  - Sincroniza apenas talentos modificados recentemente")
    print("  - NAO cobre os ~23.650 talentos antigos do pool")
    print()
    print("COBERTURA ESPERADA:")
    print("  - ~470 talentos do pool (~2% dos 23.650)")
    print()
    print("TEMPO ESTIMADO: 2-3 minutos")
    print()
    print("=" * 80)
    print()


def main():
    print_banner()

    # Confirmacao
    try:
        confirm = input("Deseja continuar? (s/N): ").strip().lower()
        if confirm not in ['s', 'sim', 'y', 'yes']:
            print("\n[CANCEL] Sincronizacao cancelada pelo usuario.\n")
            return
    except (EOFError, KeyboardInterrupt):
        print("\n\n[CANCEL] Sincronizacao cancelada.\n")
        return

    print()
    print("[>>>] Iniciando sincronizacao...\n")

    # Criar engine e session
    logger.info("Conectando ao banco de dados...")
    print("[INFO] Conectando ao banco de dados...")

    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    start_time = time.time()

    try:
        # STEP 1: Buscar IDs de talentos que JA TEM candidaturas
        print()
        print("[STEP 1] Identificando talentos com candidaturas...")

        # Query mais rapida: distinct talent_inhire_id
        result = session.query(Candidatura.talent_inhire_id).distinct().all()
        talent_ids_with_apps = {row[0] for row in result if row[0]}

        print(f"   Total de talentos COM candidaturas: {len(talent_ids_with_apps):,}")
        logger.info(f"Talentos com candidaturas: {len(talent_ids_with_apps):,}")

        # STEP 2: Buscar total atual no BD
        print()
        print("[STEP 2] Contando talentos no banco...")
        count_before = session.query(Talento).count()
        print(f"   Total no BD: {count_before:,} talentos")
        logger.info(f"Talentos no BD ANTES: {count_before:,}")

        # STEP 3: Buscar TODOS da API (retorna ~473)
        print()
        print("[STEP 3] Buscando talentos da API...")
        print("   (Isso pode demorar 1-2 minutos)")
        print()

        api_client = InhireAPIClient()

        talentos_pool = []
        all_from_api = []

        for talento in api_client.get_all_talentos():
            all_from_api.append(talento.id)

            # Filtrar apenas SEM candidaturas
            if talento.id not in talent_ids_with_apps:
                talentos_pool.append(talento)

        print(f"   Total retornado pela API: {len(all_from_api)}")
        print(f"   Talentos SEM candidaturas: {len(talentos_pool)}")

        logger.info(f"API retornou: {len(all_from_api)} talentos")
        logger.info(f"Talentos sem candidaturas: {len(talentos_pool)}")

        # STEP 4: Verificar se ha algo a sincronizar
        if len(talentos_pool) == 0:
            print()
            print("=" * 80)
            print("[OK] NENHUM TALENTO NOVO NO POOL")
            print("=" * 80)
            print()
            print("Todos os talentos retornados pela API ja estao no banco.")
            print("Isso significa que:")
            print("  - Talentos recentes do pool ja foram sincronizados")
            print("  - OU a API nao esta retornando talentos sem candidaturas")
            print()
            print("Os ~23.650 talentos restantes provavelmente sao antigos e")
            print("nao sao retornados pela API /talents/paginated.")
            print()
            print("Para sincronizar TODOS, contactar suporte Inhire.")
            print()
            return

        # STEP 5: Sincronizar
        print()
        print(f"[STEP 4] Sincronizando {len(talentos_pool)} talentos do pool...")

        sync_service = SyncService(session)
        db_service = sync_service.db

        created = 0
        updated = 0
        failed = 0

        for i, talento in enumerate(talentos_pool, 1):
            try:
                result = db_service.upsert_talento(talento)
                if result == 'created':
                    created += 1
                elif result == 'updated':
                    updated += 1

                # Log a cada 50
                if i % 50 == 0:
                    print(f"   ... {i}/{len(talentos_pool)} processados")

            except Exception as e:
                failed += 1
                logger.error(f"Erro ao sincronizar {talento.id}: {e}")

        session.commit()

        # STEP 6: Verificar estado final
        print()
        print("[INFO] Verificando resultado...")
        count_after = session.query(Talento).count()
        diff = count_after - count_before

        elapsed = time.time() - start_time
        elapsed_min = elapsed / 60

        # RESULTADO FINAL
        print()
        print("=" * 80)
        print("RESULTADO DA SINCRONIZACAO")
        print("=" * 80)
        print()
        print(f"[TIME]  Tempo total: {elapsed:.1f}s ({elapsed_min:.2f} min)")
        print()
        print(f"[INFO] Talentos no banco:")
        print(f"   Antes:  {count_before:,}")
        print(f"   Depois: {count_after:,}")

        if diff > 0:
            print(f"   [+] Novos: {diff:,} talentos")
        elif diff < 0:
            print(f"   [-] Removidos: {abs(diff):,} talentos (inesperado!)")
        else:
            print(f"   [OK] Sem mudancas")

        print()
        print(f"[STAT] Estatisticas:")
        print(f"   Candidatos no pool: {len(talentos_pool)}")
        print(f"   Criados:            {created}")
        print(f"   Atualizados:        {updated}")
        print(f"   Falhados:           {failed}")
        print()

        # Analise
        if created > 0:
            print(f"[SUCCESS] {created} novos talentos do pool foram adicionados!")
            print()
            print("IMPORTANTE:")
            print(f"  - Ainda faltam ~{23650 - created:,} talentos do pool")
            print("  - A API /talents/paginated tem limitacao conhecida")
            print("  - Contactar suporte Inhire para sincronizar 100%")
            print()
        elif updated > 0:
            print(f"[OK] {updated} talentos do pool foram atualizados.")
            print()
        else:
            print("[INFO] Nenhum talento novo ou atualizado.")
            print()
            print("Isso pode significar:")
            print("  - Talentos do pool ja foram sincronizados anteriormente")
            print("  - API nao retorna talentos sem candidaturas")
            print()

        if failed > 0:
            print(f"[WARN] {failed} falhas durante sincronizacao.")
            print("   Verifique os logs: tail -f logs/inhire_sync.log")
            print()

        print("=" * 80)
        print()

        logger.info(f"Sincronizacao concluida: {created} criados, {updated} atualizados, {failed} falhas")

    except KeyboardInterrupt:
        print("\n\n[WARN] Sincronizacao interrompida pelo usuario.\n")
        logger.warning("Sincronizacao interrompida pelo usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro durante sincronizacao: {str(e)}", exc_info=True)
        print()
        print("=" * 80)
        print("[ERROR] ERRO DURANTE SINCRONIZACAO")
        print("=" * 80)
        print()
        print(f"Erro: {str(e)}")
        print()
        print("Stack trace:")
        traceback.print_exc()
        print()
        print("Verifique os logs para mais detalhes:")
        print("  tail -f logs/inhire_sync.log")
        print()
        sys.exit(1)
    finally:
        session.close()
        logger.info("Conexao com banco encerrada")


if __name__ == "__main__":
    main()
