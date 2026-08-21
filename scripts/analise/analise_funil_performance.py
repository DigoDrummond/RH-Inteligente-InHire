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
print("ANÁLISE: DADOS DISPONÍVEIS PARA FUNIL & PERFORMANCE")
print("=" * 80)

# ========================================
# 1. MÉTRICAS PRINCIPAIS (Cards no topo)
# ========================================
print("\n1. MÉTRICAS PRINCIPAIS")
print("-" * 80)

# Total de Candidaturas
cur.execute("SELECT COUNT(*) FROM candidaturas")
total_candidaturas = cur.fetchone()[0]
print(f"   Total de Candidaturas: {total_candidaturas}")

# Ativos (status = 'ACTIVE')
cur.execute("SELECT COUNT(*) FROM candidaturas WHERE status::text = 'ACTIVE'")
ativos = cur.fetchone()[0]
print(f"   Ativos: {ativos} ({round(ativos/total_candidaturas*100, 1)}%)")

# Reprovados (status = 'REJECTED')
cur.execute("SELECT COUNT(*) FROM candidaturas WHERE status::text = 'REJECTED'")
reprovados = cur.fetchone()[0]
print(f"   Reprovados: {reprovados} ({round(reprovados/total_candidaturas*100, 1)}%)")

# Desistentes (status = 'DECLINED')
cur.execute("SELECT COUNT(*) FROM candidaturas WHERE status::text = 'DECLINED'")
desistentes = cur.fetchone()[0]
print(f"   Desistentes: {desistentes} ({round(desistentes/total_candidaturas*100, 1)}%)")

# Contratados (status = 'HIRED')
cur.execute("SELECT COUNT(*) FROM candidaturas WHERE status::text = 'HIRED'")
contratados = cur.fetchone()[0]
print(f"   Contratados: {contratados}")

# ========================================
# 2. CANDIDATURAS POR MÊS
# ========================================
print("\n2. CANDIDATURAS POR MÊS (2025)")
print("-" * 80)

cur.execute("""
    SELECT
        TO_CHAR(created_at, 'YYYY-MM') as mes,
        COUNT(*) as total
    FROM candidaturas
    WHERE DATE_PART('year', created_at) = 2025
    GROUP BY mes
    ORDER BY mes
""")

for mes, total in cur.fetchall():
    print(f"   {mes}: {total} candidaturas")

# ========================================
# 3. CANDIDATURAS POR FONTE (Source)
# ========================================
print("\n3. CANDIDATURAS POR FONTE")
print("-" * 80)

cur.execute("""
    SELECT
        COALESCE(source, 'Não informado') as fonte,
        COUNT(*) as total
    FROM candidaturas
    GROUP BY source
    ORDER BY total DESC
    LIMIT 10
""")

for fonte, total in cur.fetchall():
    print(f"   {fonte}: {total}")

# ========================================
# 4. FUNIL DE CONVERSÃO POR ETAPA (Stage)
# ========================================
print("\n4. FUNIL DE CONVERSÃO POR ETAPA (Stage)")
print("-" * 80)

cur.execute("""
    SELECT
        COALESCE(stage_name, 'Não informado') as etapa,
        COUNT(*) as total,
        COUNT(CASE WHEN status::text = 'ACTIVE' THEN 1 END) as ativos,
        COUNT(CASE WHEN status::text = 'REJECTED' THEN 1 END) as reprovados,
        COUNT(CASE WHEN status::text = 'HIRED' THEN 1 END) as contratados
    FROM candidaturas
    GROUP BY stage_name
    ORDER BY total DESC
    LIMIT 15
""")

for etapa, total, ativos, reprovados, contratados in cur.fetchall():
    print(f"   {etapa[:40]:40} | Total: {total:5} | Ativos: {ativos:4} | Reprovados: {reprovados:4} | Contratados: {contratados:3}")

# ========================================
# 5. CANDIDATURAS POR VAGA (Top 10)
# ========================================
print("\n5. TOP 10 VAGAS COM MAIS CANDIDATURAS")
print("-" * 80)

cur.execute("""
    SELECT
        v.name,
        COUNT(c.id) as total_candidaturas,
        COUNT(CASE WHEN c.status::text = 'ACTIVE' THEN 1 END) as ativos,
        COUNT(CASE WHEN c.status::text = 'HIRED' THEN 1 END) as contratados
    FROM candidaturas c
    JOIN vagas v ON c.vaga_id = v.id
    GROUP BY v.id, v.name
    ORDER BY total_candidaturas DESC
    LIMIT 10
""")

for nome_vaga, total, ativos, contratados in cur.fetchall():
    print(f"   {nome_vaga[:50]:50} | {total:4} candidaturas | {ativos:3} ativos | {contratados:2} contratados")

# ========================================
# 6. ANÁLISE DE RECRUTADORES
# ========================================
print("\n6. CANDIDATURAS POR RECRUTADOR")
print("-" * 80)

cur.execute("""
    SELECT
        COALESCE(recruiter_name, 'Não informado') as recrutador,
        COUNT(*) as total_candidaturas,
        COUNT(CASE WHEN status::text = 'ACTIVE' THEN 1 END) as ativos,
        COUNT(CASE WHEN status::text = 'HIRED' THEN 1 END) as contratados
    FROM candidaturas
    GROUP BY recruiter_name
    ORDER BY total_candidaturas DESC
    LIMIT 10
""")

for recrutador, total, ativos, contratados in cur.fetchall():
    print(f"   {recrutador[:40]:40} | {total:5} candidaturas | {ativos:4} ativos | {contratados:2} contratados")

# ========================================
# 7. ANÁLISE DE PRETENSÃO SALARIAL
# ========================================
print("\n7. ANÁLISE DE PRETENSÃO SALARIAL")
print("-" * 80)

cur.execute("""
    SELECT
        COUNT(*) as total_com_pretensao,
        AVG(salary_expectation) as media_pretensao,
        MIN(salary_expectation) as min_pretensao,
        MAX(salary_expectation) as max_pretensao
    FROM candidaturas
    WHERE salary_expectation IS NOT NULL AND salary_expectation > 0
""")

result = cur.fetchone()
if result[0] > 0:
    print(f"   Candidaturas com pretensão salarial: {result[0]}")
    print(f"   Pretensão salarial média: R$ {result[1]:,.2f}")
    print(f"   Pretensão mínima: R$ {result[2]:,.2f}")
    print(f"   Pretensão máxima: R$ {result[3]:,.2f}")
else:
    print("   Nenhuma candidatura possui pretensão salarial informada")

# ========================================
# 8. TEMPO MÉDIO NO PROCESSO
# ========================================
print("\n8. TEMPO MÉDIO NO PROCESSO")
print("-" * 80)

cur.execute("""
    SELECT
        AVG(dias_no_processo) as media_dias_processo,
        AVG(dias_no_stage_atual) as media_dias_stage_atual
    FROM candidaturas
    WHERE dias_no_processo IS NOT NULL
""")

result = cur.fetchone()
if result[0]:
    print(f"   Média de dias no processo: {result[0]:.1f} dias")
    print(f"   Média de dias no stage atual: {result[1]:.1f} dias" if result[1] else "   Média de dias no stage atual: N/A")

# ========================================
# 9. MOTIVOS DE REPROVAÇÃO
# ========================================
print("\n9. MOTIVOS DE REPROVAÇÃO/DESISTÊNCIA")
print("-" * 80)

cur.execute("""
    SELECT
        COALESCE(reject_reason, 'Não informado') as motivo,
        status::text,
        COUNT(*) as total
    FROM candidaturas
    WHERE status::text IN ('REJECTED', 'DECLINED') AND reject_reason IS NOT NULL
    GROUP BY reject_reason, status::text
    ORDER BY total DESC
    LIMIT 10
""")

motivos = cur.fetchall()
if motivos:
    for motivo, status, total in motivos:
        print(f"   [{status:8}] {motivo[:60]:60} | {total:4}")
else:
    print("   Nenhum motivo de reprovação/desistência registrado")

# ========================================
# 10. TIMELINE DE CANDIDATURAS
# ========================================
print("\n10. EVENTOS NA TIMELINE")
print("-" * 80)

cur.execute("""
    SELECT
        stage_type,
        COUNT(*) as total
    FROM candidatura_timeline
    WHERE stage_type IS NOT NULL
    GROUP BY stage_type
    ORDER BY total DESC
""")

eventos = cur.fetchall()
if eventos:
    for stage_type, total in eventos:
        print(f"   {stage_type}: {total} eventos")
else:
    print("   Nenhum evento na timeline")

# ========================================
# 11. ESTRUTURA DAS TABELAS RELEVANTES
# ========================================
print("\n11. ESTRUTURA DAS TABELAS DISPONÍVEIS")
print("-" * 80)

# Candidaturas
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'candidaturas'
    ORDER BY ordinal_position
""")

print("\n   Tabela: CANDIDATURAS")
for col, dtype in cur.fetchall():
    print(f"      - {col} ({dtype})")

# Talentos
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'talentos'
    ORDER BY ordinal_position
""")

print("\n   Tabela: TALENTOS")
for col, dtype in cur.fetchall():
    print(f"      - {col} ({dtype})")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("ANÁLISE CONCLUÍDA")
print("=" * 80)
