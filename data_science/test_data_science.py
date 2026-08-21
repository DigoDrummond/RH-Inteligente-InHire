"""
Script de Teste do Ambiente de Ciência de Dados
Valida que conseguimos conectar, carregar dados e fazer análises básicas
"""

import sys
sys.path.append('..')

import pandas as pd
from sqlalchemy import create_engine
from config_ds import Config

def test_connection():
    """Teste 1: Verificar conexão com banco"""
    print("\n" + "="*80)
    print("TESTE 1: CONEXAO COM BANCO DE DADOS")
    print("="*80)

    try:
        engine = create_engine(Config.DATABASE_URL)
        conn = engine.connect()
        conn.close()
        print("[OK] Conexao com PostgreSQL bem-sucedida!")
        return True
    except Exception as e:
        print(f"[ERRO] Falha na conexao: {e}")
        return False

def test_load_data():
    """Teste 2: Carregar dados em DataFrame"""
    print("\n" + "="*80)
    print("TESTE 2: CARREGAR DADOS EM DATAFRAME")
    print("="*80)

    try:
        engine = create_engine(Config.DATABASE_URL)

        # Carregar amostra de vagas
        query = "SELECT id, name, status, area, seniority FROM vagas LIMIT 10"
        df_vagas = pd.read_sql_query(query, engine)

        print(f"[OK] Carregados {len(df_vagas)} registros de vagas")
        print("\nPrimeiras 5 linhas:")
        print(df_vagas.head().to_string())

        return True
    except Exception as e:
        print(f"[ERRO] Falha ao carregar dados: {e}")
        return False

def test_data_analysis():
    """Teste 3: Análise básica com pandas"""
    print("\n" + "="*80)
    print("TESTE 3: ANALISE BASICA COM PANDAS")
    print("="*80)

    try:
        engine = create_engine(Config.DATABASE_URL)

        # Carregar dados
        query = "SELECT status, COUNT(*) as total FROM vagas GROUP BY status"
        df_status = pd.read_sql_query(query, engine)

        print("[OK] Distribuicao de status das vagas:")
        print(df_status.to_string(index=False))

        return True
    except Exception as e:
        print(f"[ERRO] Falha na analise: {e}")
        return False

def test_ml_data_availability():
    """Teste 4: Verificar dados para ML"""
    print("\n" + "="*80)
    print("TESTE 4: DADOS DISPONIVEIS PARA MACHINE LEARNING")
    print("="*80)

    try:
        engine = create_engine(Config.DATABASE_URL)

        # Modelo 1: Tempo de contratacao
        query1 = """
            SELECT COUNT(*) as total
            FROM posicoes
            WHERE hired_at IS NOT NULL
              AND opened_at IS NOT NULL
              AND hired_at > opened_at
        """
        df1 = pd.read_sql_query(query1, engine)
        total_modelo1 = df1['total'].iloc[0]

        # Modelo 2: Conversao de candidatos
        query2 = "SELECT COUNT(*) as total FROM candidaturas WHERE vaga_id IS NOT NULL"
        df2 = pd.read_sql_query(query2, engine)
        total_modelo2 = df2['total'].iloc[0]

        print(f"[OK] Posicoes para Modelo 1 (Tempo Contratacao): {total_modelo1:,}")
        print(f"[OK] Candidaturas para Modelo 2 (Conversao):     {total_modelo2:,}")

        # Validar minimios
        if total_modelo1 >= 600:
            print(f"    [OK] Modelo 1 tem dados suficientes (>= 600)")
        else:
            print(f"    [AVISO] Modelo 1 tem poucos dados (< 600)")

        if total_modelo2 >= 80000:
            print(f"    [OK] Modelo 2 tem dados suficientes (>= 80,000)")
        else:
            print(f"    [AVISO] Modelo 2 tem poucos dados (< 80,000)")

        return True
    except Exception as e:
        print(f"[ERRO] Falha ao verificar dados ML: {e}")
        return False

def main():
    """Executar todos os testes"""
    print("\n" + "="*80)
    print("TESTE DO AMBIENTE DE CIENCIA DE DADOS - INHIRE")
    print("="*80)
    print(f"Python Version: {sys.version}")
    print(f"Pandas Version: {pd.__version__}")
    print()

    resultados = []

    # Executar testes
    resultados.append(("Conexao com Banco", test_connection()))
    resultados.append(("Carregar Dados", test_load_data()))
    resultados.append(("Analise Basica", test_data_analysis()))
    resultados.append(("Dados para ML", test_ml_data_availability()))

    # Resumo
    print("\n" + "="*80)
    print("RESUMO DOS TESTES")
    print("="*80)

    for nome, sucesso in resultados:
        status = "[OK]" if sucesso else "[FALHA]"
        print(f"{status:8s} {nome}")

    total_sucesso = sum(1 for _, s in resultados if s)
    total = len(resultados)

    print("\n" + "="*80)
    if total_sucesso == total:
        print(f"RESULTADO: {total_sucesso}/{total} TESTES PASSARAM - AMBIENTE PRONTO!")
    else:
        print(f"RESULTADO: {total_sucesso}/{total} TESTES PASSARAM - VERIFICAR FALHAS")
    print("="*80)

    return total_sucesso == total

if __name__ == '__main__':
    sucesso = main()
    sys.exit(0 if sucesso else 1)
