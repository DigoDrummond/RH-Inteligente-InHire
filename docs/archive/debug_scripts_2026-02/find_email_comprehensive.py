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
print("ANALISE COMPLETA DE CUSTOM_FIELDS EM REQUISICOES")
print("=" * 80)

# Buscar TODOS os campos diferentes nos custom_fields
cur.execute("""
    SELECT custom_fields
    FROM requisicoes
    WHERE custom_fields IS NOT NULL
""")

all_field_names = set()
email_fields = {}

for (cf,) in cur.fetchall():
    if isinstance(cf, list):
        for item in cf:
            if isinstance(item, dict):
                field_name = item.get('name', '')
                if field_name:
                    all_field_names.add(field_name)
                    value = item.get('value', '')

                    # Procurar por email ou E-mail
                    if ('email' in field_name.lower() or
                        'e-mail' in field_name.lower() or
                        'mail' in field_name.lower()):

                        if field_name not in email_fields:
                            email_fields[field_name] = []

                        if value and len(email_fields[field_name]) < 3:
                            email_fields[field_name].append(value)

print("\nTOTAL DE CAMPOS UNICOS ENCONTRADOS:", len(all_field_names))
print("\nTODOS OS CAMPOS:")
print("-" * 80)
for i, name in enumerate(sorted(all_field_names), 1):
    marker = " <- POSSIVEL EMAIL!" if any(kw in name.lower() for kw in ['email', 'e-mail', 'mail']) else ""
    print(f"{i:2}. {name}{marker}")

if email_fields:
    print("\n" + "=" * 80)
    print("CAMPOS COM 'EMAIL' ENCONTRADOS:")
    print("=" * 80)
    for field_name, examples in email_fields.items():
        print(f"\nCampo: {field_name}")
        print(f"Exemplos de valores ({len(examples)}):")
        for i, val in enumerate(examples, 1):
            print(f"  {i}. {val}")
else:
    print("\n*** NENHUM CAMPO COM EMAIL ENCONTRADO ***")
    print("\nCampos relacionados a responsavel/contato/gestor:")
    print("-" * 80)

    for name in sorted(all_field_names):
        if any(keyword in name.lower() for keyword in
               ['responsavel', 'contato', 'gestor', 'solicitante', 'requester', 'user']):
            print(f"  - {name}")

# Mostrar exemplo completo de um custom_fields
print("\n" + "=" * 80)
print("EXEMPLO COMPLETO DE 1 CUSTOM_FIELDS:")
print("=" * 80)

cur.execute("""
    SELECT custom_fields
    FROM requisicoes
    WHERE custom_fields IS NOT NULL
    LIMIT 1
""")

result = cur.fetchone()
if result:
    cf = result[0]
    if isinstance(cf, list):
        for i, item in enumerate(cf, 1):
            print(f"\n{i}. {json.dumps(item, indent=2, ensure_ascii=False)}")

print("\n" + "=" * 80)

cur.close()
conn.close()
