"""
Script para exportar views do banco de dados para Google Sheets usando OAuth 2.0
"""
import os
import sys
import psycopg2
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configurar encoding para UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configurações
SPREADSHEET_ID = "1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw"
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"

# Páginas e views
EXPORTS = [
    {
        'view': 'vw_analise_posicoes',
        'sheet_name': 'Teste_API',
        'description': 'View de análise de posições'
    },
    {
        'view': 'vw_dados_jade',
        'sheet_name': 'API_Dados_Jade',
        'description': 'View de dados para Jade'
    }
]


def get_sheets_service():
    """Cria o serviço do Google Sheets usando OAuth 2.0"""
    try:
        # Carregar credenciais do token.json
        if not os.path.exists(TOKEN_FILE):
            raise FileNotFoundError(f"Arquivo {TOKEN_FILE} não encontrado")

        # Criar credenciais a partir do token
        creds = Credentials.from_authorized_user_file(TOKEN_FILE)

        # Construir o serviço
        service = build('sheets', 'v4', credentials=creds)
        print("[OK] Autenticação com Google Sheets realizada com sucesso")
        return service

    except Exception as e:
        print(f"[ERRO] ao autenticar: {str(e)}")
        raise


def get_database_connection():
    """Conecta ao banco de dados PostgreSQL"""
    try:
        conn = psycopg2.connect(
            dbname="inhire",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        print("[OK] Conexão com banco de dados estabelecida")
        return conn
    except Exception as e:
        print(f"[ERRO] ao conectar no banco: {str(e)}")
        raise


def fetch_view_data(conn, view_name):
    """Busca todos os dados de uma view"""
    try:
        cursor = conn.cursor()

        # Buscar nomes das colunas
        cursor.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{view_name}'
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cursor.fetchall()]

        # Buscar dados
        cursor.execute(f"SELECT * FROM {view_name}")
        rows = cursor.fetchall()

        cursor.close()

        # Converter para formato do Sheets (lista de listas)
        # Primeira linha: cabeçalhos
        data = [columns]

        # Demais linhas: dados
        for row in rows:
            # Converter valores None para string vazia e demais para string
            data.append([str(val) if val is not None else '' for val in row])

        print(f"[OK] Dados da view {view_name}: {len(columns)} colunas, {len(rows)} linhas")
        return data

    except Exception as e:
        print(f"[ERRO] ao buscar dados da view {view_name}: {str(e)}")
        raise


def clear_sheet(service, spreadsheet_id, sheet_name):
    """Limpa todos os dados de uma aba"""
    try:
        # Limpar todo o conteúdo da aba
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A:ZZ",  # Limpar todas as colunas
            body={}
        ).execute()
        print(f"  [OK] Aba '{sheet_name}' limpa")
    except Exception as e:
        print(f"  [ERRO] ao limpar aba '{sheet_name}': {str(e)}")
        raise


def write_to_sheet(service, spreadsheet_id, sheet_name, data):
    """Escreve dados em uma aba do Google Sheets"""
    try:
        # Escrever dados
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption='RAW',
            body={'values': data}
        ).execute()

        updated_cells = result.get('updatedCells', 0)
        print(f"  [OK] {updated_cells} células escritas na aba '{sheet_name}'")
        return result

    except Exception as e:
        print(f"  [ERRO] ao escrever na aba '{sheet_name}': {str(e)}")
        raise


def main():
    """Função principal"""
    print("=" * 80)
    print("EXPORTAÇÃO DE VIEWS PARA GOOGLE SHEETS (OAuth 2.0)")
    print("=" * 80)
    print()

    try:
        # Conectar ao Google Sheets
        print("1. Autenticando com Google Sheets...")
        sheets_service = get_sheets_service()
        print()

        # Conectar ao banco de dados
        print("2. Conectando ao banco de dados...")
        db_conn = get_database_connection()
        print()

        # Processar cada exportação
        for i, export in enumerate(EXPORTS, 1):
            view_name = export['view']
            sheet_name = export['sheet_name']
            description = export['description']

            print(f"{i + 2}. Exportando {view_name} -> {sheet_name}")
            print(f"   ({description})")

            # Buscar dados da view
            data = fetch_view_data(db_conn, view_name)

            # Limpar aba
            clear_sheet(sheets_service, SPREADSHEET_ID, sheet_name)

            # Escrever dados
            write_to_sheet(sheets_service, SPREADSHEET_ID, sheet_name, data)
            print()

        # Fechar conexão
        db_conn.close()

        print("=" * 80)
        print("[OK] EXPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        print()
        print(f"Planilha: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        print()

    except Exception as e:
        print()
        print("=" * 80)
        print(f"[ERRO] DURANTE A EXPORTAÇÃO: {str(e)}")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
