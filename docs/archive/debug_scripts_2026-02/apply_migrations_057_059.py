"""
Script para aplicar migrations 057 (restaurar) e 059 (adicionar motivo_status)
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from config import settings

def main():
    engine = create_engine(settings.DATABASE_URL, poolclass=NullPool, connect_args={'connect_timeout': 60})

    try:
        with engine.connect() as conn:
            # Set statement timeout (120 seconds)
            conn.execute(text("SET statement_timeout = 120000"))

            # ETAPA 1: Restaurar migration 057
            print("=" * 80)
            print("ETAPA 1: Restaurando migration 057 (32 campos)")
            print("=" * 80)

            migration_057 = project_root / 'migrations' / '057_add_workflow_name_to_view.sql'
            sql_057 = migration_057.read_text(encoding='utf-8')

            print("Aplicando migration 057...")
            conn.execute(text(sql_057))
            conn.commit()
            print("[OK] Migration 057 restaurada!")

            # Verificar colunas
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.columns
                WHERE table_name = 'vw_analise_posicoes'
            """)).fetchone()
            print(f"Total de colunas após 057: {result[0]}")

            # ETAPA 2: Aplicar migration 059
            print("\n" + "=" * 80)
            print("ETAPA 2: Aplicando migration 059 (adicionar motivo_status)")
            print("=" * 80)

            migration_059 = project_root / 'migrations' / '059_add_motivo_status_to_view.sql'
            sql_059 = migration_059.read_text(encoding='utf-8')

            print("Aplicando migration 059...")
            conn.execute(text(sql_059))
            conn.commit()
            print("[OK] Migration 059 aplicada!")

            # Verificar colunas finais
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.columns
                WHERE table_name = 'vw_analise_posicoes'
            """)).fetchone()
            print(f"Total de colunas após 059: {result[0]}")

            # Verificar se motivo_status existe
            result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'vw_analise_posicoes'
                  AND column_name = 'motivo_status'
            """)).fetchone()

            if result:
                print(f"\n[OK] Coluna 'motivo_status' criada com sucesso!")
                print(f"     Tipo: {result[1]}")
            else:
                print("\n[!] ERRO: Coluna 'motivo_status' não encontrada!")

            print("\n" + "=" * 80)
            print("[OK] MIGRATIONS APLICADAS COM SUCESSO!")
            print("=" * 80)

    except Exception as e:
        print(f"\n[ERRO] Falha ao aplicar migrations: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        engine.dispose()

    return 0

if __name__ == "__main__":
    sys.exit(main())
