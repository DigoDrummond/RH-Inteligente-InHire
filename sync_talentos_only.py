"""
Script para sincronizar APENAS a entidade TALENTOS (sincronização FULL)

USO:
    python sync_talentos_only.py

CARACTERÍSTICAS:
    - Sincroniza TODOS os talentos da API InHire
    - Não sincroniza outras entidades
    - Tempo estimado: 6-13 minutos
    - Volume: ~85.562 talentos (completo)

QUANDO USAR:
    - Após detectar divergências em dados de talentos
    - Para atualizar informações de contato/perfil
    - Após correções manuais que afetaram apenas talentos

Data: 2026-03-19
"""

import sys
import os
from pathlib import Path

# Fix de encoding
os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ['TZ'] = 'America/Sao_Paulo'

# Limpar variáveis de ambiente problemáticas
for key in list(os.environ.keys()):
    if key.startswith('PG') and key != 'PGCLIENTENCODING':
        del os.environ[key]

# Adicionar root ao path
sys.path.insert(0, str(Path(__file__).parent))

from services.sync_service import SyncService
from config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.logger import get_logger
from models.database import Talento
import time

logger = get_logger(__name__)

def print_banner():
    """Exibe banner informativo"""
    print()
    print("=" * 80)
    print("SINCRONIZAÇÃO FULL - APENAS TALENTOS")
    print("=" * 80)
    print()
    print("Este script sincronizará TODOS os talentos da API InHire")
    print()
    print("Informações:")
    print("  • Entidade: TALENTOS")
    print("  • Modo: FULL (todos os registros)")
    print("  • Volume esperado: ~85.562 talentos")
    print("  • Tempo estimado: 6-13 minutos")
    print()
    print("O que sera sincronizado:")
    print("  [+] Dados pessoais (nome, email, telefone)")
    print("  [+] Perfil profissional")
    print("  [+] Status e tags")
    print("  [+] Arquivos (curriculos, documentos)")
    print()
    print("O que NAO sera sincronizado:")
    print("  [-] Vagas")
    print("  [-] Posicoes")
    print("  [-] Candidaturas")
    print("  [-] Outras entidades")
    print()
    print("=" * 80)
    print()

def main():
    print_banner()

    # Confirmação
    try:
        confirm = input("Deseja continuar? (s/N): ").strip().lower()
        if confirm not in ['s', 'sim', 'y', 'yes']:
            print("\n[ERROR] Sincronização cancelada pelo usuário.\n")
            return
    except (EOFError, KeyboardInterrupt):
        print("\n\n[ERROR] Sincronização cancelada.\n")
        return

    print()
    print("[>>>] Iniciando sincronização...")
    print()

    # Criar engine e session
    logger.info("Conectando ao banco de dados...")
    print("[INFO] Conectando ao banco de dados...")

    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Inicializar serviço
        logger.info("Inicializando SyncService...")
        sync_service = SyncService(session)

        # Verificar estado ANTES
        print("[STAT] Contando talentos no banco ANTES da sincronização...")
        count_before = session.query(Talento).count()
        logger.info(f"Talentos no banco ANTES: {count_before:,}")
        print(f"   Total atual: {count_before:,} talentos")
        print()

        # Executar sincronização
        print("[SYNC] Sincronizando TODOS os talentos da API Inhire...")
        print("   (Isso pode demorar 6-13 minutos)")
        print()

        start_time = time.time()

        # Chamar método de sync FULL (None = todos os talentos)
        stats = sync_service._sync_talentos_full(talent_ids=None)

        elapsed = time.time() - start_time
        elapsed_min = elapsed / 60

        # Verificar estado DEPOIS
        print()
        print("[INFO] Contando talentos no banco DEPOIS da sincronização...")
        count_after = session.query(Talento).count()
        logger.info(f"Talentos no banco DEPOIS: {count_after:,}")

        # Calcular diferença
        diff = count_after - count_before

        # Resumo
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
            print(f"   [-] Removidos: {abs(diff):,} talentos")
        else:
            print(f"   [OK] Sem mudanças")
        print()
        print(f"[STAT] Estatísticas:")
        print(f"   Processados: {stats.get('processed', 0):,}")
        print(f"   Criados:     {stats.get('created', 0):,}")
        print(f"   Atualizados: {stats.get('updated', 0):,}")
        print(f"   Pulados:     {stats.get('skipped', 0):,}")
        print(f"   Falhados:    {stats.get('failed', 0):,}")
        print()

        # Taxa de skip
        if stats.get('processed', 0) > 0:
            skip_rate = (stats.get('skipped', 0) / stats['processed']) * 100
            print(f"   Skip rate: {skip_rate:.1f}%")
            print()

        print("=" * 80)
        print()

        # Status final
        if stats.get('failed', 0) == 0:
            print("[OK] Sincronização concluída com SUCESSO!\n")
            logger.info("Sincronização de talentos concluída com sucesso")
        else:
            print(f"[WARN]  Sincronização concluída com {stats['failed']} falhas\n")
            print("   Verifique os logs para mais detalhes:")
            print("   tail -f logs/inhire_sync.log\n")
            logger.warning(f"Sincronização concluída com {stats['failed']} falhas")

        # Verificação final
        if count_after >= 85000:
            print("[SUCCESS] Banco de dados agora contém a maioria dos talentos esperados!")
        elif diff > 0:
            print(f"[INFO]  {diff:,} novos talentos foram adicionados.")
            remaining = 85562 - count_after
            if remaining > 0:
                print(f"   Ainda faltam ~{remaining:,} talentos para atingir o total esperado (85.562).")

        print()

    except KeyboardInterrupt:
        print("\n\n[WARN]  Sincronização interrompida pelo usuário.\n")
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
        print("Verifique os logs para mais detalhes:")
        print("  tail -f logs/inhire_sync.log")
        print()
        import traceback
        traceback.print_exc()
        print()
        sys.exit(1)
    finally:
        session.close()
        logger.info("Conexão com banco encerrada")

if __name__ == "__main__":
    main()
