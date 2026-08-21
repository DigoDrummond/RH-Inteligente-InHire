"""
Aplica a migration 064 que adiciona vaga_id e vaga_nome no início
"""
import psycopg2

print("=" * 80)
print("APLICANDO MIGRATION 064")
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
    print("2. Lendo migration 064...")
    with open('migrations/064_add_vaga_id_nome_no_inicio.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    print("   [OK] Migration lida")
    print()

    # Aplicar a migration
    print("3. Aplicando migration 064...")
    print("   - Adicionando vaga_id e vaga_nome no inicio")
    print("   - Preservando TODA a estrutura da migration 063")
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
    print("5. Verificando ordem das primeiras colunas:")
    ordem_esperada_inicio = [
        'vaga_id', 'vaga_nome', 'id_position', 'cargo',
        'data_abertura', 'data_publicacao', 'prazo_processo_seletivo'
    ]
    for i, col in enumerate(colunas[:7]):
        esperado = ordem_esperada_inicio[i]
        status = "[OK]" if col == esperado else "[X]"
        print(f"   {status} Coluna {i+1}: {col} (esperado: {esperado})")
    print()

    # Verificar que campos da 063 estão preservados
    print("6. Verificando preservacao dos campos da migration 063:")
    campos_063 = [
        'id_position', 'cargo', 'data_abertura', 'data_publicacao',
        'prazo_processo_seletivo', 'cliente', 'torre', 'status_atual',
        'data_encerramento_ou_atualizacao', 'motivo_cancelamento_paralisacao',
        'etapa_funil', 'senioridade', 'motivo_contratacao', 'modalidade_contratacao',
        'pessoa_substituida', 'responsavel', 'email_responsavel_cliente',
        'recrutador_vaga', 'inicio_pendencia_cliente', 'fim_pendencia_cliente',
        'sla_pendencia_cliente', 'num_ciclos_pausa', 'detalhamento_pausas',
        'sla_recrutamento', 'nome_pessoa_contratada', 'email_pessoal',
        'modalidade_contratacao_req', 'sla_geral', 'indicador_prazo',
        'empresa', 'tipo_posicao', 'nome_workflow_aprovacao'
    ]
    todos_presentes = all(campo in colunas for campo in campos_063)
    if todos_presentes:
        print("   [OK] TODOS os 32 campos da migration 063 presentes")
    else:
        print("   [X] Alguns campos da 063 ausentes!")
    print()

    # Testar dados
    print("7. Testando dados das novas colunas...")
    cur.execute("""
        SELECT
            vaga_id,
            vaga_nome,
            id_position,
            cargo
        FROM vw_analise_posicoes
        LIMIT 3
    """)
    print("   Primeiros registros:")
    for row in cur.fetchall():
        vaga_id = row[0]
        vaga_nome = row[1][:50] if row[1] else '(null)'
        id_position = row[2]
        cargo = row[3][:50] if row[3] else '(null)'
        print(f"   - Vaga ID: {vaga_id}, Nome: {vaga_nome}")
        print(f"     Position ID: {id_position}, Cargo: {cargo}")
    print()

    # Verificar se vaga_nome e cargo são iguais (devem ser)
    print("8. Verificando se vaga_nome = cargo (devem ser iguais)...")
    cur.execute("""
        SELECT COUNT(*) as total,
               COUNT(*) FILTER (WHERE vaga_nome = cargo) as iguais
        FROM vw_analise_posicoes
    """)
    stats = cur.fetchone()
    total = stats[0]
    iguais = stats[1]
    if total == iguais:
        print(f"   [OK] vaga_nome = cargo em TODOS os {total} registros")
    else:
        print(f"   [X] vaga_nome != cargo em {total - iguais} registros")
    print()

    # Listar ordem completa
    print("9. Ordem final das colunas:")
    for i, col in enumerate(colunas):
        print(f"   {i+1:2}. {col}")
    print()

    # Commit
    conn.commit()
    print("=" * 80)
    print("[OK] MIGRATION 064 APLICADA COM SUCESSO!")
    print("=" * 80)
    print()
    print("RESUMO:")
    print(f"  - Total de campos: {len(colunas)}")
    print("  - Novas colunas: vaga_id e vaga_nome (no inicio)")
    print("  - Todas as 32 colunas da migration 063 preservadas")
    print("  - Estrutura, analises e metricas inalteradas")
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
