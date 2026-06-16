#!/usr/bin/env python
"""Investigar discrepância entre talent_ids"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings

def main():
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("\n" + "="*80)
    print("INVESTIGACAO: Discrepancia talent_ids")
    print("="*80 + "\n")

    # Query 1: Listar posições hired sem talento
    print("[1] Posicoes hired SEM talento correspondente...")
    query1 = text("""
    SELECT
        p.id,
        p.inhire_id,
        p.vaga_id,
        p.talent_id,
        p.hired_at::date,
        t.id as talento_existe
    FROM posicoes p
    LEFT JOIN talentos t ON t.inhire_id = p.talent_id
    WHERE p.hired_at IS NOT NULL
      AND t.id IS NULL
    LIMIT 10
    """)
    result1 = session.execute(query1).fetchall()
    if result1:
        print(f"  Encontradas {len(result1)} posicoes (mostrando primeiras 10):\n")
        print("  ID | Inhire ID | Vaga | talent_id | Hired")
        for row in result1:
            print(f"  {row[0]:4d} | {row[1][:8]}... | {row[2]:4d} | {row[3][:8] if row[3] else 'NULL'}... | {row[4]}")
    else:
        print("  Nenhuma posicao encontrada!")

    # Query 2: Contar talent_ids distintos que não existem
    print("\n[2] Talent_ids DISTINTOS que nao existem em talentos...")
    query2 = text("""
    SELECT DISTINCT p.talent_id
    FROM posicoes p
    LEFT JOIN talentos t ON t.inhire_id = p.talent_id
    WHERE p.hired_at IS NOT NULL
      AND p.talent_id IS NOT NULL
      AND t.id IS NULL
    """)
    result2 = session.execute(query2).fetchall()
    if result2:
        talent_ids = [row[0] for row in result2]
        print(f"  Total de talent_ids DISTINTOS faltantes: {len(talent_ids)}\n")
        print("  Primeiros 10:")
        for tid in talent_ids[:10]:
            print(f"  - {tid}")
    else:
        print("  Nenhum talent_id faltante!")

    # Query 3: Verificar se talent_id está NULL
    print("\n[3] Verificar se talent_id esta NULL nas posicoes...")
    query3 = text("""
    SELECT COUNT(*)
    FROM posicoes
    WHERE hired_at IS NOT NULL
      AND talent_id IS NULL
    """)
    result3 = session.execute(query3).fetchone()
    count_null = result3[0]
    print(f"  Posicoes hired com talent_id NULL: {count_null}")

    # Query 4: Verificar se talent_id está vazio (string vazia)
    print("\n[4] Verificar se talent_id esta vazio (string vazia)...")
    query4 = text("""
    SELECT COUNT(*)
    FROM posicoes
    WHERE hired_at IS NOT NULL
      AND talent_id = ''
    """)
    result4 = session.execute(query4).fetchone()
    count_empty = result4[0]
    print(f"  Posicoes hired com talent_id = '': {count_empty}")

    print("\n" + "="*80)
    print("INVESTIGACAO CONCLUIDA")
    print("="*80 + "\n")

    session.close()

if __name__ == "__main__":
    main()
