import psycopg2

conn = psycopg2.connect(
    dbname="inhire",
    user="postgres",
    password="postgres",
    host="localhost"
)

cur = conn.cursor()

print("=" * 80)
print("VERIFICAR TIPO DA COLUNA custom_fields")
print("=" * 80)

cur.execute("""
    SELECT column_name, data_type, udt_name
    FROM information_schema.columns
    WHERE table_name = 'requisicoes'
    AND column_name = 'custom_fields'
""")

result = cur.fetchone()
if result:
    col_name, data_type, udt_name = result
    print(f"\nTabela: requisicoes")
    print(f"Coluna: {col_name}")
    print(f"Tipo: {data_type}")
    print(f"UDT: {udt_name}")
else:
    print("\nColuna custom_fields NAO encontrada")

print("\n" + "=" * 80)

cur.close()
conn.close()
