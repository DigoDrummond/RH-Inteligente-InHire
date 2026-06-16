"""
Wrapper para inicializar o banco de dados com fix de encoding
"""
import os
import sys

# Fix de encoding ANTES de importar qualquer coisa
os.environ['PGCLIENTENCODING'] = 'UTF8'

# Limpar variáveis de ambiente problemáticas
for key in list(os.environ.keys()):
    if key.startswith('PG') and key != 'PGCLIENTENCODING':
        del os.environ[key]

# Agora importar o resto
import psycopg2
from sqlalchemy import create_engine, inspect
from models.database import Base
from config import settings

def main():
    print("=" * 70)
    print(" INICIALIZACAO DO BANCO DE DADOS")
    print("=" * 70)
    print()
    print(f"Banco: {settings.DB_NAME}")
    print(f"Host: {settings.DB_HOST}:{settings.DB_PORT}")
    print(f"User: {settings.DB_USER}")
    print()

    # Testar conexão primeiro
    print("[1] Testando conexao com PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            client_encoding='UTF8',
            connect_timeout=10
        )
        print("    OK - Conexao estabelecida")

        # Listar tabelas existentes
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)

        tabelas_antes = [row[0] for row in cursor.fetchall()]
        print(f"    Tabelas existentes: {len(tabelas_antes)}")
        for t in tabelas_antes:
            print(f"      - {t}")

        cursor.close()
        conn.close()
        print()

    except Exception as e:
        print(f"    ERRO ao conectar: {str(e)}")
        return

    # Criar engine SQLAlchemy
    print("[2] Criando engine SQLAlchemy...")
    try:
        # Construir URL com encoding
        database_url = (
            f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            f"?client_encoding=utf8"
        )

        engine = create_engine(
            database_url,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            echo=False,
            connect_args={
                'client_encoding': 'utf8',
                'connect_timeout': 10
            }
        )
        print("    OK - Engine criada")
        print()

    except Exception as e:
        print(f"    ERRO ao criar engine: {str(e)}")
        return

    # Criar todas as tabelas
    print("[3] Criando tabelas do modelo...")
    try:
        Base.metadata.create_all(engine)
        print("    OK - Tabelas criadas")
        print()

    except Exception as e:
        print(f"    ERRO ao criar tabelas: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # Verificar tabelas criadas
    print("[4] Verificando tabelas criadas...")
    try:
        inspector = inspect(engine)
        tabelas_depois = inspector.get_table_names()

        print(f"    Total de tabelas: {len(tabelas_depois)}")
        print()

        for i, tabela in enumerate(sorted(tabelas_depois), 1):
            colunas = inspector.get_columns(tabela)
            print(f"    {i}. {tabela:30s} ({len(colunas)} colunas)")

        print()

    except Exception as e:
        print(f"    ERRO ao verificar tabelas: {str(e)}")
        return

    # Resumo
    print("=" * 70)
    print(" RESULTADO")
    print("=" * 70)
    print()

    tabelas_esperadas = [
        't_tenant',
        'sync_configuration',
        'sync_log',
        'vagas',
        'posicoes',
        'candidaturas',
        'talentos'
    ]

    tabelas_criadas = []
    tabelas_faltando = []

    for tabela in tabelas_esperadas:
        if tabela in tabelas_depois:
            tabelas_criadas.append(tabela)
        else:
            tabelas_faltando.append(tabela)

    if tabelas_criadas:
        print("Tabelas criadas/existentes:")
        for t in tabelas_criadas:
            print(f"  [OK] {t}")
        print()

    if tabelas_faltando:
        print("Tabelas faltando:")
        for t in tabelas_faltando:
            print(f"  [X] {t}")
        print()

    if len(tabelas_criadas) == len(tabelas_esperadas):
        print("[OK] BANCO INICIALIZADO COM SUCESSO!")
        print()
        print("Proximo passo: python run_sync.py --full")
        print("               (sincronizacao completa ~55 minutos)")
    else:
        print("[!] Banco inicializado parcialmente")
        print(f"    Criadas: {len(tabelas_criadas)}/{len(tabelas_esperadas)}")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
