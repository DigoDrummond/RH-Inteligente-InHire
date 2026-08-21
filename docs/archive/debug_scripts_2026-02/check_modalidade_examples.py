"""
Script para verificar exemplos de requisições com Modalidade de Contratação
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
        # 1. Estatísticas gerais
        print("=" * 80)
        print("ESTATÍSTICAS - Campo 'Modalidade de Contratação'")
        print("=" * 80)

        query_stats = text("""
            SELECT
                COUNT(*) as total_requisicoes,
                COUNT(CASE WHEN custom_fields::text LIKE '%Modalidade de Contrata%' THEN 1 END) as com_campo
            FROM requisicoes
        """)

        result = conn.execute(query_stats).fetchone()
        if result:
            total = result[0]
            com_campo = result[1]
            print(f"\nTotal de requisições: {total}")
            print(f"  Com 'Modalidade de Contratação': {com_campo} ({com_campo/total*100:.1f}%)")
            print(f"  SEM 'Modalidade de Contratação': {total - com_campo} ({(total-com_campo)/total*100:.1f}%)")

        # 2. Verificar valores usando a função
        print("\n" + "=" * 80)
        print("VALORES DISTINTOS (usando get_custom_field_value)")
        print("=" * 80)

        query_valores = text("""
            SELECT
                get_custom_field_value(r.custom_fields, 'Modalidade de Contratação') as valor,
                COUNT(*) as count
            FROM requisicoes r
            WHERE get_custom_field_value(r.custom_fields, 'Modalidade de Contratação') IS NOT NULL
            GROUP BY get_custom_field_value(r.custom_fields, 'Modalidade de Contratação')
            ORDER BY count DESC
        """)

        result = conn.execute(query_valores).fetchall()
        if result:
            print(f"\nValores encontrados:")
            for row in result:
                print(f"  '{row[0]}': {row[1]} requisições")
        else:
            print("\n[!] Nenhum valor encontrado (função retorna NULL)")

        # 3. Exemplo de requisição COM o campo
        print("\n" + "=" * 80)
        print("EXEMPLO DE REQUISIÇÃO COM O CAMPO")
        print("=" * 80)

        query_exemplo = text("""
            SELECT
                r.id,
                r.custom_fields
            FROM requisicoes r
            WHERE custom_fields::text LIKE '%Modalidade de Contrata%'
            LIMIT 1
        """)

        result = conn.execute(query_exemplo).fetchone()
        if result:
            req_id = result[0]
            custom_fields = result[1]

            print(f"\nRequisição ID: {req_id}")
            print(f"Tipo: {type(custom_fields)}")

            if isinstance(custom_fields, dict):
                modalidade = custom_fields.get('Modalidade de Contratação')
                print(f"\nValor do campo: '{modalidade}'")

                print(f"\nTodos os campos (apenas não vazios):")
                for key in sorted(custom_fields.keys()):
                    valor = custom_fields[key]
                    if valor and valor != '':
                        print(f"  - '{key}': '{valor}'")

        # 4. Comparação: requisição 906 vs uma que TEM o campo
        print("\n" + "=" * 80)
        print("COMPARAÇÃO: Requisição 906 vs uma COM o campo")
        print("=" * 80)

        query_comp = text("""
            SELECT
                r.id,
                get_custom_field_value(r.custom_fields, 'Modalidade de Contratação') as modalidade,
                get_custom_field_value(r.custom_fields, 'Empresa') as empresa,
                get_custom_field_value(r.custom_fields, 'Tipo de Serviço') as tipo_servico
            FROM requisicoes r
            WHERE r.id = 906
               OR custom_fields::text LIKE '%Modalidade de Contrata%'
            LIMIT 5
        """)

        result = conn.execute(query_comp).fetchall()
        print(f"\n{'ID':>6} | {'Modalidade':30} | {'Empresa':15} | {'Tipo Serviço':25}")
        print("-" * 90)
        for row in result:
            modalidade = row[1] if row[1] else '[NULL]'
            empresa = row[2] if row[2] else '[NULL]'
            tipo_servico = row[3] if row[3] else '[NULL]'
            print(f"{row[0]:>6} | {modalidade[:30]:30} | {empresa[:15]:15} | {tipo_servico[:25]:25}")

        print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
