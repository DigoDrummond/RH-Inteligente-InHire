"""
Script para Sincronizar TODOS os Talentos da API Inhire

OBJETIVO:
    Sincronizar 100% dos talentos retornados pela API, incluindo:
    - Talentos COM candidaturas
    - Talentos SEM candidaturas (talent pool)

DIFERENÇA DO sync_full():
    - sync_full() sincroniza apenas talentos COM candidaturas (~61k)
    - Este script força sync de TODOS retornados pela API (~473-500)

LIMITAÇÃO DA API:
    A API /talents/paginated retorna apenas ~473-500 talentos (modificados recentemente).
    Mesmo este script não conseguirá sincronizar os 94.612 talentos totais.

    Para 100% de cobertura, contactar suporte Inhire solicitando:
    - Endpoint que retorne TODOS os talentos do tenant
    - Ou parâmetro para incluir talentos antigos/inativos

QUANDO USAR:
    - Após sync_full() regular
    - Para capturar talentos do pool retornados pela API
    - 1x por semana como manutenção

TEMPO ESTIMADO: 2-5 minutos
COBERTURA: ~473-500 talentos da API (não 94.612 totais)

USO:
    python sync_all_talentos.py

Data: 2026-06-23
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
from models.database import Talento
import traceback

logger = get_logger(__name__)


def print_banner():
    """Exibe banner informativo"""
    print()
    print("=" * 80)
    print("SINCRONIZAÇÃO: TODOS OS TALENTOS DA API")
    print("=" * 80)
    print()
    print("Este script sincroniza TODOS os talentos retornados pela API Inhire,")
    print("incluindo talentos COM e SEM candidaturas.")
    print()
    print("IMPORTANTE:")
    print("  - Total na Inhire:     94.612 talentos")
    print("  - Retornado pela API:  ~473-500 talentos (limitação da API)")
    print("  - Serão sincronizados: Todos retornados pela API")
    print()
    print("LIMITAÇÃO DA API:")
    print("  - A API /talents/paginated NÃO retorna todos os 94.612 talentos")
    print("  - Retorna apenas talentos modificados recentemente (~473-500)")
    print("  - ~94.000 talentos antigos NÃO são acessíveis via API paginada")
    print()
    print("PARA 100% DE COBERTURA:")
    print("  - Contactar suporte Inhire")
    print("  - Solicitar endpoint que retorne TODOS os talentos")
    print("  - Ou solicitar export CSV/JSON completo")
    print()
    print("TEMPO ESTIMADO: 2-5 minutos")
    print()
    print("=" * 80)
    print()


def main():
    print_banner()

    # Confirmação
    try:
        confirm = input("Deseja continuar? (s/N): ").strip().lower()
        if confirm not in ['s', 'sim', 'y', 'yes']:
            print("\n[CANCEL] Sincronização cancelada pelo usuário.\n")
            return
    except (EOFError, KeyboardInterrupt):
        print("\n\n[CANCEL] Sincronização cancelada.\n")
        return

    print()
    print("[>>>] Iniciando sincronização...\n")

    # Criar engine e session
    logger.info("Conectando ao banco de dados...")
    print("[INFO] Conectando ao banco de dados...")

    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    start_time = time.time()

    try:
        # STEP 1: Verificar total atual no BD
        print()
        print("[STEP 1] Contando talentos no banco...")
        count_before = session.query(Talento).count()
        print(f"   Total no BD ANTES: {count_before:,} talentos")
        logger.info(f"Talentos no BD ANTES: {count_before:,}")

        # STEP 2: Buscar TODOS da API
        print()
        print("[STEP 2] Buscando TODOS os talentos da API...")
        print("   (Isso pode demorar 1-3 minutos)")
        print()

        api_client = InhireAPIClient()
        sync_service = SyncService(session)
        db_service = sync_service.db

        # Contador
        talentos_api = []
        for talento in api_client.get_all_talentos():
            talentos_api.append(talento)

        total_api = len(talentos_api)
        print(f"   Total retornado pela API: {total_api:,} talentos")
        logger.info(f"API retornou: {total_api} talentos")

        if total_api == 0:
            print()
            print("=" * 80)
            print("[ERROR] API NÃO RETORNOU NENHUM TALENTO")
            print("=" * 80)
            print()
            print("Possíveis causas:")
            print("  - Problema de autenticação com a API")
            print("  - Endpoint /talents/paginated offline")
            print("  - Credenciais inválidas")
            print()
            print("Verifique os logs: tail -f logs/inhire_sync.log")
            print()
            return

        # STEP 3: Sincronizar todos
        print()
        print(f"[STEP 3] Sincronizando {total_api:,} talentos...")

        created = 0
        updated = 0
        skipped = 0
        failed = 0

        for i, talento in enumerate(talentos_api, 1):
            try:
                result = db_service.upsert_talento(talento)
                if result == 'created':
                    created += 1
                elif result == 'updated':
                    updated += 1
                else:
                    skipped += 1

                # Log a cada 100
                if i % 100 == 0:
                    print(f"   ... {i}/{total_api} processados ({created} criados, {updated} atualizados)")

            except Exception as e:
                failed += 1
                logger.error(f"Erro ao sincronizar {talento.id}: {e}")

        session.commit()

        # STEP 4: Verificar estado final
        print()
        print("[INFO] Verificando resultado...")
        count_after = session.query(Talento).count()
        diff = count_after - count_before

        elapsed = time.time() - start_time
        elapsed_min = elapsed / 60

        # RESULTADO FINAL
        print()
        print("=" * 80)
        print("RESULTADO DA SINCRONIZAÇÃO")
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
            print(f"   [OK] Sem mudanças")

        print()
        print(f"[STAT] Estatísticas:")
        print(f"   Retornados pela API: {total_api:,}")
        print(f"   Criados:             {created:,}")
        print(f"   Atualizados:         {updated:,}")
        print(f"   Pulados (já atuais): {skipped:,}")
        print(f"   Falhados:            {failed:,}")
        print()

        # Análise da cobertura
        print("=" * 80)
        print("ANÁLISE DE COBERTURA")
        print("=" * 80)
        print()
        print(f"Total na Inhire (interface):  94.612 talentos")
        print(f"Total no Banco de Dados:      {count_after:,} talentos")
        print(f"Divergência:                  {94612 - count_after:,} talentos ({((94612 - count_after) / 94612 * 100):.1f}%)")
        print()
        print("IMPORTANTE:")
        print("  - A API /talents/paginated retorna apenas ~473-500 talentos")
        print("  - Estes são os talentos modificados recentemente")
        print(f"  - ~{94612 - total_api:,} talentos antigos NÃO são retornados pela API")
        print()
        print("PARA SINCRONIZAR 100% DOS TALENTOS:")
        print("  1. Contactar suporte da Inhire")
        print("  2. Perguntar sobre endpoint que retorne TODOS os talentos")
        print("  3. Ou solicitar export CSV/JSON de todos os talentos")
        print()

        if created > 0:
            print(f"[SUCCESS] {created:,} novos talentos foram adicionados!")
            print()
        elif updated > 0:
            print(f"[OK] {updated:,} talentos foram atualizados.")
            print()
        else:
            print("[INFO] Todos os talentos da API já estavam sincronizados.")
            print()

        if failed > 0:
            print(f"[WARN] {failed} falhas durante sincronização.")
            print("   Verifique os logs: tail -f logs/inhire_sync.log")
            print()

        print("=" * 80)
        print()

        logger.info(f"Sincronização concluída: {created} criados, {updated} atualizados, {failed} falhas")
        logger.info(f"Cobertura: {count_after}/{94612} talentos ({count_after/94612*100:.1f}%)")

    except KeyboardInterrupt:
        print("\n\n[WARN] Sincronização interrompida pelo usuário.\n")
        logger.warning("Sincronização interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro durante sincronização: {str(e)}", exc_info=True)
        print()
        print("=" * 80)
        print("[ERROR] ERRO DURANTE SINCRONIZAÇÃO")
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
        logger.info("Conexão com banco encerrada")


if __name__ == "__main__":
    main()
