"""
Script para investigar por que há nomes de talentos vazios na vw_funil_performance
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
print("INVESTIGAÇÃO: Nomes de Talentos Vazios na vw_funil_performance")
print("=" * 80)
print()

# 1. Total de registros
print("1. Contagem geral:")
cursor.execute("""
    SELECT
        COUNT(*) as total_candidaturas,
        COUNT(nome_talento) as com_nome_talento,
        COUNT(*) - COUNT(nome_talento) as sem_nome_talento
    FROM vw_funil_performance
""")
row = cursor.fetchone()
print(f"   Total de candidaturas: {row[0]}")
print(f"   Com nome do talento: {row[1]}")
print(f"   SEM nome do talento: {row[2]}")
print()

# 2. Verificar se talent_inhire_id está NULL
print("2. Candidaturas sem talent_inhire_id:")
cursor.execute("""
    SELECT COUNT(*)
    FROM candidaturas
    WHERE talent_inhire_id IS NULL
""")
sem_talent_id = cursor.fetchone()[0]
print(f"   Candidaturas com talent_inhire_id NULL: {sem_talent_id}")
print()

# 3. Verificar se talent_inhire_id existe mas não tem match na tabela talentos
print("3. Candidaturas com talent_inhire_id mas sem talento correspondente:")
cursor.execute("""
    SELECT COUNT(*)
    FROM candidaturas c
    WHERE c.talent_inhire_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM talentos t WHERE t.inhire_id = c.talent_inhire_id)
""")
sem_match = cursor.fetchone()[0]
print(f"   Candidaturas sem match na tabela talentos: {sem_match}")
print()

# 4. Verificar talentos com nome NULL ou vazio
print("4. Talentos com nome NULL ou vazio:")
cursor.execute("""
    SELECT COUNT(*)
    FROM talentos
    WHERE name IS NULL OR TRIM(name) = ''
""")
talentos_sem_nome = cursor.fetchone()[0]
print(f"   Talentos sem nome na tabela: {talentos_sem_nome}")
print()

# 5. Exemplos de candidaturas sem nome de talento
print("5. Exemplos de candidaturas sem nome de talento (primeiras 10):")
cursor.execute("""
    SELECT
        c.id as candidatura_id,
        c.talent_inhire_id,
        c.talent_name,
        c.talent_email,
        c.vaga_id,
        v.name as vaga_name,
        t.inhire_id as talento_existe
    FROM candidaturas c
    LEFT JOIN vagas v ON v.id = c.vaga_id
    LEFT JOIN talentos t ON t.inhire_id = c.talent_inhire_id
    WHERE c.talent_inhire_id IS NOT NULL
    AND t.inhire_id IS NULL
    LIMIT 10
""")
print()
print("   ID Cand | Talent Inhire ID                     | Nome (API) | Email | Vaga")
print("   " + "-" * 75)
for row in cursor.fetchall():
    cand_id = row[0]
    talent_id = row[1] or 'NULL'
    talent_name = row[2] or '(vazio)'
    talent_email = row[3] or '(vazio)'
    vaga_name = row[5] or '(vazio)'
    print(f"   {cand_id:7} | {talent_id[:36]:36} | {talent_name[:15]:15} | {talent_email[:20]:20}")

print()
print("=" * 80)
print("CONCLUSÃO:")
print("=" * 80)
print()
print("A view vw_funil_performance usa:")
print("  LEFT JOIN talentos t ON t.inhire_id = c.talent_inhire_id")
print()
print("Nomes vazios ocorrem quando:")
print("  1. c.talent_inhire_id é NULL (candidatura sem ID do talento)")
print("  2. Talento não foi sincronizado da API (não existe na tabela talentos)")
print("  3. Talento existe mas tem nome NULL/vazio")
print()
print("SOLUÇÃO RECOMENDADA:")
print("  - Executar sync de talentos para garantir que todos os talents estão no BD")
print("  - Usar fallback: c.talent_name (campo direto da candidatura) quando t.name é NULL")
print()

cursor.close()
conn.close()
