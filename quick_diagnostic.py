#!/usr/bin/env python
"""Script rápido de diagnóstico - E-mails NULL"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings
import logging

logging.basicConfig(level=logging.INFO)

def main():
    # Criar engine e session
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("\n" + "="*80)
    print("DIAGNOSTICO: E-mails NULL em Candidatos Contratados")
    print("="*80 + "\n")

    # Query 1: Total de posições com hired_at
    print("[Query 1] Posicoes com hired_at...")
    query1 = text("""
    SELECT
        COUNT(*) as total_posicoes_hired,
        COUNT(talent_id) as com_talent_id,
        COUNT(*) FILTER (WHERE talent_id IS NULL) as sem_talent_id
    FROM posicoes
    WHERE hired_at IS NOT NULL
    """)
    result1 = session.execute(query1).fetchall()
    if result1:
        row = result1[0]
        print(f"  Total posicoes com hired_at: {row[0]}")
        print(f"  Com talent_id preenchido: {row[1]}")
        print(f"  Sem talent_id (NULL): {row[2]}")
        if row[0] > 0:
            pct = (row[2] / row[0]) * 100
            print(f"  Percentual sem talent_id: {pct:.2f}%\n")

    # Query 2: Verificar candidaturas com e-mails
    print("[Query 2] Candidaturas em estagio 'Contratacao' com e-mail...")
    query2 = text("""
    SELECT
        COUNT(*) as total_contratacao,
        COUNT(talent_name) as com_nome,
        COUNT(talent_email) as com_email
    FROM candidaturas
    WHERE stage_name = 'Contratação'
    """)
    result2 = session.execute(query2).fetchall()
    if result2:
        row = result2[0]
        print(f"  Total candidaturas 'Contratacao': {row[0]}")
        print(f"  Com nome do talento: {row[1]}")
        print(f"  Com e-mail do talento: {row[2]}\n")

    # Query 3: Cruzar posições hired com candidaturas
    print("[Query 3] Cruzamento posicoes x candidaturas...")
    query3 = text("""
    SELECT
        COUNT(DISTINCT p.id) as posicoes_hired,
        COUNT(DISTINCT c.vaga_id) as posicoes_com_candidatura_contratacao,
        COUNT(DISTINCT c.id) FILTER (WHERE c.talent_email IS NOT NULL) as candidaturas_com_email
    FROM posicoes p
    LEFT JOIN candidaturas c ON c.vaga_id = p.vaga_id
                             AND c.stage_name = 'Contratação'
    WHERE p.hired_at IS NOT NULL
    """)
    result3 = session.execute(query3).fetchall()
    if result3:
        row = result3[0]
        print(f"  Posicoes com hired_at: {row[0]}")
        print(f"  Posicoes que tem candidatura em 'Contratacao': {row[1]}")
        print(f"  Candidaturas com e-mail disponivel: {row[2]}\n")

    # Query 4: Amostra de casos problemáticos
    print("[Query 4] Amostra de 10 casos sem talent_id...")
    query4 = text("""
    SELECT
        p.id,
        p.inhire_id,
        p.vaga_id,
        p.hired_at::date,
        p.talent_id,
        c.talent_name,
        c.talent_email
    FROM posicoes p
    LEFT JOIN candidaturas c ON c.vaga_id = p.vaga_id
                             AND c.stage_name = 'Contratação'
    WHERE p.hired_at IS NOT NULL
      AND p.talent_id IS NULL
    ORDER BY p.hired_at DESC
    LIMIT 10
    """)
    result4 = session.execute(query4).fetchall()
    if result4:
        print("\n  Amostra de casos (ID | Inhire ID | Vaga | Hired | talent_id | Nome | Email):")
        for row in result4:
            print(f"  {row[0]:4d} | {row[1][:8]}... | {row[2]:4d} | {row[3]} | {row[4] or 'NULL'} | {row[5] or 'NULL'} | {row[6] or 'NULL'}")

    # Query 5: Verificar colunas da tabela posicoes
    print("\n[Query 5] Listar colunas da tabela posicoes...")
    query5 = text("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'posicoes'
    AND column_name LIKE '%motivo%'
    ORDER BY column_name
    """)
    result5 = session.execute(query5).fetchall()
    if result5:
        colunas = [row[0] for row in result5]
        print(f"  Colunas com 'motivo': {', '.join(colunas) if colunas else 'Nenhuma encontrada'}\n")
    else:
        print("  Nenhuma coluna com 'motivo' encontrada\n")

    # Query 6: Verificar casos onde talent_id está OK mas email pode estar NULL na view
    print("[Query 6] Cruzar com talentos para verificar e-mails...")
    query6 = text("""
    SELECT
        COUNT(DISTINCT p.id) as posicoes_hired,
        COUNT(DISTINCT t.id) as talentos_encontrados,
        COUNT(t.email) FILTER (WHERE t.email IS NOT NULL) as talentos_com_email
    FROM posicoes p
    LEFT JOIN talentos t ON t.inhire_id = p.talent_id
    WHERE p.hired_at IS NOT NULL
    """)
    result6 = session.execute(query6).fetchall()
    if result6:
        row = result6[0]
        print(f"  Posicoes hired: {row[0]}")
        print(f"  Talentos encontrados (JOIN com talent_id): {row[1]}")
        print(f"  Talentos com e-mail preenchido: {row[2]}\n")

    print("\n" + "="*80)
    print("DIAGNOSTICO CONCLUIDO")
    print("="*80 + "\n")

    session.close()

if __name__ == "__main__":
    main()
