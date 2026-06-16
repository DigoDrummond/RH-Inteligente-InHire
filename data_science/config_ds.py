"""
================================================================================
CONFIGURAÇÕES DO PROJETO DE CIÊNCIA DE DADOS - INHIRE
================================================================================
Data: 2026-03-05
Autor: Framework Digital

Este arquivo centraliza todas as configurações do projeto de ciência de dados,
incluindo paths, parâmetros de modelos, conexão com banco de dados, etc.

Uso:
    from config_ds import Config
    config = Config()
    print(config.DB_HOST)
================================================================================
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env (pasta raiz do projeto)
ENV_PATH = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(ENV_PATH)


class Config:
    """
    Classe de configuração centralizada para o projeto de ciência de dados
    """

    # ========================================================================
    # PATHS - Caminhos de Diretórios e Arquivos
    # ========================================================================

    # Diretório raiz do projeto de ciência de dados
    BASE_DIR = Path(__file__).resolve().parent

    # Diretório raiz do projeto Inhire completo
    PROJECT_ROOT = BASE_DIR.parent

    # Subdiretórios
    NOTEBOOKS_DIR = BASE_DIR / 'notebooks'
    SCRIPTS_DIR = BASE_DIR / 'scripts'
    MODELS_DIR = BASE_DIR / 'models'
    DASHBOARDS_DIR = BASE_DIR / 'dashboards'
    DATA_DIR = BASE_DIR / 'data'
    DATASETS_DIR = DATA_DIR / 'datasets_preparados'
    DOCS_DIR = BASE_DIR / 'docs'

    # Arquivos de datasets (serão criados pelos scripts)
    DATASET_TEMPO_CONTRATACAO = DATASETS_DIR / 'dataset_tempo_contratacao.csv'
    DATASET_CONVERSAO_CANDIDATOS = DATASETS_DIR / 'dataset_conversao_candidatos.csv'
    DATASET_FUNIL_AGREGADO = DATASETS_DIR / 'dataset_funil_agregado.csv'

    # Arquivos de modelos treinados (serão salvos após treinamento)
    MODEL_TEMPO_CONTRATACAO = MODELS_DIR / 'modelo_tempo_contratacao.pkl'
    MODEL_CONVERSAO_CANDIDATOS = MODELS_DIR / 'modelo_conversao_candidatos.pkl'

    # ========================================================================
    # DATABASE - Configurações do PostgreSQL
    # ========================================================================

    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_NAME = os.getenv('DB_NAME', 'inhire')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    DB_SCHEMA = os.getenv('DB_SCHEMA', 'public')

    # String de conexão SQLAlchemy
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # String de conexão psycopg2 (alternativa)
    PSYCOPG2_CONN_STRING = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"

    # ========================================================================
    # MACHINE LEARNING - Parâmetros Gerais
    # ========================================================================

    # Seed para reprodutibilidade
    RANDOM_STATE = 42

    # Train/Test Split
    TEST_SIZE = 0.2  # 20% dos dados para teste

    # Cross-Validation
    CV_FOLDS = 5  # 5-fold cross-validation

    # ========================================================================
    # MODELO 1 - PREVISÃO DE TEMPO DE CONTRATAÇÃO (Regressão)
    # ========================================================================

    # Target: dias_para_contratar
    TEMPO_TARGET_COL = 'dias_para_contratar'

    # Features principais
    TEMPO_FEATURES = [
        'area',
        'seniority',
        'salary_max',
        'sla_days_goal',
        'torre',
        'modalidade_contratacao',
        'num_candidaturas',
        'mes_abertura',
        'trimestre_abertura',
        'dia_semana_abertura',
        'tem_salario_informado',
        'tem_sla_definido'
    ]

    # Hiperparâmetros Random Forest (Regressão)
    TEMPO_RF_PARAMS = {
        'n_estimators': 100,
        'max_depth': 10,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'random_state': RANDOM_STATE,
        'n_jobs': -1  # Usar todos os cores disponíveis
    }

    # Hiperparâmetros XGBoost (Regressão)
    TEMPO_XGB_PARAMS = {
        'n_estimators': 100,
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': RANDOM_STATE,
        'n_jobs': -1
    }

    # ========================================================================
    # MODELO 2 - PREVISÃO DE CONVERSÃO DE CANDIDATOS (Classificação)
    # ========================================================================

    # Target: foi_contratado (0 ou 1)
    CONVERSAO_TARGET_COL = 'foi_contratado'

    # Features principais
    CONVERSAO_FEATURES = [
        'source',
        'stage_order',
        'area_vaga',
        'seniority_vaga',
        'salary_max_vaga',
        'tem_linkedin',
        'tem_email',
        'location_categoria',  # Agrupado (SP, RJ, Outros)
        'diversidade_black',
        'diversidade_woman',
        'mes_candidatura',
        'trimestre_candidatura'
    ]

    # Hiperparâmetros Random Forest (Classificação)
    CONVERSAO_RF_PARAMS = {
        'n_estimators': 100,
        'max_depth': 8,
        'min_samples_split': 10,
        'min_samples_leaf': 5,
        'class_weight': 'balanced',  # Importante para dados desbalanceados
        'random_state': RANDOM_STATE,
        'n_jobs': -1
    }

    # Hiperparâmetros XGBoost (Classificação)
    CONVERSAO_XGB_PARAMS = {
        'n_estimators': 100,
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'scale_pos_weight': 10,  # Balancear classes (ajustar conforme necessário)
        'random_state': RANDOM_STATE,
        'n_jobs': -1
    }

    # ========================================================================
    # ANÁLISE DE FUNIL - Configurações
    # ========================================================================

    # Etapas normalizadas do funil (ordem)
    FUNIL_ETAPAS = [
        'Hunting',
        'Abordagem',
        'Inscrição',
        'Bate papo | Pessoas e Cultura',
        'Etapa técnica | Talent IA',
        'Aguardando Devolutiva IA',
        'Bate Papo | Cliente',
        'Formalização de Proposta',
        'Contratação'
    ]

    # Cores para visualização do funil (Plotly)
    FUNIL_CORES = [
        '#1f77b4',  # Azul
        '#ff7f0e',  # Laranja
        '#2ca02c',  # Verde
        '#d62728',  # Vermelho
        '#9467bd',  # Roxo
        '#8c564b',  # Marrom
        '#e377c2',  # Rosa
        '#7f7f7f',  # Cinza
        '#bcbd22'   # Verde-amarelo
    ]

    # ========================================================================
    # VISUALIZAÇÃO - Configurações de Gráficos
    # ========================================================================

    # Tamanho padrão de figuras (matplotlib)
    FIGSIZE_DEFAULT = (12, 6)
    FIGSIZE_LARGE = (15, 8)
    FIGSIZE_SQUARE = (10, 10)

    # Estilo matplotlib/seaborn
    PLOT_STYLE = 'seaborn-v0_8-darkgrid'  # Estilo visual dos gráficos

    # Paleta de cores (seaborn)
    COLOR_PALETTE = 'Set2'

    # ========================================================================
    # DASHBOARD STREAMLIT - Configurações
    # ========================================================================

    # Título do dashboard
    DASHBOARD_TITLE = "Inhire - Análise de Recrutamento e Seleção"

    # Ícone da página (emoji)
    DASHBOARD_ICON = "📊"

    # Layout (wide ou centered)
    DASHBOARD_LAYOUT = "wide"

    # ========================================================================
    # LOGS - Configurações
    # ========================================================================

    # Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_LEVEL = 'INFO'

    # Formato de log
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # ========================================================================
    # MÉTODOS HELPER
    # ========================================================================

    @classmethod
    def criar_diretorios(cls):
        """
        Cria todos os diretórios necessários se não existirem
        """
        diretorios = [
            cls.NOTEBOOKS_DIR,
            cls.SCRIPTS_DIR,
            cls.MODELS_DIR,
            cls.DASHBOARDS_DIR,
            cls.DATA_DIR,
            cls.DATASETS_DIR,
            cls.DOCS_DIR
        ]

        for diretorio in diretorios:
            diretorio.mkdir(parents=True, exist_ok=True)

        print("[OK] Diretorios criados/verificados com sucesso!")

    @classmethod
    def verificar_conexao_db(cls):
        """
        Verifica se a conexão com o banco de dados está funcionando

        Returns:
            bool: True se conectou, False caso contrário
        """
        try:
            import psycopg2
            conn = psycopg2.connect(cls.PSYCOPG2_CONN_STRING)
            conn.close()
            print("[OK] Conexao com PostgreSQL OK!")
            return True
        except Exception as e:
            print(f"[ERRO] Erro ao conectar com PostgreSQL: {e}")
            return False

    @classmethod
    def info(cls):
        """
        Exibe informações sobre a configuração atual
        """
        print("=" * 80)
        print("CONFIGURAÇÃO DO PROJETO DE CIÊNCIA DE DADOS - INHIRE")
        print("=" * 80)
        print(f"Base Directory:       {cls.BASE_DIR}")
        print(f"Project Root:         {cls.PROJECT_ROOT}")
        print(f"Database:             {cls.DB_NAME}@{cls.DB_HOST}:{cls.DB_PORT}")
        print(f"Random State:         {cls.RANDOM_STATE}")
        print(f"Test Size:            {cls.TEST_SIZE * 100}%")
        print(f"CV Folds:             {cls.CV_FOLDS}")
        print("=" * 80)


# ============================================================================
# EXECUÇÃO DIRETA (para testes)
# ============================================================================

if __name__ == '__main__':
    # Criar diretórios
    Config.criar_diretorios()

    # Exibir informações
    Config.info()

    # Verificar conexão com banco
    Config.verificar_conexao_db()
