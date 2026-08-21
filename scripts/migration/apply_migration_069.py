"""
Script para aplicar migration 069 - Adicionar custom_fields em candidaturas
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Fix encoding para Windows
sys.stdout.reconfigure(encoding='utf-8')

# Carregar .env
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(env_path)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'inhire')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD')

print("=== Aplicando Migration 069: custom_fields em candidaturas ===\n")

try:
    # Conectar ao banco
    print(f"Conectando ao banco {DB_NAME}...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    conn.autocommit = False
    cur = conn.cursor()

    # 1. Verificar se coluna já existe
    print("1. Verificando se coluna custom_fields já existe...")
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'candidaturas' AND column_name = 'custom_fields'
    """)
    coluna_existe = cur.fetchone() is not None

    if coluna_existe:
        print("   ✓ Coluna custom_fields já existe")
        # Verificar tipo atual
        cur.execute("""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'candidaturas' AND column_name = 'custom_fields'
        """)
        tipo_atual = cur.fetchone()[0]
        print(f"   - Tipo atual: {tipo_atual}")

        if tipo_atual == 'json':
            print("   - Convertendo de JSON para JSONB...")
            cur.execute("ALTER TABLE candidaturas ALTER COLUMN custom_fields TYPE JSONB USING custom_fields::jsonb;")
            print("   ✓ Coluna convertida para JSONB")
    else:
        print("   - Coluna custom_fields não existe, criando...")
        # 2. Adicionar coluna (JSONB para suportar índice GIN)
        cur.execute("ALTER TABLE candidaturas ADD COLUMN custom_fields JSONB;")
        print("   ✓ Coluna custom_fields criada (tipo JSONB)")

    # 3. Adicionar comentário
    print("2. Adicionando comentário...")
    cur.execute("""
        COMMENT ON COLUMN candidaturas.custom_fields IS
        'Custom fields responses (JOB_TALENTS) - formato: {"field_id": ["valor1", "valor2"]}'
    """)
    print("   ✓ Comentário adicionado")

    # 4. Criar índice GIN (requer JSONB, não JSON)
    print("3. Criando índice GIN...")
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_candidaturas_custom_fields
        ON candidaturas USING GIN (custom_fields)
    """)
    print("   ✓ Índice idx_candidaturas_custom_fields criado")

    # 5. Commit
    conn.commit()
    print("\n✅ Migration 069 aplicada com sucesso!")
    print("   - Tabela: candidaturas")
    print("   - Coluna: custom_fields (JSON)")
    print("   - Índice: idx_candidaturas_custom_fields (GIN)")

except psycopg2.Error as e:
    print(f"\n❌ Erro ao aplicar migration: {e}")
    if conn:
        conn.rollback()
    sys.exit(1)

except Exception as e:
    print(f"\n❌ Erro inesperado: {e}")
    if conn:
        conn.rollback()
    sys.exit(1)

finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
    print("\nConexão fechada.")
