import psycopg2
import csv
from datetime import datetime

# Conectar ao banco
conn = psycopg2.connect(
    dbname="inhire",
    user="postgres",
    password="postgres",
    host="localhost"
)

cur = conn.cursor()

# Exportar Vagas abertas
print("=== VAGAS ABERTAS ===")
cur.execute("""
    SELECT
        id,
        inhire_id,
        name,
        status::text,
        area,
        seniority::text,
        active_talents,
        open_positions,
        user_name,
        created_at,
        updated_at_inhire
    FROM vagas
    WHERE status::text = 'OPEN'
    ORDER BY id
""")

vagas = cur.fetchall()
print(f"\nTotal de vagas abertas: {len(vagas)}\n")

# Salvar CSV de Vagas
with open('G:/Meu Drive/Framework_Data/Inhire/vagas_abertas.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['ID', 'ID Inhire', 'Nome', 'Status', 'Área', 'Senioridade', 'Talentos Ativos', 'Posições Abertas', 'Responsável', 'Criado em', 'Atualizado em'])
    for vaga in vagas:
        writer.writerow(vaga)

print("Primeiras 5 vagas:")
for vaga in vagas[:5]:
    print(f"  ID: {vaga[0]}, Inhire ID: {vaga[1]}, Nome: {vaga[2]}")

# Exportar Posições abertas
print("\n=== POSIÇÕES ABERTAS ===")
cur.execute("""
    SELECT
        p.id,
        p.inhire_id,
        p.vaga_id,
        v.name as vaga_nome,
        p.status,
        p.created_at,
        p.updated_at_inhire
    FROM posicoes p
    JOIN vagas v ON p.vaga_id = v.id
    WHERE p.status = 'open'
    ORDER BY p.id
""")

posicoes = cur.fetchall()
print(f"\nTotal de posições abertas: {len(posicoes)}\n")

# Salvar CSV de Posições
with open('G:/Meu Drive/Framework_Data/Inhire/posicoes_abertas.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['ID', 'ID Inhire', 'ID Vaga', 'Nome da Vaga', 'Status', 'Criado em', 'Atualizado em'])
    for posicao in posicoes:
        writer.writerow(posicao)

print("Primeiras 5 posições:")
for posicao in posicoes[:5]:
    print(f"  ID: {posicao[0]}, Inhire ID: {posicao[1]}, Vaga: {posicao[3]}")

cur.close()
conn.close()

print("\n>>> Arquivos CSV gerados com sucesso!")
print("   - vagas_abertas.csv")
print("   - posicoes_abertas.csv")
