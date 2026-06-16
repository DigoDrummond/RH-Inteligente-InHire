"""
Serviço de integração com Google Sheets
"""
import os
from typing import List, Dict, Optional
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from utils.logger import get_logger


class GoogleSheetsService:
    """Gerencia operações com Google Sheets"""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Inicializa o serviço do Google Sheets

        Args:
            credentials_path: Caminho para o arquivo de credenciais JSON
                             Se não fornecido, usa GOOGLE_CREDENTIALS_PATH do env
        """
        self.logger = get_logger(__name__)
        self.credentials_path = credentials_path or os.getenv('GOOGLE_CREDENTIALS_PATH')

        if not self.credentials_path:
            raise ValueError(
                "Caminho das credenciais não fornecido. "
                "Configure GOOGLE_CREDENTIALS_PATH no .env ou passe credentials_path"
            )

        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(
                f"Arquivo de credenciais não encontrado: {self.credentials_path}"
            )

        self.service = self._authenticate()

    def _authenticate(self):
        """Autentica com Google Sheets API usando service account"""
        try:
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            service = build('sheets', 'v4', credentials=creds)
            self.logger.info("Autenticação com Google Sheets API realizada com sucesso")
            return service
        except Exception as e:
            self.logger.error(f"Erro ao autenticar com Google Sheets: {str(e)}")
            raise

    def read_sheet(
        self,
        spreadsheet_id: str,
        range_name: str
    ) -> List[List[str]]:
        """
        Lê dados de uma planilha

        Args:
            spreadsheet_id: ID da planilha (extraído da URL)
            range_name: Range a ser lido (ex: 'Sheet1!A1:E10')

        Returns:
            Lista de listas com os valores das células
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])
            self.logger.info(f"Lidos {len(values)} linhas de {range_name}")
            return values

        except Exception as e:
            self.logger.error(f"Erro ao ler planilha: {str(e)}")
            raise

    def write_sheet(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List],
        value_input_option: str = 'RAW'
    ) -> Dict:
        """
        Escreve dados em uma planilha

        Args:
            spreadsheet_id: ID da planilha
            range_name: Range onde escrever (ex: 'Sheet1!A1')
            values: Lista de listas com os valores a escrever
            value_input_option: 'RAW' ou 'USER_ENTERED'

        Returns:
            Resultado da operação
        """
        try:
            body = {'values': values}

            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()

            self.logger.info(
                f"Escritas {result.get('updatedCells')} células em {range_name}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Erro ao escrever na planilha: {str(e)}")
            raise

    def append_sheet(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List],
        value_input_option: str = 'RAW'
    ) -> Dict:
        """
        Adiciona dados no final de uma planilha

        Args:
            spreadsheet_id: ID da planilha
            range_name: Range base (ex: 'Sheet1!A:E')
            values: Lista de listas com os valores a adicionar
            value_input_option: 'RAW' ou 'USER_ENTERED'

        Returns:
            Resultado da operação
        """
        try:
            body = {'values': values}

            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()

            self.logger.info(
                f"Adicionadas {result.get('updates', {}).get('updatedRows')} linhas"
            )
            return result

        except Exception as e:
            self.logger.error(f"Erro ao adicionar na planilha: {str(e)}")
            raise

    def clear_sheet(self, spreadsheet_id: str, range_name: str) -> Dict:
        """
        Limpa dados de um range

        Args:
            spreadsheet_id: ID da planilha
            range_name: Range a limpar (ex: 'Sheet1!A2:E100')

        Returns:
            Resultado da operação
        """
        try:
            result = self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                body={}
            ).execute()

            self.logger.info(f"Range {range_name} limpo com sucesso")
            return result

        except Exception as e:
            self.logger.error(f"Erro ao limpar planilha: {str(e)}")
            raise

    def batch_update(
        self,
        spreadsheet_id: str,
        data: List[Dict]
    ) -> Dict:
        """
        Atualiza múltiplos ranges em uma única requisição

        Args:
            spreadsheet_id: ID da planilha
            data: Lista de dicionários com 'range' e 'values'
                  Ex: [{'range': 'Sheet1!A1', 'values': [['Value']]}]

        Returns:
            Resultado da operação
        """
        try:
            body = {
                'valueInputOption': 'RAW',
                'data': data
            }

            result = self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()

            self.logger.info(
                f"Batch update: {result.get('totalUpdatedCells')} células atualizadas"
            )
            return result

        except Exception as e:
            self.logger.error(f"Erro no batch update: {str(e)}")
            raise

    def create_sheet(
        self,
        spreadsheet_id: str,
        sheet_title: str
    ) -> Dict:
        """
        Cria uma nova aba na planilha

        Args:
            spreadsheet_id: ID da planilha
            sheet_title: Nome da nova aba

        Returns:
            Resultado da operação
        """
        try:
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_title
                        }
                    }
                }]
            }

            result = self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()

            self.logger.info(f"Aba '{sheet_title}' criada com sucesso")
            return result

        except Exception as e:
            self.logger.error(f"Erro ao criar aba: {str(e)}")
            raise

    @staticmethod
    def extract_spreadsheet_id(url: str) -> str:
        """
        Extrai o ID da planilha de uma URL do Google Sheets

        Args:
            url: URL completa da planilha

        Returns:
            ID da planilha

        Example:
            https://docs.google.com/spreadsheets/d/ABC123/edit
            -> ABC123
        """
        if '/d/' in url:
            return url.split('/d/')[1].split('/')[0]
        return url
