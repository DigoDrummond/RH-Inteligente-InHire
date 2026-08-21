"""
Script para atualizar arquivos CSV de análise na pasta exports_analise
"""
import psycopg2
import csv
from datetime import datetime
import sys
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def main():
    # Conectar ao banco
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='inhire',
        user='postgres',
        password='postgres'
    )
    cur = conn.cursor()

    base_path = 'G:/Meu Drive/Framework_Data/Inhire/exports_analise/'

    # 1. Vagas abertas
    print('Atualizando vagas_abertas.csv...')
    cur.execute('''
        SELECT
            v.inhire_id,
            v.name,
            v.area,
            v.status::text,
            COUNT(DISTINCT p.id) as num_posicoes,
            COUNT(DISTINCT c.id) as num_candidaturas,
            v.created_at,
            v.updated_at_inhire
        FROM vagas v
        LEFT JOIN posicoes p ON v.id = p.vaga_id
        LEFT JOIN candidaturas c ON v.id = c.vaga_id
        WHERE v.status::text = 'open'
        GROUP BY v.id, v.inhire_id, v.name, v.area, v.status, v.created_at, v.updated_at_inhire
        ORDER BY v.name
    ''')
    with open(base_path + 'vagas_abertas.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['inhire_id', 'nome', 'area', 'status', 'num_posicoes', 'num_candidaturas', 'criado_em', 'atualizado_em'])
        writer.writerows(cur.fetchall())
    print('OK - vagas_abertas.csv atualizado')

    # 2. Posicoes abertas
    print('Atualizando posicoes_abertas.csv...')
    cur.execute('''
        SELECT
            p.inhire_id,
            p.status,
            v.name as vaga_nome,
            v.area,
            p.created_at,
            p.updated_at_inhire
        FROM posicoes p
        JOIN vagas v ON p.vaga_id = v.id
        WHERE p.status = 'open'
        ORDER BY v.name
    ''')
    with open(base_path + 'posicoes_abertas.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['inhire_id', 'status', 'vaga_nome', 'area', 'criado_em', 'atualizado_em'])
        writer.writerows(cur.fetchall())
    print('OK - posicoes_abertas.csv atualizado')

    # 3. Funil por etapa
    print('Atualizando funil_por_etapa.csv...')
    cur.execute('''
        SELECT
            stage_name,
            status,
            COUNT(*) as total_candidaturas,
            COUNT(CASE WHEN DATE_PART('year', created_at) = 2025 THEN 1 END) as candidaturas_2025,
            COUNT(CASE WHEN DATE_PART('year', created_at) = 2026 THEN 1 END) as candidaturas_2026
        FROM candidaturas
        WHERE stage_name IS NOT NULL
        GROUP BY stage_name, status
        ORDER BY total_candidaturas DESC
    ''')
    with open(base_path + 'funil_por_etapa.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['etapa', 'status', 'total_candidaturas', 'candidaturas_2025', 'candidaturas_2026'])
        writer.writerows(cur.fetchall())
    print('OK - funil_por_etapa.csv atualizado')

    # 4. Candidaturas por fonte
    print('Atualizando candidaturas_por_fonte.csv...')
    cur.execute('''
        SELECT
            COALESCE(source, 'Nao informado') as fonte,
            status,
            COUNT(*) as total,
            COUNT(CASE WHEN DATE_PART('year', created_at) = 2025 THEN 1 END) as candidaturas_2025,
            COUNT(CASE WHEN DATE_PART('year', created_at) = 2026 THEN 1 END) as candidaturas_2026
        FROM candidaturas
        GROUP BY source, status
        ORDER BY total DESC
        LIMIT 50
    ''')
    with open(base_path + 'candidaturas_por_fonte.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['fonte', 'status', 'total', 'candidaturas_2025', 'candidaturas_2026'])
        writer.writerows(cur.fetchall())
    print('OK - candidaturas_por_fonte.csv atualizado')

    # 5. Candidatos contratados
    print('Atualizando candidatos_em_contratacao.csv...')
    cur.execute('''
        SELECT
            c.inhire_id,
            t.name as candidato_nome,
            t.email,
            v.name as vaga_nome,
            c.stage_name as etapa_atual,
            c.status::text,
            c.created_at,
            c.updated_at_inhire
        FROM candidaturas c
        JOIN talentos t ON c.talento_id = t.id
        JOIN vagas v ON c.vaga_id = v.id
        WHERE c.status::text = 'hired'
        ORDER BY c.updated_at_inhire DESC
    ''')
    with open(base_path + 'candidatos_em_contratacao.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['inhire_id', 'candidato_nome', 'email', 'vaga_nome', 'etapa_atual', 'status', 'criado_em', 'atualizado_em'])
        writer.writerows(cur.fetchall())
    print('OK - candidatos_em_contratacao.csv atualizado')

    # 6. Estatisticas gerais
    print('Criando estatisticas_gerais.csv...')
    cur.execute('''
        SELECT
            'Total de Vagas' as metrica,
            COUNT(*)::text as valor,
            COUNT(CASE WHEN status::text = 'open' THEN 1 END)::text as abertas
        FROM vagas
        UNION ALL
        SELECT
            'Total de Posicoes',
            COUNT(*)::text,
            COUNT(CASE WHEN status = 'open' THEN 1 END)::text
        FROM posicoes
        UNION ALL
        SELECT
            'Total de Candidaturas',
            COUNT(*)::text,
            COUNT(CASE WHEN status::text = 'active' THEN 1 END)::text
        FROM candidaturas
        UNION ALL
        SELECT
            'Total de Talentos',
            COUNT(*)::text,
            NULL
        FROM talentos
        UNION ALL
        SELECT
            'Contratacoes',
            COUNT(*)::text,
            NULL
        FROM candidaturas
        WHERE status::text = 'hired'
    ''')
    with open(base_path + 'estatisticas_gerais.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['metrica', 'total', 'ativas_ou_abertas'])
        writer.writerows(cur.fetchall())
    print('OK - estatisticas_gerais.csv criado')

    # 7. Timeline recente
    print('Criando timeline_recente.csv...')
    cur.execute('''
        SELECT
            ct.candidatura_inhire_id,
            v.name as vaga_nome,
            t.name as candidato_nome,
            ct.stage_name,
            ct.stage_type,
            ct.created_at
        FROM candidatura_timeline ct
        JOIN candidaturas c ON ct.candidatura_id = c.id
        JOIN vagas v ON c.vaga_id = v.id
        LEFT JOIN talentos t ON c.talento_id = t.id
        WHERE ct.created_at >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY ct.created_at DESC
        LIMIT 1000
    ''')
    with open(base_path + 'timeline_recente.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['candidatura_id', 'vaga_nome', 'candidato_nome', 'stage_name', 'stage_type', 'criado_em'])
        writer.writerows(cur.fetchall())
    print('OK - timeline_recente.csv criado')

    cur.close()
    conn.close()

    print()
    print('=' * 70)
    print(' TODOS OS ARQUIVOS ATUALIZADOS!')
    print('=' * 70)
    print(f' Data: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(' Total de arquivos: 7')

if __name__ == "__main__":
    main()
