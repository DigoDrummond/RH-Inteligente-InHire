#!/usr/bin/env python3
"""
Script para Gerar Relatórios de Requisições e Candidaturas

Este script executa as queries SQL e gera relatórios em formato:
- Excel (.xlsx)
- CSV (.csv)
- JSON (.json)

Data de criação: 2026-07-21
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

# Diretório base (onde este script está)
BASE_DIR = Path(__file__).parent
SQL_DIR = BASE_DIR
EXPORT_DIR = BASE_DIR / 'exports'

# Criar diretório de exports se não existir
EXPORT_DIR.mkdir(exist_ok=True)

# Configurações de conexão com o banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'inhire',
    'user': 'postgres',
    'password': os.getenv('DB_PASSWORD', 'postgres')
}


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def conectar_banco() -> psycopg2.extensions.connection:
    """
    Estabelece conexão com o banco de dados PostgreSQL

    Returns:
        Conexão psycopg2

    Raises:
        Exception: Se não conseguir conectar
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("✅ Conectado ao banco de dados PostgreSQL")
        return conn
    except Exception as e:
        logger.error(f"❌ Erro ao conectar ao banco: {e}")
        raise


def executar_query_sql(conn: psycopg2.extensions.connection,
                       query: str) -> List[Dict[str, Any]]:
    """
    Executa uma query SQL e retorna os resultados como lista de dicionários

    Args:
        conn: Conexão psycopg2
        query: Query SQL a executar

    Returns:
        Lista de dicionários com os resultados
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            results = cur.fetchall()

            # Converter RealDictRow para dict normal
            results = [dict(row) for row in results]

            logger.info(f"✅ Query executada com sucesso. {len(results)} registros retornados.")
            return results

    except Exception as e:
        logger.error(f"❌ Erro ao executar query: {e}")
        raise


def carregar_query_arquivo(arquivo_sql: Path) -> str:
    """
    Carrega a query SQL de um arquivo

    Args:
        arquivo_sql: Caminho para o arquivo .sql

    Returns:
        String com a query SQL
    """
    if not arquivo_sql.exists():
        raise FileNotFoundError(f"Arquivo SQL não encontrado: {arquivo_sql}")

    with open(arquivo_sql, 'r', encoding='utf-8') as f:
        query = f.read()

    # Extrair apenas a primeira query (antes de comentários de queries alternativas)
    # Procurar por "-- =====" que indica início de nova seção
    linhas = query.split('\n')
    query_principal = []
    dentro_query = False

    for linha in linhas:
        # Iniciar captura após primeiro SELECT
        if 'SELECT' in linha.upper() and not dentro_query:
            dentro_query = True

        # Parar captura em nova seção de queries alternativas
        if dentro_query and linha.strip().startswith('-- ====='):
            # Verificar se é uma query alternativa
            if 'ALTERNATIVA' in linha or 'AUXILIAR' in linha or 'NOTAS' in linha:
                break

        if dentro_query:
            query_principal.append(linha)

    query_final = '\n'.join(query_principal).strip()

    # Remover ponto-e-vírgula final se houver
    if query_final.endswith(';'):
        query_final = query_final[:-1]

    logger.info(f"✅ Query carregada de: {arquivo_sql.name}")
    return query_final


def exportar_para_excel(df: pd.DataFrame, arquivo_saida: Path) -> None:
    """
    Exporta DataFrame para arquivo Excel com formatação

    Args:
        df: DataFrame pandas
        arquivo_saida: Caminho do arquivo de saída
    """
    try:
        with pd.ExcelWriter(arquivo_saida, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Dados')

            # Obter objetos de formatação
            workbook = writer.book
            worksheet = writer.sheets['Dados']

            # Formato de cabeçalho
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })

            # Aplicar formato ao cabeçalho
            for col_num, col_name in enumerate(df.columns):
                worksheet.write(0, col_num, col_name, header_format)

            # Ajustar largura das colunas
            for col_num, col_name in enumerate(df.columns):
                # Calcular largura máxima
                max_len = max(
                    df[col_name].astype(str).map(len).max(),
                    len(str(col_name))
                )
                worksheet.set_column(col_num, col_num, min(max_len + 2, 50))

            # Congelar primeira linha
            worksheet.freeze_panes(1, 0)

        logger.info(f"✅ Arquivo Excel criado: {arquivo_saida}")

    except Exception as e:
        logger.error(f"❌ Erro ao criar Excel: {e}")
        raise


def exportar_para_csv(df: pd.DataFrame, arquivo_saida: Path) -> None:
    """
    Exporta DataFrame para arquivo CSV

    Args:
        df: DataFrame pandas
        arquivo_saida: Caminho do arquivo de saída
    """
    try:
        df.to_csv(arquivo_saida, index=False, encoding='utf-8-sig')
        logger.info(f"✅ Arquivo CSV criado: {arquivo_saida}")

    except Exception as e:
        logger.error(f"❌ Erro ao criar CSV: {e}")
        raise


def exportar_para_json(df: pd.DataFrame, arquivo_saida: Path) -> None:
    """
    Exporta DataFrame para arquivo JSON

    Args:
        df: DataFrame pandas
        arquivo_saida: Caminho do arquivo de saída
    """
    try:
        # Converter datetime para string antes de serializar
        df_copy = df.copy()
        for col in df_copy.columns:
            if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                df_copy[col] = df_copy[col].astype(str)

        # Converter para JSON
        data = df_copy.to_dict(orient='records')

        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"✅ Arquivo JSON criado: {arquivo_saida}")

    except Exception as e:
        logger.error(f"❌ Erro ao criar JSON: {e}")
        raise


def gerar_relatorio(
    conn: psycopg2.extensions.connection,
    nome_relatorio: str,
    arquivo_sql: Path,
    formatos: List[str] = ['excel', 'csv', 'json']
) -> Optional[pd.DataFrame]:
    """
    Gera um relatório completo a partir de uma query SQL

    Args:
        conn: Conexão com banco de dados
        nome_relatorio: Nome do relatório (usado para nomear arquivos)
        arquivo_sql: Caminho para o arquivo .sql
        formatos: Lista de formatos de exportação ('excel', 'csv', 'json')

    Returns:
        DataFrame com os dados ou None se houver erro
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 GERANDO RELATÓRIO: {nome_relatorio}")
    logger.info(f"{'='*80}\n")

    try:
        # Carregar query SQL
        query = carregar_query_arquivo(arquivo_sql)

        # Executar query
        logger.info("⏳ Executando query...")
        resultados = executar_query_sql(conn, query)

        if not resultados:
            logger.warning(f"⚠️ Nenhum resultado encontrado para {nome_relatorio}")
            return None

        # Converter para DataFrame
        df = pd.DataFrame(resultados)
        logger.info(f"📊 DataFrame criado: {len(df)} linhas × {len(df.columns)} colunas")

        # Gerar timestamp para arquivos
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Exportar para cada formato solicitado
        for formato in formatos:
            nome_arquivo = f"{nome_relatorio}_{timestamp}"

            if formato.lower() == 'excel':
                arquivo_saida = EXPORT_DIR / f"{nome_arquivo}.xlsx"
                exportar_para_excel(df, arquivo_saida)

            elif formato.lower() == 'csv':
                arquivo_saida = EXPORT_DIR / f"{nome_arquivo}.csv"
                exportar_para_csv(df, arquivo_saida)

            elif formato.lower() == 'json':
                arquivo_saida = EXPORT_DIR / f"{nome_arquivo}.json"
                exportar_para_json(df, arquivo_saida)

        logger.info(f"\n✅ Relatório '{nome_relatorio}' gerado com sucesso!")
        logger.info(f"📁 Arquivos salvos em: {EXPORT_DIR}\n")

        return df

    except Exception as e:
        logger.error(f"❌ Erro ao gerar relatório '{nome_relatorio}': {e}")
        return None


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """
    Função principal - gera todos os relatórios
    """
    logger.info("\n" + "="*80)
    logger.info("🚀 INICIANDO GERAÇÃO DE RELATÓRIOS - INHIRE")
    logger.info("="*80 + "\n")

    conn = None

    try:
        # Conectar ao banco
        conn = conectar_banco()

        # Relatório 1: Requisições
        df_requisicoes = gerar_relatorio(
            conn=conn,
            nome_relatorio='relatorio_requisicoes',
            arquivo_sql=SQL_DIR / 'relatorio_requisicoes.sql',
            formatos=['excel', 'csv', 'json']
        )

        # Relatório 2: Candidaturas
        df_candidaturas = gerar_relatorio(
            conn=conn,
            nome_relatorio='relatorio_candidaturas',
            arquivo_sql=SQL_DIR / 'relatorio_candidaturas.sql',
            formatos=['excel', 'csv', 'json']
        )

        # Resumo final
        logger.info("\n" + "="*80)
        logger.info("✅ TODOS OS RELATÓRIOS FORAM GERADOS COM SUCESSO!")
        logger.info("="*80)

        if df_requisicoes is not None:
            logger.info(f"📊 Requisições: {len(df_requisicoes)} registros")

        if df_candidaturas is not None:
            logger.info(f"📊 Candidaturas: {len(df_candidaturas)} registros")

        logger.info(f"\n📁 Arquivos disponíveis em: {EXPORT_DIR.absolute()}\n")

    except Exception as e:
        logger.error(f"\n❌ ERRO GERAL: {e}")
        sys.exit(1)

    finally:
        if conn:
            conn.close()
            logger.info("🔌 Conexão com banco de dados encerrada\n")


# ============================================================================
# EXECUÇÃO
# ============================================================================

if __name__ == '__main__':
    main()
