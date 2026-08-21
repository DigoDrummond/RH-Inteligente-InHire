import psycopg2
import json

conn = psycopg2.connect(
    dbname="inhire",
    user="postgres",
    password="postgres",
    host="localhost"
)

cur = conn.cursor()

print("=" * 80)
print("VERIFICAR ESTRUTURA DE CUSTOM_FIELDS EM REQUISICOES")
print("=" * 80)

# Verificar tipos de custom_fields
cur.execute("""
    SELECT
        id,
        custom_fields,
        json_typeof(custom_fields) as tipo
    FROM requisicoes
    WHERE custom_fields IS NOT NULL
    LIMIT 10
""")

print("\nPrimeiras 10 requisicoes com custom_fields:\n")
for req_id, cf, tipo in cur.fetchall():
    print(f"ID {req_id}: tipo = {tipo}")
    if tipo != 'array':
        print(f"  ATENCAO: NAO E ARRAY!")
        print(f"  Conteudo: {json.dumps(cf, indent=2, ensure_ascii=False)[:200]}...")

# Contar por tipo
cur.execute("""
    SELECT
        json_typeof(custom_fields) as tipo,
        COUNT(*) as total
    FROM requisicoes
    WHERE custom_fields IS NOT NULL
    GROUP BY json_typeof(custom_fields)
    ORDER BY total DESC
""")

print("\n" + "=" * 80)
print("DISTRIBUICAO POR TIPO:")
print("=" * 80)
for tipo, total in cur.fetchall():
    print(f"{tipo}: {total} registros")

# Verificar estrutura na tabela vagas também
print("\n" + "=" * 80)
print("VERIFICAR CUSTOM_FIELDS EM VAGAS")
print("=" * 80)

cur.execute("""
    SELECT column_name, data_type, udt_name
    FROM information_schema.columns
    WHERE table_name = 'vagas'
    AND column_name = 'custom_fields'
""")

result = cur.fetchone()
if result:
    col_name, data_type, udt_name = result
    print(f"\nTabela: vagas")
    print(f"Coluna: {col_name}")
    print(f"Tipo: {data_type}")

cur.execute("""
    SELECT
        json_typeof(custom_fields) as tipo,
        COUNT(*) as total
    FROM vagas
    WHERE custom_fields IS NOT NULL
    GROUP BY json_typeof(custom_fields)
    ORDER BY total DESC
""")

print("\nDistribuicao por tipo em vagas:")
for tipo, total in cur.fetchall():
    print(f"{tipo}: {total} registros")

print("\n" + "=" * 80)

cur.close()
conn.close()
