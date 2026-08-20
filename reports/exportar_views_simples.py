#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Simples para Exportar Views dos Relatórios

Exporta diretamente das views do banco para Excel e CSV

Uso:
    python exportar_views_simples.py
"""

import sys
import io
import html
from datetime import datetime
from pathlib import Path
import pandas as pd
import psycopg2

# Forçar encoding UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurações
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'inhire',
    'user': 'postgres',
    'password': 'postgres'
}

EXPORT_DIR = Path(__file__).parent / 'exports'
EXPORT_DIR.mkdir(exist_ok=True)


def exportar_view(conn, view_name, nome_arquivo):
    """Exporta uma view para Excel e CSV"""
    print(f"\n{'='*80}")
    print(f"EXPORTANDO: {view_name}")
    print(f"{'='*80}")

    # Query
    query = f"SELECT * FROM {view_name}"

    # Carregar dados
    print("⏳ Carregando dados do banco...")
    df = pd.read_sql_query(query, conn)
    print(f"✅ {len(df):,} registros carregados")

    # Converter entidades HTML em todas as colunas de texto
    print("⏳ Convertendo entidades HTML...")
    for col in df.columns:
        if df[col].dtype == 'object':  # Colunas de texto
            df[col] = df[col].apply(lambda x: html.unescape(str(x)) if pd.notna(x) else x)
    print("✅ Entidades HTML convertidas")

    # Remover timezone de colunas datetime (para compatibilidade com Excel)
    for col in df.columns:
        if pd.api.types.is_datetime64tz_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    # Timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Exportar Excel
    arquivo_excel = EXPORT_DIR / f"{nome_arquivo}_{timestamp}.xlsx"
    print(f"⏳ Salvando Excel...")
    df.to_excel(arquivo_excel, index=False, engine='xlsxwriter')
    print(f"✅ Excel salvo: {arquivo_excel.name}")

    # Exportar CSV
    arquivo_csv = EXPORT_DIR / f"{nome_arquivo}_{timestamp}.csv"
    print(f"⏳ Salvando CSV...")
    df.to_csv(arquivo_csv, index=False, encoding='utf-8-sig')
    print(f"✅ CSV salvo: {arquivo_csv.name}")

    # Resumo
    print(f"\n📊 RESUMO:")
    print(f"   Registros: {len(df):,}")
    print(f"   Colunas: {len(df.columns)}")
    print(f"   Tamanho Excel: {arquivo_excel.stat().st_size / 1024:.1f} KB")
    print(f"   Tamanho CSV: {arquivo_csv.stat().st_size / 1024:.1f} KB")


def main():
    """Função principal"""
    print("\n" + "="*80)
    print("EXPORTAÇÃO SIMPLIFICADA - VIEWS DOS RELATÓRIOS")
    print("="*80)

    try:
        # Conectar
        print("\n⏳ Conectando ao banco...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Conectado!")

        # Exportar Requisições
        exportar_view(
            conn,
            'vw_relatorio_requisicoes',
            'requisicoes_2026'
        )

        # Exportar Candidaturas
        exportar_view(
            conn,
            'vw_relatorio_candidaturas',
            'candidaturas'
        )

        # Fechar
        conn.close()

        # Resumo final
        print("\n" + "="*80)
        print("✅ EXPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*80)
        print(f"\n📁 Arquivos salvos em: {EXPORT_DIR.absolute()}")
        print("\nArquivos criados:")
        for arquivo in sorted(EXPORT_DIR.glob('*')):
            if arquivo.is_file():
                print(f"  - {arquivo.name}")
        print("\n" + "="*80 + "\n")

    except Exception as e:
        print(f"\n❌ ERRO: {e}\n")


if __name__ == '__main__':
    main()
