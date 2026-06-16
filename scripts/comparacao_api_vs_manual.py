"""
Script de Comparacao: API Inhire vs Planilha Manual
Compara dados da view vw_analise_posicoes com dados da planilha manual do Google Sheets
Gera relatorio de divergencias em nova aba no Google Sheets

Versao 3.0: Token-Based Fuzzy Matching com Threshold Dinamico
- Token-based matching usando fuzzywuzzy (ignora ordem de palavras)
- Normaliza modificadores de cargo (Senior, Pleno, Junior, Hibrido, Remoto, etc.)
- Threshold dinamico: 75% se cliente+datas batem, 85% caso contrario
- Remove acentos, espacos extras, caracteres especiais
- Prioriza matching por: cliente + data publicacao + data encerramento

Autor: Framework Data Team
Data: 2026-03-13
Versao: 3.0
"""
import os
import sys
import pickle
import re
import unicodedata
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
from fuzzywuzzy import fuzz
from dotenv import load_dotenv

# Adiciona o diretorio raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Carrega variaveis de ambiente do .env
load_dotenv()

import psycopg2
from psycopg2 import extras
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scopes necessarios
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Configuracoes
SPREADSHEET_ID = '1E5OPRJPuv333xGXcd2ITlwzM0zNzEZa3Uun3ZHTLv9U'
ABA_MANUAL = 'Acompanhamento Vagas'
ABA_DIVERGENCIAS = 'Divergencias'

# Mapeamento de status API -> Planilha Manual
STATUS_MAPPING = {
    'open': 'Aberto',
    'closed': 'Fechado',
    'canceled': 'Cancelado',
    'paused': 'Pausado',
    'archived': 'Arquivado'
}

# Mapeamento inverso para normalizar
STATUS_REVERSE_MAPPING = {v: k for k, v in STATUS_MAPPING.items()}


def get_google_sheets_service():
    """Autentica e retorna o servico do Google Sheets"""
    creds = None
    token_path = 'token.pickle'

    # Carrega credenciais salvas
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # Se nao ha credenciais validas, faz login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Salva as credenciais para proxima execucao
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('sheets', 'v4', credentials=creds)


def connect_database():
    """Conecta ao banco de dados PostgreSQL"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'inhire'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        print("   [OK] Conectado ao banco de dados PostgreSQL")
        return conn
    except Exception as e:
        print(f"   [ERRO] Erro ao conectar ao banco: {str(e)}")
        raise


def fetch_api_data(conn) -> List[Dict]:
    """
    Busca dados da API (view vw_analise_posicoes)

    Returns:
        Lista de dicionarios com dados da API
    """
    try:
        cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

        query = """
            SELECT
                cargo,
                data_publicacao,
                cliente,
                status_atual,
                data_encerramento_ou_atualizacao
            FROM vw_analise_posicoes
            WHERE cargo IS NOT NULL
                AND cliente IS NOT NULL
                AND data_publicacao IS NOT NULL
            ORDER BY cargo, cliente, data_publicacao
        """

        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()

        # Converte para lista de dicts
        data = []
        for row in rows:
            data.append({
                'cargo': str(row['cargo']).strip() if row['cargo'] else '',
                'data_publicacao': row['data_publicacao'],
                'cliente': str(row['cliente']).strip() if row['cliente'] else '',
                'status': str(row['status_atual']).strip().lower() if row['status_atual'] else '',
                'data_encerramento': row['data_encerramento_ou_atualizacao']
            })

        print(f"   [OK] Extraidos {len(data):,} registros da API (vw_analise_posicoes)")
        return data

    except Exception as e:
        print(f"   [ERRO] Erro ao buscar dados da API: {str(e)}")
        raise


def fetch_manual_data(service) -> List[Dict]:
    """
    Busca dados da planilha manual

    Args:
        service: Servico do Google Sheets

    Returns:
        Lista de dicionarios com dados manuais
    """
    try:
        # Le dados da aba
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{ABA_MANUAL}!A:Z"
        ).execute()

        values = result.get('values', [])

        if not values:
            print(f"   [ERRO] Aba '{ABA_MANUAL}' esta vazia")
            return []

        # Primeira linha eh o cabecalho
        headers = values[0]

        # Indices fixos baseados na estrutura conhecida da planilha
        # Coluna 5: Cargo
        # Coluna 7: Data da publicacao
        # Coluna 8: Cliente
        # Coluna 10: Status
        # Coluna 11: Data de Encerramento
        cargo_idx = 5
        data_pub_idx = 7
        cliente_idx = 8
        status_idx = 10
        data_enc_idx = 11

        print(f"\n   Colunas mapeadas (indices fixos):")
        print(f"      Cargo: coluna {cargo_idx} ({headers[cargo_idx]})")
        print(f"      Data Publicacao: coluna {data_pub_idx} ({headers[data_pub_idx]})")
        print(f"      Cliente: coluna {cliente_idx} ({headers[cliente_idx]})")
        print(f"      Status: coluna {status_idx} ({headers[status_idx]})")
        print(f"      Data Encerramento: coluna {data_enc_idx} ({headers[data_enc_idx]})\n")

        # Processa linhas de dados
        data = []
        for i, row in enumerate(values[1:], start=2):
            # Pula linhas vazias
            if not row or len(row) == 0:
                continue

            # Extrai valores
            cargo = row[cargo_idx].strip() if len(row) > cargo_idx and row[cargo_idx] else ''
            data_pub = row[data_pub_idx].strip() if len(row) > data_pub_idx and row[data_pub_idx] else ''
            cliente = row[cliente_idx].strip() if len(row) > cliente_idx and row[cliente_idx] else ''
            status = row[status_idx].strip() if len(row) > status_idx and row[status_idx] else ''
            data_enc = row[data_enc_idx].strip() if data_enc_idx is not None and len(row) > data_enc_idx and row[data_enc_idx] else ''

            # Pula linhas sem dados essenciais
            if not cargo or not cliente or not data_pub:
                continue

            data.append({
                'cargo': cargo,
                'data_publicacao': parse_date(data_pub),
                'cliente': cliente,
                'status': normalize_status(status),
                'data_encerramento': parse_date(data_enc),
                'row_number': i  # Para referencia
            })

        print(f"   [OK] Extraidos {len(data):,} registros da planilha manual (aba '{ABA_MANUAL}')")
        return data

    except Exception as e:
        print(f"   [ERRO] Erro ao buscar dados da planilha manual: {str(e)}")
        raise


def parse_date(date_str: str) -> Optional[date]:
    """
    Converte string de data para objeto date
    Aceita formatos: DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY
    """
    if not date_str or date_str.strip() == '':
        return None

    date_str = date_str.strip()

    # Tenta diferentes formatos
    formats = [
        '%d/%m/%Y',
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%d/%m/%y',
        '%Y/%m/%d'
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    print(f"      AVISO: Nao foi possivel converter data '{date_str}'")
    return None


def remove_accents(text: str) -> str:
    """
    Remove acentos de uma string
    Ex: 'Analista Financeiro' -> 'Analista Financeiro'
        'Gerente Sênior' -> 'Gerente Senior'
    """
    if not text:
        return ''

    # Normaliza para NFD (decompõe caracteres acentuados)
    nfd = unicodedata.normalize('NFD', text)
    # Remove caracteres de marcação (acentos)
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')


def normalize_string(text: str) -> str:
    """
    Normaliza uma string para comparação:
    - Remove acentos
    - Converte para lowercase
    - Remove espaços extras
    - Remove caracteres especiais
    """
    if not text:
        return ''

    # Remove acentos
    text = remove_accents(text)

    # Lowercase
    text = text.lower()

    # Remove caracteres especiais, mantém apenas letras, números e espaços
    text = re.sub(r'[^a-z0-9\s]', ' ', text)

    # Remove espaços extras
    text = ' '.join(text.split())

    return text.strip()


def normalize_cargo_advanced(cargo: str) -> str:
    """
    Normaliza cargo removendo modificadores de senioridade e modalidade

    Remove:
    - Senioridades: Senior, Sênior, Pleno, Junior, Júnior, Jr, Sr
    - Modalidades: Remoto, Presencial, Híbrido, Hibrido
    - Outros: PCD, Aprendiz, Temporário, Full-time, Part-time
    - Conteúdo entre parênteses: (BI), (Squad), etc.

    Exemplo:
        "Analista de ChatBot - Senior" -> "analista chatbot"
        "Curador Analista de ChatBot - Hibrido" -> "curador analista chatbot"
    """
    if not cargo:
        return ''

    # Primeiro normaliza (remove acentos, lowercase, etc.)
    cargo_norm = normalize_string(cargo)

    # Lista de modificadores a remover
    modifiers = [
        r'\bsenior\b', r'\bsenior\b', r'\bsr\b',
        r'\bpleno\b', r'\bpl\b',
        r'\bjunior\b', r'\bjunior\b', r'\bjr\b',
        r'\bremoto\b',
        r'\bpresencial\b',
        r'\bhibrido\b', r'\bhibrido\b',
        r'\bfull time\b', r'\bpart time\b',
        r'\bpcd\b',
        r'\baprendiz\b',
        r'\btemporario\b',
        r'\bestagiario\b',
        r'\binternship\b'
    ]

    # Remove modificadores
    for mod in modifiers:
        cargo_norm = re.sub(mod, '', cargo_norm, flags=re.IGNORECASE)

    # Remove conteúdo entre parênteses
    cargo_norm = re.sub(r'\s*\([^)]*\)\s*', ' ', cargo_norm)

    # Remove espaços extras
    cargo_norm = ' '.join(cargo_norm.split())

    return cargo_norm.strip()


def string_similarity(str1: str, str2: str) -> float:
    """
    Calcula similaridade entre duas strings usando fuzzywuzzy token-based matching
    Retorna valor entre 0.0 (totalmente diferente) e 1.0 (idêntico)

    Usa 3 algoritmos e retorna o melhor score:
    1. token_set_ratio: ignora ordem de palavras e duplicatas
    2. token_sort_ratio: ordena tokens antes de comparar
    3. partial_ratio: encontra substrings similares
    """
    if not str1 or not str2:
        return 0.0

    # Normaliza ambas as strings
    s1 = normalize_string(str1)
    s2 = normalize_string(str2)

    # Usa diferentes algoritmos fuzzy e pega o melhor score
    scores = [
        fuzz.token_set_ratio(s1, s2),      # Ignora ordem e duplicatas
        fuzz.token_sort_ratio(s1, s2),     # Ordena tokens
        fuzz.partial_ratio(s1, s2)         # Match parcial
    ]

    # Retorna o melhor score (0-100) convertido para 0-1
    return max(scores) / 100.0


def normalize_status(status_str: str) -> str:
    """
    Normaliza status para formato padrao (lowercase)
    Converte status traduzidos para ingles
    """
    if not status_str:
        return ''

    status_clean = status_str.strip()

    # Se ja esta em ingles (lowercase)
    if status_clean.lower() in STATUS_MAPPING.keys():
        return status_clean.lower()

    # Se esta em portugues, converte
    if status_clean in STATUS_REVERSE_MAPPING:
        return STATUS_REVERSE_MAPPING[status_clean]

    # Tenta match case-insensitive
    for pt, en in STATUS_REVERSE_MAPPING.items():
        if status_clean.lower() == pt.lower():
            return en

    return status_clean.lower()


def create_key_strategy_1(record: Dict) -> str:
    """
    Estrategia 1: Match perfeito normalizado
    Chave: cargo_normalizado + cliente_normalizado + data_pub
    """
    cargo = normalize_string(record.get('cargo', ''))
    cliente = normalize_string(record.get('cliente', ''))
    data_pub = record.get('data_publicacao')

    if isinstance(data_pub, date):
        data_str = data_pub.isoformat()
    elif isinstance(data_pub, str):
        data_str = data_pub
    else:
        data_str = ''

    return f"{cargo}||{cliente}||{data_str}"


def create_key_strategy_2(record: Dict) -> str:
    """
    Estrategia 2: Match por cliente + datas (ignora cargo)
    Chave: cliente_normalizado + data_pub + data_enc
    """
    cliente = normalize_string(record.get('cliente', ''))
    data_pub = record.get('data_publicacao')
    data_enc = record.get('data_encerramento')

    data_pub_str = data_pub.isoformat() if isinstance(data_pub, date) else str(data_pub) if data_pub else 'none'
    data_enc_str = data_enc.isoformat() if isinstance(data_enc, date) else str(data_enc) if data_enc else 'none'

    return f"{cliente}||{data_pub_str}||{data_enc_str}"


def create_key_strategy_3(record: Dict) -> str:
    """
    Estrategia 3: Match por cliente + data_pub (ignora cargo e data_enc)
    Chave: cliente_normalizado + data_pub
    """
    cliente = normalize_string(record.get('cliente', ''))
    data_pub = record.get('data_publicacao')

    data_pub_str = data_pub.isoformat() if isinstance(data_pub, date) else str(data_pub) if data_pub else 'none'

    return f"{cliente}||{data_pub_str}"


def find_best_match(api_record: Dict, manual_data: List[Dict], used_indices: set, base_threshold: float = 0.85) -> Tuple[Optional[Dict], Optional[str], Optional[float]]:
    """
    Encontra o melhor match para um registro da API na planilha manual
    usando multiplas estrategias com THRESHOLD DINAMICO

    Args:
        api_record: Registro da API
        manual_data: Lista de registros manuais
        used_indices: Set de indices ja usados (para evitar duplicatas)
        base_threshold: Threshold base para matching fuzzy (0-1), default 0.85

    Returns:
        Tupla (registro_manual_matched, estrategia_usada, similarity_score) ou (None, None, None)
    """

    # Estrategia 1: Match perfeito normalizado (cargo + cliente + data_pub)
    key_s1 = create_key_strategy_1(api_record)
    for idx, manual_record in enumerate(manual_data):
        if idx in used_indices:
            continue
        if create_key_strategy_1(manual_record) == key_s1:
            return manual_record, 'Match Perfeito (cargo+cliente+data_pub)', 1.0

    # Estrategia 2: Match por cliente + datas (ignora cargo)
    key_s2 = create_key_strategy_2(api_record)
    if key_s2 != '||none||none':  # Ignora se nao tem datas
        for idx, manual_record in enumerate(manual_data):
            if idx in used_indices:
                continue
            if create_key_strategy_2(manual_record) == key_s2:
                # Calcula similaridade mesmo para este match (para relatorio)
                sim = string_similarity(api_record.get('cargo', ''), manual_record.get('cargo', ''))
                return manual_record, 'Match por Cliente+Datas (ignora cargo)', sim

    # Estrategia 3: Match fuzzy de cargo + cliente + data_pub COM THRESHOLD DINAMICO
    api_cliente_norm = normalize_string(api_record.get('cliente', ''))
    api_data_pub = api_record.get('data_publicacao')
    api_data_pub_str = api_data_pub.isoformat() if isinstance(api_data_pub, date) else str(api_data_pub) if api_data_pub else None

    best_match = None
    best_similarity = 0.0

    for idx, manual_record in enumerate(manual_data):
        if idx in used_indices:
            continue

        # Deve ter mesmo cliente e mesma data de publicacao
        manual_cliente_norm = normalize_string(manual_record.get('cliente', ''))
        manual_data_pub = manual_record.get('data_publicacao')
        manual_data_pub_str = manual_data_pub.isoformat() if isinstance(manual_data_pub, date) else str(manual_data_pub) if manual_data_pub else None

        if api_cliente_norm != manual_cliente_norm or api_data_pub_str != manual_data_pub_str:
            continue

        # Calcula similaridade do cargo
        similarity = string_similarity(api_record.get('cargo', ''), manual_record.get('cargo', ''))

        # THRESHOLD DINAMICO: Se cliente + data_pub batem, usa threshold mais baixo
        threshold = 0.75  # 75% quando cliente+data_pub batem (vs 85% padrao)

        if similarity >= threshold and similarity > best_similarity:
            best_similarity = similarity
            best_match = manual_record

    if best_match:
        return best_match, f'Match Fuzzy cargo ({best_similarity:.1%}) + Cliente+Data_Pub', best_similarity

    # Estrategia 4: Match por cliente + data_pub (ignora cargo e data_enc)
    key_s3 = create_key_strategy_3(api_record)
    if key_s3 != '||none':
        for idx, manual_record in enumerate(manual_data):
            if idx in used_indices:
                continue
            if create_key_strategy_3(manual_record) == key_s3:
                # Calcula similaridade mesmo para este match
                sim = string_similarity(api_record.get('cargo', ''), manual_record.get('cargo', ''))
                return manual_record, 'Match por Cliente+Data_Pub (ignora cargo e data_enc)', sim

    return None, None, None


def compare_data(api_data: List[Dict], manual_data: List[Dict]) -> Dict:
    """
    Compara dados da API com dados manuais usando matching fuzzy e multiplas estrategias

    Returns:
        Dicionario com estatisticas e divergencias
    """
    print("\n   Comparando dados usando token-based fuzzy matching...")
    print("   Estrategias de matching:")
    print("      1. Match Perfeito: cargo+cliente+data_pub (normalizados)")
    print("      2. Match por Datas: cliente+data_pub+data_enc (ignora cargo)")
    print("      3. Match Fuzzy: cargo similar (>=75%) + cliente+data_pub [THRESHOLD DINAMICO]")
    print("      4. Match Relaxado: cliente+data_pub (ignora cargo e data_enc)\n")

    # Estatisticas
    stats = {
        'total_api': len(api_data),
        'total_manual': len(manual_data),
        'apenas_api': 0,
        'apenas_manual': 0,
        'com_divergencias': 0,
        'sem_divergencias': 0,
        'divergencias_status': 0,
        'divergencias_data_pub': 0,
        'divergencias_data_enc': 0,
        'divergencias_cliente': 0,
        'divergencias_cargo_fuzzy': 0,
        'match_strategy_1': 0,
        'match_strategy_2': 0,
        'match_strategy_3': 0,
        'match_strategy_4': 0
    }

    divergencias = []
    used_manual_indices = set()

    # 1. Para cada registro da API, tenta encontrar match na planilha manual
    for api_record in api_data:
        manual_match, strategy, similarity_score = find_best_match(api_record, manual_data, used_manual_indices)

        if manual_match:
            # Encontrou match - marca como usado
            manual_idx = manual_data.index(manual_match)
            used_manual_indices.add(manual_idx)

            # Atualiza estatisticas de estrategia
            if 'Perfeito' in strategy:
                stats['match_strategy_1'] += 1
            elif 'Datas' in strategy:
                stats['match_strategy_2'] += 1
            elif 'Fuzzy' in strategy:
                stats['match_strategy_3'] += 1
                stats['divergencias_cargo_fuzzy'] += 1
            elif 'Relaxado' in strategy:
                stats['match_strategy_4'] += 1

            # Verifica divergencias
            divergencias_encontradas = []

            # Compara status
            if api_record['status'] != manual_match['status']:
                stats['divergencias_status'] += 1
                divergencias_encontradas.append(f"Status: API='{STATUS_MAPPING.get(api_record['status'], api_record['status'])}' vs Manual='{STATUS_MAPPING.get(manual_match['status'], manual_match['status'])}'")

            # Compara data de encerramento
            api_enc = api_record.get('data_encerramento')
            manual_enc = manual_match.get('data_encerramento')

            if api_enc != manual_enc:
                # Ignora se ambos sao None/vazios
                if not (api_enc is None and manual_enc is None):
                    stats['divergencias_data_enc'] += 1
                    api_enc_str = api_enc.isoformat() if isinstance(api_enc, date) else str(api_enc) if api_enc else 'N/A'
                    manual_enc_str = manual_enc.isoformat() if isinstance(manual_enc, date) else str(manual_enc) if manual_enc else 'N/A'
                    divergencias_encontradas.append(f"Data Encerramento: API={api_enc_str} vs Manual={manual_enc_str}")

            # Verifica se cargo e diferente (para estrategias que ignoram cargo)
            if normalize_string(api_record['cargo']) != normalize_string(manual_match['cargo']):
                divergencias_encontradas.append(f"Cargo: API='{api_record['cargo']}' vs Manual='{manual_match['cargo']}'")

            # Se houver divergencias, adiciona ao relatorio
            if divergencias_encontradas:
                stats['com_divergencias'] += 1
                divergencias.append({
                    'tipo': 'DIVERGENCIA',
                    'cargo': api_record['cargo'],
                    'cargo_manual': manual_match['cargo'],
                    'cliente': api_record['cliente'],
                    'data_publicacao': api_record['data_publicacao'],
                    'status_api': api_record['status'],
                    'status_manual': manual_match['status'],
                    'data_enc_api': api_record.get('data_encerramento'),
                    'data_enc_manual': manual_match.get('data_encerramento'),
                    'match_strategy': strategy,
                    'similarity_score': similarity_score,
                    'detalhes': '; '.join(divergencias_encontradas)
                })
            else:
                stats['sem_divergencias'] += 1

        else:
            # Nao encontrou match - vaga existe apenas na API
            stats['apenas_api'] += 1
            divergencias.append({
                'tipo': 'APENAS_API',
                'cargo': api_record['cargo'],
                'cargo_manual': '',
                'cliente': api_record['cliente'],
                'data_publicacao': api_record['data_publicacao'],
                'status_api': api_record['status'],
                'status_manual': '',
                'data_enc_api': api_record.get('data_encerramento'),
                'data_enc_manual': None,
                'match_strategy': 'N/A',
                'similarity_score': None,
                'detalhes': 'Vaga existe apenas na API, nao encontrada na planilha manual'
            })

    # 2. Registros da planilha manual que nao foram matched
    for idx, manual_record in enumerate(manual_data):
        if idx not in used_manual_indices:
            stats['apenas_manual'] += 1
            divergencias.append({
                'tipo': 'APENAS_MANUAL',
                'cargo': manual_record['cargo'],
                'cargo_manual': manual_record['cargo'],
                'cliente': manual_record['cliente'],
                'data_publicacao': manual_record['data_publicacao'],
                'status_api': '',
                'status_manual': manual_record['status'],
                'data_enc_api': None,
                'data_enc_manual': manual_record.get('data_encerramento'),
                'match_strategy': 'N/A',
                'similarity_score': None,
                'detalhes': 'Vaga existe apenas na planilha manual, nao encontrada na API'
            })

    print(f"   [OK] Comparacao concluida")
    print(f"\n   Estatisticas de Matching:")
    print(f"      Estrategia 1 (Perfeito): {stats['match_strategy_1']:,}")
    print(f"      Estrategia 2 (Datas): {stats['match_strategy_2']:,}")
    print(f"      Estrategia 3 (Fuzzy): {stats['match_strategy_3']:,}")
    print(f"      Estrategia 4 (Relaxado): {stats['match_strategy_4']:,}")
    print(f"      Total de matches: {stats['match_strategy_1'] + stats['match_strategy_2'] + stats['match_strategy_3'] + stats['match_strategy_4']:,}\n")

    return {
        'stats': stats,
        'divergencias': divergencias
    }


def export_to_sheets(service, stats: Dict, divergencias: List[Dict]):
    """
    Exporta relatorio de divergencias para Google Sheets
    """
    print(f"\n   Exportando relatorio para aba '{ABA_DIVERGENCIAS}'...")

    try:
        # Tenta criar a aba (se ja existir, vai dar erro e vamos ignorar)
        try:
            request = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': ABA_DIVERGENCIAS
                        }
                    }
                }]
            }
            service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=request
            ).execute()
            print(f"      [OK] Aba '{ABA_DIVERGENCIAS}' criada")
        except HttpError:
            print(f"      [INFO] Aba '{ABA_DIVERGENCIAS}' ja existe, sera sobrescrita")

        # Limpa a aba
        service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{ABA_DIVERGENCIAS}!A:Z",
            body={}
        ).execute()

        # Prepara dados para exportacao
        values = []

        # SECAO 1: RESUMO EXECUTIVO
        total_matches = stats['match_strategy_1'] + stats['match_strategy_2'] + stats['match_strategy_3'] + stats['match_strategy_4']

        values.append(['RELATORIO DE COMPARACAO: API vs PLANILHA MANUAL (COM MATCHING FUZZY)'])
        values.append(['Data/Hora:', datetime.now().strftime('%d/%m/%Y %H:%M:%S')])
        values.append(['Versao:', '2.0 - Matching Fuzzy e Multiplas Estrategias'])
        values.append([])
        values.append(['RESUMO EXECUTIVO'])
        values.append(['=' * 80])
        values.append(['Total de vagas na API:', stats['total_api']])
        values.append(['Total de vagas na planilha manual:', stats['total_manual']])
        values.append([])
        values.append(['Vagas apenas na API:', stats['apenas_api']])
        values.append(['Vagas apenas na planilha manual:', stats['apenas_manual']])
        values.append([])
        values.append(['Vagas em ambas as fontes (match):', total_matches])
        values.append(['  - Sem divergencias:', f"{stats['sem_divergencias']} ({100*stats['sem_divergencias']/total_matches if total_matches > 0 else 0:.1f}%)"])
        values.append(['  - Com divergencias:', f"{stats['com_divergencias']} ({100*stats['com_divergencias']/total_matches if total_matches > 0 else 0:.1f}%)"])
        values.append([])
        values.append(['ESTRATEGIAS DE MATCHING USADAS'])
        values.append(['=' * 80])
        values.append(['Match Perfeito (cargo+cliente+data_pub):', f"{stats['match_strategy_1']} ({100*stats['match_strategy_1']/total_matches if total_matches > 0 else 0:.1f}%)"])
        values.append(['Match por Datas (cliente+data_pub+data_enc):', f"{stats['match_strategy_2']} ({100*stats['match_strategy_2']/total_matches if total_matches > 0 else 0:.1f}%)"])
        values.append(['Match Fuzzy cargo >85% (cargo+cliente+data_pub):', f"{stats['match_strategy_3']} ({100*stats['match_strategy_3']/total_matches if total_matches > 0 else 0:.1f}%)"])
        values.append(['Match Relaxado (cliente+data_pub):', f"{stats['match_strategy_4']} ({100*stats['match_strategy_4']/total_matches if total_matches > 0 else 0:.1f}%)"])
        values.append([])
        values.append(['BREAKDOWN DE DIVERGENCIAS'])
        values.append(['=' * 80])
        values.append(['Divergencias de status:', stats['divergencias_status']])
        values.append(['Divergencias de data de encerramento:', stats['divergencias_data_enc']])
        values.append(['Divergencias de cargo (fuzzy match):', stats['divergencias_cargo_fuzzy']])
        values.append([])
        values.append([])

        # SECAO 2: TABELA DE DIVERGENCIAS
        values.append(['DETALHAMENTO DAS DIVERGENCIAS'])
        values.append(['=' * 80])
        values.append([])

        # Cabecalho da tabela
        values.append([
            'Tipo',
            'Cargo API',
            'Cargo Manual',
            'Cliente',
            'Data Publicacao',
            'Status API',
            'Status Manual',
            'Data Encerramento API',
            'Data Encerramento Manual',
            'Estrategia de Match',
            'Similaridade %',
            'Detalhes'
        ])

        # Linhas de divergencias
        for div in divergencias:
            # Formata datas
            data_pub_str = div['data_publicacao'].isoformat() if isinstance(div['data_publicacao'], date) else str(div['data_publicacao']) if div['data_publicacao'] else ''
            data_enc_api_str = div['data_enc_api'].isoformat() if isinstance(div['data_enc_api'], date) else str(div['data_enc_api']) if div['data_enc_api'] else ''
            data_enc_manual_str = div['data_enc_manual'].isoformat() if isinstance(div['data_enc_manual'], date) else str(div['data_enc_manual']) if div['data_enc_manual'] else ''

            # Traduz status para portugues
            status_api_pt = STATUS_MAPPING.get(div['status_api'], div['status_api']) if div['status_api'] else ''
            status_manual_pt = STATUS_MAPPING.get(div['status_manual'], div['status_manual']) if div['status_manual'] else ''

            # Formata similaridade
            similarity_score = div.get('similarity_score')
            if similarity_score is not None:
                similarity_str = f"{similarity_score:.1%}"
            else:
                similarity_str = 'N/A'

            values.append([
                div['tipo'],
                div['cargo'],
                div.get('cargo_manual', ''),
                div['cliente'],
                data_pub_str,
                status_api_pt,
                status_manual_pt,
                data_enc_api_str,
                data_enc_manual_str,
                div.get('match_strategy', 'N/A'),
                similarity_str,
                div['detalhes']
            ])

        # Escreve tudo de uma vez
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{ABA_DIVERGENCIAS}!A1",
            valueInputOption='USER_ENTERED',
            body={'values': values}
        ).execute()

        print(f"      [OK] {len(values):,} linhas escritas na aba '{ABA_DIVERGENCIAS}'")
        print(f"\n   URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

    except Exception as e:
        print(f"   [ERRO] Erro ao exportar para Google Sheets: {str(e)}")
        raise


def print_summary(stats: Dict, divergencias: List[Dict]):
    """Imprime resumo no console"""
    print("\n" + "="*80)
    print(" RESUMO DA COMPARACAO (COM MATCHING FUZZY)")
    print("="*80)
    print(f"\nTOTAL DE VAGAS:")
    print(f"  API (vw_analise_posicoes): {stats['total_api']:,}")
    print(f"  Planilha Manual:            {stats['total_manual']:,}")
    print(f"\nVAGAS UNICAS:")
    print(f"  Apenas na API:              {stats['apenas_api']:,}")
    print(f"  Apenas na Planilha Manual:  {stats['apenas_manual']:,}")

    total_matches = stats['match_strategy_1'] + stats['match_strategy_2'] + stats['match_strategy_3'] + stats['match_strategy_4']

    print(f"\nVAGAS EM AMBAS AS FONTES (MATCHES):")
    print(f"  Total com match:            {total_matches:,}")
    print(f"  - Sem divergencias:         {stats['sem_divergencias']:,} ({100*stats['sem_divergencias']/total_matches if total_matches > 0 else 0:.1f}%)")
    print(f"  - Com divergencias:         {stats['com_divergencias']:,} ({100*stats['com_divergencias']/total_matches if total_matches > 0 else 0:.1f}%)")

    print(f"\nESTRATEGIAS DE MATCHING USADAS:")
    print(f"  Match Perfeito:             {stats['match_strategy_1']:,} ({100*stats['match_strategy_1']/total_matches if total_matches > 0 else 0:.1f}%)")
    print(f"  Match por Datas:            {stats['match_strategy_2']:,} ({100*stats['match_strategy_2']/total_matches if total_matches > 0 else 0:.1f}%)")
    print(f"  Match Fuzzy (cargo):        {stats['match_strategy_3']:,} ({100*stats['match_strategy_3']/total_matches if total_matches > 0 else 0:.1f}%)")
    print(f"  Match Relaxado:             {stats['match_strategy_4']:,} ({100*stats['match_strategy_4']/total_matches if total_matches > 0 else 0:.1f}%)")

    print(f"\nBREAKDOWN DE DIVERGENCIAS:")
    print(f"  Status:                     {stats['divergencias_status']:,}")
    print(f"  Data de Encerramento:       {stats['divergencias_data_enc']:,}")
    print(f"  Cargo (fuzzy match):        {stats['divergencias_cargo_fuzzy']:,}")
    print(f"\nTOTAL DE DIVERGENCIAS ENCONTRADAS: {len(divergencias):,}")
    print("="*80 + "\n")


def main():
    """Funcao principal"""
    try:
        print("\n" + "="*80)
        print(" COMPARACAO DE DADOS: API INHIRE vs PLANILHA MANUAL")
        print("="*80 + "\n")

        # 1. Conecta ao banco
        print("1. Conectando ao banco de dados PostgreSQL")
        print("-" * 80)
        conn = connect_database()

        # 2. Autentica com Google Sheets
        print("\n2. Autenticando com Google Sheets API (OAuth2)")
        print("-" * 80)
        print("   Se necessario, sera aberta uma janela do navegador para autorizacao...")
        service = get_google_sheets_service()
        print("   [OK] Autenticado com sucesso")

        # 3. Busca dados da API
        print("\n3. Buscando dados da API (vw_analise_posicoes)")
        print("-" * 80)
        api_data = fetch_api_data(conn)

        # 4. Busca dados da planilha manual
        print(f"\n4. Buscando dados da planilha manual (aba '{ABA_MANUAL}')")
        print("-" * 80)
        manual_data = fetch_manual_data(service)

        # 5. Compara dados
        print("\n5. Comparando dados")
        print("-" * 80)
        resultado = compare_data(api_data, manual_data)

        # 6. Exporta relatorio
        print("\n6. Exportando relatorio para Google Sheets")
        print("-" * 80)
        export_to_sheets(service, resultado['stats'], resultado['divergencias'])

        # 7. Imprime resumo
        print_summary(resultado['stats'], resultado['divergencias'])

        # Fecha conexao
        conn.close()

        print("="*80)
        print(" COMPARACAO CONCLUIDA COM SUCESSO!")
        print("="*80)
        print(f"\nAcesse a aba '{ABA_DIVERGENCIAS}' em:")
        print(f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}\n")

    except Exception as e:
        print(f"\n[ERRO] {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
