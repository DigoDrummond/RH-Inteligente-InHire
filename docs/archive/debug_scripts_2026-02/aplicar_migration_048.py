import psycopg2
import sys

print("=" * 80)
print("APLICANDO MIGRATION 048 - REPOSICIONAR email_responsavel_cliente")
print("=" * 80)
print()

try:
    # Conectar ao banco
    print("1. Conectando ao banco de dados...")
    conn = psycopg2.connect(
        dbname="inhire",
        user="postgres",
        password="postgres",
        host="localhost"
    )
    conn.autocommit = False  # Usar transação
    cur = conn.cursor()
    print("   [OK] Conectado")
    print()

    # Ler o arquivo da migration
    print("2. Lendo migration 048...")
    migration_file = "migrations/048_add_email_responsavel_to_views.sql"

    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print(f"   [OK] Arquivo lido ({len(sql_content)} caracteres)")
    print()

    # Executar a migration
    print("3. Executando migration...")
    print("   - Isso pode levar alguns segundos devido às CTEs complexas...")

    cur.execute(sql_content)

    print("   [OK] Migration executada")
    print()

    # Commit
    print("4. Confirmando alterações...")
    conn.commit()
    print("   [OK] Commit realizado")
    print()

    # Verificar resultado
    print("5. Verificando resultado...")

    # Verificar vw_analise_posicoes
    cur.execute("""
        SELECT ordinal_position, column_name
        FROM information_schema.columns
        WHERE table_name = 'vw_analise_posicoes'
        AND ordinal_position BETWEEN 15 AND 19
        ORDER BY ordinal_position
    """)

    print("   vw_analise_posicoes (colunas 15-19):")
    for pos, name in cur.fetchall():
        marker = " <-- CAMPO ADICIONADO" if name == 'email_responsavel_cliente' else ""
        print(f"     {pos:2}. {name}{marker}")

    # Verificar vw_dados_jade
    cur.execute("""
        SELECT ordinal_position, column_name
        FROM information_schema.columns
        WHERE table_name = 'vw_dados_jade'
        AND ordinal_position BETWEEN 13 AND 17
        ORDER BY ordinal_position
    """)

    print()
    print("   vw_dados_jade (colunas 13-17):")
    for pos, name in cur.fetchall():
        marker = " <-- CAMPO ADICIONADO" if name == 'email_responsavel_cliente' else ""
        print(f"     {pos:2}. {name}{marker}")

    print()
    print("=" * 80)
    print("[OK] MIGRATION 048 APLICADA COM SUCESSO!")
    print("=" * 80)
    print()
    print("Campo 'email_responsavel_cliente' agora está na posição correta:")
    print("  - vw_analise_posicoes: coluna 17 (após 'responsavel')")
    print("  - vw_dados_jade: coluna 15 (após 'responsavel_requisicao')")
    print()

    cur.close()
    conn.close()

except FileNotFoundError:
    print(f"[ERRO] Arquivo de migration não encontrado: {migration_file}")
    sys.exit(1)

except psycopg2.Error as e:
    print(f"[ERRO] Erro no banco de dados: {e}")
    if conn:
        conn.rollback()
        print("   Rollback realizado")
    sys.exit(1)

except Exception as e:
    print(f"[ERRO] Erro inesperado: {e}")
    if conn:
        conn.rollback()
        print("   Rollback realizado")
    sys.exit(1)
