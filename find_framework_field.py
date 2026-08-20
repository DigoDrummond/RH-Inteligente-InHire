# -*- coding: utf-8 -*-
"""Script para encontrar o campo 'Você conhecia a Framework Digital?'"""
import sys
import os
from dotenv import load_dotenv
from services.auth_service import AuthService
from services.api_client import InhireAPIClient
import json

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

print("\n" + "="*80)
print("BUSCANDO CAMPO 'VOCÊ CONHECIA A FRAMEWORK DIGITAL?'")
print("="*80)

# Autenticar
print("\n1. Autenticando...")
auth_service = AuthService()
if not auth_service.authenticate():
    print("   ❌ Falha na autenticação")
    sys.exit(1)

api_client = InhireAPIClient(auth_service=auth_service)
print("   ✅ Autenticado")

# Buscar vagas com custom fields
print("\n2. Buscando vagas com custom fields...")

try:
    vagas = list(api_client.get_all_vagas())
    print(f"   - Total de vagas: {len(vagas)}")

    # Procurar vagas com customFields
    vagas_com_custom_fields = []

    for vaga in vagas:
        # Verificar se tem customFields
        if hasattr(vaga, 'customFields') and vaga.customFields:
            vagas_com_custom_fields.append(vaga)

    print(f"   - Vagas com customFields: {len(vagas_com_custom_fields)}")

    if not vagas_com_custom_fields:
        print("\n   ⚠️ Nenhuma vaga tem customFields configurado!")
        print("   Isso significa que os campos personalizados não estão nas vagas,")
        print("   mas sim nas candidaturas (job talents).")

        print("\n3. Analisando custom fields das CANDIDATURAS salvas no BD...")

        # Importar para consultar BD
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker

        DB_HOST = os.getenv('DB_HOST', 'localhost')
        DB_PORT = os.getenv('DB_PORT', '5432')
        DB_NAME = os.getenv('DB_NAME', 'inhire')
        DB_USER = os.getenv('DB_USER', 'postgres')
        DB_PASSWORD = os.getenv('DB_PASSWORD')

        engine = create_engine(
            f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}',
            pool_pre_ping=True,
            pool_size=1
        )
        Session = sessionmaker(bind=engine)
        session = Session()

        # Buscar TODOS os IDs de custom fields únicos
        result = session.execute(text("""
            SELECT DISTINCT jsonb_object_keys(custom_fields) as field_id
            FROM candidaturas
            WHERE custom_fields IS NOT NULL
        """))

        field_ids = [row[0] for row in result.fetchall()]

        print(f"\n   IDs de custom fields encontrados: {len(field_ids)}")

        for field_id in field_ids:
            print(f"\n   Analisando campo: {field_id}")

            # Pegar exemplos deste campo
            result = session.execute(text(f"""
                SELECT
                    custom_fields->>'{field_id}' as valor_raw,
                    talent_name
                FROM candidaturas
                WHERE custom_fields ? '{field_id}'
                LIMIT 3
            """))

            rows = result.fetchall()

            if rows:
                print(f"      Exemplos de valores:")
                for i, row in enumerate(rows[:3], 1):
                    try:
                        valor = json.loads(row[0])
                        if isinstance(valor, list) and len(valor) > 0:
                            if isinstance(valor[0], dict):
                                label = valor[0].get('label', 'N/A')
                                print(f"         {i}. {row[1]}: {label}")
                            else:
                                print(f"         {i}. {row[1]}: {valor[0]}")
                    except:
                        print(f"         {i}. {row[1]}: {row[0]}")

        # Tentar identificar qual é o campo "Você conhecia a Framework Digital?"
        print("\n\n4. Tentando identificar o campo correto...")

        # Buscar campo com valores "Sim" ou "Não"
        for field_id in field_ids:
            result = session.execute(text(f"""
                SELECT
                    custom_fields->>'{field_id}' as valor_raw,
                    COUNT(*) as total
                FROM candidaturas
                WHERE custom_fields ? '{field_id}'
                  AND (
                      custom_fields->>'{field_id}' LIKE '%Sim%'
                      OR custom_fields->>'{field_id}' LIKE '%Não%'
                  )
                GROUP BY custom_fields->>'{field_id}'
                LIMIT 10
            """))

            rows = result.fetchall()

            if rows:
                print(f"\n   ✓ Campo {field_id} tem valores Sim/Não:")
                for row in rows:
                    print(f"      - {row[0]}: {row[1]} candidaturas")

                # Verificar se é o campo Framework
                result = session.execute(text(f"""
                    SELECT
                        talent_name,
                        custom_fields->>'{field_id}' as valor
                    FROM candidaturas
                    WHERE custom_fields ? '{field_id}'
                    LIMIT 5
                """))

                print(f"\n      Exemplos:")
                for row in result.fetchall():
                    print(f"         - {row[0]}: {row[1]}")

        session.close()
        engine.dispose()

    else:
        print("\n3. Vagas com customFields:")

        for i, vaga in enumerate(vagas_com_custom_fields[:5], 1):
            print(f"\n   {i}. Vaga: {vaga.name}")
            print(f"      CustomFields: {vaga.customFields}")

except Exception as e:
    print(f"\n   ❌ Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("BUSCA CONCLUÍDA")
print("="*80 + "\n")
