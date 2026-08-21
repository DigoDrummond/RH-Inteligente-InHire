"""
Script para exportar views do banco de dados para Google Sheets
Exporta vw_analise_posicoes e vw_dados_jade para planilha especificada
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Carrega variáveis de ambiente do .env
load_dotenv()

import psycopg2
from psycopg2 import extras
from services.google_sheets_service import GoogleSheetsService
from utils.logger import get_logger

logger = get_logger(__name__)


def connect_database():
    """Conecta ao banco de dados PostgreSQL"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'inhire'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        logger.info("Conectado ao banco de dados com sucesso")
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco: {str(e)}")
        raise


def fetch_view_data(conn, view_name: str):
    """
    Busca dados de uma view do banco

    Args:
        conn: Conexão com o banco
        view_name: Nome da view

    Returns:
        Tuple com (colunas, dados)
    """
    try:
        cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

        # Busca os dados da view
        query = f"SELECT * FROM {view_name}"
        cursor.execute(query)

        rows = cursor.fetchall()

        if not rows:
            logger.warning(f"Nenhum dado encontrado na view {view_name}")
            return [], []

        # Extrai os nomes das colunas
        columns = list(rows[0].keys())

        # Converte para lista de listas (formato do Sheets)
        data = []
        for row in rows:
            row_data = []
            for col in columns:
                value = row[col]
                # Converte valores especiais para string
                if value is None:
                    row_data.append('')
                elif isinstance(value, (datetime,)):
                    row_data.append(value.isoformat())
                else:
                    row_data.append(str(value))
            data.append(row_data)

        cursor.close()
        logger.info(f"Extraídos {len(data)} registros da view {view_name}")

        return columns, data

    except Exception as e:
        logger.error(f"Erro ao buscar dados da view {view_name}: {str(e)}")
        raise


def export_to_sheet(
    sheets_service: GoogleSheetsService,
    spreadsheet_id: str,
    sheet_name: str,
    columns: list,
    data: list
):
    """
    Exporta dados para uma aba específica do Google Sheets

    Args:
        sheets_service: Serviço do Google Sheets
        spreadsheet_id: ID da planilha
        sheet_name: Nome da aba/página
        columns: Lista com nomes das colunas
        data: Lista de listas com os dados
    """
    try:
        # Limpa a aba primeiro
        logger.info(f"Limpando aba '{sheet_name}'...")
        sheets_service.clear_sheet(spreadsheet_id, f"{sheet_name}!A:ZZ")

        # Prepara os dados com cabeçalho
        values = [columns] + data

        # Escreve os dados
        logger.info(f"Escrevendo {len(data)} linhas na aba '{sheet_name}'...")
        result = sheets_service.write_sheet(
            spreadsheet_id=spreadsheet_id,
            range_name=f"{sheet_name}!A1",
            values=values,
            value_input_option='USER_ENTERED'
        )

        logger.info(
            f"✓ Exportação concluída: {result.get('updatedCells')} células "
            f"atualizadas na aba '{sheet_name}'"
        )

    except Exception as e:
        logger.error(f"Erro ao exportar para aba '{sheet_name}': {str(e)}")
        raise


def main():
    """Função principal"""
    try:
        print("\n" + "="*60)
        print("EXPORTAÇÃO DE VIEWS PARA GOOGLE SHEETS")
        print("="*60 + "\n")

        # URL e ID da planilha
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw"
        spreadsheet_id = GoogleSheetsService.extract_spreadsheet_id(spreadsheet_url)

        print(f"Planilha: {spreadsheet_id}\n")

        # Conecta ao banco
        print("1. Conectando ao banco de dados...")
        conn = connect_database()

        # Inicializa serviço do Sheets
        print("2. Autenticando com Google Sheets API...")
        sheets_service = GoogleSheetsService()

        # Exporta vw_analise_posicoes
        print("\n3. Exportando vw_analise_posicoes...")
        print("-" * 60)
        columns1, data1 = fetch_view_data(conn, 'vw_analise_posicoes')
        if columns1 and data1:
            export_to_sheet(
                sheets_service=sheets_service,
                spreadsheet_id=spreadsheet_id,
                sheet_name='Teste_API',
                columns=columns1,
                data=data1
            )
            print(f"   ✓ {len(data1)} registros exportados para 'Teste_API'")
        else:
            print("   ⚠ Nenhum dado encontrado em vw_analise_posicoes")

        # Exporta vw_dados_jade
        print("\n4. Exportando vw_dados_jade...")
        print("-" * 60)
        columns2, data2 = fetch_view_data(conn, 'vw_dados_jade')
        if columns2 and data2:
            export_to_sheet(
                sheets_service=sheets_service,
                spreadsheet_id=spreadsheet_id,
                sheet_name='API_Dados_Jade',
                columns=columns2,
                data=data2
            )
            print(f"   ✓ {len(data2)} registros exportados para 'API_Dados_Jade'")
        else:
            print("   ⚠ Nenhum dado encontrado em vw_dados_jade")

        # Fecha conexão
        conn.close()

        print("\n" + "="*60)
        print("EXPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60 + "\n")
        print(f"Acesse: {spreadsheet_url}")
        print()

    except Exception as e:
        logger.error(f"Erro na exportação: {str(e)}")
        print(f"\nERRO: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
