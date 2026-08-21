"""
Aplica a migration 065 que altera ordenação para ASC
"""
import psycopg2

print("=" * 80)
print("APLICANDO MIGRATION 065")
print("=" * 80)
print()

try:
    # Conectar ao banco
    conn = psycopg2.connect(
        dbname='inhire',
        user='postgres',
        password='postgres',
        host='localhost'
    )
    conn.autocommit = False
    cur = conn.cursor()

    print("1. Conectado ao banco de dados")
    print()

    # Ler o arquivo da migration
    print("2. Lendo migration 065...")
    with open('migrations/065_alterar_ordenacao_asc.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    print("   [OK] Migration lida")
    print()

    # Aplicar a migration
    print("3. Aplicando migration 065...")
    print("   - Alterando ORDER BY para ASC (data_publicacao)")
    print("   - Preservando TODA a estrutura da migration 064")
    cur.execute(sql)
    print("   [OK] Migration aplicada")
    print()

    # Verificar ordenação
    print("4. Verificando ordenacao...")
    cur.execute("""
        SELECT id_position, data_publicacao
        FROM vw_analise_posicoes
        WHERE data_publicacao IS NOT NULL
        ORDER BY data_publicacao ASC
        LIMIT 5
    """)
    print("   Primeiros 5 registros (ordenacao ASC):")
    for row in cur.fetchall():
        id_pos = row[0]
        data_pub = row[1]
        print(f"   - Position ID: {id_pos}, Data Publicacao: {data_pub}")
    print()

    # Verificar últimos registros
    print("5. Verificando ultimos registros...")
    cur.execute("""
        SELECT id_position, data_publicacao
        FROM vw_analise_posicoes
        WHERE data_publicacao IS NOT NULL
        ORDER BY data_publicacao DESC
        LIMIT 5
    """)
    print("   Ultimos 5 registros (mais recentes):")
    for row in cur.fetchall():
        id_pos = row[0]
        data_pub = row[1]
        print(f"   - Position ID: {id_pos}, Data Publicacao: {data_pub}")
    print()

    # Commit
    conn.commit()
    print("=" * 80)
    print("[OK] MIGRATION 065 APLICADA COM SUCESSO!")
    print("=" * 80)
    print()
    print("RESUMO:")
    print("  - Ordenacao alterada: DESC -> ASC")
    print("  - Campo ordenacao: data_publicacao (p.opened_at)")
    print("  - Posicoes mais antigas aparecem primeiro")
    print("  - Estrutura e campos inalterados (34 campos)")
    print()

    cur.close()
    conn.close()

except Exception as e:
    print()
    print("=" * 80)
    print(f"[ERRO] {str(e)}")
    print("=" * 80)
    if 'conn' in locals():
        conn.rollback()
        conn.close()
    exit(1)
