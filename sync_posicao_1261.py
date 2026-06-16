"""Sincroniza especificamente a posição 1261 da API Inhire"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import psycopg2
from services.api_client import InhireAPIClient
from services.database_service import DatabaseService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings

print("\n" + "="*80)
print("SINCRONIZACAO ESPECIFICA - POSICAO 1261")
print("="*80)

# Conectar ao banco
conn = psycopg2.connect(
    host='localhost',
    database='inhire',
    user='postgres',
    password='postgres'
)
cur = conn.cursor()

# Buscar informações da posição 1261
print("\n[1] Buscando informações da posição 1261 no BD...")
cur.execute("""
    SELECT
        p.id,
        p.inhire_id,
        p.vaga_id,
        v.inhire_id as vaga_inhire_id,
        v.name as vaga_nome,
        p.status as status_atual
    FROM posicoes p
    JOIN vagas v ON p.vaga_id = v.id
    WHERE p.id = 1261
""")

row = cur.fetchone()
if not row:
    print("ERRO: Posição 1261 não encontrada no BD!")
    sys.exit(1)

pos_id, pos_inhire_id, vaga_id, vaga_inhire_id, vaga_nome, status_atual = row

print(f"  ID BD: {pos_id}")
print(f"  Inhire ID: {pos_inhire_id}")
print(f"  Vaga: {vaga_nome}")
print(f"  Vaga Inhire ID: {vaga_inhire_id}")
print(f"  Status Atual: {status_atual}")

# Inicializar API client
print("\n[2] Conectando à API Inhire...")
api_client = InhireAPIClient()

try:
    # Buscar posição da API
    print("\n[3] Buscando dados atualizados da API...")

    # Buscar positions da vaga
    from config import InhireEndpoints
    endpoint = InhireEndpoints.POSITIONS_PAGINATED.format(job_id=vaga_inhire_id)

    response = api_client.get(endpoint, params={"page": 1, "pageSize": 1000})

    if not response or 'data' not in response:
        print("ERRO: Resposta inválida da API")
        sys.exit(1)

    positions = response.get('data', [])

    # Encontrar a posição específica
    posicao_api = None
    for pos in positions:
        if pos.get('id') == pos_inhire_id:
            posicao_api = pos
            break

    if not posicao_api:
        print(f"ERRO: Posição {pos_inhire_id} não encontrada na API!")
        sys.exit(1)

    print("  OK - Dados da API recebidos")
    print(f"\n  Status na API: {posicao_api.get('status', 'N/A')}")
    print(f"  Reason: {posicao_api.get('reason', 'N/A')}")
    print(f"  Updated At: {posicao_api.get('updatedAt', 'N/A')}")

    # Verificar timeline
    timeline = posicao_api.get('timeline', [])
    print(f"\n  Timeline: {len(timeline)} eventos")

    if timeline:
        print("\n  Últimos 5 eventos:")
        for i, evento in enumerate(sorted(timeline, key=lambda x: x.get('changedAt', ''), reverse=True)[:5]):
            print(f"    {i+1}. {evento.get('changedAt', 'N/A')} | {evento.get('previousStatus', 'N/A')} -> {evento.get('newStatus', 'N/A')}")

    # Atualizar posição no BD
    print("\n[4] Atualizando posição no BD...")

    cur.execute("""
        UPDATE posicoes
        SET
            status = %s,
            reason = %s,
            updated_at_inhire = %s,
            updated_at = NOW()
        WHERE id = %s
    """, (
        posicao_api.get('status'),
        posicao_api.get('reason'),
        posicao_api.get('updatedAt'),
        pos_id
    ))

    print(f"  OK - Posição {pos_id} atualizada")

    # Atualizar timeline
    print("\n[5] Atualizando timeline...")

    eventos_novos = 0
    eventos_atualizados = 0

    for evento in timeline:
        changed_at = evento.get('changedAt')
        prev_status = evento.get('previousStatus')
        new_status = evento.get('newStatus')
        notes = evento.get('notes')

        if not changed_at:
            continue

        # Verificar se evento já existe
        cur.execute("""
            SELECT id FROM position_timeline
            WHERE posicao_id = %s
              AND changed_at = %s
              AND previous_status = %s
              AND new_status = %s
        """, (pos_id, changed_at, prev_status, new_status))

        if cur.fetchone():
            # Evento já existe, apenas atualizar notes se necessário
            cur.execute("""
                UPDATE position_timeline
                SET notes = %s
                WHERE posicao_id = %s
                  AND changed_at = %s
                  AND previous_status = %s
                  AND new_status = %s
            """, (notes, pos_id, changed_at, prev_status, new_status))
            eventos_atualizados += 1
        else:
            # Inserir novo evento
            cur.execute("""
                INSERT INTO position_timeline
                (posicao_id, changed_at, previous_status, new_status, notes, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (pos_id, changed_at, prev_status, new_status, notes))
            eventos_novos += 1

    print(f"  OK - {eventos_novos} novos eventos inseridos")
    print(f"  OK - {eventos_atualizados} eventos atualizados")

    # Commit
    conn.commit()
    print("\n[6] Alterações gravadas com sucesso!")

    # Validação final
    print("\n" + "="*80)
    print("VALIDACAO FINAL")
    print("="*80)

    cur.execute("""
        SELECT
            p.status as status_bd,
            COUNT(pt.id) as total_eventos,
            MAX(pt.changed_at) as ultimo_evento
        FROM posicoes p
        LEFT JOIN position_timeline pt ON p.id = pt.posicao_id
        WHERE p.id = 1261
        GROUP BY p.status
    """)

    row = cur.fetchone()
    if row:
        status, total_eventos, ultimo_evento = row
        print(f"\nStatus: {status}")
        print(f"Total de eventos na timeline: {total_eventos}")
        print(f"Último evento: {ultimo_evento}")

    # Mostrar últimos eventos
    cur.execute("""
        SELECT changed_at, previous_status, new_status, notes
        FROM position_timeline
        WHERE posicao_id = (SELECT id FROM posicoes WHERE id = 1261)
        ORDER BY changed_at DESC
        LIMIT 5
    """)

    print("\nÚltimos 5 eventos da timeline:")
    for dt, prev, new, notes in cur.fetchall():
        notes_str = f" ({notes})" if notes else ""
        print(f"  {dt} | {prev:10s} -> {new:10s}{notes_str}")

    print("\n" + "="*80)
    print("SINCRONIZACAO CONCLUIDA COM SUCESSO!")
    print("="*80 + "\n")

except Exception as e:
    conn.rollback()
    print(f"\nERRO: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    cur.close()
    conn.close()
