"""
Wrapper para executar sincronização com fix de encoding
"""
import os
import sys
import time
from datetime import datetime
import pytz

# Fix de encoding ANTES de importar qualquer coisa
os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ['TZ'] = 'America/Sao_Paulo'

# Limpar variáveis de ambiente problemáticas
for key in list(os.environ.keys()):
    if key.startswith('PG') and key != 'PGCLIENTENCODING':
        del os.environ[key]

# Agora importar o resto
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from services.sync_service import SyncService

def print_header(title):
    print()
    print("=" * 70)
    print(f" {title}")
    print("=" * 70)
    print()

def print_progress(current, total, entity_name):
    pct = (current / total * 100) if total > 0 else 0
    print(f"  [{current}/{total}] {entity_name}: {pct:.1f}%", end='\r')

def main():
    # Verificar argumento
    if len(sys.argv) < 2 or sys.argv[1] not in ['--full', '--incremental', '--express']:
        print("Uso: python run_sync.py [--full|--incremental|--express]")
        print()
        print("  --full          Sincronizacao completa (todos os dados, ~55 min)")
        print("  --incremental   Sincronizacao incremental (tudo incluindo Candidaturas, ~20 min)")
        print("  --express       Sincronizacao express (apenas dados criticos, ~5 min)")
        return

    sync_type = sys.argv[1].replace('--', '')
    express_mode = False  # Sempre modo completo (incremental)

    print_header(f"SINCRONIZACAO {sync_type.upper()} - InHire")

    print(f"Tipo: {sync_type}")
    print(f"Banco: {settings.DB_NAME}")
    sp_tz = pytz.timezone('America/Sao_Paulo')
    print(f"Inicio: {datetime.now(sp_tz).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()

    if sync_type == 'full':
        print("AVISO: Sincronizacao completa pode demorar ~55 minutos")
        print("       Volume estimado: ~104.558 registros")
        print()

    # Conectar ao banco
    print("[1] Conectando ao banco de dados...")
    try:
        database_url = (
            f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            f"?client_encoding=utf8"
        )

        engine = create_engine(
            database_url,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            echo=False,
            connect_args={
                'client_encoding': 'utf8',
                'connect_timeout': 10
            }
        )

        Session = sessionmaker(bind=engine)
        session = Session()

        print("    OK - Conexao estabelecida")
        print()

    except Exception as e:
        print(f"    ERRO ao conectar: {str(e)}")
        return

    # Inicializar serviço de sincronização
    print("[2] Inicializando servico de sincronizacao...")
    try:
        sync_service = SyncService(session=session)

        print("    OK - Servico inicializado")
        print()

    except Exception as e:
        print(f"    ERRO ao inicializar: {str(e)}")
        session.close()
        return

    # Executar sincronização
    start_time = time.time()

    try:
        if sync_type == 'full':
            print_header("SINCRONIZACAO COMPLETA")
            print("[3] Executando sincronizacao completa...")
            print("    (vagas -> posicoes -> candidaturas -> talentos)")
            print()

            result = sync_service.sync_full()

            elapsed = time.time() - start_time
            print()
            print_header("RESULTADO DA SINCRONIZACAO")

            total_records = result.get('processed', 0)

            print(f"Registros processados: {total_records:,}")
            print(f"Novos:                 {result.get('created', 0):,}")
            print(f"Atualizados:           {result.get('updated', 0):,}")
            print(f"Ignorados:             {result.get('skipped', 0):,}")
            print(f"Falhas:                {result.get('failed', 0):,}")
            print()

        elif sync_type == 'express':
            print_header("SINCRONIZACAO EXPRESS")
            print("[3] Sincronizando apenas dados criticos (vagas abertas + candidatos ativos)...")
            print()

            result = sync_service.sync_express()
            elapsed = time.time() - start_time

            stats = result.get('stats', {})
            print()
            print_header("RESULTADO DA SINCRONIZACAO")
            print(f"Registros processados: {stats.get('processed', 0):,}")
            print(f"Novos:                 {stats.get('created', 0):,}")
            print(f"Atualizados:           {stats.get('updated', 0):,}")
            print(f"Ignorados:             {stats.get('skipped', 0):,}")
            print(f"Falhas:                {stats.get('failed', 0):,}")
            print()

        else:  # incremental
            print_header("SINCRONIZACAO INCREMENTAL")
            print("[3] Sincronizando todas as entidades incluindo Candidaturas (~20 min)...")

            result = sync_service.sync_incremental(express_mode=False)
            elapsed = time.time() - start_time
            print(f"    OK - {result.get('stats', {}).get('processed', 0)} registros processados")
            print()

    except Exception as e:
        print(f"\n    ERRO durante sincronizacao: {str(e)}")
        import traceback
        traceback.print_exc()
        session.rollback()
        session.close()
        return

    # Finalizar
    elapsed_total = time.time() - start_time
    elapsed_min = elapsed_total / 60

    print("=" * 70)
    print(f" Tempo total: {elapsed_total:.1f}s ({elapsed_min:.1f} minutos)")
    print("=" * 70)
    print()

    if sync_type == 'full':
        print("[OK] SINCRONIZACAO COMPLETA FINALIZADA!")
    elif sync_type == 'express':
        print("[OK] SINCRONIZACAO EXPRESS FINALIZADA!")
    else:
        print("[OK] SINCRONIZACAO INCREMENTAL FINALIZADA!")

    print()
    print("Proximo passo: Consultar os dados sincronizados")
    print()

    session.close()


if __name__ == "__main__":
    main()
