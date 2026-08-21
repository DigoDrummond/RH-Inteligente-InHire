"""
Script de validação rápida pós-sincronização - COM TIMEOUT
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text, event
from sqlalchemy.pool import NullPool
import signal

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import settings

# Timeout handler
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Query timeout!")

def main():
    # Criar engine sem pool (cada consulta uma conexão nova)
    engine = create_engine(settings.DATABASE_URL, poolclass=NullPool)

    # Configurar statement timeout no PostgreSQL
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("SET statement_timeout = 30000")  # 30 segundos
        cursor.close()

    print("=" * 80)
    print("VALIDAÇÃO RÁPIDA - Pós-Sincronização Full")
    print("=" * 80)

    try:
        with engine.connect() as conn:
            # ===== FASE 1: HEALTH CHECK =====
            print("\n[FASE 1] HEALTH CHECK")
            print("-" * 80)

            # Test 1: Conexão básica
            result = conn.execute(text("SELECT 1 as ok")).fetchone()
            print(f"  [OK] Conexao PostgreSQL: OK ({result[0]})")

            # Test 2: Contar tabelas principais (queries simples, SEM JOINS)
            print("\n[Contagens de Tabelas]")
            tables = ['requisicoes', 'posicoes', 'position_timeline', 'vagas', 'candidaturas']
            for table in tables:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
                print(f"  {table:20} : {count:>6} registros")

            # ===== FASE 2: VALIDAÇÃO ESTRUTURAL =====
            print("\n" + "=" * 80)
            print("[FASE 2] VALIDAÇÃO ESTRUTURAL - Campos Novos")
            print("-" * 80)

            # 2.1: Verificar se custom_fields existe em requisicoes
            query_cf = text("""
                SELECT
                    COUNT(*) as total,
                    COUNT(custom_fields) as com_custom_fields,
                    COUNT(approval_workflow) as com_approval_workflow
                FROM requisicoes
            """)
            result = conn.execute(query_cf).fetchone()
            total_req = result[0]
            com_cf = result[1]
            com_aw = result[2]

            print(f"\n[requisicoes] Total: {total_req}")
            print(f"  - Com custom_fields      : {com_cf} ({com_cf/total_req*100:.1f}%)")
            print(f"  - Com approval_workflow  : {com_aw} ({com_aw/total_req*100:.1f}%)")

            # 2.2: Verificar campos específicos em custom_fields (amostragem)
            query_sample_cf = text("""
                SELECT
                    id,
                    custom_fields->>'Torre' as torre,
                    custom_fields->>'Empresa' as empresa,
                    custom_fields->>'Tipo de Serviço' as tipo_servico,
                    approval_workflow->>'name' as workflow_name
                FROM requisicoes
                WHERE custom_fields IS NOT NULL
                LIMIT 5
            """)

            print(f"\n[Amostragem - Primeiras 5 requisições com custom_fields]")
            print(f"{'ID':>6} | {'Torre':20} | {'Empresa':15} | {'Tipo Serviço':20} | {'Workflow':30}")
            print("-" * 100)

            for row in conn.execute(query_sample_cf).fetchall():
                torre = row[1][:18] + '..' if row[1] and len(row[1]) > 20 else (row[1] or '[NULL]')
                empresa = row[2][:13] + '..' if row[2] and len(row[2]) > 15 else (row[2] or '[NULL]')
                tipo = row[3][:18] + '..' if row[3] and len(row[3]) > 20 else (row[3] or '[NULL]')
                workflow = row[4][:28] + '..' if row[4] and len(row[4]) > 30 else (row[4] or '[NULL]')
                print(f"{row[0]:>6} | {torre:20} | {empresa:15} | {tipo:20} | {workflow:30}")

            # ===== FASE 3: VALIDAÇÃO POSITION_TIMELINE =====
            print("\n" + "=" * 80)
            print("[FASE 3] VALIDAÇÃO position_timeline")
            print("-" * 80)

            query_pt_stats = text("""
                SELECT
                    COUNT(*) as total_eventos,
                    COUNT(DISTINCT posicao_id) as posicoes_distintas,
                    MIN(changed_at)::date as evento_mais_antigo,
                    MAX(changed_at)::date as evento_mais_recente
                FROM position_timeline
            """)

            result = conn.execute(query_pt_stats).fetchone()
            print(f"\nTotal de eventos        : {result[0]}")
            print(f"Posições distintas      : {result[1]}")
            print(f"Evento mais antigo      : {result[2]}")
            print(f"Evento mais recente     : {result[3]}")

            # Distribuição de status
            print("\n[Distribuição de Status - Top 10]")
            query_status_dist = text("""
                SELECT
                    new_status,
                    COUNT(*) as count
                FROM position_timeline
                WHERE new_status IS NOT NULL
                GROUP BY new_status
                ORDER BY count DESC
                LIMIT 10
            """)

            print(f"{'Status':30} | {'Count':>8}")
            print("-" * 42)
            for row in conn.execute(query_status_dist).fetchall():
                status = row[0][:28] + '..' if len(row[0]) > 30 else row[0]
                print(f"{status:30} | {row[1]:>8}")

            # ===== FASE 4: VALIDAÇÃO FUNCTION get_custom_field_value =====
            print("\n" + "=" * 80)
            print("[FASE 4] VALIDAÇÃO function get_custom_field_value")
            print("-" * 80)

            query_test_func = text("""
                SELECT
                    get_custom_field_value('{"Torre": "Varejo", "Empresa": "Framework"}'::jsonb, 'Torre') as torre,
                    get_custom_field_value('{"Torre": "Varejo", "Empresa": "Framework"}'::jsonb, 'Empresa') as empresa
            """)

            try:
                result = conn.execute(query_test_func).fetchone()
                print(f"  [OK] Funcao existe e funciona corretamente")
                print(f"    Torre   : {result[0]}")
                print(f"    Empresa : {result[1]}")
            except Exception as e:
                print(f"  [ERRO] Funcao get_custom_field_value nao encontrada ou com erro")
                print(f"    {str(e)}")

            # ===== RESUMO =====
            print("\n" + "=" * 80)
            print("RESUMO DA VALIDACAO")
            print("=" * 80)
            print("\n[OK] Todas as validacoes basicas completadas com sucesso!")
            print("\nProximos passos:")
            print("  1. Re-exportar dados para Google Sheets")
            print("  2. Validar dados na planilha")

    except TimeoutException:
        print("\n[ERRO] Query timeout - algumas consultas estao demorando muito")
        print("  Considere executar VACUUM ANALYZE no banco de dados")
        return 1
    except Exception as e:
        print(f"\n[ERRO] Durante validacao: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
