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
print("PROCURANDO CAMPO DE EMAIL NOS CUSTOM_FIELDS DE REQUISICOES")
print("=" * 80)

# Buscar todos os campos diferentes nos custom_fields
cur.execute("""
    SELECT custom_fields
    FROM requisicoes
    WHERE custom_fields IS NOT NULL
    LIMIT 20
""")

all_field_names = set()
email_examples = []

for (cf,) in cur.fetchall():
    if isinstance(cf, list):
        for item in cf:
            if isinstance(item, dict):
                field_name = item.get('name', '')
                if field_name:
                    all_field_names.add(field_name)
                    # Procurar por email
                    if 'email' in field_name.lower() or 'e-mail' in field_name.lower():
                        email_examples.append({
                            'name': field_name,
                            'value': item.get('value', ''),
                            'type': item.get('type', '')
                        })

print("\nTODOS OS CAMPOS ENCONTRADOS:")
print("-" * 80)
for i, name in enumerate(sorted(all_field_names), 1):
    marker = " <- POSSÍVEL EMAIL" if 'email' in name.lower() or 'e-mail' in name.lower() else ""
    print(f"{i:2}. {name}{marker}")

if email_examples:
    print("\n" + "=" * 80)
    print("CAMPOS QUE CONTÊM 'EMAIL':")
    print("=" * 80)
    for ex in email_examples:
        print(f"\nNome do campo: {ex['name']}")
        print(f"Tipo: {ex['type']}")
        print(f"Exemplo de valor: {ex['value'][:100] if ex['value'] else '(vazio)'}")
else:
    print("\n⚠️  NENHUM CAMPO COM 'EMAIL' ENCONTRADO")
    print("\nVou buscar campos com 'responsável' ou 'contato':")
    print("-" * 80)

    for name in sorted(all_field_names):
        if any(keyword in name.lower() for keyword in ['responsável', 'responsavel', 'contato', 'gestor', 'solicitante', 'requester']):
            print(f"  - {name}")

print("\n" + "=" * 80)

cur.close()
conn.close()
