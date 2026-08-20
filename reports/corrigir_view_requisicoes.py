#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir view de requisições
"""

import sys
import io
import psycopg2

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
    print("CORRIGINDO VIEW: vw_relatorio_requisicoes")
    print("="*80)

    conn = psycopg2.connect(**DB_CONFIG)

    query = """
    DROP VIEW IF EXISTS vw_relatorio_requisicoes CASCADE;

    CREATE VIEW vw_relatorio_requisicoes AS
    SELECT
        -- Remover HTML da descrição
        TRIM(
            REGEXP_REPLACE(
                REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        COALESCE(r.description, ''),
                        '<[^>]+>', '', 'g'
                    ),
                    '&nbsp;', ' ', 'g'
                ),
                '\\s+', ' ', 'g'
            )
        ) AS descricao,

        -- Usar nome da vaga quando requisição não tem título
        COALESCE(
            NULLIF(TRIM(r.name), ''),
            NULLIF(TRIM(v.name), ''),
            'Sem título'
        ) AS titulo,

        r.requested_at AT TIME ZONE 'America/Sao_Paulo' AS data_solicitacao

    FROM requisicoes r
    LEFT JOIN vagas v ON r.job_inhire_id = v.inhire_id
    WHERE r.requested_at IS NOT NULL
    ORDER BY r.requested_at DESC;
    """

    try:
        print("\n⏳ Recriando view...")
        with conn.cursor() as cur:
            cur.execute(query)
            conn.commit()
        print("✅ View recriada com sucesso!")

        # Testar
        print("\n⏳ Testando view...")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE titulo = 'Sem título') as sem_titulo,
                    COUNT(*) FILTER (WHERE titulo != 'Sem título') as com_titulo
                FROM vw_relatorio_requisicoes
            """)
            total, sem_titulo, com_titulo = cur.fetchone()

            print(f"\n📊 RESULTADO:")
            print(f"   Total de requisições: {total:,}")
            print(f"   Com título válido:    {com_titulo:,}")
            print(f"   Sem título:           {sem_titulo:,}")

        # Mostrar exemplos
        print("\n📋 EXEMPLOS (primeiras 10 requisições de 2026):")
        print("-"*80)

        with conn.cursor() as cur:
            cur.execute("""
                SELECT titulo, data_solicitacao
                FROM vw_relatorio_requisicoes
                WHERE EXTRACT(YEAR FROM data_solicitacao) = 2026
                ORDER BY data_solicitacao DESC
                LIMIT 10
            """)

            for i, (titulo, data) in enumerate(cur.fetchall(), 1):
                titulo_trunc = (titulo[:60] + '...') if len(titulo) > 63 else titulo
                print(f"{i:2}. {titulo_trunc:<63} {data.strftime('%Y-%m-%d')}")

        print("\n" + "="*80)
        print("✅ VIEW CORRIGIDA E TESTADA COM SUCESSO!")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ ERRO: {e}\n")
        conn.rollback()

    finally:
        conn.close()


if __name__ == '__main__':
    main()
