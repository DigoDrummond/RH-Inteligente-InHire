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
print("ANALISE DE CUSTOM_FIELDS EM REQUISICOES")
print("=" * 80)

# Buscar custom_fields que não são nulos
cur.execute("""
    SELECT id, custom_fields
    FROM requisicoes
    WHERE custom_fields IS NOT NULL
    LIMIT 5
""")

found_time_rethink = False
found_tipo_posicao = False

for req_id, cf in cur.fetchall():
    print(f"\nRequisição ID: {req_id}")
    print("-" * 80)

    if isinstance(cf, list):
        for item in cf:
            if isinstance(item, dict):
                name = item.get('name', '')
                value = item.get('value', '')

                if name == 'Time Rethink':
                    found_time_rethink = True
                    print(f"  [ENCONTRADO] Time Rethink")
                    print(f"    Name: {name}")
                    print(f"    Value: {value}")
                    print(f"    Type: {item.get('type', '')}")
                    print(f"    Full: {json.dumps(item, indent=4, ensure_ascii=False)}")

                elif name == 'Tipo de Posição':
                    found_tipo_posicao = True
                    print(f"  [ENCONTRADO] Tipo de Posição")
                    print(f"    Name: {name}")
                    print(f"    Value: {value}")
                    print(f"    Type: {item.get('type', '')}")
                    print(f"    Full: {json.dumps(item, indent=4, ensure_ascii=False)}")

print("\n" + "=" * 80)
print("RESUMO DA BUSCA")
print("=" * 80)
print(f"Time Rethink encontrado? {'SIM' if found_time_rethink else 'NAO'}")
print(f"Tipo de Posição encontrado? {'SIM' if found_tipo_posicao else 'NAO'}")

# Mostrar todos os nomes de campos disponíveis
print("\n" + "=" * 80)
print("TODOS OS CAMPOS CUSTOM_FIELDS DISPONIVEIS")
print("=" * 80)

cur.execute("""
    SELECT custom_fields
    FROM requisicoes
    WHERE custom_fields IS NOT NULL
    LIMIT 100
""")

all_fields = set()
for (cf,) in cur.fetchall():
    if isinstance(cf, list):
        for item in cf:
            if isinstance(item, dict):
                name = item.get('name', '')
                if name:
                    all_fields.add(name)

for i, field_name in enumerate(sorted(all_fields), 1):
    marker = ""
    if field_name == 'Time Rethink':
        marker = " <-- EMPRESA"
    elif field_name == 'Tipo de Posição':
        marker = " <-- TIPO POSICAO"
    print(f"{i:2}. {field_name}{marker}")

print("\n" + "=" * 80)

cur.close()
conn.close()
