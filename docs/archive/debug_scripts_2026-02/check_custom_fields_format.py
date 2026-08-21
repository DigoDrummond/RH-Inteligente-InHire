"""
Script para investigar o formato de requisicoes.custom_fields
"""

import sys
from pathlib import Path
import json

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from config import settings

def main():
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        print("=" * 80)
        print("INVESTIGAÇÃO: Formato de requisicoes.custom_fields")
        print("=" * 80)

        # 1. Verificar tipo de custom_fields em requisicoes
        query_type = text("""
            SELECT
                r.id,
                json_typeof(r.custom_fields) as tipo,
                r.custom_fields
            FROM requisicoes r
            WHERE r.custom_fields IS NOT NULL
            LIMIT 10
        """)

        result = conn.execute(query_type).fetchall()

        print("\n[1] TIPO DE custom_fields (primeiras 10 requisições):")
        print("-" * 80)

        array_count = 0
        object_count = 0

        for row in result:
            req_id = row[0]
            tipo = row[1]
            custom_fields = row[2]

            print(f"\nRequisição ID: {req_id}")
            print(f"  Tipo JSON: {tipo}")

            if tipo == 'array':
                array_count += 1
                print(f"  É um ARRAY com {len(custom_fields)} elementos")
                # Mostrar primeiro elemento
                if len(custom_fields) > 0:
                    print(f"  Primeiro elemento:")
                    print(f"    {json.dumps(custom_fields[0], indent=4, ensure_ascii=False)}")
            elif tipo == 'object':
                object_count += 1
                print(f"  É um OBJETO")
                # Mostrar algumas chaves
                keys = list(custom_fields.keys())[:3]
                print(f"  Primeiras chaves: {keys}")

        print(f"\n[Resumo] Array: {array_count}, Object: {object_count}")

        # 2. Contar totais
        print("\n" + "=" * 80)
        print("[2] TOTAIS POR TIPO")
        print("=" * 80)

        query_totals = text("""
            SELECT
                json_typeof(custom_fields) as tipo,
                COUNT(*) as total
            FROM requisicoes
            WHERE custom_fields IS NOT NULL
            GROUP BY json_typeof(custom_fields)
        """)

        result = conn.execute(query_totals).fetchall()
        for row in result:
            print(f"  {row[0]}: {row[1]} requisições")

        # 3. Buscar especificamente "Modalidade de Contratação" em formato array
        print("\n" + "=" * 80)
        print("[3] BUSCAR 'Modalidade de Contratação' em formato ARRAY")
        print("=" * 80)

        query_array = text("""
            SELECT
                r.id,
                r.custom_fields
            FROM requisicoes r
            WHERE json_typeof(r.custom_fields) = 'array'
              AND r.custom_fields::text LIKE '%Modalidade de Contrata%'
            LIMIT 5
        """)

        result = conn.execute(query_array).fetchall()

        if result:
            print(f"\nEncontradas {len(result)} requisições (array) com 'Modalidade de Contratação':")
            for row in result:
                req_id = row[0]
                custom_fields = row[1]

                print(f"\n--- Requisição ID: {req_id} ---")

                # Buscar o campo no array
                for item in custom_fields:
                    if isinstance(item, dict) and item.get('name') == 'Modalidade de Contratação':
                        print(f"  [ENCONTRADO]")
                        print(f"    name: {item.get('name')}")
                        print(f"    value: {item.get('value')}")
                        print(f"    type: {item.get('type')}")
                        break
        else:
            print("\n[!] Nenhuma requisição encontrada (formato array)")

        # 4. Testar a função get_custom_field_value com formato array
        print("\n" + "=" * 80)
        print("[4] TESTAR get_custom_field_value em requisições com ARRAY")
        print("=" * 80)

        query_test = text("""
            SELECT
                r.id,
                json_typeof(r.custom_fields) as tipo,
                get_custom_field_value(r.custom_fields, 'Modalidade de Contratação') as modalidade
            FROM requisicoes r
            WHERE json_typeof(r.custom_fields) = 'array'
            LIMIT 10
        """)

        result = conn.execute(query_test).fetchall()

        if result:
            print(f"\n{'ID':>6} | {'Tipo':10} | {'Modalidade de Contratação':<40}")
            print("-" * 60)
            for row in result:
                modalidade = row[2] if row[2] else '[NULL]'
                print(f"{row[0]:>6} | {row[1]:10} | {modalidade:<40}")
        else:
            print("\n[!] Nenhuma requisição com formato array")

        # 5. Comparar requisição 906 (object) vs uma com array
        print("\n" + "=" * 80)
        print("[5] COMPARAÇÃO: Requisição 906 (object) vs requisições com array")
        print("=" * 80)

        query_comp = text("""
            SELECT
                r.id,
                json_typeof(r.custom_fields) as tipo,
                get_custom_field_value(r.custom_fields, 'Modalidade de Contratação') as modalidade,
                get_custom_field_value(r.custom_fields, 'Empresa') as empresa
            FROM requisicoes r
            WHERE r.id = 906
               OR json_typeof(r.custom_fields) = 'array'
            LIMIT 6
        """)

        result = conn.execute(query_comp).fetchall()

        print(f"\n{'ID':>6} | {'Tipo':10} | {'Modalidade':20} | {'Empresa':15}")
        print("-" * 60)
        for row in result:
            modalidade = row[2][:17] + '...' if row[2] and len(row[2]) > 20 else (row[2] or '[NULL]')
            empresa = row[3][:12] + '...' if row[3] and len(row[3]) > 15 else (row[3] or '[NULL]')
            print(f"{row[0]:>6} | {row[1]:10} | {modalidade:20} | {empresa:15}")

        print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
