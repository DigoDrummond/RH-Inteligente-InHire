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
print("EXPORTANDO POSIÇÕES (EXCETO CANCELADAS E FECHADAS)")
print("=" * 80)

# Verificar status disponíveis
print("\n1. Verificando status de posições:")
cur.execute("""
    SELECT status, COUNT(*) as total
    FROM posicoes
    GROUP BY status
    ORDER BY total DESC
""")

print("\nStatus disponíveis:")
for status, count in cur.fetchall():
    print(f"   {status}: {count} posições")

# Exportar posições (exceto canceled e closed)
print("\n2. Exportando posições abertas (status != canceled e != closed):")
cur.execute("""
    SELECT
        p.id,
        p.inhire_id,
        p.vaga_id,
        v.name as vaga_nome,
        v.area,
        v.seniority::text as senioridade,
        p.status,
        p.reason,
        p.requisition_id,
        p.user_name as responsavel,
        p.created_at,
        p.updated_at_inhire,
        p.approved_at,
        p.hired_at,
        p.opened_at
    FROM posicoes p
    JOIN vagas v ON p.vaga_id = v.id
    WHERE p.status NOT IN ('canceled', 'closed')
    ORDER BY p.updated_at_inhire DESC, p.id
""")

posicoes = cur.fetchall()

print(f"\nTotal de posições encontradas: {len(posicoes)}")

# Agrupar por status
status_count = {}
for posicao in posicoes:
    status = posicao[6]  # índice do status
    status_count[status] = status_count.get(status, 0) + 1

print("\nDistribuição por status:")
for status, count in sorted(status_count.items(), key=lambda x: x[1], reverse=True):
    print(f"   {status}: {count} posições")

# Exportar CSV
with open('G:/Meu Drive/Framework_Data/Inhire/exports_analise/posicoes_abertas.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow([
        'ID', 'ID Inhire', 'ID Vaga', 'Nome da Vaga', 'Área', 'Senioridade',
        'Status', 'Motivo', 'ID Requisição', 'Responsável',
        'Criado em', 'Atualizado em', 'Aprovado em', 'Contratado em', 'Aberto em'
    ])

    for row in posicoes:
        writer.writerow(row)

print(f"\n>>> Exportadas {len(posicoes)} posições para 'exports_analise/posicoes_abertas.csv'")

# Estatísticas adicionais
print("\n3. Estatísticas adicionais:")

# Por vaga
cur.execute("""
    SELECT
        v.name,
        COUNT(p.id) as total_posicoes,
        COUNT(CASE WHEN p.status = 'open' THEN 1 END) as abertas,
        COUNT(CASE WHEN p.status = 'filled' THEN 1 END) as preenchidas,
        COUNT(CASE WHEN p.status = 'pending' THEN 1 END) as pendentes
    FROM posicoes p
    JOIN vagas v ON p.vaga_id = v.id
    WHERE p.status NOT IN ('canceled', 'closed')
    GROUP BY v.id, v.name
    HAVING COUNT(p.id) > 0
    ORDER BY total_posicoes DESC
    LIMIT 15
""")

print("\nTop 15 vagas com mais posições (exceto canceladas/fechadas):")
print(f"{'Vaga':<50} | {'Total':>6} | {'Abertas':>7} | {'Preench':>8} | {'Pendent':>7}")
print("-" * 100)

for vaga, total, abertas, preenchidas, pendentes in cur.fetchall():
    print(f"{vaga[:50]:<50} | {total:>6} | {abertas:>7} | {preenchidas:>8} | {pendentes:>7}")

# Por área
cur.execute("""
    SELECT
        COALESCE(v.area, 'Não informado') as area,
        COUNT(p.id) as total_posicoes,
        COUNT(CASE WHEN p.status = 'open' THEN 1 END) as abertas
    FROM posicoes p
    JOIN vagas v ON p.vaga_id = v.id
    WHERE p.status NOT IN ('canceled', 'closed')
    GROUP BY v.area
    ORDER BY total_posicoes DESC
""")

print("\n\nPosições por área:")
for area, total, abertas in cur.fetchall():
    print(f"   {area:<20} | Total: {total:>3} | Abertas: {abertas:>3}")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("EXPORTAÇÃO CONCLUÍDA!")
print("=" * 80)
