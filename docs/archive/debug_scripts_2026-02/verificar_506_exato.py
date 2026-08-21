import psycopg2

conn = psycopg2.connect(
    dbname="inhire",
    user="postgres",
    password="postgres",
    host="localhost"
)

cur = conn.cursor()

print("=" * 80)
print("BUSCANDO EXATOS 506 REGISTROS")
print("=" * 80)
print()

# Testar várias combinações
combinacoes = []

# 1. Closed + Canceled apenas 2024 e 2025
cur.execute("""
    SELECT COUNT(*)
    FROM posicoes p
    WHERE p.status IN ('closed', 'canceled')
    AND EXTRACT(YEAR FROM p.opened_at) IN (2024, 2025)
    AND p.vaga_id NOT IN (114, 99, 479, 88, 680)
""")
count1 = cur.fetchone()[0]
combinacoes.append(("Closed+Canceled apenas 2024-2025", count1))

# 2. Status != open (2024-2025)
cur.execute("""
    SELECT COUNT(*)
    FROM posicoes p
    WHERE p.status != 'open'
    AND EXTRACT(YEAR FROM p.opened_at) IN (2024, 2025)
    AND p.vaga_id NOT IN (114, 99, 479, 88, 680)
""")
count2 = cur.fetchone()[0]
combinacoes.append(("Status != open (2024-2025)", count2))

# 3. Closed + Canceled (2024-2026) SEM os filtros de vaga
cur.execute("""
    SELECT COUNT(*)
    FROM posicoes p
    WHERE p.status IN ('closed', 'canceled')
    AND EXTRACT(YEAR FROM p.opened_at) BETWEEN 2024 AND 2026
""")
count3 = cur.fetchone()[0]
combinacoes.append(("Closed+Canceled 2024-2026 SEM FILTROS", count3))

# 4. Closed + Canceled 2024-2025 SEM filtros
cur.execute("""
    SELECT COUNT(*)
    FROM posicoes p
    WHERE p.status IN ('closed', 'canceled')
    AND EXTRACT(YEAR FROM p.opened_at) IN (2024, 2025)
""")
count4 = cur.fetchone()[0]
combinacoes.append(("Closed+Canceled 2024-2025 SEM FILTROS", count4))

# 5. Canceled apenas (2024-2026)
cur.execute("""
    SELECT COUNT(*)
    FROM posicoes p
    WHERE p.status = 'canceled'
    AND EXTRACT(YEAR FROM p.opened_at) BETWEEN 2024 AND 2026
    AND p.vaga_id NOT IN (114, 99, 479, 88, 680)
""")
count5 = cur.fetchone()[0]
combinacoes.append(("Apenas Canceled (2024-2026)", count5))

# 6. Todas exceto open e paused (2024-2025)
cur.execute("""
    SELECT COUNT(*)
    FROM posicoes p
    WHERE p.status NOT IN ('open', 'paused')
    AND EXTRACT(YEAR FROM p.opened_at) IN (2024, 2025)
    AND p.vaga_id NOT IN (114, 99, 479, 88, 680)
""")
count6 = cur.fetchone()[0]
combinacoes.append(("Status NOT IN (open,paused) 2024-2025", count6))

# 7. Verificar contagem na tabela VAGAS
cur.execute("""
    SELECT COUNT(*)
    FROM vagas v
    WHERE v.created_at >= '2024-01-01'
    AND v.created_at < '2026-01-01'
    AND v.id NOT IN (114, 99, 479, 88, 680)
    AND (v.custom_fields->>'Tipo' IS NULL OR v.custom_fields->>'Tipo' != 'Banco de Talentos')
""")
count7 = cur.fetchone()[0]
combinacoes.append(("Vagas criadas 2024-2025", count7))

# 8. Closed + Canceled com data_encerramento em 2024-2025
cur.execute("""
    WITH ultimo_status AS (
        SELECT DISTINCT ON (pt.posicao_id)
            pt.posicao_id,
            pt.new_status,
            pt.changed_at
        FROM position_timeline pt
        ORDER BY pt.posicao_id, pt.changed_at DESC
    )
    SELECT COUNT(*)
    FROM ultimo_status us
    INNER JOIN posicoes p ON p.id = us.posicao_id
    WHERE us.new_status IN ('closed', 'canceled')
    AND EXTRACT(YEAR FROM us.changed_at) IN (2024, 2025)
    AND p.vaga_id NOT IN (114, 99, 479, 88, 680)
""")
count8 = cur.fetchone()[0]
combinacoes.append(("Data encerramento (timeline) 2024-2025", count8))

# 9. Posições com data_publicacao em 2024-2025 e status closed/canceled
cur.execute("""
    SELECT COUNT(*)
    FROM posicoes p
    WHERE p.status IN ('closed', 'canceled')
    AND DATE(p.opened_at) >= '2024-01-01'
    AND DATE(p.opened_at) < '2026-01-01'
    AND p.vaga_id NOT IN (114, 99, 479, 88, 680)
""")
count9 = cur.fetchone()[0]
combinacoes.append(("Data publicacao 2024-2025 e closed/canceled", count9))

print("Testando combinacoes:")
print("-" * 80)
print(f"{'Descricao':<55} {'Total':>10} {'Diff 506':>10}")
print("-" * 80)

for desc, count in sorted(combinacoes, key=lambda x: abs(x[1] - 506)):
    diff = count - 506
    marker = " <-- PROXIMO!" if abs(diff) <= 20 else ""
    print(f"{desc:<55} {count:>10} {diff:>+10}{marker}")

# Análise detalhada da combinação mais próxima
print("\n" + "=" * 80)
print("ANALISE DETALHADA DA COMBINACAO MAIS PROXIMA")
print("=" * 80)

closest = min(combinacoes, key=lambda x: abs(x[1] - 506))
print(f"\nCombinacao: {closest[0]}")
print(f"Total: {closest[1]}")
print(f"Diferenca de 506: {closest[1] - 506:+d}")

# Se for closed+canceled 2024-2025, mostrar breakdown
if "2024-2025" in closest[0] and "Closed+Canceled" in closest[0]:
    print("\nBreakdown por ano:")
    cur.execute("""
        SELECT
            EXTRACT(YEAR FROM p.opened_at) as ano,
            COUNT(CASE WHEN p.status = 'closed' THEN 1 END) as closed,
            COUNT(CASE WHEN p.status = 'canceled' THEN 1 END) as canceled,
            COUNT(*) as total
        FROM posicoes p
        WHERE p.status IN ('closed', 'canceled')
        AND EXTRACT(YEAR FROM p.opened_at) IN (2024, 2025)
        AND p.vaga_id NOT IN (114, 99, 479, 88, 680)
        GROUP BY EXTRACT(YEAR FROM p.opened_at)
        ORDER BY ano
    """)

    print(f"{'Ano':<8} {'Closed':>10} {'Canceled':>10} {'Total':>10}")
    print("-" * 40)
    for ano, closed, canceled, total in cur.fetchall():
        print(f"{int(ano):<8} {closed:>10} {canceled:>10} {total:>10}")

print("\n" + "=" * 80)

cur.close()
conn.close()
