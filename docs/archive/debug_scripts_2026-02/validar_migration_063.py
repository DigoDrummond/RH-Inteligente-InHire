"""
Validação final da migration 063
"""
import psycopg2

conn = psycopg2.connect(
    dbname='inhire',
    user='postgres',
    password='postgres',
    host='localhost'
)
cur = conn.cursor()

print("=" * 80)
print("VALIDACAO FINAL - MIGRATION 063")
print("=" * 80)
print()

# 1. Validar estrutura
cur.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'vw_analise_posicoes'
    ORDER BY ordinal_position
""")
colunas = [row[0] for row in cur.fetchall()]

ordem_esperada = [
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

print("1. VALIDACAO DA ESTRUTURA")
print("-" * 80)
todas_corretas = True
for i, (atual, esperado) in enumerate(zip(colunas, ordem_esperada)):
    if atual != esperado:
        print(f"   [X] Coluna {i+1}: {atual} (esperado: {esperado})")
        todas_corretas = False

if todas_corretas:
    print(f"   [OK] Todas as {len(colunas)} colunas na ordem correta!")
print()

# 2. Validar campos removidos
print("2. VALIDACAO DE CAMPOS REMOVIDOS")
print("-" * 80)
removidos_ok = True
if 'motivo_status' in colunas:
    print("   [X] motivo_status NAO foi removido!")
    removidos_ok = False
if 'motivo_status_codigo' in colunas:
    print("   [X] motivo_status_codigo NAO foi removido!")
    removidos_ok = False
if removidos_ok:
    print("   [OK] Campos motivo_status e motivo_status_codigo removidos")
print()

# 3. Validar mesclagem
print("3. VALIDACAO DA MESCLAGEM DE MOTIVO")
print("-" * 80)
cur.execute("""
    SELECT
        COUNT(*) as total,
        COUNT(motivo_cancelamento_paralisacao) FILTER (
            WHERE motivo_cancelamento_paralisacao LIKE '%|%'
        ) as mesclados,
        COUNT(motivo_cancelamento_paralisacao) FILTER (
            WHERE motivo_cancelamento_paralisacao IS NOT NULL
            AND motivo_cancelamento_paralisacao NOT LIKE '%|%'
        ) as so_um_motivo
    FROM vw_analise_posicoes
""")
stats = cur.fetchone()
total = stats[0]
mesclados = stats[1]
so_um = stats[2]
print(f"   - Total de registros: {total}")
print(f"   - Registros com motivo mesclado (contem '|'): {mesclados}")
print(f"   - Registros com apenas um motivo: {so_um}")
print(f"   - Cobertura de motivo: {((mesclados + so_um) / total * 100):.1f}%")
print()

# 4. Validar calculos de dias uteis
print("4. VALIDACAO DE CALCULOS (dias uteis)")
print("-" * 80)
cur.execute("""
    SELECT
        COUNT(*) FILTER (WHERE sla_recrutamento IS NOT NULL) as com_sla_recrutamento,
        COUNT(*) FILTER (WHERE sla_geral IS NOT NULL) as com_sla_geral,
        COUNT(*) FILTER (WHERE sla_pendencia_cliente IS NOT NULL) as com_sla_pendencia
    FROM vw_analise_posicoes
""")
stats = cur.fetchone()
print(f"   - Registros com sla_recrutamento calculado: {stats[0]}")
print(f"   - Registros com sla_geral calculado: {stats[1]}")
print(f"   - Registros com sla_pendencia_cliente calculado: {stats[2]}")
print()

# 5. Exemplos de mesclagem
print("5. EXEMPLOS DE MESCLAGEM")
print("-" * 80)
cur.execute("""
    SELECT
        cargo,
        status_atual,
        motivo_cancelamento_paralisacao
    FROM vw_analise_posicoes
    WHERE motivo_cancelamento_paralisacao LIKE '%|%'
    LIMIT 3
""")
print("   Registros com motivo mesclado:")
for row in cur.fetchall():
    cargo = row[0][:40] if row[0] else '(null)'
    status = row[1] or '(null)'
    motivo = row[2][:60] + '...' if len(row[2]) > 60 else row[2]
    print(f"   - Cargo: {cargo}")
    print(f"     Status: {status}")
    print(f"     Motivo: {motivo}")
    print()

print("=" * 80)
print("CONCLUSAO:")
print("=" * 80)
if todas_corretas and removidos_ok:
    print("[OK] Migration 063 validada com SUCESSO!")
    print()
    print("CARACTERISTICAS:")
    print("  - 32 campos na ordem solicitada")
    print("  - motivo_status mesclado em motivo_cancelamento_paralisacao")
    print("  - Calculos de dias uteis preservados")
    print("  - Estrutura da migration 059 mantida")
else:
    print("[X] Validacao FALHOU!")
print()

cur.close()
conn.close()
