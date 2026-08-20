#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Busca onde está a resposta "Sim" do ADLER sobre "Você conhecia a Framework Digital?"
"""

import sys
import io
import json
import psycopg2
from psycopg2.extras import RealDictCursor

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'inhire',
    'user': 'postgres',
    'password': 'postgres'
}


def main():
    print("\n" + "="*80)
    print("BUSCANDO RESPOSTA DO CANDIDATO ADLER")
    print("="*80)

    conn = psycopg2.connect(**DB_CONFIG)

    # 1. Buscar candidato e talento relacionado
    print("\n1. DADOS DO CANDIDATO")
    print("-"*80)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                c.id as candidatura_id,
                c.talent_name,
                c.talent_email,
                c.talent_inhire_id,
                c.talento_id,
                t.id as talento_bd_id,
                t.attributes,
                v.name as vaga_nome,
                v.custom_fields as vaga_custom_fields
            FROM candidaturas c
            LEFT JOIN talentos t ON c.talento_id = t.id
            LEFT JOIN vagas v ON c.vaga_id = v.id
            WHERE c.talent_email = 'adlerbcc95@hotmail.com'
            LIMIT 1
        """)

        row = cur.fetchone()

        if not row:
            print("❌ Candidato não encontrado!")
            conn.close()
            return

        print(f"✅ Candidato: {row['talent_name']}")
        print(f"   Email: {row['talent_email']}")
        print(f"   Vaga: {row['vaga_nome']}")
        print(f"   Candidatura ID: {row['candidatura_id']}")
        print(f"   Talento ID (BD): {row['talento_bd_id']}")

        # 2. Verificar attributes do talento
        print(f"\n2. ATTRIBUTES DO TALENTO")
        print("-"*80)

        if row['attributes']:
            print(f"Tipo: {type(row['attributes'])}")
            print(f"\nConteúdo:")
            print(json.dumps(row['attributes'], indent=2, ensure_ascii=False))

            # Buscar "framework" ou "conhecia" no attributes
            attrs_str = json.dumps(row['attributes'], ensure_ascii=False).lower()
            if 'framework' in attrs_str or 'conhecia' in attrs_str:
                print(f"\n✅ Encontrado referência a 'framework' ou 'conhecia' nos attributes!")
            else:
                print(f"\n❌ Não encontrado 'framework' ou 'conhecia' nos attributes")
        else:
            print("(vazio)")

        # 3. Verificar custom fields da vaga
        print(f"\n3. CUSTOM FIELDS DA VAGA")
        print("-"*80)

        if row['vaga_custom_fields']:
            print(f"Tipo: {type(row['vaga_custom_fields'])}")
            print(f"\nConteúdo:")
            print(json.dumps(row['vaga_custom_fields'], indent=2, ensure_ascii=False)[:500])
        else:
            print("(vazio)")

    # 4. Buscar em todas as tabelas relacionadas
    print(f"\n4. BUSCANDO EM OUTRAS TABELAS")
    print("-"*80)

    tabelas = [
        ('candidaturas', 'stage_metadata', 'talent_email = \'adlerbcc95@hotmail.com\''),
        ('candidaturas', 'phase_metadata', 'talent_email = \'adlerbcc95@hotmail.com\''),
        ('talentos', 'attributes', 'email = \'adlerbcc95@hotmail.com\''),
        ('talentos', 'jobs', 'email = \'adlerbcc95@hotmail.com\''),
    ]

    for tabela, coluna, condicao in tabelas:
        try:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT {coluna}::text
                    FROM {tabela}
                    WHERE {condicao}
                    LIMIT 1
                """)

                result = cur.fetchone()

                if result and result[0]:
                    data_str = result[0].lower()
                    if 'framework' in data_str or 'conhecia' in data_str or 'sim' in data_str:
                        print(f"\n✅ {tabela}.{coluna}:")
                        print(f"   Contém possível resposta!")
                        print(f"   Preview: {result[0][:300]}...")
        except Exception as e:
            print(f"❌ Erro ao buscar em {tabela}.{coluna}: {e}")

    # 5. Buscar em requisicoes custom_fields
    print(f"\n5. BUSCANDO EM REQUISIÇÕES")
    print("-"*80)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                r.id,
                r.name,
                r.custom_fields
            FROM requisicoes r
            INNER JOIN vagas v ON r.job_inhire_id = v.inhire_id
            INNER JOIN candidaturas c ON c.vaga_id = v.id
            WHERE c.talent_email = 'adlerbcc95@hotmail.com'
              AND r.custom_fields IS NOT NULL
            LIMIT 1
        """)

        row = cur.fetchone()

        if row and row['custom_fields']:
            print(f"✅ Requisição encontrada: {row['name']}")
            print(f"\nCustom fields:")
            print(json.dumps(row['custom_fields'], indent=2, ensure_ascii=False)[:500])
        else:
            print("❌ Nenhuma requisição com custom_fields encontrada")

    conn.close()

    print("\n" + "="*80)
    print("INVESTIGAÇÃO CONCLUÍDA")
    print("="*80)
    print("\n💡 DICA: O campo pode estar em:")
    print("   1. talentos.attributes (JSON)")
    print("   2. candidaturas.stage_metadata ou phase_metadata")
    print("   3. vagas.custom_fields")
    print("   4. Pode não estar sincronizado do Inhire")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
