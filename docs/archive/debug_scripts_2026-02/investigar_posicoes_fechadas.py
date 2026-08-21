import psycopg2
from datetime import datetime

conn = psycopg2.connect(
    dbname="inhire",
    user="postgres",
    password="postgres",
    host="localhost"
)

cur = conn.cursor()

print("=" * 80)
print("INVESTIGACAO: POSICOES FECHADAS (2024-2026)")
print("=" * 80)
print()

# 1. Contar posições fechadas na vw_analise_posicoes
print("1. POSICOES NA VIEW vw_analise_posicoes")
print("-" * 80)

cur.execute("""
    SELECT COUNT(*) as total
    FROM vw_analise_posicoes
""")
total_view = cur.fetchone()[0]
print(f"Total de posicoes na view: {total_view}")

# Contar por status
cur.execute("""
    SELECT
        status_atual,
        COUNT(*) as total
    FROM vw_analise_posicoes
    GROUP BY status_atual
    ORDER BY total DESC
""")
print("\nDistribuicao por status na view:")
for status, total in cur.fetchall():
    print(f"  {status}: {total}")

# 2. Contar posições fechadas direto na tabela posicoes
print("\n2. POSICOES NA TABELA posicoes (2024-2026)")
print("-" * 80)

cur.execute("""
    SELECT COUNT(*) as total
    FROM posicoes
    WHERE EXTRACT(YEAR FROM opened_at) BETWEEN 2024 AND 2026
""")
total_posicoes = cur.fetchone()[0]
print(f"Total de posicoes 2024-2026: {total_posicoes}")

# Contar por status
cur.execute("""
    SELECT
        status,
        COUNT(*) as total
    FROM posicoes
    WHERE EXTRACT(YEAR FROM opened_at) BETWEEN 2024 AND 2026
    GROUP BY status
    ORDER BY total DESC
""")
print("\nDistribuicao por status na tabela posicoes:")
for status, total in cur.fetchall():
    print(f"  {status}: {total}")

# 3. Verificar posições com hired_at (contratadas)
print("\n3. POSICOES CONTRATADAS (hired_at preenchido)")
print("-" * 80)

cur.execute("""
    SELECT COUNT(*) as total
    FROM posicoes
    WHERE hired_at IS NOT NULL
    AND EXTRACT(YEAR FROM opened_at) BETWEEN 2024 AND 2026
""")
total_hired = cur.fetchone()[0]
print(f"Total com hired_at preenchido: {total_hired}")

# 4. Verificar position_timeline para status 'closed'
print("\n4. POSICOES COM STATUS 'closed' NO TIMELINE")
print("-" * 80)

cur.execute("""
    SELECT COUNT(DISTINCT pt.posicao_id) as total
    FROM position_timeline pt
    INNER JOIN posicoes p ON p.id = pt.posicao_id
    WHERE pt.new_status = 'closed'
    AND EXTRACT(YEAR FROM p.opened_at) BETWEEN 2024 AND 2026
""")
total_closed_timeline = cur.fetchone()[0]
print(f"Total de posicoes que tiveram status 'closed': {total_closed_timeline}")

# 5. Verificar posições que NÃO estão na view
print("\n5. VERIFICAR FILTROS DA VIEW")
print("-" * 80)

cur.execute("""
    SELECT COUNT(*) as total
    FROM posicoes p
    WHERE p.vaga_id IN (114, 99, 479, 88, 680)
    AND EXTRACT(YEAR FROM p.opened_at) BETWEEN 2024 AND 2026
""")
filtradas_ids = cur.fetchone()[0]
print(f"Posicoes filtradas por ID de vaga: {filtradas_ids}")

cur.execute("""
    SELECT COUNT(*) as total
    FROM posicoes p
    INNER JOIN vagas v ON p.vaga_id = v.id
    WHERE v.custom_fields->>'Tipo' = 'Banco de Talentos'
    AND EXTRACT(YEAR FROM p.opened_at) BETWEEN 2024 AND 2026
""")
filtradas_banco = cur.fetchone()[0]
print(f"Posicoes filtradas por 'Banco de Talentos': {filtradas_banco}")

# 6. Comparar com a planilha - critérios de "fechada"
print("\n6. POSSIVEIS CRITERIOS PARA 'POSICAO FECHADA'")
print("-" * 80)

# Status closed OU hired
cur.execute("""
    SELECT COUNT(*) as total
    FROM posicoes p
    WHERE (p.status = 'closed' OR p.hired_at IS NOT NULL)
    AND EXTRACT(YEAR FROM p.opened_at) BETWEEN 2024 AND 2026
    AND p.vaga_id NOT IN (114, 99, 479, 88, 680)
""")
total_fechadas_criterio1 = cur.fetchone()[0]
print(f"Criterio 1 (status=closed OU hired_at preenchido): {total_fechadas_criterio1}")

# Último status do timeline = closed
cur.execute("""
    WITH ultimo_status AS (
        SELECT DISTINCT ON (pt.posicao_id)
            pt.posicao_id,
            pt.new_status
        FROM position_timeline pt
        ORDER BY pt.posicao_id, pt.changed_at DESC
    )
    SELECT COUNT(*) as total
    FROM ultimo_status us
    INNER JOIN posicoes p ON p.id = us.posicao_id
    WHERE us.new_status = 'closed'
    AND EXTRACT(YEAR FROM p.opened_at) BETWEEN 2024 AND 2026
    AND p.vaga_id NOT IN (114, 99, 479, 88, 680)
""")
total_fechadas_criterio2 = cur.fetchone()[0]
print(f"Criterio 2 (ultimo status timeline = closed): {total_fechadas_criterio2}")

# Status closed OU canceled
cur.execute("""
    SELECT COUNT(*) as total
    FROM posicoes p
    WHERE p.status IN ('closed', 'canceled')
    AND EXTRACT(YEAR FROM p.opened_at) BETWEEN 2024 AND 2026
    AND p.vaga_id NOT IN (114, 99, 479, 88, 680)
""")
total_fechadas_criterio3 = cur.fetchone()[0]
print(f"Criterio 3 (status IN (closed, canceled)): {total_fechadas_criterio3}")

# 7. Análise detalhada de status
print("\n7. ANALISE DETALHADA - TODAS AS POSICOES 2024-2026")
print("-" * 80)

cur.execute("""
    SELECT
        p.status as status_tabela,
        COALESCE(usp.new_status, 'NULL') as ultimo_status_timeline,
        COUNT(*) as total
    FROM posicoes p
    LEFT JOIN (
        SELECT DISTINCT ON (posicao_id)
            posicao_id,
            new_status
        FROM position_timeline
        ORDER BY posicao_id, changed_at DESC
    ) usp ON usp.posicao_id = p.id
    WHERE EXTRACT(YEAR FROM p.opened_at) BETWEEN 2024 AND 2026
    AND p.vaga_id NOT IN (114, 99, 479, 88, 680)
    GROUP BY p.status, usp.new_status
    ORDER BY total DESC
""")

print("\nCombinacoes status_tabela vs ultimo_status_timeline:")
print(f"{'Status Tabela':<20} {'Status Timeline':<20} {'Total':>10}")
print("-" * 52)
for status_tab, status_tl, total in cur.fetchall():
    print(f"{status_tab:<20} {status_tl:<20} {total:>10}")

print("\n" + "=" * 80)
print("RESUMO")
print("=" * 80)
print(f"View vw_analise_posicoes: {total_view} posicoes")
print(f"Tabela posicoes (2024-2026): {total_posicoes} posicoes")
print(f"Posicoes 'fechadas' - diversos criterios:")
print(f"  - Hired (hired_at preenchido): {total_hired}")
print(f"  - Status closed OU hired: {total_fechadas_criterio1}")
print(f"  - Ultimo status timeline = closed: {total_fechadas_criterio2}")
print(f"  - Status closed OU canceled: {total_fechadas_criterio3}")
print("=" * 80)

cur.close()
conn.close()
