"""
Script para investigar position 1714 - Engenheiro de Dados Especialista
Verifica os campos: torre, empresa, tipo_posicao, indicador_prazo
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
        # 1. Dados da view
        print("=" * 80)
        print("DADOS DA VIEW vw_analise_posicoes (Position 1714)")
        print("=" * 80)

        query_view = text("""
            SELECT
                id_position,
                cargo,
                torre,
                empresa,
                tipo_posicao,
                prazo_processo_seletivo,
                indicador_prazo,
                status_atual,
                data_publicacao,
                data_encerramento_ou_atualizacao
            FROM vw_analise_posicoes
            WHERE id_position = 1714
        """)

        result = conn.execute(query_view).fetchone()
        if result:
            print(f"\nID Position: {result[0]}")
            print(f"Cargo: {result[1]}")
            print(f"Torre: {result[2] if result[2] else '[NULL]'}")
            print(f"Empresa: {result[3] if result[3] else '[NULL]'}")
            print(f"Tipo Posição: {result[4] if result[4] else '[NULL]'}")
            print(f"Prazo Processo Seletivo: {result[5]}")
            print(f"Indicador Prazo: {result[6]}")
            print(f"Status Atual: {result[7]}")
            print(f"Data Publicação: {result[8]}")
            print(f"Data Encerramento: {result[9]}")

        # 2. Dados da tabela posicoes + vagas
        print("\n" + "=" * 80)
        print("DADOS BRUTOS - POSICOES + VAGAS")
        print("=" * 80)

        query_raw = text("""
            SELECT
                p.id,
                p.vaga_id,
                p.status,
                p.hired_at,
                v.name as vaga_nome,
                v.inhire_id as vaga_inhire_id,
                v.sla_days_goal,
                v.custom_fields->>'Torre' as torre_vaga,
                v.custom_fields->>'Senioridade' as senioridade_vaga
            FROM posicoes p
            JOIN vagas v ON p.vaga_id = v.id
            WHERE p.id = 1714
        """)

        result = conn.execute(query_raw).fetchone()
        if result:
            print(f"\nPosition ID: {result[0]}")
            print(f"Vaga ID: {result[1]}")
            print(f"Status: {result[2]}")
            print(f"Hired At: {result[3]}")
            print(f"Vaga Nome: {result[4]}")
            print(f"Vaga InHire ID: {result[5]}")
            print(f"SLA Days Goal: {result[6]}")
            print(f"Torre (vagas.custom_fields): {result[7] if result[7] else '[NULL]'}")
            print(f"Senioridade (vagas.custom_fields): {result[8] if result[8] else '[NULL]'}")

            vaga_inhire_id = result[5]

        # 3. Dados da tabela requisicoes
        print("\n" + "=" * 80)
        print("DADOS BRUTOS - REQUISICOES")
        print("=" * 80)

        query_req = text("""
            SELECT
                r.id,
                r.job_inhire_id,
                r.user_name,
                r.custom_fields
            FROM requisicoes r
            WHERE r.job_inhire_id = :vaga_id
        """)

        result = conn.execute(query_req, {'vaga_id': vaga_inhire_id}).fetchone()
        if result:
            print(f"\nRequisição ID: {result[0]}")
            print(f"Job InHire ID: {result[1]}")
            print(f"User Name: {result[2]}")
            print(f"\nCustom Fields (JSONB):")

            custom_fields = result[3] or {}

            # Campos específicos que estamos procurando
            campos_interesse = [
                'Email do responsável por parte do cliente',
                'Modalidade de Contratação',
                'Time Rethink',
                'Tipo de Posição',
                'Tipo de Serviço'
            ]

            for campo in campos_interesse:
                valor = custom_fields.get(campo)
                print(f"  - {campo}: {valor if valor else '[NULL]'}")

            print(f"\n  Total de custom fields: {len(custom_fields)}")

            if len(custom_fields) > 0:
                print(f"\n  Todos os custom fields disponíveis:")
                for key in sorted(custom_fields.keys()):
                    print(f"    - {key}: {custom_fields[key]}")
        else:
            print("\n[!] Nenhuma requisição encontrada para esta vaga!")
            print(f"    Vaga InHire ID: {vaga_inhire_id}")

        # 4. Estatísticas gerais
        print("\n" + "=" * 80)
        print("ESTATÍSTICAS GERAIS DA VIEW")
        print("=" * 80)

        query_stats = text("""
            SELECT
                COUNT(*) as total,
                COUNT(torre) as torre_preenchido,
                COUNT(empresa) as empresa_preenchido,
                COUNT(tipo_posicao) as tipo_posicao_preenchido,
                COUNT(*) FILTER (WHERE indicador_prazo != 'Sem Meta Definida') as indicador_prazo_calculado
            FROM vw_analise_posicoes
        """)

        result = conn.execute(query_stats).fetchone()
        if result:
            total = result[0]
            print(f"\nTotal de posições: {total}")
            print(f"Torre preenchido: {result[1]} ({result[1]/total*100:.1f}%)")
            print(f"Empresa preenchido: {result[2]} ({result[2]/total*100:.1f}%)")
            print(f"Tipo Posição preenchido: {result[3]} ({result[3]/total*100:.1f}%)")
            print(f"Indicador Prazo calculado: {result[4]} ({result[4]/total*100:.1f}%)")

        print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
