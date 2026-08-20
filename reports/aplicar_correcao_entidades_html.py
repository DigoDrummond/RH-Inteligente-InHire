#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar correção de entidades HTML na view
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


def executar_migration(conn, nome, sql):
    """Executa uma migration"""
    print(f"\n{'='*80}")
    print(f"EXECUTANDO: {nome}")
    print(f"{'='*80}")

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
        print(f"✅ {nome} executada com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao executar {nome}: {e}")
        conn.rollback()
        return False


def testar_conversao(conn):
    """Testa se a conversão de entidades está funcionando"""
    print(f"\n{'='*80}")
    print("TESTANDO CONVERSÃO DE ENTIDADES HTML")
    print(f"{'='*80}")

    with conn.cursor() as cur:
        # Testar função html_decode
        cur.execute("SELECT html_decode('Experi&ecirc;ncia com &eacute; &aacute; &atilde;o')")
        resultado = cur.fetchone()[0]
        print(f"\n1. Teste da função html_decode():")
        print(f"   Input:  'Experi&ecirc;ncia com &eacute; &aacute; &atilde;o'")
        print(f"   Output: '{resultado}'")

        # Testar view
        cur.execute("""
            SELECT titulo, SUBSTRING(descricao, 1, 200) as desc_sample
            FROM vw_relatorio_requisicoes
            WHERE LENGTH(descricao) > 100
              AND EXTRACT(YEAR FROM data_solicitacao) = 2026
            LIMIT 1
        """)

        row = cur.fetchone()
        if row:
            titulo, desc = row
            print(f"\n2. Teste da view vw_relatorio_requisicoes:")
            print(f"   Título: {titulo}")
            print(f"   Descrição (200 chars): {desc}...")

            # Verificar se ainda tem entidades HTML
            if '&' in desc and ';' in desc:
                print(f"\n   ⚠️ ATENÇÃO: Ainda existem entidades HTML na descrição!")
                print(f"   Exemplo encontrado: {[x for x in desc.split() if '&' in x][:3]}")
            else:
                print(f"\n   ✅ Descrição limpa! Sem entidades HTML detectadas.")


def main():
    print("\n" + "="*80)
    print("CORREÇÃO DE ENTIDADES HTML - VIEW DE REQUISIÇÕES")
    print("="*80)

    conn = psycopg2.connect(**DB_CONFIG)

    # Migration 066: Criar função html_decode
    migration_066 = """
    CREATE OR REPLACE FUNCTION html_decode(text_input TEXT)
    RETURNS TEXT AS $$
    DECLARE
        result TEXT;
    BEGIN
        result := text_input;

        -- Entidades HTML mais comuns
        result := REPLACE(result, '&aacute;', 'á');
        result := REPLACE(result, '&Aacute;', 'Á');
        result := REPLACE(result, '&acirc;', 'â');
        result := REPLACE(result, '&Acirc;', 'Â');
        result := REPLACE(result, '&agrave;', 'à');
        result := REPLACE(result, '&Agrave;', 'À');
        result := REPLACE(result, '&atilde;', 'ã');
        result := REPLACE(result, '&Atilde;', 'Ã');

        result := REPLACE(result, '&eacute;', 'é');
        result := REPLACE(result, '&Eacute;', 'É');
        result := REPLACE(result, '&ecirc;', 'ê');
        result := REPLACE(result, '&Ecirc;', 'Ê');

        result := REPLACE(result, '&iacute;', 'í');
        result := REPLACE(result, '&Iacute;', 'Í');

        result := REPLACE(result, '&oacute;', 'ó');
        result := REPLACE(result, '&Oacute;', 'Ó');
        result := REPLACE(result, '&ocirc;', 'ô');
        result := REPLACE(result, '&Ocirc;', 'Ô');
        result := REPLACE(result, '&otilde;', 'õ');
        result := REPLACE(result, '&Otilde;', 'Õ');

        result := REPLACE(result, '&uacute;', 'ú');
        result := REPLACE(result, '&Uacute;', 'Ú');
        result := REPLACE(result, '&ucirc;', 'û');
        result := REPLACE(result, '&Ucirc;', 'Û');

        result := REPLACE(result, '&ccedil;', 'ç');
        result := REPLACE(result, '&Ccedil;', 'Ç');

        result := REPLACE(result, '&nbsp;', ' ');
        result := REPLACE(result, '&quot;', '"');
        result := REPLACE(result, '&apos;', '''');
        result := REPLACE(result, '&lt;', '<');
        result := REPLACE(result, '&gt;', '>');
        result := REPLACE(result, '&amp;', '&');

        RETURN result;
    END;
    $$ LANGUAGE plpgsql IMMUTABLE;
    """

    # Migration 067: Atualizar view
    migration_067 = """
    DROP VIEW IF EXISTS vw_relatorio_requisicoes CASCADE;

    CREATE VIEW vw_relatorio_requisicoes AS
    SELECT
        html_decode(
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
            )
        ) AS descricao,

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

    # Executar migrations
    sucesso_066 = executar_migration(conn, "Migration 066: Criar função html_decode()", migration_066)
    sucesso_067 = executar_migration(conn, "Migration 067: Atualizar view", migration_067)

    if sucesso_066 and sucesso_067:
        # Testar
        testar_conversao(conn)

        print("\n" + "="*80)
        print("✅ CORREÇÃO APLICADA COM SUCESSO!")
        print("="*80)
        print("\nAgora você pode consultar a view e verá o texto limpo:")
        print("  SELECT * FROM vw_relatorio_requisicoes WHERE EXTRACT(YEAR FROM data_solicitacao) = 2026;")
        print("\n" + "="*80 + "\n")
    else:
        print("\n" + "="*80)
        print("❌ ERRO AO APLICAR CORREÇÕES")
        print("="*80 + "\n")

    conn.close()


if __name__ == '__main__':
    main()
