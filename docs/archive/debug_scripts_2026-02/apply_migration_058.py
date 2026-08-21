"""
Script para aplicar migration 058 com timeout
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from config import settings

def main():
    engine = create_engine(settings.DATABASE_URL, poolclass=NullPool, connect_args={'connect_timeout': 30})

    try:
        with engine.connect() as conn:
            # Set statement timeout (60 seconds)
            conn.execute(text("SET statement_timeout = 60000"))

            # Read migration file
            migration_file = project_root / 'migrations' / '058_add_motivo_status_to_view.sql'
            migration_sql = migration_file.read_text(encoding='utf-8')

            print("Aplicando migration 058...")
            conn.execute(text(migration_sql))
            conn.commit()

            print("[OK] Migration 058 aplicada com sucesso!")

            # Verificar nova coluna
            result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'vw_analise_posicoes'
                  AND column_name = 'motivo_status'
            """)).fetchone()

            if result:
                print(f"[OK] Coluna 'motivo_status' criada com sucesso (tipo: {result[1]})")
            else:
                print("[!] AVISO: Coluna 'motivo_status' não encontrada!")

    except Exception as e:
        print(f"[ERRO] Falha ao aplicar migration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        engine.dispose()

    return 0

if __name__ == "__main__":
    sys.exit(main())
