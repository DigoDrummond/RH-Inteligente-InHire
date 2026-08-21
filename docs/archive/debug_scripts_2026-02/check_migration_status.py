"""
Script para verificar o status da migration 061
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
print("VERIFICAÇÃO DO STATUS DA MIGRATION 061")
print("=" * 80)
print()

# 1. Verificar se tabela de tradução existe
cur.execute("""
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'motivo_status_traducao'
    )
""")
tabela_existe = cur.fetchone()[0]
print(f"1. Tabela motivo_status_traducao existe: {tabela_existe}")

if tabela_existe:
    cur.execute("SELECT COUNT(*) FROM motivo_status_traducao WHERE ativo = TRUE")
    count = cur.fetchone()[0]
    print(f"   - Total de traduções ativas: {count}")
print()

# 2. Verificar colunas da view
cur.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'vw_analise_posicoes'
    ORDER BY ordinal_position
""")
colunas = [row[0] for row in cur.fetchall()]
print(f"2. Total de colunas na view: {len(colunas)}")
print()

# 3. Verificar presença dos campos da migration 061
campos_061 = ['motivo_status', 'motivo_status_codigo']
print("3. Campos da migration 061:")
for campo in campos_061:
    presente = campo in colunas
    status = "[OK]" if presente else "[X]"
    print(f"   {status} {campo}: {presente}")
print()

# 4. Verificar se motivo_status tem tradução
cur.execute("""
    SELECT
        COUNT(*) as total,
        COUNT(motivo_status) FILTER (WHERE motivo_status IS NOT NULL) as com_motivo,
        COUNT(motivo_status_codigo) FILTER (WHERE motivo_status_codigo IS NOT NULL) as com_codigo
    FROM vw_analise_posicoes
    LIMIT 1
""")
stats = cur.fetchone()
print("4. Estatísticas de motivo_status:")
print(f"   - Total de registros na view: {stats[0]}")
print(f"   - Registros com motivo_status preenchido: {stats[1]}")
print(f"   - Registros com motivo_status_codigo preenchido: {stats[2]}")
print()

# 5. Verificar se JOIN com tradução está funcionando
cur.execute("""
    SELECT
        motivo_status_codigo,
        motivo_status,
        COUNT(*) as qtd
    FROM vw_analise_posicoes
    WHERE motivo_status_codigo IS NOT NULL
    GROUP BY motivo_status_codigo, motivo_status
    ORDER BY COUNT(*) DESC
    LIMIT 5
""")
print("5. Top 5 motivos (para verificar se tradução está funcionando):")
for row in cur.fetchall():
    codigo = row[0] or '(null)'
    traducao = row[1] or '(null)'
    qtd = row[2]
    print(f"   - Código: {codigo}")
    print(f"     Tradução: {traducao}")
    print(f"     Quantidade: {qtd}")
    print()

# 6. Verificar campos ausentes (comparação com migration 061 completa)
campos_esperados_061 = [
    'id_position', 'cargo', 'cliente', 'torre',
    'data_abertura', 'data_publicacao', 'data_encerramento_ou_atualizacao',
    'status_atual', 'motivo_cancelamento_paralisacao', 'etapa_funil',
    'motivo_status', 'motivo_status_codigo',  # Campos da 061
    'senioridade', 'modalidade_contratacao', 'pessoa_substituida',
    'responsavel', 'recrutador_vaga',
    'inicio_pendencia_cliente', 'fim_pendencia_cliente',
    'sla_pendencia_cliente', 'num_ciclos_pausa', 'detalhamento_pausas',
    'sla_recrutamento', 'prazo_processo_seletivo', 'sla_geral', 'indicador_prazo',
    'motivo_contratacao', 'nome_pessoa_contratada', 'email_pessoal',
    'source_candidato', 'is_referral'
]

print(f"6. Comparação de campos (esperados vs presentes):")
print(f"   - Campos esperados na migration 061: {len(campos_esperados_061)}")
print(f"   - Campos presentes na view: {len(colunas)}")
ausentes = set(campos_esperados_061) - set(colunas)
if ausentes:
    print(f"   - Campos ausentes: {ausentes}")
extras = set(colunas) - set(campos_esperados_061)
if extras:
    print(f"   - Campos extras: {extras}")
print()

print("=" * 80)
print("CONCLUSAO:")
print("=" * 80)
if tabela_existe and all(c in colunas for c in campos_061):
    print("[OK] Migration 061 esta APLICADA (versao simplificada com 31 colunas)")
    print("  - Tabela de traducao existe")
    print("  - Campos motivo_status e motivo_status_codigo presentes")
else:
    print("[X] Migration 061 NAO esta completamente aplicada")
print()

cur.close()
conn.close()
