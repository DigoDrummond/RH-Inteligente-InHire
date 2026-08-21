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
print("ANALISE DA REQUISICAO ID 897")
print("=" * 80)

# Buscar a requisição 897
cur.execute("""
    SELECT
        id,
        inhire_id,
        user_name,
        requester_name,
        custom_fields
    FROM requisicoes
    WHERE id = 897
""")

result = cur.fetchone()

if result:
    req_id, inhire_id, user_name, requester_name, custom_fields = result

    print(f"\nID: {req_id}")
    print(f"InHire ID: {inhire_id}")
    print(f"User Name: {user_name}")
    print(f"Requester Name: {requester_name}")

    print("\n" + "=" * 80)
    print("CUSTOM FIELDS:")
    print("=" * 80)

    if custom_fields:
        if isinstance(custom_fields, list):
            for i, field in enumerate(custom_fields, 1):
                print(f"\n{i}. Campo:")
                if isinstance(field, dict):
                    for key, value in field.items():
                        print(f"   {key}: {value}")

                        # Destacar campos com email
                        if isinstance(value, str) and '@' in value:
                            print(f"   >>> POSSIVEL EMAIL ENCONTRADO! <<<")
        elif isinstance(custom_fields, dict):
            for key, value in custom_fields.items():
                print(f"\n{key}: {value}")
                if isinstance(value, str) and '@' in value:
                    print(f"   >>> POSSIVEL EMAIL ENCONTRADO! <<<")
    else:
        print("\nNenhum custom_fields encontrado")
else:
    print("\nRequisicao 897 nao encontrada")

cur.close()
conn.close()

print("\n" + "=" * 80)
