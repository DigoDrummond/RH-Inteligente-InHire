# -*- coding: utf-8 -*-
"""Verifica a aplicação dos filtros e quantidades"""
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
    print("\n=== VERIFICAÇÃO DE FILTROS ===\n")

    # 1. Total de candidaturas 2026
    result = session.execute(text("""
        SELECT COUNT(*)
        FROM candidaturas c
        WHERE EXTRACT(YEAR FROM c.created_at) = 2026
    """))
    total_2026 = result.scalar()
    print(f"1. Total candidaturas 2026: {total_2026}")

    # 2. Com filtro de empresa
    result = session.execute(text("""
        SELECT COUNT(*)
        FROM candidaturas c
        INNER JOIN vagas v ON c.vaga_id = v.id
        LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
        WHERE EXTRACT(YEAR FROM c.created_at) = 2026
          AND cl.name = 'Framework'
    """))
    com_framework = result.scalar()
    print(f"2. Candidaturas 2026 + Framework: {com_framework}")

    # 3. Com filtro de workflow
    result = session.execute(text("""
        SELECT COUNT(*)
        FROM candidaturas c
        INNER JOIN vagas v ON c.vaga_id = v.id
        LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
        WHERE EXTRACT(YEAR FROM c.created_at) = 2026
          AND r.approval_workflow->>'name' = 'Requisição Posições Billable'
    """))
    com_workflow = result.scalar()
    print(f"3. Candidaturas 2026 + Workflow Billable: {com_workflow}")

    # 4. Com AMBOS os filtros (AND)
    result = session.execute(text("""
        SELECT COUNT(*)
        FROM candidaturas c
        INNER JOIN vagas v ON c.vaga_id = v.id
        LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
        LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
        WHERE EXTRACT(YEAR FROM c.created_at) = 2026
          AND cl.name = 'Framework'
          AND r.approval_workflow->>'name' = 'Requisição Posições Billable'
    """))
    com_ambos = result.scalar()
    print(f"4. Candidaturas 2026 + Framework + Workflow: {com_ambos}")

    # 5. Verificar se existem vagas Framework SEM workflow
    result = session.execute(text("""
        SELECT COUNT(DISTINCT v.id)
        FROM vagas v
        LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
        LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
        WHERE cl.name = 'Framework'
          AND r.approval_workflow IS NULL
    """))
    vagas_sem_workflow = result.scalar()
    print(f"5. Vagas Framework SEM workflow: {vagas_sem_workflow}")

    # 6. Verificar se existem vagas Framework com workflow diferente
    result = session.execute(text("""
        SELECT
            r.approval_workflow->>'name' as workflow,
            COUNT(DISTINCT v.id) as vagas_count
        FROM vagas v
        LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
        LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
        WHERE cl.name = 'Framework'
          AND r.approval_workflow IS NOT NULL
        GROUP BY r.approval_workflow->>'name'
        ORDER BY vagas_count DESC
    """))

    print(f"\n6. Workflows nas vagas Framework:")
    for row in result.fetchall():
        print(f"   - '{row[0]}': {row[1]} vagas")

    # 7. Amostra de candidaturas Framework
    result = session.execute(text("""
        SELECT
            c.id,
            c.talent_name,
            v.name as vaga_nome,
            cl.name as cliente,
            r.approval_workflow->>'name' as workflow
        FROM candidaturas c
        INNER JOIN vagas v ON c.vaga_id = v.id
        LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
        LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
        WHERE EXTRACT(YEAR FROM c.created_at) = 2026
          AND cl.name = 'Framework'
        LIMIT 10
    """))

    print(f"\n7. Amostra de candidaturas Framework (10 primeiras):")
    for row in result.fetchall():
        print(f"   - {row[1]}: {row[2]}")
        print(f"     Cliente: {row[3]}, Workflow: {row[4]}")

    print("\n" + "="*60)

finally:
    session.close()
    engine.dispose()
