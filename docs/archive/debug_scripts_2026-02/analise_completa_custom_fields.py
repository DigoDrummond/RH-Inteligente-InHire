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
print("ANALISE COMPLETA DE CUSTOM_FIELDS")
print("=" * 80)
print()

# Analisar custom_fields de REQUISICOES
print("1. CUSTOM_FIELDS EM REQUISICOES")
print("=" * 80)

cur.execute("""
    SELECT
        json_typeof(custom_fields) as tipo,
        COUNT(*) as total
    FROM requisicoes
    WHERE custom_fields IS NOT NULL
    GROUP BY tipo
    ORDER BY total DESC
""")

print("\nFormato dos custom_fields:")
for tipo, total in cur.fetchall():
    print(f"  {tipo}: {total} registros")

# Coletar todos os campos únicos
cur.execute("""
    SELECT custom_fields
    FROM requisicoes
    WHERE custom_fields IS NOT NULL
""")

all_fields_req = {}
for (cf,) in cur.fetchall():
    if cf is None:
        continue

    field_type = json.dumps(cf)[:20]  # Peek

    # Se for array
    if isinstance(cf, list):
        for item in cf:
            if isinstance(item, dict):
                name = item.get('name', '')
                value = item.get('value', '')
                if name:
                    if name not in all_fields_req:
                        all_fields_req[name] = {
                            'count': 0,
                            'examples': [],
                            'types': set()
                        }
                    all_fields_req[name]['count'] += 1
                    if value and len(all_fields_req[name]['examples']) < 3:
                        all_fields_req[name]['examples'].append(str(value)[:50])
                    if 'type' in item:
                        all_fields_req[name]['types'].add(item['type'])
    # Se for objeto
    elif isinstance(cf, dict):
        for key, value in cf.items():
            if key not in all_fields_req:
                all_fields_req[key] = {
                    'count': 0,
                    'examples': [],
                    'types': set()
                }
            all_fields_req[key]['count'] += 1
            if value and len(all_fields_req[key]['examples']) < 3:
                all_fields_req[key]['examples'].append(str(value)[:50])

print(f"\nTotal de campos unicos encontrados: {len(all_fields_req)}")
print("\nCampos e suas estatisticas:")
print("-" * 80)
print(f"{'Campo':<50} {'Qtd':>6} {'Tipo':<15} {'Exemplos'}")
print("-" * 80)

for field_name in sorted(all_fields_req.keys()):
    info = all_fields_req[field_name]
    types_str = ','.join(info['types']) if info['types'] else '-'
    examples = ' | '.join(info['examples'][:2]) if info['examples'] else '-'
    print(f"{field_name:<50} {info['count']:>6} {types_str:<15} {examples[:50]}")

# Analisar custom_fields de VAGAS
print("\n\n2. CUSTOM_FIELDS EM VAGAS")
print("=" * 80)

cur.execute("""
    SELECT
        jsonb_typeof(custom_fields) as tipo,
        COUNT(*) as total
    FROM vagas
    WHERE custom_fields IS NOT NULL
    GROUP BY tipo
    ORDER BY total DESC
""")

print("\nFormato dos custom_fields:")
for tipo, total in cur.fetchall():
    print(f"  {tipo}: {total} registros")

cur.execute("""
    SELECT custom_fields
    FROM vagas
    WHERE custom_fields IS NOT NULL
    LIMIT 500
""")

all_fields_vaga = {}
for (cf,) in cur.fetchall():
    if cf is None or not isinstance(cf, dict):
        continue

    for key, value in cf.items():
        if key not in all_fields_vaga:
            all_fields_vaga[key] = {
                'count': 0,
                'examples': []
            }
        all_fields_vaga[key]['count'] += 1
        if value and len(all_fields_vaga[key]['examples']) < 3:
            all_fields_vaga[key]['examples'].append(str(value)[:50])

print(f"\nTotal de campos unicos encontrados: {len(all_fields_vaga)}")
print("\nCampos e suas estatisticas:")
print("-" * 80)
print(f"{'Campo':<50} {'Qtd':>6} {'Exemplos'}")
print("-" * 80)

for field_name in sorted(all_fields_vaga.keys()):
    info = all_fields_vaga[field_name]
    examples = ' | '.join(info['examples'][:2]) if info['examples'] else '-'
    print(f"{field_name:<50} {info['count']:>6} {examples[:50]}")

# Identificar campos úteis que ainda não estão na view
print("\n\n3. CAMPOS POTENCIALMENTE UTEIS NAO UTILIZADOS")
print("=" * 80)

campos_ja_usados_req = {
    'Email do responsável por parte do cliente',
    'Modalidade de Contratação',
    'Time Rethink',
    'Tipo de Posição',
    'Custo Hora (ideal) - Ex. R$ xx,xx',  # usado em vw_dados_jade
    'Valor da venda',  # usado em vw_dados_jade
    'Salário acordado com o talento'  # usado em vw_dados_jade
}

campos_ja_usados_vaga = {
    'Torre',
    'Motivo de Cancelamento',
    'Senioridade',
    'Modalidade de Contratação',
    'Gestor',
    'Se substituição, informar o nome do colaborador: ',
    'Tipo'
}

print("\nREQUISICOES - Campos ainda nao utilizados:")
for field_name, info in sorted(all_fields_req.items(), key=lambda x: x[1]['count'], reverse=True):
    if field_name not in campos_ja_usados_req and info['count'] > 10:
        examples = ' | '.join(info['examples'][:2]) if info['examples'] else '-'
        print(f"  {field_name} ({info['count']} registros)")
        print(f"    Exemplos: {examples}")

print("\nVAGAS - Campos ainda nao utilizados:")
for field_name, info in sorted(all_fields_vaga.items(), key=lambda x: x[1]['count'], reverse=True):
    if field_name not in campos_ja_usados_vaga and info['count'] > 10:
        examples = ' | '.join(info['examples'][:2]) if info['examples'] else '-'
        print(f"  {field_name} ({info['count']} registros)")
        print(f"    Exemplos: {examples}")

print("\n" + "=" * 80)

cur.close()
conn.close()
