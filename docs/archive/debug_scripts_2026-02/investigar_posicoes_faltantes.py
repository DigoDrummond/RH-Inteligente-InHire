import psycopg2

conn = psycopg2.connect(
    dbname="inhire",
    user="postgres",
    password="postgres",
    host="localhost"
)

cur = conn.cursor()

print("=" * 80)
print("INVESTIGACAO: POSICOES FALTANTES (VAGAS vs POSICOES)")
print("=" * 80)
print()

# 1. Contagem básica
print("1. CONTAGEM BASICA")
print("-" * 80)

cur.execute("SELECT COUNT(*) FROM vagas")
total_vagas = cur.fetchone()[0]
print(f"Total de vagas: {total_vagas}")

cur.execute("SELECT COUNT(*) FROM posicoes")
total_posicoes = cur.fetchone()[0]
print(f"Total de posicoes: {total_posicoes}")

print(f"Diferenca: {total_posicoes - total_vagas} posicoes")
print(f"Razao: {total_posicoes / total_vagas:.2f} posicoes por vaga")

# 2. Vagas SEM posição
print("\n2. VAGAS SEM POSICAO")
print("-" * 80)

cur.execute("""
    SELECT COUNT(*)
    FROM vagas v
    WHERE NOT EXISTS (
        SELECT 1 FROM posicoes p WHERE p.vaga_id = v.id
    )
""")
vagas_sem_posicao = cur.fetchone()[0]
print(f"Vagas sem nenhuma posicao: {vagas_sem_posicao}")
print(f"Percentual: {100 * vagas_sem_posicao / total_vagas:.1f}%")

# Mostrar exemplos
cur.execute("""
    SELECT v.id, v.name, v.created_at, v.status
    FROM vagas v
    WHERE NOT EXISTS (
        SELECT 1 FROM posicoes p WHERE p.vaga_id = v.id
    )
    ORDER BY v.id DESC
    LIMIT 10
""")

print("\nExemplos de vagas sem posicao:")
print(f"{'ID':<8} {'Nome':<50} {'Status':<12} {'Criada em'}")
print("-" * 90)
for vaga_id, nome, criada, status in cur.fetchall():
    nome_trunc = (nome[:47] + '...') if len(nome) > 50 else nome
    print(f"{vaga_id:<8} {nome_trunc:<50} {status:<12} {str(criada)[:10]}")

# 3. Distribuição de posições por vaga
print("\n3. DISTRIBUICAO DE POSICOES POR VAGA")
print("-" * 80)

cur.execute("""
    SELECT
        num_posicoes,
        COUNT(*) as quantidade_vagas,
        COUNT(*) * num_posicoes as total_posicoes
    FROM (
        SELECT v.id, COUNT(p.id) as num_posicoes
        FROM vagas v
        LEFT JOIN posicoes p ON p.vaga_id = v.id
        GROUP BY v.id
    ) sub
    GROUP BY num_posicoes
    ORDER BY num_posicoes
""")

print(f"{'Num Posicoes':<15} {'Qtd Vagas':>12} {'Total Posicoes':>20}")
print("-" * 50)
for num_pos, qtd_vagas, total_pos in cur.fetchall():
    print(f"{num_pos:<15} {qtd_vagas:>12} {total_pos:>20}")

# 4. Vagas com múltiplas posições
print("\n4. VAGAS COM MULTIPLAS POSICOES")
print("-" * 80)

cur.execute("""
    SELECT
        v.id,
        v.name,
        COUNT(p.id) as num_posicoes,
        STRING_AGG(p.status, ', ' ORDER BY p.id) as status_posicoes
    FROM vagas v
    INNER JOIN posicoes p ON p.vaga_id = v.id
    GROUP BY v.id, v.name
    HAVING COUNT(p.id) > 1
    ORDER BY COUNT(p.id) DESC
    LIMIT 15
""")

print(f"{'Vaga ID':<10} {'Num Pos':>8} {'Nome':<40} {'Status das Posicoes'}")
print("-" * 100)
for vaga_id, nome, num_pos, status in cur.fetchall():
    nome_trunc = (nome[:37] + '...') if len(nome) > 40 else nome
    status_trunc = (status[:40] + '...') if len(status) > 40 else status
    print(f"{vaga_id:<10} {num_pos:>8} {nome_trunc:<40} {status_trunc}")

# 5. Análise temporal
print("\n5. ANALISE TEMPORAL - VAGAS vs POSICOES POR ANO")
print("-" * 80)

cur.execute("""
    SELECT
        EXTRACT(YEAR FROM v.created_at) as ano_vaga,
        COUNT(DISTINCT v.id) as total_vagas,
        COUNT(p.id) as total_posicoes,
        COUNT(p.id)::float / NULLIF(COUNT(DISTINCT v.id), 0) as razao
    FROM vagas v
    LEFT JOIN posicoes p ON p.vaga_id = v.id
    WHERE v.created_at IS NOT NULL
    GROUP BY EXTRACT(YEAR FROM v.created_at)
    ORDER BY ano_vaga DESC
""")

print(f"{'Ano':<8} {'Vagas':>10} {'Posicoes':>12} {'Razao':>10}")
print("-" * 45)
for ano, vagas, posicoes, razao in cur.fetchall():
    if ano:
        print(f"{int(ano):<8} {vagas:>10} {posicoes:>12} {razao:>10.2f}")

# 6. Status das posições
print("\n6. DISTRIBUICAO DE STATUS DAS POSICOES")
print("-" * 80)

cur.execute("""
    SELECT
        status,
        COUNT(*) as total,
        COUNT(CASE WHEN hired_at IS NOT NULL THEN 1 END) as com_hired
    FROM posicoes
    GROUP BY status
    ORDER BY total DESC
""")

print(f"{'Status':<15} {'Total':>10} {'Com hired_at':>15}")
print("-" * 42)
for status, total, com_hired in cur.fetchall():
    print(f"{status:<15} {total:>10} {com_hired:>15}")

# 7. Posições por status "closed"
print("\n7. POSICOES COM STATUS 'CLOSED'")
print("-" * 80)

cur.execute("""
    SELECT COUNT(*)
    FROM posicoes
    WHERE status = 'closed'
""")
total_closed = cur.fetchone()[0]
print(f"Total de posicoes com status 'closed': {total_closed}")

cur.execute("""
    SELECT COUNT(DISTINCT vaga_id)
    FROM posicoes
    WHERE status = 'closed'
""")
vagas_com_closed = cur.fetchone()[0]
print(f"Vagas com pelo menos 1 posicao 'closed': {vagas_com_closed}")

# 8. Verificar se há padrão nas vagas sem posição
print("\n8. CARACTERISTICAS DAS VAGAS SEM POSICAO")
print("-" * 80)

cur.execute("""
    SELECT
        COALESCE(v.status, 'NULL') as status,
        COUNT(*) as total
    FROM vagas v
    WHERE NOT EXISTS (
        SELECT 1 FROM posicoes p WHERE p.vaga_id = v.id
    )
    GROUP BY v.status
    ORDER BY total DESC
""")

print("Status das vagas sem posicao:")
for status, total in cur.fetchall():
    print(f"  {status}: {total}")

# 9. Total esperado vs real
print("\n" + "=" * 80)
print("RESUMO")
print("=" * 80)
print(f"Total de vagas: {total_vagas}")
print(f"Total de posicoes: {total_posicoes}")
print(f"Vagas sem posicao: {vagas_sem_posicao} ({100 * vagas_sem_posicao / total_vagas:.1f}%)")
print(f"Posicoes 'closed': {total_closed}")
print()
print(f"PROBLEMA IDENTIFICADO:")
print(f"  - Temos {vagas_sem_posicao} vagas sem nenhuma posicao")
print(f"  - Isso representa {100 * vagas_sem_posicao / total_vagas:.1f}% das vagas")
print(f"  - Se cada vaga tivesse ao menos 1 posicao: {total_vagas} posicoes")
print(f"  - Temos apenas: {total_posicoes} posicoes")
print(f"  - Faltam aproximadamente: {vagas_sem_posicao} posicoes (minimo)")
print()
print(f"COMPARACAO COM PLANILHA EXTERNA:")
print(f"  - Planilha menciona: 1003 posicoes")
print(f"  - Banco tem: {total_posicoes} posicoes")
print(f"  - Diferenca: {1003 - total_posicoes} posicoes")
print("=" * 80)

cur.close()
conn.close()
