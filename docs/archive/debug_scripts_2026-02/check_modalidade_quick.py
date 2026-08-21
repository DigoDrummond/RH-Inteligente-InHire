"""
Script rápido para verificar modalidade_contratacao_req
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
        # Buscar custom_fields da requisição 906
        query = text("""
            SELECT r.id, r.custom_fields
            FROM requisicoes r
            WHERE r.id = 906
        """)

        result = conn.execute(query).fetchone()
        if result:
            req_id = result[0]
            custom_fields = result[1]

            print(f"Requisicao ID: {req_id}")
            print(f"Tipo de custom_fields: {type(custom_fields)}")
            print(f"\nCustom Fields (JSON):")

            if isinstance(custom_fields, (dict, list)):
                print(json.dumps(custom_fields, indent=2, ensure_ascii=False))

                # Se for um dicionário, buscar diretamente
                if isinstance(custom_fields, dict):
                    modalidade = custom_fields.get('Modalidade de Contratação')
                    print(f"\n'Modalidade de Contratação' (direto): {modalidade if modalidade else '[NULL ou não existe]'}")

                # Se for um array, buscar pelo name
                elif isinstance(custom_fields, list):
                    print(f"\n[!] Custom fields é um ARRAY com {len(custom_fields)} elementos")
                    modalidade = None
                    for item in custom_fields:
                        if isinstance(item, dict) and item.get('name') == 'Modalidade de Contratação':
                            modalidade = item.get('value')
                            break
                    print(f"'Modalidade de Contratação' (buscado no array): {modalidade if modalidade else '[NULL ou não encontrado]'}")

        # Testar a função do PostgreSQL
        print("\n" + "=" * 80)
        print("TESTE DA FUNÇÃO get_custom_field_value")
        print("=" * 80)

        query_func = text("""
            SELECT
                get_custom_field_value(r.custom_fields, 'Modalidade de Contratação') as modalidade
            FROM requisicoes r
            WHERE r.id = 906
        """)

        result = conn.execute(query_func).fetchone()
        if result:
            print(f"\nResultado da função: '{result[0] if result[0] else '[NULL]'}'")

if __name__ == "__main__":
    main()
