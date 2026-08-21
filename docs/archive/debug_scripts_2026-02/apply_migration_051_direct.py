"""
Script para aplicar migration 051 diretamente
"""
import psycopg2
from config import Settings

def apply_migration():
    """Aplica migration 051 diretamente"""
    settings = Settings()
    conn = None
    try:
        # Conectar ao banco
        print("Conectando ao banco...")
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()

        print("Aplicando alterações em vagas...")
        cursor.execute("""
            ALTER TABLE vagas
            ADD COLUMN IF NOT EXISTS specialization VARCHAR(50);
        """)
        print("OK - Coluna specialization adicionada")

        cursor.execute("""
            ALTER TABLE vagas
            ADD COLUMN IF NOT EXISTS metadata JSONB;
        """)
        print("OK - Coluna metadata adicionada")

        print("\nAplicando alteracoes em candidaturas...")
        cursor.execute("""
            ALTER TABLE candidaturas
            ADD COLUMN IF NOT EXISTS stage_metadata JSONB;
        """)
        print("OK - Coluna stage_metadata adicionada")

        cursor.execute("""
            ALTER TABLE candidaturas
            ADD COLUMN IF NOT EXISTS phase_metadata JSONB;
        """)
        print("OK - Coluna phase_metadata adicionada")

        print("\nCriando indices...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_vagas_metadata
            ON vagas USING GIN (metadata);
        """)
        print("OK - Indice idx_vagas_metadata criado")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_vagas_specialization
            ON vagas (specialization)
            WHERE specialization IS NOT NULL;
        """)
        print("OK - Indice idx_vagas_specialization criado")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_candidaturas_stage_metadata
            ON candidaturas USING GIN (stage_metadata);
        """)
        print("OK - Indice idx_candidaturas_stage_metadata criado")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_candidaturas_phase_metadata
            ON candidaturas USING GIN (phase_metadata);
        """)
        print("OK - Indice idx_candidaturas_phase_metadata criado")

        # Verificar
        print("\n" + "="*60)
        print("VERIFICAÇÃO")
        print("="*60)

        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'vagas'
            AND column_name IN ('specialization', 'metadata')
            ORDER BY column_name;
        """)
        vagas_cols = cursor.fetchall()
        print(f"\nColunas em vagas: {[col[0] for col in vagas_cols]}")

        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'candidaturas'
            AND column_name IN ('stage_metadata', 'phase_metadata')
            ORDER BY column_name;
        """)
        cand_cols = cursor.fetchall()
        print(f"Colunas em candidaturas: {[col[0] for col in cand_cols]}")

        print("\n" + "="*60)
        print("SUCESSO! MIGRATION 051 APLICADA COM SUCESSO!")
        print("="*60)

        cursor.close()

    except Exception as e:
        print(f"\nERRO: {e}")
        raise
    finally:
        if conn:
            conn.close()
            print("\nConexão fechada.")

if __name__ == "__main__":
    apply_migration()
