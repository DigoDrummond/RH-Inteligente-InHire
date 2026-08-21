# -*- coding: utf-8 -*-
"""
Script para aplicar migration 070 - Atualizar view vw_relatorio_candidaturas
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Fix encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Carregar .env
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(env_path)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'inhire')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD')

print("=== Aplicando Migration 070: Atualizar view vw_relatorio_candidaturas ===\n")

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

    # Ler SQL da migration
    migration_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'migrations',
        '070_update_view_candidaturas_custom_fields.sql'
    )

    print("Lendo arquivo de migration...")
    with open(migration_path, 'r', encoding='utf-8') as f:
        sql = f.read()

    print("Executando migration...")
    cur.execute(sql)

    # Commit
    conn.commit()
    print("\n✅ Migration 070 aplicada com sucesso!")
    print("   - View: vw_relatorio_candidaturas")
    print("   - Campo extraído: Você conhecia a Framework Digital?")
    print("   - ID do campo: 55282edb-bb11-4445-8cd6-3c0c6b9ddb9a")

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
