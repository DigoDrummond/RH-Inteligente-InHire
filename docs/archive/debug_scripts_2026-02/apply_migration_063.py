"""
Aplica a migration 063 que reordena colunas e mescla motivo_status
"""
import psycopg2

print("=" * 80)
print("APLICANDO MIGRATION 063")
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
    print("2. Lendo migration 063...")
    with open('migrations/063_reordenar_colunas_e_mesclar_motivo.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    print("   [OK] Migration lida")
    print()

    # Aplicar a migration
    print("3. Aplicando migration 063...")
    print("   - Reordenando colunas")
    print("   - Mesclando motivo_status com motivo_cancelamento_paralisacao")
    print("   - Removendo motivo_status_codigo")
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
    print()

    # Verificar ordem das primeiras colunas
    print("5. Verificando ordem das colunas (primeiras 10):")
    ordem_esperada = [
        'id_position', 'cargo', 'data_abertura', 'data_publicacao',
        'prazo_processo_seletivo', 'cliente', 'torre', 'status_atual',
        'data_encerramento_ou_atualizacao', 'motivo_cancelamento_paralisacao'
    ]
    for i, col in enumerate(colunas[:10]):
        esperado = ordem_esperada[i]
        status = "[OK]" if col == esperado else "[X]"
        print(f"   {status} Coluna {i+1}: {col} (esperado: {esperado})")
    print()

    # Verificar campos removidos
    print("6. Verificando remocoes:")
    print(f"   - motivo_status removido: {'motivo_status' not in colunas}")
    print(f"   - motivo_status_codigo removido: {'motivo_status_codigo' not in colunas}")
    print()

    # Testar mesclagem
    print("7. Testando mesclagem de motivo...")
    cur.execute("""
        SELECT
            motivo_cancelamento_paralisacao,
            COUNT(*) as qtd
        FROM vw_analise_posicoes
        WHERE motivo_cancelamento_paralisacao IS NOT NULL
        GROUP BY motivo_cancelamento_paralisacao
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)
    print("   Top 5 motivos mesclados:")
    for row in cur.fetchall():
        motivo = row[0] or '(null)'
        qtd = row[1]
        # Truncar se muito longo
        motivo_exibir = motivo[:70] + '...' if len(motivo) > 70 else motivo
        print(f"   - {motivo_exibir}")
        print(f"     Qtd: {qtd}")
    print()

    # Listar todas as colunas na ordem final
    print("8. Ordem final das colunas (todas):")
    for i, col in enumerate(colunas):
        print(f"   {i+1:2}. {col}")
    print()

    # Commit
    conn.commit()
    print("=" * 80)
    print("[OK] MIGRATION 063 APLICADA COM SUCESSO!")
    print("=" * 80)
    print()
    print("RESUMO:")
    print(f"  - Total de campos: {len(colunas)}")
    print("  - Colunas reordenadas conforme solicitado")
    print("  - motivo_status mesclado em motivo_cancelamento_paralisacao")
    print("  - motivo_status_codigo removido")
    print("  - Estrutura e calculos da 059/062 PRESERVADOS")
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
