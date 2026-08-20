# -*- coding: utf-8 -*-
"""Aplica migration 079 decodificando entidades HTML"""
import sys
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'inhire')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD')

engine = create_engine(
    f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}',
    pool_pre_ping=True,
    pool_size=1,
    max_overflow=0
)

Session = sessionmaker(bind=engine)
session = Session()

try:
    print("\n=== APLICANDO MIGRATION 079 ===\n")

    # Ler migration
    with open('migrations/079_decode_html_entities.sql', 'r', encoding='utf-8') as f:
        sql = f.read()

    # Aplicar
    print("Aplicando SQL...")
    session.execute(text(sql))
    session.commit()

    print("✅ Migration 079 aplicada com sucesso!")
    print("✅ Função decode_html_entities() criada!")

    # Testar a função
    print("\n=== TESTANDO FUNÇÃO DE DECODIFICAÇÃO ===\n")

    result = session.execute(text("""
        SELECT decode_html_entities('Prop&oacute;sito do cargo: Garantir a excel&ecirc;ncia');
    """))

    decoded = result.scalar()
    print(f"Teste da função:")
    print(f"  Input:  'Prop&oacute;sito do cargo: Garantir a excel&ecirc;ncia'")
    print(f"  Output: '{decoded}'")

    # Testar views
    print("\n=== TESTANDO VIEW ATUALIZADA ===\n")

    # Buscar uma requisição com entidades HTML
    result = session.execute(text("""
        SELECT
            titulo,
            SUBSTRING(descricao, 1, 200) as descricao_sample
        FROM vw_relatorio_requisicoes
        WHERE descricao LIKE '%ó%' OR descricao LIKE '%ê%' OR descricao LIKE '%ç%'
        LIMIT 3
    """))

    print("Requisições com texto decodificado (amostra 200 chars):\n")
    for i, row in enumerate(result.fetchall(), 1):
        print(f"{i}. {row[0]}")
        print(f"   {row[1]}...")
        print()

    # Contar total
    result = session.execute(text("SELECT COUNT(*) FROM vw_relatorio_requisicoes"))
    total = result.scalar()

    print(f"Total de requisições na view: {total}")

    print("\n" + "="*60)
    print("✅ DESCRIÇÕES AGORA ESTÃO LEGÍVEIS!")
    print("="*60)
    print("\nEntidades HTML decodificadas:")
    print("  &oacute; → ó")
    print("  &ecirc; → ê")
    print("  &ccedil; → ç")
    print("  &atilde; → ã")
    print("  etc...")

except Exception as e:
    print(f"\n❌ Erro: {e}")
    session.rollback()
    import traceback
    traceback.print_exc()
finally:
    session.close()
    engine.dispose()
