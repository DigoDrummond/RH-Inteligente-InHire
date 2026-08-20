#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exportar views de relatórios atualizadas (requisições e candidaturas)
"""

import sys
import io
import html
from datetime import datetime
import pandas as pd
import psycopg2
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'inhire',
    'user': 'postgres',
    'password': 'postgres'
}


def exportar_view(conn, view_name, output_folder):
    """Exporta uma view para Excel, CSV e JSON"""

    print(f"\n{'='*80}")
    print(f"EXPORTANDO: {view_name}")
    print(f"{'='*80}")

    # Ler dados
    df = pd.read_sql_query(f"SELECT * FROM {view_name}", conn)

    # Converter HTML entities
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(lambda x: html.unescape(str(x)) if pd.notna(x) else x)

    # Remover timezone para Excel
    for col in df.columns:
        if pd.api.types.is_datetime64tz_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    # Criar pasta de saída
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    # Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{view_name}_{timestamp}"

    # 1. Excel
    excel_file = output_path / f"{base_name}.xlsx"
    df.to_excel(excel_file, index=False, engine='xlsxwriter')
    print(f"✅ Excel: {excel_file}")

    # 2. CSV
    csv_file = output_path / f"{base_name}.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8-sig', sep=';')
    print(f"✅ CSV: {csv_file}")

    # 3. JSON
    json_file = output_path / f"{base_name}.json"
    df.to_json(json_file, orient='records', date_format='iso', force_ascii=False, indent=2)
    print(f"✅ JSON: {json_file}")

    # Estatísticas
    print(f"\n📊 Estatísticas:")
    print(f"   - Total de registros: {len(df)}")
    print(f"   - Total de colunas: {len(df.columns)}")
    print(f"   - Colunas: {', '.join(df.columns.tolist())}")

    return len(df)


def main():
    print("\n" + "="*80)
    print("EXPORTAÇÃO DE RELATÓRIOS ATUALIZADOS")
    print("="*80)

    conn = psycopg2.connect(**DB_CONFIG)

    output_folder = "reports/exports"

    # 1. Exportar Requisições
    total_requisicoes = exportar_view(conn, 'vw_relatorio_requisicoes', output_folder)

    # 2. Exportar Candidaturas
    total_candidaturas = exportar_view(conn, 'vw_relatorio_candidaturas', output_folder)

    conn.close()

    print("\n" + "="*80)
    print("EXPORTAÇÃO CONCLUÍDA")
    print("="*80)
    print(f"\n📁 Arquivos salvos em: {output_folder}/")
    print(f"\n📊 Resumo:")
    print(f"   - Requisições: {total_requisicoes} registros")
    print(f"   - Candidaturas: {total_candidaturas} registros")
    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    main()
