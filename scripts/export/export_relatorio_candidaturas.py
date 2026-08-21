"""
Script para exportar vw_relatorio_candidaturas para Google Sheets usando OAuth2
Exporta dados de candidaturas (ano 2026, workflow Billable)
"""
import os
import sys
import json
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


def ensure_sheet_capacity(service, spreadsheet_id: str, sheet_name: str, required_rows: int, required_cols: int):
    """
    Garante que a aba tenha capacidade suficiente para os dados

    Args:
        service: Serviço do Google Sheets
        spreadsheet_id: ID da planilha
        sheet_name: Nome da aba
        required_rows: Número de linhas necessárias
        required_cols: Número de colunas necessárias
    """
    try:
        # 1. Obter metadados da planilha
        sheet_metadata = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id).execute()

        # 2. Encontrar aba pelo nome
        sheet_id = None
        current_rows = 0
        current_cols = 0

        for sheet in sheet_metadata.get('sheets', []):
            if sheet['properties']['title'] == sheet_name:
                sheet_id = sheet['properties']['sheetId']
                grid_props = sheet['properties']['gridProperties']
                current_rows = grid_props.get('rowCount', 0)
                current_cols = grid_props.get('columnCount', 0)
                break

        if sheet_id is None:
            print(f"   [!] Aba '{sheet_name}' nao encontrada. Sera criada automaticamente na primeira escrita.")
            return

        # 3. Verificar se precisa expandir
        print(f"   Capacidade atual da aba: {current_rows:,} linhas x {current_cols} colunas")

        needs_expansion = False
        if current_rows < required_rows:
            print(f"   [!] Aba tem apenas {current_rows:,} linhas, mas precisa de {required_rows:,}")
            needs_expansion = True

        if current_cols < required_cols:
            print(f"   [!] Aba tem apenas {current_cols} colunas, mas precisa de {required_cols}")
            needs_expansion = True

        # 4. Expandir se necessário
        if needs_expansion:
            new_rows = max(required_rows, current_rows)
            new_cols = max(required_cols, current_cols)

            print(f"   Expandindo aba para {new_rows:,} linhas x {new_cols} colunas...")

            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    'requests': [{
                        'updateSheetProperties': {
                            'properties': {
                                'sheetId': sheet_id,
                                'gridProperties': {
                                    'rowCount': new_rows,
                                    'columnCount': new_cols
                                }
                            },
                            'fields': 'gridProperties(rowCount,columnCount)'
                        }
                    }]
                }
            ).execute()

            print(f"   [OK] Aba expandida com sucesso!\n")
        else:
            print(f"   [OK] Aba tem capacidade suficiente\n")

    except Exception as e:
        print(f"   [!] Erro ao verificar/expandir aba: {str(e)}")
        print(f"   Tentando continuar mesmo assim...\n")


def get_view_statistics(conn, view_name: str):
    """
    Obtém estatísticas da view

    Args:
        conn: Conexão com o banco
        view_name: Nome da view

    Returns:
        Dict com estatísticas
    """
    try:
        cursor = conn.cursor()

        # Query para obter estatísticas
        query = f"""
            SELECT
                COUNT(*) as total_registros,
                MAX(ultima_atualizacao) as ultima_sincronizacao
            FROM {view_name}
        """
        cursor.execute(query)
        result = cursor.fetchone()

        stats = {
            'total_registros': result[0] if result else 0,
            'ultima_sincronizacao': result[1].isoformat() if result and result[1] else None
        }

        cursor.close()
        return stats

    except Exception as e:
        print(f"   Erro ao obter estatísticas: {str(e)}")
        return {'total_registros': 0, 'ultima_sincronizacao': None}


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
        # Valida e expande a aba se necessário
        total_rows_needed = len(data) + 1  # +1 para cabeçalho
        total_cols_needed = len(columns)

        print(f"   Validando capacidade da aba...")
        print(f"   Registros a exportar: {len(data):,}")
        print(f"   Linhas necessárias: {total_rows_needed:,} (dados + cabeçalho)")
        print(f"   Colunas necessárias: {total_cols_needed}\n")

        ensure_sheet_capacity(
            service=service,
            spreadsheet_id=spreadsheet_id,
            sheet_name=sheet_name,
            required_rows=total_rows_needed + 100,  # +100 margem de segurança
            required_cols=total_cols_needed + 5      # +5 margem para colunas extras
        )

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
        print(" EXPORTACAO vw_relatorio_candidaturas PARA GOOGLE SHEETS")
        print("="*70 + "\n")

        # URL e ID da planilha (fornecida pelo usuário)
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1E6Bv5JkL7Bmlj_v02FArthRlG07sBdwSOYAVbtTSKTQ"
        spreadsheet_id = "1E6Bv5JkL7Bmlj_v02FArthRlG07sBdwSOYAVbtTSKTQ"

        print(f"Planilha: {spreadsheet_id}")
        print(f"View: vw_relatorio_candidaturas")
        print(f"Aba destino: [INHIRE]_relatorio_candidaturas\n")

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

        # Exporta vw_relatorio_candidaturas
        print("3. Exportando vw_relatorio_candidaturas -> [INHIRE]_relatorio_candidaturas")
        print("-" * 70)
        print("   Buscando dados da view (pode levar alguns segundos)...")

        columns, data = fetch_view_data(conn, 'vw_relatorio_candidaturas')

        if columns and data:
            export_to_sheet(
                service=service,
                spreadsheet_id=spreadsheet_id,
                sheet_name='[INHIRE]_relatorio_candidaturas',
                columns=columns,
                data=data
            )
        else:
            print("   Nenhum dado encontrado\n")

        # Obtem estatísticas da view
        print("\n4. Coletando estatísticas da exportação")
        print("-" * 70)
        stats = get_view_statistics(conn, 'vw_relatorio_candidaturas')

        # Fecha conexão
        conn.close()

        # Prepara estatísticas completas
        export_time = datetime.now()
        full_stats = {
            'data_hora_exportacao': export_time.strftime('%d/%m/%Y %H:%M:%S'),
            'total_registros': len(data),
            'total_colunas': len(columns),
            'ultima_sincronizacao': stats.get('ultima_sincronizacao'),
            'planilha_id': spreadsheet_id,
            'aba': '[INHIRE]_relatorio_candidaturas'
        }

        # Salva estatísticas em arquivo JSON
        stats_file = 'logs/export_candidaturas_stats.json'
        os.makedirs('logs', exist_ok=True)
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(full_stats, f, indent=2, ensure_ascii=False)

        print(f"   Estatísticas salvas em: {stats_file}\n")

        print("="*70)
        print(" EXPORTACAO CONCLUIDA COM SUCESSO!")
        print("="*70)
        print(f"\nAcesse: {spreadsheet_url}\n")

        print("ESTATISTICAS:")
        print(f"  - Data/Hora: {full_stats['data_hora_exportacao']}")
        print(f"  - Registros exportados: {full_stats['total_registros']:,}")
        print(f"  - Colunas: {full_stats['total_colunas']}")
        print(f"  - Última sincronização: {full_stats['ultima_sincronizacao'] or 'N/A'}")
        print(f"  - Células totais: ~{len(data) * len(columns):,}")

    except Exception as e:
        print(f"\nERRO: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
