"""
Script para validar Migration 057 - campo nome_workflow_aprovacao
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from config import settings

def main():
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        print("=" * 80)
        print("VALIDAÇÃO MIGRATION 057 - nome_workflow_aprovacao")
        print("=" * 80)

        # 1. Verificar que o campo existe
        query_field = text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'vw_analise_posicoes'
              AND column_name = 'nome_workflow_aprovacao'
        """)

        result = conn.execute(query_field).fetchone()
        if result:
            print(f"\n[OK] Campo 'nome_workflow_aprovacao' existe na view")
            print(f"     Tipo: {result[1]}")
        else:
            print("\n[ERRO] Campo 'nome_workflow_aprovacao' NÃO encontrado!")
            return

        # 2. Estatísticas do novo campo
        print("\n" + "=" * 80)
        print("ESTATÍSTICAS")
        print("=" * 80)

        query_stats = text("""
            SELECT
                COUNT(*) as total,
                COUNT(nome_workflow_aprovacao) as com_workflow,
                COUNT(DISTINCT nome_workflow_aprovacao) as workflows_distintos
            FROM vw_analise_posicoes
        """)

        result = conn.execute(query_stats).fetchone()
        if result:
            total = result[0]
            com_workflow = result[1]
            workflows_distintos = result[2]

            print(f"\nTotal de posições: {total}")
            print(f"  Com nome_workflow_aprovacao: {com_workflow} ({com_workflow/total*100:.1f}%)")
            print(f"  Workflows distintos: {workflows_distintos}")

        # 3. Valores distintos
        print("\n" + "=" * 80)
        print("VALORES DISTINTOS")
        print("=" * 80)

        query_valores = text("""
            SELECT
                nome_workflow_aprovacao,
                COUNT(*) as count
            FROM vw_analise_posicoes
            WHERE nome_workflow_aprovacao IS NOT NULL
            GROUP BY nome_workflow_aprovacao
            ORDER BY count DESC
        """)

        result = conn.execute(query_valores).fetchall()
        if result:
            print(f"\n{'Workflow':<50} {'Count':>10}")
            print("-" * 62)
            for row in result:
                workflow = row[0][:47] + '...' if len(row[0]) > 50 else row[0]
                print(f"{workflow:<50} {row[1]:>10}")
        else:
            print("\n[!] Nenhum valor encontrado")

        # 4. Verificar algumas posições específicas
        print("\n" + "=" * 80)
        print("EXEMPLOS")
        print("=" * 80)

        query_exemplos = text("""
            SELECT
                id_position,
                cargo,
                nome_workflow_aprovacao
            FROM vw_analise_posicoes
            WHERE nome_workflow_aprovacao IS NOT NULL
            LIMIT 5
        """)

        result = conn.execute(query_exemplos).fetchall()
        if result:
            print(f"\n{'ID':>6} | {'Cargo':<40} | {'Workflow':<40}")
            print("-" * 90)
            for row in result:
                cargo = row[1][:37] + '...' if len(row[1]) > 40 else row[1]
                workflow = row[2][:37] + '...' if len(row[2]) > 40 else row[2]
                print(f"{row[0]:>6} | {cargo:<40} | {workflow:<40}")

        # 5. Verificar position 1714
        print("\n" + "=" * 80)
        print("POSITION 1714 (Exemplo do usuário)")
        print("=" * 80)

        query_1714 = text("""
            SELECT
                id_position,
                cargo,
                nome_workflow_aprovacao
            FROM vw_analise_posicoes
            WHERE id_position = 1714
        """)

        result = conn.execute(query_1714).fetchone()
        if result:
            print(f"\nPosition ID: {result[0]}")
            print(f"Cargo: {result[1]}")
            print(f"nome_workflow_aprovacao: {result[2] if result[2] else '[NULL]'}")

        # 6. Total de colunas
        print("\n" + "=" * 80)
        print("TOTAL DE COLUNAS NA VIEW")
        print("=" * 80)

        query_cols = text("""
            SELECT COUNT(*) as total_colunas
            FROM information_schema.columns
            WHERE table_name = 'vw_analise_posicoes'
        """)

        result = conn.execute(query_cols).fetchone()
        if result:
            print(f"\nTotal de colunas: {result[0]}")

        print("\n" + "=" * 80)
        print("[OK] MIGRATION 057 VALIDADA COM SUCESSO!")
        print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
