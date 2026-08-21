"""
Script para investigar o campo approval_workflow em requisicoes
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
        # 1. Verificar estrutura do campo approval_workflow
        print("=" * 80)
        print("ESTRUTURA DO CAMPO approval_workflow")
        print("=" * 80)

        query_sample = text("""
            SELECT
                r.id,
                r.approval_workflow
            FROM requisicoes r
            WHERE r.approval_workflow IS NOT NULL
            LIMIT 5
        """)

        result = conn.execute(query_sample).fetchall()

        if result:
            for row in result:
                req_id = row[0]
                approval_workflow = row[1]

                print(f"\nRequisição ID: {req_id}")
                print(f"Tipo: {type(approval_workflow)}")

                if isinstance(approval_workflow, (dict, list)):
                    print(f"Conteúdo:")
                    print(json.dumps(approval_workflow, indent=2, ensure_ascii=False))

                    # Buscar campo "name"
                    if isinstance(approval_workflow, dict):
                        name = approval_workflow.get('name')
                        print(f"\nCampo 'name': {name}")
                    elif isinstance(approval_workflow, list):
                        print(f"\n[!] É uma lista com {len(approval_workflow)} elementos")
                        for idx, item in enumerate(approval_workflow):
                            if isinstance(item, dict):
                                name = item.get('name')
                                if name:
                                    print(f"  Item {idx}: name = '{name}'")

                print("-" * 80)

        # 2. Estatísticas
        print("\n" + "=" * 80)
        print("ESTATÍSTICAS")
        print("=" * 80)

        query_stats = text("""
            SELECT
                COUNT(*) as total,
                COUNT(approval_workflow) as com_approval_workflow
            FROM requisicoes
        """)

        result = conn.execute(query_stats).fetchone()
        if result:
            total = result[0]
            com_workflow = result[1]
            print(f"\nTotal de requisições: {total}")
            print(f"  Com approval_workflow: {com_workflow} ({com_workflow/total*100:.1f}%)")

        # 3. Verificar requisição 906 (position 1714)
        print("\n" + "=" * 80)
        print("REQUISIÇÃO 906 (Position 1714)")
        print("=" * 80)

        query_906 = text("""
            SELECT
                r.id,
                r.approval_workflow
            FROM requisicoes r
            WHERE r.id = 906
        """)

        result = conn.execute(query_906).fetchone()
        if result:
            req_id = result[0]
            approval_workflow = result[1]

            print(f"\nRequisição ID: {req_id}")

            if approval_workflow:
                print(f"Tipo: {type(approval_workflow)}")
                print(f"\nConteúdo:")
                print(json.dumps(approval_workflow, indent=2, ensure_ascii=False))

                # Buscar "name"
                if isinstance(approval_workflow, dict):
                    name = approval_workflow.get('name')
                    print(f"\nCampo 'name': {name if name else '[NULL]'}")
                elif isinstance(approval_workflow, list):
                    print(f"\n[!] É uma lista com {len(approval_workflow)} elementos")
                    for idx, item in enumerate(approval_workflow):
                        if isinstance(item, dict):
                            name = item.get('name')
                            if name:
                                print(f"  Item {idx}: name = '{name}'")
            else:
                print("[NULL]")

        # 4. Buscar especificamente por "Requisição Posições Billable"
        print("\n" + "=" * 80)
        print("BUSCAR 'Requisição Posições Billable'")
        print("=" * 80)

        query_billable = text("""
            SELECT
                r.id,
                r.approval_workflow::text
            FROM requisicoes r
            WHERE r.approval_workflow::text LIKE '%Billable%'
               OR r.approval_workflow::text LIKE '%billable%'
            LIMIT 10
        """)

        result = conn.execute(query_billable).fetchall()
        if result:
            print(f"\nEncontradas {len(result)} requisições com 'Billable':")
            for row in result:
                print(f"  Requisição ID: {row[0]}")
        else:
            print("\n[!] Nenhuma requisição encontrada com 'Billable'")

        print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
