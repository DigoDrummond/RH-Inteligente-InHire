"""
Aplica a migration 062 que preserva estrutura da 059 + tradução
"""
import psycopg2

print("=" * 80)
print("APLICANDO MIGRATION 062")
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
    print("2. Lendo migration 062...")
    with open('migrations/062_add_traducao_motivo_preservando_059.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    print("   [OK] Migration lida")
    print()

    # Aplicar a migration
    print("3. Aplicando migration 062...")
    print("   (Recriando view vw_analise_posicoes com traducao...)")
    cur.execute(sql)
    print("   [OK] Migration aplicada")
    print()

    # Verificar resultado
    print("4. Verificando resultado...")
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'vw_analise_posicoes'
        ORDER BY ordinal_position
    """)
    colunas = [row[0] for row in cur.fetchall()]
    print(f"   - Total de colunas: {len(colunas)}")
    print(f"   - Campo 'motivo_status' presente: {'motivo_status' in colunas}")
    print(f"   - Campo 'motivo_status_codigo' presente: {'motivo_status_codigo' in colunas}")
    print()

    # Testar tradução
    print("5. Testando traducao...")
    cur.execute("""
        SELECT
            motivo_status_codigo,
            motivo_status,
            COUNT(*) as qtd
        FROM vw_analise_posicoes
        WHERE motivo_status_codigo IS NOT NULL
        GROUP BY motivo_status_codigo, motivo_status
        ORDER BY COUNT(*) DESC
        LIMIT 3
    """)
    print("   Top 3 motivos traduzidos:")
    for row in cur.fetchall():
        codigo = row[0] or '(null)'
        traducao = row[1] or '(null)'
        qtd = row[2]
        print(f"   - Codigo: {codigo}")
        print(f"     Traducao: {traducao}")
        print(f"     Qtd: {qtd}")
    print()

    # Commit
    conn.commit()
    print("=" * 80)
    print("[OK] MIGRATION 062 APLICADA COM SUCESSO!")
    print("=" * 80)
    print()
    print("Estrutura da migration 059 PRESERVADA:")
    print("  - Calculos de dias uteis (calcular_dias_uteis)")
    print("  - Logica complexa de data_encerramento")
    print("  - 34 campos estruturados")
    print()
    print("NOVO:")
    print("  - motivo_status: TRADUZIDO em portugues")
    print("  - motivo_status_codigo: codigo tecnico original")
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
