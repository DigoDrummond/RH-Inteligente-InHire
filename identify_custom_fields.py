# -*- coding: utf-8 -*-
"""Identifica qual campo é 'Você conhecia a Framework Digital?'"""
import sys
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

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
    print("\n=== IDENTIFICANDO CAMPOS PERSONALIZADOS ===\n")

    # Vimos anteriormente que existem 2 campos:
    # - 58401823-2cf5-4e0c-93eb-07c46508eb3a
    # - 745c6a26-c3fa-4389-9b1e-75f54934c9ae

    campos = [
        "58401823-2cf5-4e0c-93eb-07c46508eb3a",
        "745c6a26-c3fa-4389-9b1e-75f54934c9ae"
    ]

    for field_id in campos:
        print(f"\nCAMPO: {field_id}")
        print("-" * 80)

        # Contar valores
        result = session.execute(text(f"""
            SELECT
                COUNT(*) as total
            FROM candidaturas
            WHERE custom_fields ? '{field_id}'
        """))
        total = result.scalar()
        print(f"Total de candidaturas com este campo: {total}")

        # Pegar exemplos de valores únicos
        result = session.execute(text(f"""
            SELECT
                custom_fields->'{field_id}' as valor_json,
                COUNT(*) as qtd
            FROM candidaturas
            WHERE custom_fields ? '{field_id}'
            GROUP BY custom_fields->'{field_id}'
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """))

        print(f"\nValores únicos encontrados:")
        for i, row in enumerate(result.fetchall(), 1):
            try:
                valor_json = row[0]
                if isinstance(valor_json, list) and len(valor_json) > 0:
                    if isinstance(valor_json[0], dict):
                        label = valor_json[0].get('label', 'N/A')
                        print(f"   {i}. '{label}' - {row[1]} candidaturas")
                    else:
                        print(f"   {i}. {valor_json[0]} - {row[1]} candidaturas")
                else:
                    print(f"   {i}. {valor_json} - {row[1]} candidaturas")
            except Exception as e:
                print(f"   {i}. {row[0]} - {row[1]} candidaturas (erro: {e})")

    # Identificar qual é qual
    print("\n\n=== IDENTIFICAÇÃO ===\n")

    # Campo 1: Sim/Não
    result = session.execute(text(f"""
        SELECT
            (custom_fields->>'{campos[0]}')::jsonb->0->>'label' as resposta,
            COUNT(*) as qtd
        FROM candidaturas
        WHERE custom_fields ? '{campos[0]}'
        GROUP BY resposta
        ORDER BY qtd DESC
    """))

    print(f"Campo {campos[0]}:")
    respostas_campo1 = []
    for row in result.fetchall():
        print(f"   - {row[0]}: {row[1]} candidaturas")
        respostas_campo1.append(row[0])

    # Campo 2: CLT/PJ
    result = session.execute(text(f"""
        SELECT
            (custom_fields->>'{campos[1]}')::jsonb->0->>'label' as resposta,
            COUNT(*) as qtd
        FROM candidaturas
        WHERE custom_fields ? '{campos[1]}'
        GROUP BY resposta
        ORDER BY qtd DESC
    """))

    print(f"\nCampo {campos[1]}:")
    respostas_campo2 = []
    for row in result.fetchall():
        print(f"   - {row[0]}: {row[1]} candidaturas")
        respostas_campo2.append(row[0])

    # Conclusão
    print("\n\n=== CONCLUSÃO ===\n")

    if 'Sim' in respostas_campo1 and 'Não' in respostas_campo1:
        print(f"✓ Campo {campos[0]} parece ser 'Você conhecia a Framework Digital?'")
        print(f"  (Respostas: Sim/Não)")
        print(f"\n  ID CORRETO: {campos[0]}")
    else:
        print(f"Campo {campos[0]} NÃO é 'conhecia framework' (respostas: {respostas_campo1})")

    if 'CLT' in str(respostas_campo2) or 'PJ' in str(respostas_campo2):
        print(f"\n✓ Campo {campos[1]} parece ser 'Tipo de contratação'")
        print(f"  (Respostas: CLT Flex, PJ, etc)")

except Exception as e:
    print(f"\nErro: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
    engine.dispose()
