import psycopg2
import json
import csv

conn = psycopg2.connect(
    dbname="inhire",
    user="postgres",
    password="postgres",
    host="localhost"
)

cur = conn.cursor()

print("=" * 80)
print("EXTRAÇÃO FINAL: CONTRATAÇÕES E PRETENSÃO SALARIAL")
print("=" * 80)

# ========================================
# 1. CONTRATAÇÕES (585 candidatos)
# ========================================
print("\n1. EXPORTANDO CANDIDATOS EM CONTRATAÇÃO")
print("-" * 80)

cur.execute("""
    SELECT
        c.id,
        c.inhire_id,
        c.talent_name,
        c.talent_email,
        c.talent_headline,
        c.talent_company,
        c.talent_location,
        v.name as vaga,
        v.area,
        v.seniority::text as senioridade,
        c.status::text,
        c.stage_name,
        c.user_name as responsavel,
        c.source,
        c.created_at,
        c.updated_at_inhire
    FROM candidaturas c
    JOIN vagas v ON c.vaga_id = v.id
    WHERE c.stage_name ILIKE '%contrata%'
    ORDER BY c.updated_at_inhire DESC
""")

candidatos = cur.fetchall()

with open('G:/Meu Drive/Framework_Data/Inhire/candidatos_em_contratacao.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow([
        'ID', 'ID Inhire', 'Nome', 'Email', 'Headline', 'Empresa', 'Localização',
        'Vaga', 'Área', 'Senioridade', 'Status', 'Etapa', 'Responsável', 'Fonte',
        'Criado em', 'Atualizado em'
    ])

    for row in candidatos:
        writer.writerow(row)

print(f"✓ Exportados {len(candidatos)} candidatos para 'candidatos_em_contratacao.csv'")

# Resumo por status
cur.execute("""
    SELECT status::text, COUNT(*)
    FROM candidaturas
    WHERE stage_name ILIKE '%contrata%'
    GROUP BY status::text
""")

print("\nDistribuição por status:")
for status, count in cur.fetchall():
    print(f"   {status}: {count}")

# ========================================
# 2. PRETENSÃO SALARIAL - Form Responses
# ========================================
print("\n\n2. ANALISANDO PRETENSÃO SALARIAL (Form Responses)")
print("-" * 80)

cur.execute("""
    SELECT COUNT(*) FROM form_responses
""")
total_responses = cur.fetchone()[0]
print(f"\nTotal de form_responses: {total_responses:,}")

# Verificar campos JSON
cur.execute("""
    SELECT
        id,
        candidatura_id,
        form_type,
        generic_form_responses,
        forms_answers
    FROM form_responses
    WHERE generic_form_responses IS NOT NULL
       OR forms_answers IS NOT NULL
    LIMIT 5
""")

print("\nExemplo de respostas (primeiras 5):")
pretensoes_encontradas = []

for fid, cid, form_type, generic, forms in cur.fetchall():
    print(f"\n   Form Response ID: {fid} | Candidatura: {cid} | Tipo: {form_type}")

    # Verificar generic_form_responses
    if generic:
        print(f"      generic_form_responses: {str(generic)[:100]}...")
        try:
            if isinstance(generic, str):
                data = json.loads(generic)
            else:
                data = generic

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        question = item.get('question', item.get('label', ''))
                        answer = item.get('answer', item.get('value', ''))
                        if 'pretens' in str(question).lower() or 'salar' in str(question).lower():
                            print(f"         >>> ENCONTRADO: {question} = {answer}")
        except Exception as e:
            print(f"         Erro: {e}")

    # Verificar forms_answers
    if forms:
        print(f"      forms_answers: {str(forms)[:100]}...")

# Buscar pretensão salarial em generic_form_responses
print("\n\nBUSCANDO 'Pretensão Salarial' em todos os form_responses...")

cur.execute("""
    SELECT
        fr.id,
        fr.candidatura_id,
        c.talent_name,
        c.talent_email,
        fr.generic_form_responses
    FROM form_responses fr
    JOIN candidaturas c ON fr.candidatura_id = c.id
    WHERE fr.generic_form_responses::text ILIKE '%pretens%'
       OR fr.generic_form_responses::text ILIKE '%salar%'
    LIMIT 100
""")

resultados_pretensao = cur.fetchall()
print(f"Encontrados {len(resultados_pretensao)} registros com pretensão/salário")

pretensoes_data = []

for fid, cid, name, email, generic in resultados_pretensao:
    if generic:
        try:
            if isinstance(generic, str):
                data = json.loads(generic)
            else:
                data = generic

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        question = item.get('question', item.get('label', ''))
                        answer = item.get('answer', item.get('value', ''))

                        if 'pretens' in str(question).lower() or 'salar' in str(question).lower():
                            # Tentar converter para número
                            valor = None
                            if answer:
                                # Limpar e converter
                                answer_str = str(answer).replace('R$', '').replace('.', '').replace(',', '.').strip()
                                try:
                                    valor = float(answer_str)
                                except:
                                    valor = answer

                            pretensoes_data.append([
                                cid, name, email, question, answer, valor
                            ])
        except Exception as e:
            pass

if pretensoes_data:
    print(f"\n{len(pretensoes_data)} respostas de pretensão salarial encontradas!")

    # Exportar CSV
    with open('G:/Meu Drive/Framework_Data/Inhire/pretensao_salarial.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['ID Candidatura', 'Nome', 'Email', 'Pergunta', 'Resposta', 'Valor'])
        writer.writerows(pretensoes_data)

    print("✓ Exportado para 'pretensao_salarial.csv'")

    # Calcular estatísticas
    valores_numericos = [p[5] for p in pretensoes_data if isinstance(p[5], (int, float))]
    if valores_numericos:
        print(f"\n   Estatísticas de {len(valores_numericos)} valores numéricos:")
        print(f"   Média: R$ {sum(valores_numericos)/len(valores_numericos):,.2f}")
        print(f"   Mínimo: R$ {min(valores_numericos):,.2f}")
        print(f"   Máximo: R$ {max(valores_numericos):,.2f}")
else:
    print("   Nenhuma pretensão salarial encontrada :(")

# ========================================
# 3. ATTRIBUTES DE TALENTOS
# ========================================
print("\n\n3. VERIFICANDO ATTRIBUTES DOS TALENTOS")
print("-" * 80)

cur.execute("""
    SELECT COUNT(*), COUNT(attributes)
    FROM talentos
""")

total_talentos, com_attributes = cur.fetchone()
print(f"\nTotal de talentos: {total_talentos:,}")
print(f"Com attributes: {com_attributes:,}")

# Ver exemplo
cur.execute("""
    SELECT name, attributes
    FROM talentos
    WHERE attributes IS NOT NULL
    LIMIT 3
""")

print("\nExemplo de attributes (primeiros 3):")
for name, attrs in cur.fetchall():
    print(f"\n   {name}:")
    if attrs:
        try:
            if isinstance(attrs, str):
                data = json.loads(attrs)
            else:
                data = attrs

            # Mostrar apenas as chaves
            if isinstance(data, dict):
                print(f"      Chaves: {', '.join(data.keys())}")
        except:
            pass

cur.close()
conn.close()

print("\n" + "=" * 80)
print("RESUMO:")
print("=" * 80)
print(f"✓ {len(candidatos)} candidatos na etapa 'Contratação'")
print(f"✓ {total_responses:,} form_responses no banco")
if pretensoes_data:
    print(f"✓ {len(pretensoes_data)} respostas de pretensão salarial")
else:
    print("✗ Pretensão salarial não encontrada em form_responses")

print("\nArquivos gerados:")
print("  - candidatos_em_contratacao.csv")
if pretensoes_data:
    print("  - pretensao_salarial.csv")

print("=" * 80)
