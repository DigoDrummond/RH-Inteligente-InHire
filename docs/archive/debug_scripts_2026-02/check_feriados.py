import psycopg2

conn = psycopg2.connect(
    dbname="inhire",
    user="postgres",
    password="postgres",
    host="localhost"
)

cur = conn.cursor()

# Verificar se tabela feriados existe
try:
    cur.execute("SELECT COUNT(*) FROM feriados")
    count = cur.fetchone()[0]
    print(f"Tabela feriados existe: {count} registros")
except:
    print("Tabela feriados NAO existe")

# Verificar se função existe
try:
    cur.execute("""
        SELECT COUNT(*)
        FROM pg_proc
        WHERE proname = 'calcular_dias_uteis'
    """)
    count = cur.fetchone()[0]
    print(f"Funcao calcular_dias_uteis existe: {'SIM' if count > 0 else 'NAO'}")
except:
    print("Erro ao verificar funcao")

cur.close()
conn.close()
