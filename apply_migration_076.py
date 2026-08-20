# -*- coding: utf-8 -*-
"""Aplica migration 076 removendo filtros e adicionando colunas"""
import sys
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

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
    print("\n=== APLICANDO MIGRATION 076 ===\n")

    # Ler migration
    with open('migrations/076_remove_filters_add_columns.sql', 'r', encoding='utf-8') as f:
        sql = f.read()

    # Aplicar
    print("Aplicando SQL...")
    session.execute(text(sql))
    session.commit()

    print("✅ Migration 076 aplicada com sucesso!")

    # Testar views
    print("\n=== TESTANDO VIEWS ===\n")

    # 1. vw_relatorio_candidaturas
    result = session.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(DISTINCT empresa) as empresas_distintas,
            COUNT(DISTINCT tipo_requisicao) as tipos_requisicao,
            COUNT(conhecia_framework) as com_framework
        FROM vw_relatorio_candidaturas
    """))

    row = result.fetchone()
    print(f"1. vw_relatorio_candidaturas:")
    print(f"   - Total de candidaturas: {row[0]}")
    print(f"   - Empresas distintas: {row[1]}")
    print(f"   - Tipos de requisição: {row[2]}")
    print(f"   - Com conhecia_framework: {row[3]}")

    # Distribuição por empresa (top 5)
    print(f"\n   Top 5 empresas:")
    result = session.execute(text("""
        SELECT
            COALESCE(empresa, 'SEM EMPRESA') as empresa,
            COUNT(*) as count
        FROM vw_relatorio_candidaturas
        GROUP BY empresa
        ORDER BY count DESC
        LIMIT 5
    """))

    for row in result.fetchall():
        print(f"   - {row[0]}: {row[1]} candidaturas")

    # Distribuição por tipo de requisição
    print(f"\n   Tipos de requisição:")
    result = session.execute(text("""
        SELECT
            COALESCE(tipo_requisicao, 'SEM WORKFLOW') as tipo,
            COUNT(*) as count
        FROM vw_relatorio_candidaturas
        GROUP BY tipo_requisicao
        ORDER BY count DESC
    """))

    for row in result.fetchall():
        print(f"   - {row[0]}: {row[1]} candidaturas")

    # 2. vw_relatorio_requisicoes
    result = session.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(DISTINCT empresa) as empresas_distintas,
            COUNT(DISTINCT tipo_requisicao) as tipos_requisicao
        FROM vw_relatorio_requisicoes
    """))

    row = result.fetchone()
    print(f"\n2. vw_relatorio_requisicoes:")
    print(f"   - Total de requisições: {row[0]}")
    print(f"   - Empresas distintas: {row[1]}")
    print(f"   - Tipos de requisição: {row[2]}")

    # Exemplo de dados
    print(f"\n   Exemplo de dados (3 primeiras):")
    result = session.execute(text("""
        SELECT titulo, empresa, tipo_requisicao, status
        FROM vw_relatorio_requisicoes
        LIMIT 3
    """))

    for row in result.fetchall():
        print(f"   - {row[0]}")
        print(f"     Empresa: {row[1] or 'N/A'}, Tipo: {row[2] or 'N/A'}, Status: {row[3]}")

    print("\n" + "="*60)
    print("✅ VIEWS ATUALIZADAS COM SUCESSO!")
    print("="*60)
    print("\nAgora você pode filtrar por:")
    print("  - empresa (ex: WHERE empresa = 'Framework')")
    print("  - tipo_requisicao (ex: WHERE tipo_requisicao != 'Requisição Posições Non Billable')")

except Exception as e:
    print(f"\n❌ Erro: {e}")
    session.rollback()
    import traceback
    traceback.print_exc()
finally:
    session.close()
    engine.dispose()
