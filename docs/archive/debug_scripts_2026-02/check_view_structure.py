import psycopg2

conn = psycopg2.connect(
    dbname="inhire",
    user="postgres",
    password="postgres",
    host="localhost"
)

cur = conn.cursor()

print("=" * 80)
print("ESTRUTURA ATUAL DA VIEW vw_analise_posicoes")
print("=" * 80)

cur.execute("""
    SELECT ordinal_position, column_name
    FROM information_schema.columns
    WHERE table_name = 'vw_analise_posicoes'
    ORDER BY ordinal_position
""")

columns = cur.fetchall()
print(f"\nTotal de colunas: {len(columns)}\n")

for pos, name in columns:
    print(f"{pos:2}. {name}")

print("\n" + "=" * 80)

# Verificar se modalidade_contratacao já existe
modalidade_exists = any(name == 'modalidade_contratacao' for _, name in columns)
print(f"Campo 'modalidade_contratacao' existe? {'SIM' if modalidade_exists else 'NAO'}")

# Encontrar posição de email_pessoal
email_pessoal_pos = None
for pos, name in columns:
    if name == 'email_pessoal':
        email_pessoal_pos = pos
        print(f"Campo 'email_pessoal' está na posição: {pos}")
        break

if not email_pessoal_pos:
    print("Campo 'email_pessoal' NAO encontrado")

print("\n" + "=" * 80)

cur.close()
conn.close()
