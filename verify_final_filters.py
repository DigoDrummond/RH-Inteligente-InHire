# -*- coding: utf-8 -*-
"""Verificação final dos filtros aplicados"""
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
    pool_pre_ping=True
)

Session = sessionmaker(bind=engine)
session = Session()

try:
    print("\n=== VERIFICAÇÃO FINAL DOS FILTROS ===\n")

    # 1. Breakdown por workflow
    print("1. DISTRIBUIÇÃO POR WORKFLOW (candidaturas Framework 2026):\n")

    result = session.execute(text("""
        SELECT
            COALESCE(r.approval_workflow->>'name', 'SEM WORKFLOW') as workflow,
            COUNT(*) as candidaturas_count
        FROM candidaturas c
        INNER JOIN vagas v ON c.vaga_id = v.id
        LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
        LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
        WHERE EXTRACT(YEAR FROM c.created_at) = 2026
          AND cl.name = 'Framework'
        GROUP BY r.approval_workflow->>'name'
        ORDER BY candidaturas_count DESC
    """))

    total_framework = 0
    excluidas = 0
    incluidas = 0

    for row in result.fetchall():
        workflow = row[0]
        count = row[1]
        total_framework += count

        if workflow == 'Requisição Posições Non Billable':
            status = "❌ EXCLUÍDO"
            excluidas += count
        else:
            status = "✅ INCLUÍDO"
            incluidas += count

        print(f"   {status} '{workflow}': {count}")

    print(f"\n   Total Framework: {total_framework}")
    print(f"   Incluídas na view: {incluidas}")
    print(f"   Excluídas da view: {excluidas}")

    # 2. Confirmar contagem da view
    result = session.execute(text("""
        SELECT COUNT(*) FROM vw_relatorio_candidaturas
    """))
    view_count = result.scalar()

    print(f"\n2. CONFIRMAÇÃO:")
    print(f"   - Candidaturas na view: {view_count}")
    print(f"   - Esperado (calculado): {incluidas}")

    if view_count == incluidas:
        print(f"   ✅ FILTROS CORRETOS!")
    else:
        print(f"   ⚠️ DIVERGÊNCIA DETECTADA!")

    # 3. Amostra de dados
    print(f"\n3. AMOSTRA DE DADOS DA VIEW (5 primeiros):\n")

    result = session.execute(text("""
        SELECT
            talent_name,
            vaga_nome,
            conhecia_framework,
            created_at
        FROM vw_relatorio_candidaturas
        ORDER BY created_at DESC
        LIMIT 5
    """))

    for i, row in enumerate(result.fetchall(), 1):
        print(f"   {i}. {row[0]}")
        print(f"      Vaga: {row[1]}")
        print(f"      Conhecia Framework?: {row[2] or 'N/A'}")
        print(f"      Data: {row[3]}")

    print("\n" + "="*60)
    print("✅ VERIFICAÇÃO CONCLUÍDA!")
    print("="*60)

finally:
    session.close()
    engine.dispose()
