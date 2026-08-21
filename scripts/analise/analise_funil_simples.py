import psycopg2
import csv

conn = psycopg2.connect(
    dbname="inhire",
    user="postgres",
    password="postgres",
    host="localhost"
)

cur = conn.cursor()

print("=" * 80)
print("ANÁLISE COMPLETA: FUNIL & PERFORMANCE")
print("=" * 80)

# Preparar dados para exportação
dados_exportacao = {}

# ========================================
# 1. MÉTRICAS PRINCIPAIS
# ========================================
print("\n1. MÉTRICAS PRINCIPAIS")
print("-" * 80)

cur.execute("SELECT COUNT(*) FROM candidaturas")
total_candidaturas = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM candidaturas WHERE status::text = 'ACTIVE'")
ativos = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM candidaturas WHERE status::text = 'REJECTED'")
reprovados = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM candidaturas WHERE status::text = 'DECLINED'")
desistentes = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM candidaturas WHERE status::text = 'HIRED'")
contratados = cur.fetchone()[0]

print(f"   Total de Candidaturas: {total_candidaturas}")
print(f"   Ativos: {ativos} ({round(ativos/total_candidaturas*100, 1)}%)")
print(f"   Reprovados: {reprovados} ({round(reprovados/total_candidaturas*100, 1)}%)")
print(f"   Desistentes: {desistentes} ({round(desistentes/total_candidaturas*100, 1)}%)")
print(f"   Contratados: {contratados}")

dados_exportacao['metricas'] = {
    'total': total_candidaturas,
    'ativos': ativos,
    'reprovados': reprovados,
    'desistentes': desistentes,
    'contratados': contratados
}

# ========================================
# 2. CANDIDATURAS POR ETAPA (FUNIL)
# ========================================
print("\n2. FUNIL DE CONVERSÃO POR ETAPA")
print("-" * 80)

cur.execute("""
    SELECT
        COALESCE(stage_name, 'Não informado') as etapa,
        COUNT(*) as total,
        COUNT(CASE WHEN status::text = 'ACTIVE' THEN 1 END) as ativos,
        COUNT(CASE WHEN status::text = 'REJECTED' THEN 1 END) as reprovados,
        COUNT(CASE WHEN status::text = 'DECLINED' THEN 1 END) as desistentes,
        COUNT(CASE WHEN status::text = 'HIRED' THEN 1 END) as contratados
    FROM candidaturas
    GROUP BY stage_name
    ORDER BY total DESC
""")

funil_data = []
for etapa, total, ativos, reprovados, desistentes, contratados in cur.fetchall():
    print(f"   {etapa[:50]:50} | {total:5} total | {ativos:4} ativos | {reprovados:4} reprov | {desistentes:3} desist | {contratados:2} contrat")
    funil_data.append({
        'etapa': etapa,
        'total': total,
        'ativos': ativos,
        'reprovados': reprovados,
        'desistentes': desistentes,
        'contratados': contratados
    })

# Exportar CSV do Funil
with open('G:/Meu Drive/Framework_Data/Inhire/funil_por_etapa.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['Etapa', 'Total', 'Ativos', 'Reprovados', 'Desistentes', 'Contratados', '% Ativos', '% Reprovados'])
    for row in funil_data:
        pct_ativos = round(row['ativos']/row['total']*100, 1) if row['total'] > 0 else 0
        pct_reprov = round(row['reprovados']/row['total']*100, 1) if row['total'] > 0 else 0
        writer.writerow([
            row['etapa'],
            row['total'],
            row['ativos'],
            row['reprovados'],
            row['desistentes'],
            row['contratados'],
            f"{pct_ativos}%",
            f"{pct_reprov}%"
        ])

# ========================================
# 3. CANDIDATURAS POR FONTE
# ========================================
print("\n3. CANDIDATURAS POR FONTE")
print("-" * 80)

cur.execute("""
    SELECT
        COALESCE(source, 'Não informado') as fonte,
        COUNT(*) as total,
        COUNT(CASE WHEN status::text = 'ACTIVE' THEN 1 END) as ativos,
        COUNT(CASE WHEN status::text = 'HIRED' THEN 1 END) as contratados
    FROM candidaturas
    GROUP BY source
    ORDER BY total DESC
""")

fonte_data = []
for fonte, total, ativos, contratados in cur.fetchall():
    print(f"   {fonte[:30]:30} | {total:6} total | {ativos:5} ativos | {contratados:2} contratados")
    fonte_data.append([fonte, total, ativos, contratados])

# Exportar CSV das Fontes
with open('G:/Meu Drive/Framework_Data/Inhire/candidaturas_por_fonte.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['Fonte', 'Total', 'Ativos', 'Contratados'])
    writer.writerows(fonte_data)

# ========================================
# 4. TOP VAGAS COM MAIS CANDIDATURAS
# ========================================
print("\n4. TOP 20 VAGAS COM MAIS CANDIDATURAS")
print("-" * 80)

cur.execute("""
    SELECT
        v.name,
        v.area,
        v.seniority::text,
        COUNT(c.id) as total_candidaturas,
        COUNT(CASE WHEN c.status::text = 'ACTIVE' THEN 1 END) as ativos,
        COUNT(CASE WHEN c.status::text = 'REJECTED' THEN 1 END) as reprovados,
        COUNT(CASE WHEN c.status::text = 'HIRED' THEN 1 END) as contratados
    FROM candidaturas c
    JOIN vagas v ON c.vaga_id = v.id
    GROUP BY v.id, v.name, v.area, v.seniority
    ORDER BY total_candidaturas DESC
    LIMIT 20
""")

vagas_data = []
for nome, area, senioridade, total, ativos, reprovados, contratados in cur.fetchall():
    print(f"   {nome[:45]:45} | {total:4} cand | {ativos:3} ativos | {reprovados:3} reprov | {contratados:2} contrat")
    vagas_data.append([nome, area or '', senioridade or '', total, ativos, reprovados, contratados])

# Exportar CSV das Vagas
with open('G:/Meu Drive/Framework_Data/Inhire/top_vagas_candidaturas.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['Vaga', 'Área', 'Senioridade', 'Total Candidaturas', 'Ativos', 'Reprovados', 'Contratados'])
    writer.writerows(vagas_data)

# ========================================
# 5. CANDIDATURAS POR RESPONSÁVEL
# ========================================
print("\n5. CANDIDATURAS POR RESPONSÁVEL (TOP 15)")
print("-" * 80)

cur.execute("""
    SELECT
        COALESCE(user_name, 'Não informado') as responsavel,
        COUNT(*) as total_candidaturas,
        COUNT(CASE WHEN status::text = 'ACTIVE' THEN 1 END) as ativos,
        COUNT(CASE WHEN status::text = 'HIRED' THEN 1 END) as contratados
    FROM candidaturas
    GROUP BY user_name
    ORDER BY total_candidaturas DESC
    LIMIT 15
""")

responsavel_data = []
for responsavel, total, ativos, contratados in cur.fetchall():
    print(f"   {responsavel[:40]:40} | {total:5} cand | {ativos:4} ativos | {contratados:2} contrat")
    responsavel_data.append([responsavel, total, ativos, contratados])

# Exportar CSV dos Responsáveis
with open('G:/Meu Drive/Framework_Data/Inhire/candidaturas_por_responsavel.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['Responsável', 'Total Candidaturas', 'Ativos', 'Contratados'])
    writer.writerows(responsavel_data)

# ========================================
# 6. CANDIDATURAS POR MÊS
# ========================================
print("\n6. CANDIDATURAS POR MÊS (2025)")
print("-" * 80)

cur.execute("""
    SELECT
        TO_CHAR(created_at, 'YYYY-MM') as mes,
        COUNT(*) as total,
        COUNT(CASE WHEN status::text = 'ACTIVE' THEN 1 END) as ativos,
        COUNT(CASE WHEN status::text = 'REJECTED' THEN 1 END) as reprovados
    FROM candidaturas
    WHERE DATE_PART('year', created_at) = 2025
    GROUP BY mes
    ORDER BY mes
""")

mes_data = []
for mes, total, ativos, reprovados in cur.fetchall():
    print(f"   {mes}: {total:6} cand | {ativos:5} ativos | {reprovados:5} reprovados")
    mes_data.append([mes, total, ativos, reprovados])

# Exportar CSV por Mês
with open('G:/Meu Drive/Framework_Data/Inhire/candidaturas_por_mes.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['Mês', 'Total', 'Ativos', 'Reprovados'])
    writer.writerows(mes_data)

# ========================================
# 7. TEMPO MÉDIO NO PROCESSO
# ========================================
print("\n7. TEMPO MÉDIO NO PROCESSO")
print("-" * 80)

cur.execute("""
    SELECT
        AVG(dias_no_processo) as media_dias_processo,
        MIN(dias_no_processo) as min_dias,
        MAX(dias_no_processo) as max_dias,
        AVG(dias_no_stage_atual) as media_dias_stage
    FROM candidaturas
    WHERE dias_no_processo IS NOT NULL
""")

result = cur.fetchone()
if result[0]:
    print(f"   Média de dias no processo: {result[0]:.1f} dias")
    print(f"   Mínimo: {result[1]:.1f} dias | Máximo: {result[2]:.1f} dias")
    if result[3]:
        print(f"   Média de dias no stage atual: {result[3]:.1f} dias")

# ========================================
# 8. PRETENSÃO SALARIAL
# ========================================
print("\n8. ANÁLISE DE PRETENSÃO SALARIAL")
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
if result and result[0] and result[0] > 0:
    print(f"   Candidaturas com pretensão salarial: {result[0]}")
    print(f"   Pretensão salarial média: R$ {result[1]:,.2f}")
    print(f"   Pretensão mínima: R$ {result[2]:,.2f}")
    print(f"   Pretensão máxima: R$ {result[3]:,.2f}")
else:
    print("   Nenhuma candidatura possui pretensão salarial informada")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("ANÁLISE CONCLUÍDA!")
print("=" * 80)
print("\nArquivos CSV gerados:")
print("  - funil_por_etapa.csv")
print("  - candidaturas_por_fonte.csv")
print("  - top_vagas_candidaturas.csv")
print("  - candidaturas_por_responsavel.csv")
print("  - candidaturas_por_mes.csv")
