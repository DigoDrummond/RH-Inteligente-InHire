# -*- coding: utf-8 -*-
"""Script temporário para validar custom fields"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Carregar .env
load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'inhire')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Criar engine
engine = create_engine(
    f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Contar candidaturas com custom_fields
    result = session.execute(text("""
        SELECT COUNT(*) as total
        FROM candidaturas
    """))
    count_total = result.scalar()

    result = session.execute(text("""
        SELECT COUNT(*) as with_custom
        FROM candidaturas
        WHERE custom_fields IS NOT NULL
    """))
    count_with_custom = result.scalar()

    print(f"\n=== VALIDAÇÃO DE CUSTOM FIELDS ===")
    print(f"Total de candidaturas: {count_total}")
    print(f"Com custom_fields: {count_with_custom}")
    if count_total > 0:
        print(f"Percentual: {(count_with_custom/count_total*100):.2f}%")

    # Buscar exemplos com custom_fields
    print(f"\n=== EXEMPLOS COM CUSTOM FIELDS ===")
    result = session.execute(text("""
        SELECT
            id,
            talent_name,
            vaga_id,
            custom_fields,
            custom_fields->>'55282edb-bb11-4445-8cd6-3c0c6b9ddb9a' as conhecia_framework
        FROM candidaturas
        WHERE custom_fields IS NOT NULL
        LIMIT 5
    """))

    for i, row in enumerate(result.fetchall(), 1):
        print(f"\n{i}. Candidatura ID: {row[0]}")
        print(f"   Talento: {row[1]}")
        print(f"   Vaga ID: {row[2]}")
        print(f"   Custom Fields: {row[3]}")
        print(f"   Conhecia Framework?: {row[4]}")

    # Buscar ADLER
    print(f"\n=== CANDIDATO ADLER ===")
    result = session.execute(text("""
        SELECT
            id,
            talent_name,
            talent_email,
            vaga_id,
            custom_fields,
            created_at,
            updated_at_inhire
        FROM candidaturas
        WHERE LOWER(talent_name) LIKE '%adler%'
           OR LOWER(talent_email) LIKE '%adler%'
        LIMIT 1
    """))

    row = result.fetchone()
    if row:
        print(f"ID: {row[0]}")
        print(f"Nome: {row[1]}")
        print(f"Email: {row[2]}")
        print(f"Vaga ID: {row[3]}")
        print(f"Custom Fields: {row[4]}")
        print(f"Criado em: {row[5]}")
        print(f"Atualizado em (API): {row[6]}")

        if row[4] is None:
            print("\n⚠️ Custom Fields está NULL - possível que:")
            print("  1. API não retornou custom fields para esta candidatura")
            print("  2. Validação Pydantic falhou (veja erros no log de sincronização)")
            print("  3. Candidatura foi criada antes da migration 069")
    else:
        print("❌ Candidato ADLER não encontrado!")

except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
