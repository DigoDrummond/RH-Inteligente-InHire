"""
Script para investigar o campo modalidade_contratacao_req
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
        print("ANÁLISE: modalidade_contratacao_req")
        print("=" * 80)

        # 1. Verificar campo na view
        print("\n[1] Valor na view vw_analise_posicoes (Position 1714):")
        query_view = text("""
            SELECT
                id_position,
                cargo,
                modalidade_contratacao_req,
                modalidade_contratacao
            FROM vw_analise_posicoes
            WHERE id_position = 1714
        """)

        result = conn.execute(query_view).fetchone()
        if result:
            print(f"  Position: {result[0]}")
            print(f"  Cargo: {result[1]}")
            print(f"  modalidade_contratacao_req: '{result[2] if result[2] else '[NULL]'}'")
            print(f"  modalidade_contratacao (vagas): '{result[3] if result[3] else '[NULL]'}'")

        # 2. Buscar no JSONB de requisicoes
        print("\n" + "=" * 80)
        print("[2] Campos relacionados a 'Modalidade' em requisicoes.custom_fields:")
        print("=" * 80)

        query_campos = text("""
            SELECT DISTINCT
                jsonb_object_keys(custom_fields) as campo
            FROM requisicoes
            WHERE custom_fields IS NOT NULL
        """)

        result = conn.execute(query_campos).fetchall()
        campos_modalidade = [row[0] for row in result if 'modalidade' in row[0].lower() or 'contrata' in row[0].lower()]

        if campos_modalidade:
            print("\nCampos que contêm 'modalidade' ou 'contrata':")
            for campo in sorted(campos_modalidade):
                print(f"  - {campo}")
        else:
            print("\n[!] Nenhum campo contém 'modalidade' ou 'contrata'")

        # 3. Verificar valores em 'Modalidade de Contratação'
        print("\n" + "=" * 80)
        print("[3] Valores em 'Modalidade de Contratação':")
        print("=" * 80)

        query_valores = text("""
            SELECT
                custom_fields->>'Modalidade de Contratação' as valor,
                COUNT(*) as count
            FROM requisicoes
            WHERE custom_fields->>'Modalidade de Contratação' IS NOT NULL
              AND custom_fields->>'Modalidade de Contratação' != ''
            GROUP BY custom_fields->>'Modalidade de Contratação'
            ORDER BY count DESC
        """)

        result = conn.execute(query_valores).fetchall()
        if result:
            total_preenchido = sum(row[1] for row in result)
            print(f"\nTotal de requisições com este campo preenchido: {total_preenchido}")
            for row in result:
                print(f"  '{row[0]}': {row[1]} requisições")
        else:
            print("\n[!] Nenhuma requisição tem 'Modalidade de Contratação' preenchida")

        # 4. Estatísticas gerais
        print("\n" + "=" * 80)
        print("[4] Cobertura geral:")
        print("=" * 80)

        query_stats = text("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN custom_fields->>'Modalidade de Contratação' IS NOT NULL
                           AND custom_fields->>'Modalidade de Contratação' != ''
                           THEN 1 END) as com_modalidade
            FROM requisicoes
        """)

        result = conn.execute(query_stats).fetchone()
        if result:
            total = result[0]
            com_modalidade = result[1]
            print(f"\nTotal de requisições: {total}")
            print(f"  Com 'Modalidade de Contratação': {com_modalidade} ({com_modalidade/total*100:.1f}%)")

        # 5. Position 1714 - dados brutos
        print("\n" + "=" * 80)
        print("[5] Position 1714 - Dados brutos da requisição:")
        print("=" * 80)

        query_1714 = text("""
            SELECT
                r.id,
                r.custom_fields
            FROM requisicoes r
            JOIN vagas v ON v.inhire_id = r.job_inhire_id
            JOIN posicoes p ON p.vaga_id = v.id
            WHERE p.id = 1714
        """)

        result = conn.execute(query_1714).fetchone()
        if result:
            req_id = result[0]
            custom_fields = result[1] or {}

            print(f"\nRequisição ID: {req_id}")
            print(f"\nTodos os custom_fields (chaves ordenadas):")
            for key in sorted(custom_fields.keys()):
                valor = custom_fields[key]
                if valor and valor != '':
                    print(f"  - '{key}': '{valor}'")
                else:
                    print(f"  - '{key}': [VAZIO]")

        # 6. Verificar na view vw_analise_posicoes - estatísticas
        print("\n" + "=" * 80)
        print("[6] Estatísticas na view vw_analise_posicoes:")
        print("=" * 80)

        query_view_stats = text("""
            SELECT
                COUNT(*) as total,
                COUNT(modalidade_contratacao_req) as com_modalidade_req,
                COUNT(modalidade_contratacao) as com_modalidade_vaga
            FROM vw_analise_posicoes
        """)

        result = conn.execute(query_view_stats).fetchone()
        if result:
            total = result[0]
            com_req = result[1]
            com_vaga = result[2]
            print(f"\nTotal de posições: {total}")
            print(f"  Com modalidade_contratacao_req: {com_req} ({com_req/total*100:.1f}%)")
            print(f"  Com modalidade_contratacao (vagas): {com_vaga} ({com_vaga/total*100:.1f}%)")

        print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
