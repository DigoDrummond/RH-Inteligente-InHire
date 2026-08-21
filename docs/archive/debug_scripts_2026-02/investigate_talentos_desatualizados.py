"""
Script para investigar por que a tabela talentos está desatualizada
"""
import psycopg2

conn = psycopg2.connect(
    dbname="inhire",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)

cursor = conn.cursor()

print("=" * 80)
print("INVESTIGAÇÃO: Por que a tabela talentos está desatualizada?")
print("=" * 80)
print()

# 1. Quantos talentos únicos temos nas candidaturas?
print("1. Talentos únicos referenciados nas candidaturas:")
cursor.execute("""
    SELECT COUNT(DISTINCT talent_inhire_id)
    FROM candidaturas
    WHERE talent_inhire_id IS NOT NULL
""")
talentos_na_candidatura = cursor.fetchone()[0]
print(f"   Talentos únicos em candidaturas: {talentos_na_candidatura:,}")

# 2. Quantos talentos temos na tabela talentos?
cursor.execute("SELECT COUNT(*) FROM talentos")
talentos_na_tabela = cursor.fetchone()[0]
print(f"   Talentos na tabela talentos: {talentos_na_tabela:,}")

# 3. Diferença
diferenca = talentos_na_candidatura - talentos_na_tabela
print(f"   DIFERENÇA (faltando): {diferenca:,}")
print()

# 4. Data da última sincronização de talentos
print("2. Última sincronização de talentos:")
cursor.execute("""
    SELECT MAX(updated_at) as ultima_atualizacao
    FROM talentos
""")
ultima_sync = cursor.fetchone()[0]
print(f"   Última atualização na tabela talentos: {ultima_sync}")
print()

# 5. Data da última candidatura
print("3. Última candidatura registrada:")
cursor.execute("""
    SELECT MAX(updated_at_inhire) as ultima_candidatura
    FROM candidaturas
""")
ultima_candidatura = cursor.fetchone()[0]
print(f"   Última candidatura: {ultima_candidatura}")
print()

# 6. Verificar quando os 897 talentos faltantes foram criados
print("4. Quando os talentos faltantes foram criados (amostra de 20):")
cursor.execute("""
    SELECT
        c.talent_inhire_id,
        c.talent_name,
        MIN(c.created_at) as primeira_candidatura,
        MAX(c.updated_at_inhire) as ultima_candidatura,
        COUNT(*) as num_candidaturas
    FROM candidaturas c
    WHERE c.talent_inhire_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM talentos t WHERE t.inhire_id = c.talent_inhire_id)
    GROUP BY c.talent_inhire_id, c.talent_name
    ORDER BY MIN(c.created_at) DESC
    LIMIT 20
""")
print()
print("   Talent ID                            | Nome            | 1ª Cand.   | Últ. Cand. | # Cands")
print("   " + "-" * 95)
for row in cursor.fetchall():
    talent_id = str(row[0])[:36]
    name = (row[1] or '(vazio)')[:15]
    primeira = row[2].strftime('%Y-%m-%d') if row[2] else '?'
    ultima = row[3].strftime('%Y-%m-%d') if row[3] else '?'
    num = row[4]
    print(f"   {talent_id} | {name:15} | {primeira} | {ultima} | {num:3}")

print()

# 7. Distribuição temporal dos talentos faltantes
print("5. Quando os talentos faltantes apareceram (por mês):")
cursor.execute("""
    SELECT
        TO_CHAR(MIN(c.created_at), 'YYYY-MM') as mes,
        COUNT(DISTINCT c.talent_inhire_id) as talentos_faltantes
    FROM candidaturas c
    WHERE c.talent_inhire_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM talentos t WHERE t.inhire_id = c.talent_inhire_id)
    GROUP BY TO_CHAR(MIN(c.created_at), 'YYYY-MM')
    ORDER BY mes DESC
    LIMIT 12
""")
print()
print("   Mês     | Talentos Faltantes")
print("   " + "-" * 30)
for row in cursor.fetchall():
    mes = row[0]
    qtd = row[1]
    print(f"   {mes}  | {qtd:4}")

print()
print("=" * 80)
print("CONCLUSÕES:")
print("=" * 80)
print()
print(f"1. Há {diferenca:,} talentos referenciados em candidaturas mas não na tabela talentos")
print(f"2. Última sync de talentos: {ultima_sync}")
print(f"3. Última candidatura: {ultima_candidatura}")
print()
print("POSSÍVEIS CAUSAS:")
print("  a) Sync de talentos não está sendo executada regularmente")
print("  b) Sync incremental pode estar pulando alguns talentos novos")
print("  c) Candidaturas são criadas antes dos talentos serem sincronizados")
print()
print("SOLUÇÃO:")
print("  - Executar sync completa de talentos: python run_sync.py --full")
print("  - OU adicionar sync de talentos faltantes no sync incremental")
print()

cursor.close()
conn.close()
