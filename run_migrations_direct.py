"""
Script para executar migrations diretamente via psycopg2
Não precisa de senha se estiver usando trust/peer authentication
"""
import psycopg2
from psycopg2 import sql
from pathlib import Path
import sys

# Configurações
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "inhire",
    "user": "postgres",
    # Adicione senha aqui se necessário:
    # "password": "sua_senha"
}

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
MIGRATIONS = [
    "010_add_composite_index_candidatura.sql",
    "011_add_check_constraints.sql"
]


def read_migration_file(file_path: Path) -> str:
    """Lê conteúdo do arquivo SQL"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Erro ao ler {file_path.name}: {e}")
        return None


def run_migration(conn, migration_file: Path) -> bool:
    """
    Executa uma migration SQL

    Args:
        conn: Conexão psycopg2
        migration_file: Caminho do arquivo SQL

    Returns:
        True se executado com sucesso
    """
    print(f"\n{'='*60}")
    print(f"Executando: {migration_file.name}")
    print(f"{'='*60}\n")

    if not migration_file.exists():
        print(f"[ERRO] Arquivo nao encontrado: {migration_file}")
        return False

    # Ler SQL
    sql_content = read_migration_file(migration_file)
    if not sql_content:
        return False

    try:
        cursor = conn.cursor()

        # Executar SQL
        cursor.execute(sql_content)
        conn.commit()

        # Pegar notices/warnings do PostgreSQL
        for notice in conn.notices:
            print(notice.strip())

        cursor.close()
        print(f"\n[OK] {migration_file.name} executada com sucesso!\n")
        return True

    except psycopg2.Error as e:
        conn.rollback()
        print(f"\n[ERRO] Falha ao executar {migration_file.name}")
        print(f"Erro: {e}")
        return False
    except Exception as e:
        conn.rollback()
        print(f"\n[ERRO] Erro inesperado: {e}")
        return False


def verify_indexes(conn) -> None:
    """Verifica se os índices foram criados"""
    print(f"\n{'='*60}")
    print("Verificando indices criados...")
    print(f"{'='*60}\n")

    query = """
    SELECT indexname, indexdef
    FROM pg_indexes
    WHERE tablename = 'candidaturas'
      AND indexname LIKE 'idx_candidatura%'
    ORDER BY indexname;
    """

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()

        if results:
            print("Indices criados em 'candidaturas':\n")
            for row in results:
                print(f"  - {row[0]}")
            print()
        else:
            print("Nenhum indice personalizado encontrado\n")

        cursor.close()

    except Exception as e:
        print(f"Erro ao verificar indices: {e}")


def verify_constraints(conn) -> None:
    """Verifica se as constraints foram criadas"""
    print(f"\n{'='*60}")
    print("Verificando check constraints criadas...")
    print(f"{'='*60}\n")

    query = """
    SELECT
        conname as constraint_name,
        conrelid::regclass as table_name
    FROM pg_constraint
    WHERE conname LIKE 'chk_%'
    ORDER BY conrelid::regclass::text, conname;
    """

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()

        if results:
            print("Check constraints criadas:\n")
            current_table = None
            for row in results:
                constraint_name, table_name = row
                if table_name != current_table:
                    current_table = table_name
                    print(f"\n  {table_name}:")
                print(f"    - {constraint_name}")
            print()
        else:
            print("Nenhuma check constraint encontrada\n")

        cursor.close()

    except Exception as e:
        print(f"Erro ao verificar constraints: {e}")


def main():
    """Executa todas as migrations pendentes"""
    print("="*60)
    print("EXECUCAO DE MIGRATIONS - InHire Database")
    print("="*60)
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Host: {DB_CONFIG['host']}")
    print(f"User: {DB_CONFIG['user']}")
    print()

    # Verificar se pasta de migrations existe
    if not MIGRATIONS_DIR.exists():
        print(f"[ERRO] Pasta de migrations nao encontrada: {MIGRATIONS_DIR}")
        sys.exit(1)

    # Conectar ao banco
    print("Conectando ao banco de dados...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_session(autocommit=False)
        print("[OK] Conectado!\n")
    except psycopg2.Error as e:
        print(f"[ERRO] Nao foi possivel conectar ao banco:")
        print(f"  {e}")
        print("\nDica: Verifique se:")
        print("  1. PostgreSQL esta rodando")
        print("  2. Credenciais estao corretas")
        print("  3. Banco 'inhire' existe")
        sys.exit(1)

    success_count = 0
    failed_count = 0

    # Executar cada migration
    for migration_name in MIGRATIONS:
        migration_file = MIGRATIONS_DIR / migration_name

        if run_migration(conn, migration_file):
            success_count += 1
        else:
            failed_count += 1

    # Verificar resultados
    if success_count > 0:
        verify_indexes(conn)
        verify_constraints(conn)

    # Fechar conexão
    conn.close()

    # Resumo
    print(f"{'='*60}")
    print("RESUMO")
    print(f"{'='*60}")
    print(f"[OK] Migrations executadas com sucesso: {success_count}")
    print(f"[ERRO] Migrations com falha: {failed_count}")
    print()

    if failed_count == 0:
        print("[OK] TODAS AS MIGRATIONS FORAM EXECUTADAS COM SUCESSO")
    else:
        print("[AVISO] ALGUMAS MIGRATIONS FALHARAM - Verifique os erros acima")

    print("="*60)

    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
