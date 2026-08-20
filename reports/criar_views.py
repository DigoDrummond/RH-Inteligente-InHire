#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar views dos relatórios no banco de dados

Cria as views:
- vw_relatorio_requisicoes
- vw_relatorio_candidaturas

E testa com dados de 2026
"""

import sys
import io
import psycopg2
from psycopg2 import sql

# Forçar encoding UTF-8 para saída
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'inhire',
    'user': 'postgres',
    'password': 'postgres'
}

def criar_view_requisicoes(conn):
    """Cria view de requisições"""
    print("\n" + "="*80)
    print("CRIANDO VIEW: vw_relatorio_requisicoes")
    print("="*80)

    query = """
    DROP VIEW IF EXISTS vw_relatorio_requisicoes CASCADE;

    CREATE VIEW vw_relatorio_requisicoes AS
    SELECT
        description AS descricao,
        name AS titulo,
        requested_at AT TIME ZONE 'America/Sao_Paulo' AS data_solicitacao
    FROM requisicoes
    WHERE requested_at IS NOT NULL
    ORDER BY requested_at DESC;
    """

    try:
        with conn.cursor() as cur:
            cur.execute(query)
            conn.commit()
        print("✅ View vw_relatorio_requisicoes criada com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar view: {e}")
        conn.rollback()


def criar_view_candidaturas(conn):
    """Cria view de candidaturas"""
    print("\n" + "="*80)
    print("CRIANDO VIEW: vw_relatorio_candidaturas")
    print("="*80)

    query = """
    DROP VIEW IF EXISTS vw_relatorio_candidaturas CASCADE;

    CREATE VIEW vw_relatorio_candidaturas AS
    SELECT
        vaga_id,
        status AS status_candidatura,
        talent_name AS nome_candidato,
        talent_email AS email_candidato,
        stage_name AS etapa_candidatura,

        -- Extração do campo "Você conhecia a Framework?"
        CASE
            WHEN stage_metadata IS NOT NULL THEN
                COALESCE(
                    stage_metadata::jsonb->>'conhecia_framework',
                    stage_metadata::jsonb->>'conheciaFramework',
                    stage_metadata::jsonb->>'voce_conhecia_framework',
                    stage_metadata::jsonb->'customFields'->>'conhecia_framework',
                    'N/A'
                )
            WHEN phase_metadata IS NOT NULL THEN
                COALESCE(
                    phase_metadata::jsonb->>'conhecia_framework',
                    phase_metadata::jsonb->>'conheciaFramework',
                    phase_metadata::jsonb->>'voce_conhecia_framework',
                    phase_metadata::jsonb->'customFields'->>'conhecia_framework',
                    'N/A'
                )
            ELSE 'N/A'
        END AS conhecia_framework

    FROM candidaturas
    ORDER BY updated_at_inhire DESC NULLS LAST;
    """

    try:
        with conn.cursor() as cur:
            cur.execute(query)
            conn.commit()
        print("✅ View vw_relatorio_candidaturas criada com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar view: {e}")
        conn.rollback()


def testar_view_requisicoes(conn):
    """Testa view de requisições com dados de 2026"""
    print("\n" + "="*80)
    print("TESTANDO VIEW: vw_relatorio_requisicoes (dados de 2026)")
    print("="*80)

    query = """
    SELECT
        descricao,
        titulo,
        data_solicitacao
    FROM vw_relatorio_requisicoes
    WHERE EXTRACT(YEAR FROM data_solicitacao) = 2026
    ORDER BY data_solicitacao DESC
    LIMIT 10;
    """

    try:
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()

            if not results:
                print("⚠️  Nenhuma requisição encontrada em 2026")
            else:
                print(f"✅ {len(results)} requisições encontradas em 2026\n")
                print(f"{'Título':<40} {'Data Solicitação':<20}")
                print("-"*80)

                for row in results:
                    descricao, titulo, data = row
                    titulo_trunc = (titulo[:37] + '...') if titulo and len(titulo) > 40 else (titulo or 'N/A')
                    data_fmt = data.strftime('%Y-%m-%d %H:%M') if data else 'N/A'
                    print(f"{titulo_trunc:<40} {data_fmt:<20}")

    except Exception as e:
        print(f"❌ Erro ao testar view: {e}")


def testar_view_candidaturas(conn):
    """Testa view de candidaturas com dados de 2026"""
    print("\n" + "="*80)
    print("TESTANDO VIEW: vw_relatorio_candidaturas")
    print("="*80)

    query = """
    SELECT
        nome_candidato,
        email_candidato,
        status_candidatura,
        etapa_candidatura,
        conhecia_framework
    FROM vw_relatorio_candidaturas
    LIMIT 10;
    """

    try:
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()

            if not results:
                print("⚠️  Nenhuma candidatura encontrada")
            else:
                print(f"✅ {len(results)} candidaturas encontradas\n")
                print(f"{'Nome':<30} {'Status':<15} {'Etapa':<25} {'Conhecia FW?':<15}")
                print("-"*90)

                for row in results:
                    nome, email, status, etapa, conhecia = row
                    nome_trunc = (nome[:27] + '...') if nome and len(nome) > 30 else (nome or 'N/A')
                    etapa_trunc = (etapa[:22] + '...') if etapa and len(etapa) > 25 else (etapa or 'N/A')

                    print(f"{nome_trunc:<30} {status:<15} {etapa_trunc:<25} {conhecia:<15}")

    except Exception as e:
        print(f"❌ Erro ao testar view: {e}")


def contar_registros_2026(conn):
    """Conta registros de 2026"""
    print("\n" + "="*80)
    print("CONTAGEM DE REGISTROS - ANO 2026")
    print("="*80)

    queries = {
        'Requisições 2026': """
            SELECT COUNT(*)
            FROM vw_relatorio_requisicoes
            WHERE EXTRACT(YEAR FROM data_solicitacao) = 2026
        """,
        'Candidaturas (total)': """
            SELECT COUNT(*)
            FROM vw_relatorio_candidaturas
        """
    }

    for nome, query in queries.items():
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                count = cur.fetchone()[0]
                print(f"✅ {nome:<25} {count:>10,} registros")
        except Exception as e:
            print(f"❌ {nome:<25} Erro: {e}")


def main():
    """Função principal"""
    print("\n" + "="*80)
    print("CRIAÇÃO E TESTE DE VIEWS - RELATÓRIOS INHIRE")
    print("="*80)

    try:
        # Conectar ao banco
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Conectado ao banco de dados PostgreSQL\n")

        # Criar views
        criar_view_requisicoes(conn)
        criar_view_candidaturas(conn)

        # Testar views
        testar_view_requisicoes(conn)
        testar_view_candidaturas(conn)

        # Contar registros
        contar_registros_2026(conn)

        # Fechar conexão
        conn.close()

        print("\n" + "="*80)
        print("✅ VIEWS CRIADAS E TESTADAS COM SUCESSO!")
        print("="*80)
        print("\nAgora você pode consultar as views:")
        print("  SELECT * FROM vw_relatorio_requisicoes WHERE EXTRACT(YEAR FROM data_solicitacao) = 2026;")
        print("  SELECT * FROM vw_relatorio_candidaturas LIMIT 100;")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ ERRO GERAL: {e}\n")


if __name__ == '__main__':
    main()
