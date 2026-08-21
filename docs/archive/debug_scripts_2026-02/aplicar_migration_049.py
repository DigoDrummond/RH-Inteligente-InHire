import psycopg2
import sys

print("=" * 80)
print("APLICANDO MIGRATION 049 - ADICIONAR EMPRESA, TIPO POSICAO E MODALIDADE REQ")
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
    print("2. Lendo migration 049...")
    migration_file = "migrations/049_add_empresa_tipo_modalidade_req.sql"

    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print(f"   [OK] Arquivo lido ({len(sql_content)} caracteres)")
    print()

    # Executar a migration
    print("3. Executando migration...")
    print("   - Criando funcao get_custom_field_value...")
    print("   - Recriando view vw_analise_posicoes com 31 colunas...")
    print("   - Isso pode levar alguns segundos...")
    print()

    cur.execute(sql_content)

    print("   [OK] Migration executada")
    print()

    # Commit
    print("4. Confirmando alteracoes...")
    conn.commit()
    print("   [OK] Commit realizado")
    print()

    # Verificar resultado
    print("5. Verificando resultado...")
    print()

    # Contar colunas
    cur.execute("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'vw_analise_posicoes'
    """)
    total_cols = cur.fetchone()[0]
    print(f"   Total de colunas: {total_cols}")

    # Verificar novos campos
    cur.execute("""
        SELECT ordinal_position, column_name
        FROM information_schema.columns
        WHERE table_name = 'vw_analise_posicoes'
        AND column_name IN (
            'modalidade_contratacao_req',
            'empresa',
            'tipo_posicao'
        )
        ORDER BY ordinal_position
    """)

    print()
    print("   Novos campos adicionados:")
    for pos, name in cur.fetchall():
        print(f"     {pos:2}. {name}")

    # Testar se a funcao foi criada
    cur.execute("""
        SELECT COUNT(*)
        FROM pg_proc
        WHERE proname = 'get_custom_field_value'
    """)
    func_exists = cur.fetchone()[0]
    print()
    print(f"   Funcao get_custom_field_value criada? {'SIM' if func_exists > 0 else 'NAO'}")

    # Testar dados
    print()
    print("6. Testando dados...")
    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(modalidade_contratacao_req) as com_modalidade,
            COUNT(empresa) as com_empresa,
            COUNT(tipo_posicao) as com_tipo
        FROM vw_analise_posicoes
    """)
    total, com_mod, com_emp, com_tipo = cur.fetchone()
    print(f"   Total: {total} registros")
    print(f"   Com modalidade_contratacao_req: {com_mod} ({100*com_mod/total if total > 0 else 0:.1f}%)")
    print(f"   Com empresa: {com_emp} ({100*com_emp/total if total > 0 else 0:.1f}%)")
    print(f"   Com tipo_posicao: {com_tipo} ({100*com_tipo/total if total > 0 else 0:.1f}%)")

    print()
    print("=" * 80)
    print("[OK] MIGRATION 049 APLICADA COM SUCESSO!")
    print("=" * 80)
    print()
    print("Campos adicionados:")
    print("  - modalidade_contratacao_req (posicao 27)")
    print("  - empresa/Time Rethink (posicao 30)")
    print("  - tipo_posicao (posicao 31)")
    print()

    cur.close()
    conn.close()

except FileNotFoundError:
    print(f"[ERRO] Arquivo de migration nao encontrado: {migration_file}")
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
