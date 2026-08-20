# -*- coding: utf-8 -*-
"""Aplica migration 078 removendo tipo_posicao"""
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
    print("\n=== APLICANDO MIGRATION 078 ===\n")

    # Ler migration
    with open('migrations/078_remove_tipo_posicao_keep_workflow.sql', 'r', encoding='utf-8') as f:
        sql = f.read()

    # Aplicar
    print("Aplicando SQL...")
    session.execute(text(sql))
    session.commit()

    print("✅ Migration 078 aplicada com sucesso!")

    # Testar views
    print("\n=== TESTANDO VIEWS ===\n")

    # 1. vw_relatorio_candidaturas
    result = session.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(DISTINCT cliente) as clientes_distintos,
            COUNT(DISTINCT empresa) as empresas_distintas,
            COUNT(DISTINCT nome_workflow_aprovacao) as workflows
        FROM vw_relatorio_candidaturas
    """))

    row = result.fetchone()
    print(f"1. vw_relatorio_candidaturas:")
    print(f"   - Total: {row[0]}")
    print(f"   - Clientes distintos: {row[1]}")
    print(f"   - Empresas distintas: {row[2]}")
    print(f"   - Workflows: {row[3]}")

    # Distribuição por empresa
    print(f"\n   Empresas (custom field):")
    result = session.execute(text("""
        SELECT
            COALESCE(empresa, 'SEM EMPRESA') as empresa,
            COUNT(*) as count
        FROM vw_relatorio_candidaturas
        GROUP BY empresa
        ORDER BY count DESC
    """))

    for row in result.fetchall():
        print(f"   - {row[0]}: {row[1]} candidaturas")

    # Distribuição por workflow
    print(f"\n   Workflows de Aprovação:")
    result = session.execute(text("""
        SELECT
            COALESCE(nome_workflow_aprovacao, 'SEM WORKFLOW') as workflow,
            COUNT(*) as count
        FROM vw_relatorio_candidaturas
        GROUP BY nome_workflow_aprovacao
        ORDER BY count DESC
    """))

    for row in result.fetchall():
        print(f"   - {row[0]}: {row[1]} candidaturas")

    # Exemplo completo
    print(f"\n   Exemplo de dados (3 primeiros):")
    result = session.execute(text("""
        SELECT
            talent_name,
            cliente,
            empresa,
            nome_workflow_aprovacao
        FROM vw_relatorio_candidaturas
        WHERE empresa IS NOT NULL
        LIMIT 3
    """))

    for i, row in enumerate(result.fetchall(), 1):
        print(f"\n   {i}. {row[0]}")
        print(f"      Cliente: {row[1] or 'N/A'}")
        print(f"      Empresa: {row[2] or 'N/A'}")
        print(f"      Workflow: {row[3] or 'N/A'}")

    # 2. vw_relatorio_requisicoes
    result = session.execute(text("""
        SELECT COUNT(*) FROM vw_relatorio_requisicoes
    """))

    total = result.scalar()
    print(f"\n2. vw_relatorio_requisicoes:")
    print(f"   - Total: {total}")

    print("\n" + "="*60)
    print("✅ VIEWS FINALIZADAS!")
    print("="*60)
    print("\nCampos disponíveis:")
    print("  ✅ cliente (clientes.name)")
    print("  ✅ empresa (custom_fields.Empresa)")
    print("  ✅ nome_workflow_aprovacao (approval_workflow->>'name')")
    print("  ❌ tipo_posicao (REMOVIDO)")

except Exception as e:
    print(f"\n❌ Erro: {e}")
    session.rollback()
    import traceback
    traceback.print_exc()
finally:
    session.close()
    engine.dispose()
