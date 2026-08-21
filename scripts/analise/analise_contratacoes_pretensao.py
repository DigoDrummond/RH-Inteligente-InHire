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
print("ANÁLISE: CONTRATAÇÕES E PRETENSÃO SALARIAL")
print("=" * 80)

# ========================================
# 1. CONTRATAÇÕES (Etapa "Contratação")
# ========================================
print("\n1. CANDIDATOS NA ETAPA 'CONTRATAÇÃO'")
print("-" * 80)

cur.execute("""
    SELECT
        c.id,
        c.talent_name,
        c.talent_email,
        v.name as vaga,
        c.stage_name,
        c.status::text,
        c.created_at,
        c.updated_at_inhire
    FROM candidaturas c
    JOIN vagas v ON c.vaga_id = v.id
    WHERE c.stage_name ILIKE '%contrata%'
    ORDER BY c.updated_at_inhire DESC
    LIMIT 20
""")

print("\nÚltimos 20 candidatos na etapa 'Contratação':")
print(f"{'Nome':<30} | {'Vaga':<40} | {'Status':<10} | {'Atualizado em'}")
print("-" * 120)

for cid, nome, email, vaga, stage, status, created, updated in cur.fetchall():
    updated_str = updated.strftime('%Y-%m-%d') if updated else 'N/A'
    print(f"{nome[:30]:<30} | {vaga[:40]:<40} | {status:<10} | {updated_str}")

# Total por status
cur.execute("""
    SELECT
        status::text,
        COUNT(*) as total
    FROM candidaturas
    WHERE stage_name ILIKE '%contrata%'
    GROUP BY status::text
    ORDER BY total DESC
""")

print("\n\nDistribuição por STATUS na etapa 'Contratação':")
for status, total in cur.fetchall():
    print(f"   {status}: {total} candidatos")

# ========================================
# 2. PRETENSÃO SALARIAL - Form Responses
# ========================================
print("\n\n2. PRETENSÃO SALARIAL - FORM RESPONSES")
print("-" * 80)

# Verificar estrutura
cur.execute("""
    SELECT COUNT(*) FROM form_responses
""")
total_responses = cur.fetchone()[0]
print(f"\nTotal de form_responses: {total_responses}")

if total_responses > 0:
    # Ver estrutura de uma resposta
    cur.execute("""
        SELECT
            id,
            candidatura_id,
            form_id,
            question,
            answer
        FROM form_responses
        WHERE answer IS NOT NULL
        LIMIT 10
    """)

    print("\nPrimeiras 10 respostas:")
    for fid, cid, form_id, question, answer in cur.fetchall():
        print(f"   Q: {question[:60]:<60} | A: {str(answer)[:30]}")

    # Buscar pretensão salarial
    cur.execute("""
        SELECT
            question,
            COUNT(*) as total,
            COUNT(CASE WHEN answer IS NOT NULL AND answer != '' THEN 1 END) as respondidas
        FROM form_responses
        WHERE question ILIKE '%pretens%' OR question ILIKE '%salar%'
        GROUP BY question
    """)

    pretensoes = cur.fetchall()
    if pretensoes:
        print("\n\nQuestões sobre PRETENSÃO/SALÁRIO:")
        for question, total, respondidas in pretensoes:
            print(f"\n   '{question}'")
            print(f"      Total: {total} | Respondidas: {respondidas}")
    else:
        print("\n   Nenhuma questão sobre pretensão/salário encontrada")

# ========================================
# 3. ATTRIBUTES DE TALENTOS (JSON)
# ========================================
print("\n\n3. PRETENSÃO SALARIAL - ATTRIBUTES (Talentos)")
print("-" * 80)

cur.execute("""
    SELECT
        COUNT(*) as total,
        COUNT(attributes) as com_attributes
    FROM talentos
""")

result = cur.fetchone()
print(f"\nTotal de talentos: {result[0]}")
print(f"Com attributes: {result[1]}")

if result[1] > 0:
    # Ver exemplo de attributes
    cur.execute("""
        SELECT
            id,
            name,
            attributes
        FROM talentos
        WHERE attributes IS NOT NULL
        LIMIT 3
    """)

    print("\nExemplo de ATTRIBUTES (primeiros 3 talentos):")
    for tid, name, attrs in cur.fetchall():
        print(f"\n   Talento: {name} (ID: {tid})")
        if attrs:
            try:
                if isinstance(attrs, str):
                    data = json.loads(attrs)
                else:
                    data = attrs

                for key, value in data.items():
                    if 'pretens' in key.lower() or 'salar' in key.lower():
                        print(f"      >>> {key}: {value}")
                    else:
                        print(f"      - {key}: {str(value)[:50]}")
            except Exception as e:
                print(f"      Erro ao parsear: {e}")

# Buscar pretensão salarial em attributes
cur.execute("""
    SELECT
        t.id,
        t.name,
        t.attributes
    FROM talentos t
    WHERE t.attributes::text ILIKE '%pretens%'
       OR t.attributes::text ILIKE '%salar%'
    LIMIT 10
""")

pretensoes_talentos = cur.fetchall()
if pretensoes_talentos:
    print(f"\n\nEncontrados {len(pretensoes_talentos)} talentos com pretensão/salário em attributes:")
    for tid, name, attrs in pretensoes_talentos:
        print(f"\n   {name} (ID: {tid})")
        if attrs:
            try:
                if isinstance(attrs, str):
                    data = json.loads(attrs)
                else:
                    data = attrs

                for key, value in data.items():
                    if 'pretens' in key.lower() or 'salar' in key.lower():
                        print(f"      >>> {key}: {value}")
            except:
                pass

# ========================================
# 4. EXPORTAR CANDIDATOS NA CONTRATAÇÃO
# ========================================
print("\n\n4. EXPORTANDO CANDIDATOS EM CONTRATAÇÃO")
print("-" * 80)

cur.execute("""
    SELECT
        c.id,
        c.talent_name,
        c.talent_email,
        c.talent_phone,
        v.name as vaga,
        v.area,
        v.seniority::text,
        c.status::text,
        c.user_name as responsavel,
        c.created_at,
        c.updated_at_inhire,
        c.dias_no_processo
    FROM candidaturas c
    JOIN vagas v ON c.vaga_id = v.id
    WHERE c.stage_name ILIKE '%contrata%'
    ORDER BY c.updated_at_inhire DESC
""")

import csv

candidatos_contratacao = cur.fetchall()

with open('G:/Meu Drive/Framework_Data/Inhire/candidatos_em_contratacao.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow([
        'ID', 'Nome', 'Email', 'Telefone', 'Vaga', 'Área', 'Senioridade',
        'Status', 'Responsável', 'Criado em', 'Atualizado em', 'Dias no Processo'
    ])

    for row in candidatos_contratacao:
        writer.writerow(row)

print(f">>> Exportados {len(candidatos_contratacao)} candidatos para 'candidatos_em_contratacao.csv'")

# ========================================
# 5. RESUMO FINAL
# ========================================
print("\n\n" + "=" * 80)
print("RESUMO FINAL")
print("=" * 80)

cur.execute("""
    SELECT COUNT(*) FROM candidaturas WHERE stage_name ILIKE '%contrata%'
""")
total_contratacao = cur.fetchone()[0]

cur.execute("""
    SELECT COUNT(*) FROM candidaturas
    WHERE stage_name ILIKE '%contrata%' AND status::text = 'ACTIVE'
""")
ativos_contratacao = cur.fetchone()[0]

print(f"\n✓ CONTRATAÇÕES:")
print(f"   - Total na etapa 'Contratação': {total_contratacao}")
print(f"   - Ativos (em andamento): {ativos_contratacao}")
print(f"   - Consideramos 'contratados' = etapa 'Contratação'")

print(f"\n✓ PRETENSÃO SALARIAL:")
print(f"   - Total de form_responses: {total_responses}")
print(f"   - Verificar campo 'attributes' em talentos")
print(f"   - Verificar respostas de formulários")

cur.close()
conn.close()

print("\n" + "=" * 80)
