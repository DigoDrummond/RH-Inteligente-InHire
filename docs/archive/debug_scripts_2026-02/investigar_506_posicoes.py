import psycopg2

conn = psycopg2.connect(
    dbname="inhire",
    user="postgres",
    password="postgres",
    host="localhost"
)

cur = conn.cursor()

print("=" * 80)
print("INVESTIGACAO: 120 vs 506 POSICOES FECHADAS")
print("=" * 80)
print()

# Hipótese: A planilha pode estar contando posições de TODOS os anos, não só 2024-2026
print("1. POSICOES POR ANO (todos os anos)")
print("-" * 80)

cur.execute("""
    SELECT
        EXTRACT(YEAR FROM p.opened_at) as ano,
        COUNT(*) as total,
        COUNT(CASE WHEN p.status = 'closed' THEN 1 END) as status_closed,
        COUNT(CASE WHEN p.hired_at IS NOT NULL THEN 1 END) as com_hired_at
    FROM posicoes p
    WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
    GROUP BY EXTRACT(YEAR FROM p.opened_at)
    ORDER BY ano DESC
""")

print(f"{'Ano':<8} {'Total':>8} {'Status=closed':>15} {'Com hired_at':>15}")
print("-" * 50)
total_all_years = 0
total_closed_all = 0
total_hired_all = 0
for ano, total, closed, hired in cur.fetchall():
    if ano:
        print(f"{int(ano):<8} {total:>8} {closed:>15} {hired:>15}")
        total_all_years += total
        total_closed_all += closed
        total_hired_all += hired
    else:
        print(f"{'NULL':<8} {total:>8} {closed:>15} {hired:>15}")

print("-" * 50)
print(f"{'TOTAL':<8} {total_all_years:>8} {total_closed_all:>15} {total_hired_all:>15}")

# Verificar se 506 pode ser a soma de várias categorias
print("\n2. POSSIVEIS COMBINACOES QUE DÃO 506 (ou perto)")
print("-" * 80)

# Todas as posições não abertas
cur.execute("""
    SELECT COUNT(*)
    FROM posicoes p
    WHERE p.status != 'open'
    AND p.vaga_id NOT IN (114, 99, 479, 88, 680)
""")
total_nao_abertas = cur.fetchone()[0]
print(f"Posicoes com status != 'open': {total_nao_abertas}")

# Closed + Canceled (2024-2026)
cur.execute("""
    SELECT COUNT(*)
    FROM posicoes p
    WHERE p.status IN ('closed', 'canceled')
    AND EXTRACT(YEAR FROM p.opened_at) BETWEEN 2024 AND 2026
    AND p.vaga_id NOT IN (114, 99, 479, 88, 680)
""")
closed_canceled_2024_2026 = cur.fetchone()[0]
print(f"Status closed OU canceled (2024-2026): {closed_canceled_2024_2026}")

# Closed + Canceled (todos os anos)
cur.execute("""
    SELECT COUNT(*)
    FROM posicoes p
    WHERE p.status IN ('closed', 'canceled')
    AND p.vaga_id NOT IN (114, 99, 479, 88, 680)
""")
closed_canceled_all = cur.fetchone()[0]
print(f"Status closed OU canceled (todos os anos): {closed_canceled_all}")

# Verificar timeline - posições que já tiveram status closed
cur.execute("""
    SELECT COUNT(DISTINCT pt.posicao_id)
    FROM position_timeline pt
    INNER JOIN posicoes p ON p.id = pt.posicao_id
    WHERE pt.new_status IN ('closed', 'canceled')
    AND p.vaga_id NOT IN (114, 99, 479, 88, 680)
""")
timeline_closed_canceled = cur.fetchone()[0]
print(f"Posicoes que ja tiveram status closed OU canceled (timeline): {timeline_closed_canceled}")

# 3. Análise de VAGAS vs POSICOES
print("\n3. ANALISE VAGAS vs POSICOES")
print("-" * 80)

cur.execute("""
    SELECT COUNT(DISTINCT v.id)
    FROM vagas v
    WHERE v.id NOT IN (114, 99, 479, 88, 680)
    AND (v.custom_fields->>'Tipo' IS NULL OR v.custom_fields->>'Tipo' != 'Banco de Talentos')
""")
total_vagas = cur.fetchone()[0]
print(f"Total de vagas (excluindo filtros): {total_vagas}")

cur.execute("""
    SELECT COUNT(*)
    FROM posicoes p
    WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
""")
total_posicoes_all = cur.fetchone()[0]
print(f"Total de posicoes (excluindo filtros): {total_posicoes_all}")

# Verificar se há vagas com múltiplas posições
cur.execute("""
    SELECT
        v.id as vaga_id,
        v.name as cargo,
        COUNT(p.id) as num_posicoes
    FROM vagas v
    INNER JOIN posicoes p ON p.vaga_id = v.id
    WHERE v.id NOT IN (114, 99, 479, 88, 680)
    GROUP BY v.id, v.name
    HAVING COUNT(p.id) > 1
    ORDER BY num_posicoes DESC
    LIMIT 10
""")

print("\nVagas com multiplas posicoes (top 10):")
for vaga_id, cargo, num in cur.fetchall():
    print(f"  Vaga {vaga_id} - {cargo}: {num} posicoes")

# 4. Verificar se a view está usando filtros de data
print("\n4. VERIFICAR FILTRO DE DATA NA VIEW")
print("-" * 80)

cur.execute("""
    SELECT
        MIN(data_publicacao) as primeira_data,
        MAX(data_publicacao) as ultima_data,
        COUNT(*) as total
    FROM vw_analise_posicoes
""")
primeira, ultima, total = cur.fetchone()
print(f"Primeira data_publicacao: {primeira}")
print(f"Ultima data_publicacao: {ultima}")
print(f"Total de registros: {total}")

# 5. Verificar histórico completo de posições "finalizadas"
print("\n5. TODAS AS POSICOES FINALIZADAS (status != open, paused)")
print("-" * 80)

cur.execute("""
    SELECT
        EXTRACT(YEAR FROM p.opened_at) as ano,
        p.status,
        COUNT(*) as total
    FROM posicoes p
    WHERE p.status NOT IN ('open', 'paused')
    AND p.vaga_id NOT IN (114, 99, 479, 88, 680)
    GROUP BY EXTRACT(YEAR FROM p.opened_at), p.status
    ORDER BY ano DESC, total DESC
""")

print(f"{'Ano':<8} {'Status':<12} {'Total':>8}")
print("-" * 30)
total_finalizadas = 0
for ano, status, total in cur.fetchall():
    if ano:
        print(f"{int(ano):<8} {status:<12} {total:>8}")
        total_finalizadas += total
    else:
        print(f"{'NULL':<8} {status:<12} {total:>8}")

print("-" * 30)
print(f"{'TOTAL':<21} {total_finalizadas:>8}")

print("\n" + "=" * 80)
print("HIPOTESES PARA A DIVERGENCIA")
print("=" * 80)
print(f"1. Relatorio mostra {closed_canceled_2024_2026} posicoes (closed+canceled 2024-2026)")
print(f"2. Relatorio mostra {total_closed_all} posicoes (closed todos os anos)")
print(f"3. Relatorio mostra {total_hired_all} posicoes (hired_at preenchido todos os anos)")
print(f"4. Relatorio mostra {total_finalizadas} posicoes (status != open/paused todos os anos)")
print(f"5. Relatorio mostra {timeline_closed_canceled} posicoes (timeline closed+canceled)")
print()
print(f"View atual mostra: 120 posicoes com status_atual='closed'")
print(f"Usuario menciona: 506 posicoes fechadas na planilha externa")
print("=" * 80)

cur.close()
conn.close()
