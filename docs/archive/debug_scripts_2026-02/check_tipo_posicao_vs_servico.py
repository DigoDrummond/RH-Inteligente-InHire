"""
Script para comparar "Tipo de Posição" vs "Tipo de Serviço" em requisicoes.custom_fields
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
        print("ANÁLISE: 'Tipo de Posição' vs 'Tipo de Serviço'")
        print("=" * 80)

        # 1. Contagem geral
        query_count = text("""
            SELECT
                COUNT(*) as total_requisicoes,
                COUNT(CASE WHEN custom_fields->>'Tipo de Posição' IS NOT NULL
                           AND custom_fields->>'Tipo de Posição' != ''
                           THEN 1 END) as com_tipo_posicao,
                COUNT(CASE WHEN custom_fields->>'Tipo de Serviço' IS NOT NULL
                           AND custom_fields->>'Tipo de Serviço' != ''
                           THEN 1 END) as com_tipo_servico,
                COUNT(CASE WHEN (custom_fields->>'Tipo de Posição' IS NOT NULL AND custom_fields->>'Tipo de Posição' != '')
                           OR (custom_fields->>'Tipo de Serviço' IS NOT NULL AND custom_fields->>'Tipo de Serviço' != '')
                           THEN 1 END) as com_algum_tipo
            FROM requisicoes
        """)

        result = conn.execute(query_count).fetchone()
        if result:
            total = result[0]
            tipo_posicao = result[1]
            tipo_servico = result[2]
            algum_tipo = result[3]

            print(f"\nTotal de requisições: {total}")
            print(f"  Com 'Tipo de Posição' preenchido: {tipo_posicao} ({tipo_posicao/total*100:.1f}%)")
            print(f"  Com 'Tipo de Serviço' preenchido: {tipo_servico} ({tipo_servico/total*100:.1f}%)")
            print(f"  Com ALGUM dos dois preenchido: {algum_tipo} ({algum_tipo/total*100:.1f}%)")

        # 2. Valores distintos de cada campo
        print("\n" + "=" * 80)
        print("VALORES DISTINTOS EM 'Tipo de Posição'")
        print("=" * 80)

        query_valores_posicao = text("""
            SELECT
                custom_fields->>'Tipo de Posição' as valor,
                COUNT(*) as count
            FROM requisicoes
            WHERE custom_fields->>'Tipo de Posição' IS NOT NULL
              AND custom_fields->>'Tipo de Posição' != ''
            GROUP BY custom_fields->>'Tipo de Posição'
            ORDER BY count DESC
            LIMIT 20
        """)

        result = conn.execute(query_valores_posicao).fetchall()
        for row in result:
            print(f"  {row[0]}: {row[1]} requisições")

        print("\n" + "=" * 80)
        print("VALORES DISTINTOS EM 'Tipo de Serviço'")
        print("=" * 80)

        query_valores_servico = text("""
            SELECT
                custom_fields->>'Tipo de Serviço' as valor,
                COUNT(*) as count
            FROM requisicoes
            WHERE custom_fields->>'Tipo de Serviço' IS NOT NULL
              AND custom_fields->>'Tipo de Serviço' != ''
            GROUP BY custom_fields->>'Tipo de Serviço'
            ORDER BY count DESC
            LIMIT 20
        """)

        result = conn.execute(query_valores_servico).fetchall()
        for row in result:
            print(f"  {row[0]}: {row[1]} requisições")

        # 3. Verificar ambos preenchidos
        print("\n" + "=" * 80)
        print("REQUISIÇÕES COM AMBOS OS CAMPOS PREENCHIDOS")
        print("=" * 80)

        query_ambos = text("""
            SELECT
                custom_fields->>'Tipo de Posição' as tipo_posicao,
                custom_fields->>'Tipo de Serviço' as tipo_servico,
                COUNT(*) as count
            FROM requisicoes
            WHERE custom_fields->>'Tipo de Posição' IS NOT NULL
              AND custom_fields->>'Tipo de Posição' != ''
              AND custom_fields->>'Tipo de Serviço' IS NOT NULL
              AND custom_fields->>'Tipo de Serviço' != ''
            GROUP BY custom_fields->>'Tipo de Posição', custom_fields->>'Tipo de Serviço'
            ORDER BY count DESC
            LIMIT 20
        """)

        result = conn.execute(query_ambos).fetchall()
        if result:
            for row in result:
                print(f"  Tipo Posição: '{row[0]}' | Tipo Serviço: '{row[1]}' | Count: {row[2]}")
        else:
            print("  [!] Nenhuma requisição tem ambos os campos preenchidos")

        # 4. Position 1714 como exemplo
        print("\n" + "=" * 80)
        print("POSITION 1714 (EXEMPLO)")
        print("=" * 80)

        query_1714 = text("""
            SELECT
                r.id as req_id,
                r.custom_fields->>'Tipo de Posição' as tipo_posicao,
                r.custom_fields->>'Tipo de Serviço' as tipo_servico
            FROM requisicoes r
            JOIN vagas v ON v.inhire_id = r.job_inhire_id
            JOIN posicoes p ON p.vaga_id = v.id
            WHERE p.id = 1714
        """)

        result = conn.execute(query_1714).fetchone()
        if result:
            print(f"Requisição ID: {result[0]}")
            print(f"  Tipo de Posição: '{result[1] if result[1] else '[VAZIO]'}'")
            print(f"  Tipo de Serviço: '{result[2] if result[2] else '[VAZIO]'}'")

        print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
