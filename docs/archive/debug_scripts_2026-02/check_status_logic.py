"""
Script para investigar a lógica de status e datas de encerramento
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from config import settings

def main():
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        # 1. Status possíveis e suas contagens
        print("=" * 80)
        print("STATUS POSSÍVEIS NAS POSIÇÕES")
        print("=" * 80)

        query_status = text("""
            SELECT
                COALESCE(usp.new_status, p.status) as status_atual,
                COUNT(*) as total,
                COUNT(p.hired_at) as com_hired_at,
                COUNT(usp.data_ultima_mudanca) as com_data_ultima_mudanca
            FROM posicoes p
            LEFT JOIN (
                SELECT DISTINCT ON (posicao_id)
                    posicao_id,
                    new_status,
                    changed_at AS data_ultima_mudanca
                FROM position_timeline
                ORDER BY posicao_id, changed_at DESC
            ) usp ON usp.posicao_id = p.id
            GROUP BY COALESCE(usp.new_status, p.status)
            ORDER BY total DESC
        """)

        result = conn.execute(query_status).fetchall()
        print(f"\n{'Status':<15} {'Total':>8} {'c/ hired_at':>12} {'c/ última mudança':>18}")
        print("-" * 80)
        for row in result:
            print(f"{row[0]:<15} {row[1]:>8} {row[2]:>12} {row[3]:>18}")

        # 2. Exemplos de cada status
        print("\n" + "=" * 80)
        print("EXEMPLOS DE CADA STATUS (position 1714 como referência)")
        print("=" * 80)

        query_examples = text("""
            SELECT
                p.id,
                p.vaga_id,
                v.name as vaga_nome,
                COALESCE(usp.new_status, p.status) as status_atual,
                p.opened_at,
                p.hired_at,
                p.approved_at,
                usp.data_ultima_mudanca,
                v.sla_days_goal,
                CASE
                    WHEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) >= DATE(p.opened_at)
                    THEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at))
                    ELSE NULL
                END AS data_encerramento_atual
            FROM posicoes p
            JOIN vagas v ON p.vaga_id = v.id
            LEFT JOIN (
                SELECT DISTINCT ON (posicao_id)
                    posicao_id,
                    new_status,
                    changed_at AS data_ultima_mudanca
                FROM position_timeline
                ORDER BY posicao_id, changed_at DESC
            ) usp ON usp.posicao_id = p.id
            WHERE p.id = 1714 OR p.vaga_id = 1202
            ORDER BY p.id
            LIMIT 10
        """)

        result = conn.execute(query_examples).fetchall()
        for row in result:
            print(f"\nPosition ID: {row[0]}")
            print(f"  Vaga: {row[2][:60]}")
            print(f"  Status Atual: {row[3]}")
            print(f"  Opened At: {row[4]}")
            print(f"  Hired At: {row[5] if row[5] else '[NULL]'}")
            print(f"  Approved At: {row[6] if row[6] else '[NULL]'}")
            print(f"  Última Mudança (position_timeline): {row[7] if row[7] else '[NULL]'}")
            print(f"  SLA Days Goal: {row[8]}")
            print(f"  Data Encerramento (lógica atual): {row[9] if row[9] else '[NULL]'}")

        # 3. Campos de data disponíveis em posicoes
        print("\n" + "=" * 80)
        print("CAMPOS DE DATA DISPONÍVEIS NA TABELA POSICOES")
        print("=" * 80)

        query_dates = text("""
            SELECT
                COUNT(*) as total,
                COUNT(opened_at) as com_opened_at,
                COUNT(hired_at) as com_hired_at,
                COUNT(approved_at) as com_approved_at,
                COUNT(created_at) as com_created_at,
                COUNT(updated_at) as com_updated_at
            FROM posicoes
        """)

        result = conn.execute(query_dates).fetchone()
        if result:
            print(f"\nTotal posições: {result[0]}")
            print(f"  com opened_at: {result[1]} ({result[1]/result[0]*100:.1f}%)")
            print(f"  com hired_at: {result[2]} ({result[2]/result[0]*100:.1f}%)")
            print(f"  com approved_at: {result[3]} ({result[3]/result[0]*100:.1f}%)")
            print(f"  com created_at: {result[4]} ({result[4]/result[0]*100:.1f}%)")
            print(f"  com updated_at: {result[5]} ({result[5]/result[0]*100:.1f}%)")

        # 4. Analisar position 1714 especificamente
        print("\n" + "=" * 80)
        print("ANÁLISE DETALHADA - POSITION 1714")
        print("=" * 80)

        query_1714 = text("""
            SELECT
                p.id,
                p.status,
                p.opened_at,
                p.hired_at,
                p.approved_at,
                p.created_at,
                p.updated_at,
                v.sla_days_goal
            FROM posicoes p
            JOIN vagas v ON p.vaga_id = v.id
            WHERE p.id = 1714
        """)

        result = conn.execute(query_1714).fetchone()
        if result:
            print(f"\nPosition ID: {result[0]}")
            print(f"Status (campo p.status): {result[1]}")
            print(f"Opened At: {result[2]}")
            print(f"Hired At: {result[3] if result[3] else '[NULL]'}")
            print(f"Approved At: {result[4] if result[4] else '[NULL]'}")
            print(f"Created At: {result[5]}")
            print(f"Updated At: {result[6]}")
            print(f"SLA Days Goal: {result[7]}")

        # 5. Verificar position_timeline para position 1714
        print("\n" + "=" * 80)
        print("HISTÓRICO DE STATUS - POSITION 1714 (position_timeline)")
        print("=" * 80)

        query_timeline = text("""
            SELECT
                changed_at,
                previous_status,
                new_status,
                notes
            FROM position_timeline
            WHERE posicao_id = 1714
            ORDER BY changed_at DESC
            LIMIT 10
        """)

        result = conn.execute(query_timeline).fetchall()
        if result:
            for row in result:
                print(f"\n{row[0]}: {row[1] or '[NULL]'} → {row[2]}")
                if row[3]:
                    print(f"  Notes: {row[3][:100]}")
        else:
            print("\n[!] Nenhum evento no position_timeline para esta posição")

        # 6. Lógica atual do indicador_prazo
        print("\n" + "=" * 80)
        print("LÓGICA ATUAL DO INDICADOR_PRAZO (na view)")
        print("=" * 80)

        query_indicador = text("""
            SELECT
                id_position,
                cargo,
                status_atual,
                prazo_processo_seletivo,
                data_publicacao,
                data_encerramento_ou_atualizacao,
                indicador_prazo
            FROM vw_analise_posicoes
            WHERE id_position = 1714
        """)

        result = conn.execute(query_indicador).fetchone()
        if result:
            print(f"\nPosition: {result[0]} - {result[1][:50]}")
            print(f"Status: {result[2]}")
            print(f"Prazo (SLA): {result[3]} dias")
            print(f"Data Publicação: {result[4]}")
            print(f"Data Encerramento (campo na view): {result[5] if result[5] else '[NULL]'}")
            print(f"Indicador Prazo: {result[6]}")

            print("\n[Análise]")
            if result[6] == 'Sem Meta Definida':
                print("  Indicador = 'Sem Meta Definida'")
                print("  Motivo: hired_at IS NULL na lógica atual")
                print(f"  Mas SLA está definido: {result[3]} dias")
                print("\n  PROBLEMA IDENTIFICADO:")
                print("  - Posição está OPEN há vários dias")
                print("  - Deveria calcular SLA usando data atual")
                print("  - Assim seria possível ver se está 'Dentro do Prazo' ou 'Fora do Prazo'")

        print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
