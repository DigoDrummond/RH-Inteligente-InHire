# -*- coding: utf-8 -*-
"""Aplica migration 073 com views corrigidas"""
import sys
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'inhire')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD')

engine = create_engine(
    f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}',
    pool_pre_ping=True,
    pool_size=1,
    max_overflow=0
)

Session = sessionmaker(bind=engine)
session = Session()

try:
    print("\n=== APLICANDO MIGRATION 073 ===\n")

    # Ler migration
    with open('migrations/074_views_without_filters.sql', 'r', encoding='utf-8') as f:
        sql = f.read()

    # Aplicar
    print("Aplicando SQL...")
    session.execute(text(sql))
    session.commit()

    print("✅ Migration 073 aplicada com sucesso!")

    # Testar views
    print("\n=== TESTANDO VIEWS ===\n")

    # 1. vw_relatorio_candidaturas
    result = session.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(conhecia_framework) as com_framework,
            COUNT(tipo_contratacao) as com_tipo
        FROM vw_relatorio_candidaturas
    """))

    row = result.fetchone()
    print(f"1. vw_relatorio_candidaturas:")
    print(f"   - Total: {row[0]}")
    print(f"   - Com conhecia_framework: {row[1]}")
    print(f"   - Com tipo_contratacao: {row[2]}")

    # Exemplo
    result = session.execute(text("""
        SELECT talent_name, vaga_nome, conhecia_framework, tipo_contratacao
        FROM vw_relatorio_candidaturas
        WHERE conhecia_framework IS NOT NULL OR tipo_contratacao IS NOT NULL
        LIMIT 5
    """))

    print(f"\n   Exemplos:")
    for row in result.fetchall():
        print(f"   - {row[0]}: {row[1]}")
        print(f"     Framework? {row[2] or 'N/A'}, Contrato: {row[3] or 'N/A'}")

    # 2. vw_relatorio_requisicoes
    result = session.execute(text("""
        SELECT COUNT(*) as total
        FROM vw_relatorio_requisicoes
    """))

    total = result.scalar()
    print(f"\n2. vw_relatorio_requisicoes:")
    print(f"   - Total: {total}")

    # Exemplo
    result = session.execute(text("""
        SELECT titulo, data_solicitacao, status
        FROM vw_relatorio_requisicoes
        LIMIT 3
    """))

    print(f"\n   Exemplos:")
    for row in result.fetchall():
        print(f"   - {row[0]}: {row[1]} ({row[2]})")

    print("\n" + "="*60)
    print("✅ VIEWS ATUALIZADAS COM SUCESSO!")
    print("="*60)

except Exception as e:
    print(f"\n❌ Erro: {e}")
    session.rollback()
    import traceback
    traceback.print_exc()
finally:
    session.close()
    engine.dispose()
