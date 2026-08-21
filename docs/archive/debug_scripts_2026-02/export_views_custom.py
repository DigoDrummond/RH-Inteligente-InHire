"""
Script para exportar views específicas para Google Sheets usando OAuth 2.0

EXPORTAÇÕES:
1. vw_analise_posicoes -> Teste_API (spreadsheet 1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw)
2. vw_dados_jade -> API_Dados_Jade (spreadsheet 1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw)
3. vw_funil_performance -> Funil_API (spreadsheet 1pWscZVbQ_jA7D5aJWycDuRi--8M_AIPSDN9j451-Pd0)
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

# Configurações de autenticação
TOKEN_FILE = "token.json"

# Definição das exportações
EXPORTS = [
    {
        'view': 'vw_analise_posicoes',
        'sheet_name': 'Teste_API',
        'spreadsheet_id': '1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw',
        'description': 'View de análise de posições'
    },
    {
        'view': 'vw_dados_jade',
        'sheet_name': 'API_Dados_Jade',
        'spreadsheet_id': '1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw',
        'description': 'View de dados para Jade'
    },
    {
        'view': 'vw_funil_performance',
        'sheet_name': 'Funil_API',
        'spreadsheet_id': '1pWscZVbQ_jA7D5aJWycDuRi--8M_AIPSDN9j451-Pd0',
        'description': 'View de funil de performance'
    }
]


def get_sheets_service():
    """Cria o serviço do Google Sheets usando OAuth 2.0"""
    try:
        # Carregar credenciais do token.json
        if not os.path.exists(TOKEN_FILE):
            raise FileNotFoundError(f"Arquivo {TOKEN_FILE} não encontrado. Execute o script de autenticação primeiro.")

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

        print(f"  - Buscando colunas de {view_name}...")
        # Buscar nomes das colunas
        cursor.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{view_name}'
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cursor.fetchall()]

        print(f"  - Buscando dados de {view_name}...")
        # Buscar dados
        cursor.execute(f"SELECT * FROM {view_name}")
        rows = cursor.fetchall()

        cursor.close()

        # Converter para formato do Sheets (lista de listas)
        # Primeira linha: cabeçalhos
        data = [columns]

        # Demais linhas: dados
        print(f"  - Processando {len(rows)} linhas...")
        for row in rows:
            # Converter valores None para string vazia e demais para string
            data.append([str(val) if val is not None else '' for val in row])

        print(f"  [OK] {len(columns)} colunas, {len(rows)} linhas")
        return data

    except Exception as e:
        print(f"  [ERRO] ao buscar dados da view {view_name}: {str(e)}")
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
    except HttpError as e:
        if e.resp.status == 400:
            print(f"  [AVISO] Aba '{sheet_name}' pode não existir ou não pode ser acessada")
        else:
            print(f"  [ERRO] ao limpar aba '{sheet_name}': {str(e)}")
            raise
    except Exception as e:
        print(f"  [ERRO] ao limpar aba '{sheet_name}': {str(e)}")
        raise


def write_to_sheet(service, spreadsheet_id, sheet_name, data):
    """Escreve dados em uma aba do Google Sheets"""
    try:
        # Escrever dados (em lotes se necessário)
        total_rows = len(data)
        batch_size = 10000  # Limitar tamanho do lote

        if total_rows <= batch_size:
            # Escrever tudo de uma vez
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption='RAW',
                body={'values': data}
            ).execute()
            updated_cells = result.get('updatedCells', 0)
            print(f"  [OK] {updated_cells} células escritas na aba '{sheet_name}'")
        else:
            # Escrever em lotes
            print(f"  - Dados grandes ({total_rows} linhas), escrevendo em lotes...")

            # Escrever cabeçalho e primeiro lote
            first_batch = data[:batch_size]
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption='RAW',
                body={'values': first_batch}
            ).execute()
            print(f"  - Lote 1: {len(first_batch)} linhas escritas")

            # Escrever lotes restantes
            for i in range(batch_size, total_rows, batch_size):
                batch = data[i:i + batch_size]
                start_row = i + 1
                result = service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f"{sheet_name}!A{start_row}",
                    valueInputOption='RAW',
                    body={'values': batch}
                ).execute()
                print(f"  - Lote {i // batch_size + 1}: {len(batch)} linhas escritas")

            print(f"  [OK] Total de {total_rows} linhas escritas na aba '{sheet_name}'")

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
    print(f"Exportações configuradas: {len(EXPORTS)}")
    for exp in EXPORTS:
        print(f"  - {exp['view']} → {exp['sheet_name']}")
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
            spreadsheet_id = export['spreadsheet_id']
            description = export['description']

            print(f"{i + 2}. Exportando {view_name} → {sheet_name}")
            print(f"   Planilha: {spreadsheet_id}")
            print(f"   Descrição: {description}")

            # Buscar dados da view
            data = fetch_view_data(db_conn, view_name)

            # Limpar aba
            print(f"  - Limpando aba '{sheet_name}'...")
            clear_sheet(sheets_service, spreadsheet_id, sheet_name)

            # Escrever dados
            print(f"  - Escrevendo dados na aba '{sheet_name}'...")
            write_to_sheet(sheets_service, spreadsheet_id, sheet_name, data)
            print()

        # Fechar conexão
        db_conn.close()

        print("=" * 80)
        print("[OK] EXPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        print()
        print("Links das planilhas:")
        for exp in EXPORTS:
            print(f"  - {exp['sheet_name']}: https://docs.google.com/spreadsheets/d/{exp['spreadsheet_id']}")
        print()

    except Exception as e:
        print()
        print("=" * 80)
        print(f"[ERRO] DURANTE A EXPORTAÇÃO: {str(e)}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
