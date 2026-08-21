"""
Script para exportar vw_analise_posicoes para Google Sheets usando OAuth2
Exporta dados de análise de posições (1.383 registros × 34 colunas)
"""
import os
import sys
import pickle
from datetime import datetime
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Carrega variáveis de ambiente do .env
load_dotenv()

import psycopg2
from psycopg2 import extras
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scopes necessários
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def get_google_sheets_service():
    """Autentica e retorna o serviço do Google Sheets"""
    creds = None
    token_path = 'token.pickle'

    # Carrega credenciais salvas
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # Se não há credenciais válidas, faz login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Salva as credenciais para próxima execução
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('sheets', 'v4', credentials=creds)


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
        print("   Conectado ao banco de dados")
        return conn
    except Exception as e:
        print(f"   Erro ao conectar ao banco: {str(e)}")
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
            print(f"   Nenhum dado encontrado na view {view_name}")
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
        print(f"   Extraidos {len(data):,} registros da view {view_name}")

        return columns, data

    except Exception as e:
        print(f"   Erro ao buscar dados da view {view_name}: {str(e)}")
        raise


def export_to_sheet(service, spreadsheet_id: str, sheet_name: str, columns: list, data: list, batch_size: int = 5000):
    """
    Exporta dados para uma aba específica do Google Sheets usando escrita em lotes

    Args:
        service: Serviço do Google Sheets
        spreadsheet_id: ID da planilha
        sheet_name: Nome da aba/página
        columns: Lista com nomes das colunas
        data: Lista de listas com os dados
        batch_size: Tamanho do lote para escrita (padrão: 5000 linhas)
    """
    try:
        # Limpa a aba primeiro
        print(f"   Limpando aba '{sheet_name}'...")
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A:ZZ",
            body={}
        ).execute()

        total_rows = len(data)
        total_batches = (total_rows + batch_size - 1) // batch_size  # Arredonda para cima

        print(f"   Escrevendo {total_rows:,} linhas na aba '{sheet_name}' em {total_batches} lotes...")
        print(f"   Tamanho do lote: {batch_size:,} linhas\n")

        total_cells_updated = 0

        # Escreve cabeçalho primeiro
        print(f"   [Lote 0/{total_batches}] Escrevendo cabeçalho...")
        header_result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption='USER_ENTERED',
            body={'values': [columns]}
        ).execute()
        total_cells_updated += header_result.get('updatedCells', 0)

        # Escreve dados em lotes
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_rows)
            batch_data = data[start_idx:end_idx]

            # Calcula a linha inicial no Sheets (cabeçalho está na linha 1, dados começam na linha 2)
            start_row = start_idx + 2

            print(f"   [Lote {batch_num + 1}/{total_batches}] Escrevendo linhas {start_idx + 1:,} a {end_idx:,}...")

            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A{start_row}",
                valueInputOption='USER_ENTERED',
                body={'values': batch_data}
            ).execute()

            cells_updated = result.get('updatedCells', 0)
            total_cells_updated += cells_updated
            print(f"      OK - {cells_updated:,} células atualizadas")

        print(f"\n   TOTAL - {total_cells_updated:,} células atualizadas em {total_batches} lotes\n")

    except HttpError as e:
        print(f"   Erro HTTP ao exportar para aba '{sheet_name}': {str(e)}")
        raise
    except Exception as e:
        print(f"   Erro ao exportar para aba '{sheet_name}': {str(e)}")
        raise


def main():
    """Função principal"""
    try:
        print("\n" + "="*70)
        print(" EXPORTACAO vw_analise_posicoes PARA GOOGLE SHEETS")
        print("="*70 + "\n")

        # URL e ID da planilha (fornecida pelo usuário)
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw"
        spreadsheet_id = "1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw"

        print(f"Planilha: {spreadsheet_id}")
        print(f"View: vw_analise_posicoes")
        print(f"Aba destino: Teste_API\n")

        # Conecta ao banco
        print("1. Conectando ao banco de dados PostgreSQL")
        print("-" * 70)
        conn = connect_database()

        # Autentica com Google Sheets
        print("\n2. Autenticando com Google Sheets API (OAuth2)")
        print("-" * 70)
        print("   Se necessario, sera aberta uma janela do navegador para autorizacao...")
        service = get_google_sheets_service()
        print("   Autenticado com sucesso\n")

        # Exporta vw_analise_posicoes
        print("3. Exportando vw_analise_posicoes -> Teste_API")
        print("-" * 70)
        print("   Buscando dados da view (pode levar alguns segundos)...")

        columns, data = fetch_view_data(conn, 'vw_analise_posicoes')

        if columns and data:
            export_to_sheet(
                service=service,
                spreadsheet_id=spreadsheet_id,
                sheet_name='Teste_API',
                columns=columns,
                data=data
            )
        else:
            print("   Nenhum dado encontrado\n")

        # Fecha conexão
        conn.close()

        print("="*70)
        print(" EXPORTACAO CONCLUIDA COM SUCESSO!")
        print("="*70)
        print(f"\nAcesse: {spreadsheet_url}\n")

        print("ESTATISTICAS:")
        print(f"  - Registros exportados: {len(data):,}")
        print(f"  - Colunas: {len(columns)}")
        print(f"  - Celulas totais: ~{len(data) * len(columns):,}")

    except Exception as e:
        print(f"\nERRO: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()