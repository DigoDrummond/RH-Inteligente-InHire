# -*- coding: utf-8 -*-
"""Aplica migration 077 corrigindo campos empresa e tipo_posicao"""
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
    print("\n=== APLICANDO MIGRATION 077 ===\n")

    # Ler migration
    with open('migrations/077_fix_empresa_tipo_posicao_fields.sql', 'r', encoding='utf-8') as f:
        sql = f.read()

    # Aplicar
    print("Aplicando SQL...")
    session.execute(text(sql))
    session.commit()

    print("✅ Migration 077 aplicada com sucesso!")

    # Testar views
    print("\n=== TESTANDO VIEWS ===\n")

    # 1. vw_relatorio_candidaturas
    result = session.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(DISTINCT cliente) as clientes_distintos,
            COUNT(DISTINCT empresa) as empresas_distintas,
            COUNT(DISTINCT tipo_posicao) as tipos_posicao,
            COUNT(DISTINCT workflow_aprovacao) as workflows
        FROM vw_relatorio_candidaturas
    """))

    row = result.fetchone()
    print(f"1. vw_relatorio_candidaturas:")
    print(f"   - Total: {row[0]}")
    print(f"   - Clientes distintos: {row[1]}")
    print(f"   - Empresas distintas: {row[2]}")
    print(f"   - Tipos de posição: {row[3]}")
    print(f"   - Workflows: {row[4]}")

    # Distribuição por empresa (custom field)
    print(f"\n   Top 5 EMPRESAS (custom field):")
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

    # Distribuição por tipo de posição (custom field)
    print(f"\n   Tipos de Posição (custom field):")
    result = session.execute(text("""
        SELECT
            COALESCE(tipo_posicao, 'SEM TIPO') as tipo,
            COUNT(*) as count
        FROM vw_relatorio_candidaturas
        GROUP BY tipo_posicao
        ORDER BY count DESC
    """))

    for row in result.fetchall():
        print(f"   - {row[0]}: {row[1]} candidaturas")

    # Exemplo com todos os campos
    print(f"\n   Exemplo de dados (3 primeiros):")
    result = session.execute(text("""
        SELECT
            talent_name,
            cliente,
            empresa,
            tipo_posicao,
            workflow_aprovacao
        FROM vw_relatorio_candidaturas
        WHERE empresa IS NOT NULL OR tipo_posicao IS NOT NULL
        LIMIT 3
    """))

    for i, row in enumerate(result.fetchall(), 1):
        print(f"\n   {i}. {row[0]}")
        print(f"      Cliente: {row[1] or 'N/A'}")
        print(f"      Empresa: {row[2] or 'N/A'}")
        print(f"      Tipo Posição: {row[3] or 'N/A'}")
        print(f"      Workflow: {row[4] or 'N/A'}")

    # 2. vw_relatorio_requisicoes
    result = session.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(DISTINCT cliente) as clientes_distintos,
            COUNT(DISTINCT empresa) as empresas_distintas,
            COUNT(DISTINCT tipo_posicao) as tipos_posicao
        FROM vw_relatorio_requisicoes
    """))

    row = result.fetchone()
    print(f"\n2. vw_relatorio_requisicoes:")
    print(f"   - Total: {row[0]}")
    print(f"   - Clientes distintos: {row[1]}")
    print(f"   - Empresas distintas: {row[2]}")
    print(f"   - Tipos de posição: {row[3]}")

    print("\n" + "="*60)
    print("✅ VIEWS CORRIGIDAS COM SUCESSO!")
    print("="*60)
    print("\nCampos agora CORRETOS:")
    print("  - cliente: clientes.name")
    print("  - empresa: custom_fields.Empresa")
    print("  - tipo_posicao: custom_fields.'Tipo de Serviço'")
    print("  - workflow_aprovacao: approval_workflow->>'name'")

except Exception as e:
    print(f"\n❌ Erro: {e}")
    session.rollback()
    import traceback
    traceback.print_exc()
finally:
    session.close()
    engine.dispose()
