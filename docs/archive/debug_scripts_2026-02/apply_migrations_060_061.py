"""
Script para aplicar migrations 060 e 061 - Tradução de motivo_status

Migration 060: Cria tabela motivo_status_traducao
Migration 061: Atualiza view para usar traduções
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from config import settings

def main():
    engine = create_engine(settings.DATABASE_URL, poolclass=NullPool, connect_args={'connect_timeout': 60})

    try:
        with engine.connect() as conn:
            # Set statement timeout (120 seconds)
            conn.execute(text("SET statement_timeout = 120000"))

            # ========================================
            # ETAPA 1: Criar tabela de tradução
            # ========================================
            print("=" * 80)
            print("ETAPA 1: Criando tabela de tradução (migration 060)")
            print("=" * 80)

            migration_060 = project_root / 'migrations' / '060_create_motivo_status_traducao.sql'
            sql_060 = migration_060.read_text(encoding='utf-8')

            print("\nAplicando migration 060...")
            conn.execute(text(sql_060))
            conn.commit()
            print("[OK] Migration 060 aplicada!")

            # Verificar tabela criada
            result = conn.execute(text("""
                SELECT COUNT(*) FROM motivo_status_traducao
            """)).fetchone()
            print(f"Total de traduções na tabela: {result[0]}")

            # ========================================
            # ETAPA 2: Atualizar view
            # ========================================
            print("\n" + "=" * 80)
            print("ETAPA 2: Atualizando view para usar traduções (migration 061)")
            print("=" * 80)

            migration_061 = project_root / 'migrations' / '061_update_view_use_traducao_motivo.sql'
            sql_061 = migration_061.read_text(encoding='utf-8')

            print("\nAplicando migration 061...")
            conn.execute(text(sql_061))
            conn.commit()
            print("[OK] Migration 061 aplicada!")

            # Verificar colunas da view
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.columns
                WHERE table_name = 'vw_analise_posicoes'
            """)).fetchone()
            print(f"Total de colunas na view: {result[0]}")

            # Verificar se motivo_status e motivo_status_codigo existem
            result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'vw_analise_posicoes'
                  AND column_name IN ('motivo_status', 'motivo_status_codigo')
                ORDER BY column_name
            """)).fetchall()

            if result:
                print("\n[OK] Colunas de motivo criadas:")
                for row in result:
                    print(f"     - {row[0]} ({row[1]})")
            else:
                print("\n[!] ERRO: Colunas de motivo não encontradas!")

            # ========================================
            # VALIDAÇÃO: Testar tradução
            # ========================================
            print("\n" + "=" * 80)
            print("VALIDAÇÃO: Testando tradução na posição 1428")
            print("=" * 80)

            result = conn.execute(text("""
                SELECT
                    id_position,
                    cargo,
                    status_atual,
                    motivo_status_codigo,
                    motivo_status
                FROM vw_analise_posicoes
                WHERE id_position = 1428
            """)).fetchone()

            if result:
                print(f"\nPosição ID: {result[0]}")
                print(f"Cargo: {result[1]}")
                print(f"Status: {result[2]}")
                print(f"Motivo (código): {result[3]}")
                print(f"Motivo (traduzido): {result[4]}")

                if result[3] == 'waiting_schedule' and result[4] != 'waiting_schedule':
                    print("\n✅ [OK] Tradução funcionando! Código traduzido com sucesso.")
                elif result[3] == 'waiting_schedule' and result[4] == 'waiting_schedule':
                    print("\n⚠️  [AVISO] Tradução não aplicada. Verificar tabela de tradução.")
                else:
                    print(f"\n[INFO] Motivo atual: {result[3]}")
            else:
                print("\n[!] Posição 1428 não encontrada na view")

            # ========================================
            # ESTATÍSTICAS
            # ========================================
            print("\n" + "=" * 80)
            print("ESTATÍSTICAS")
            print("=" * 80)

            # Total com/sem tradução
            result = conn.execute(text("""
                SELECT
                    COUNT(*) FILTER (WHERE motivo_status_codigo IS NOT NULL) as com_motivo,
                    COUNT(*) FILTER (WHERE motivo_status_codigo IS NOT NULL
                                     AND motivo_status != motivo_status_codigo) as traduzido,
                    COUNT(*) FILTER (WHERE motivo_status_codigo IS NOT NULL
                                     AND motivo_status = motivo_status_codigo) as sem_traducao
                FROM vw_analise_posicoes
            """)).fetchone()

            print(f"\nPosições com motivo_status: {result[0]}")
            print(f"  - Traduzidas: {result[1]} ({result[1]/result[0]*100:.1f}%)")
            print(f"  - Sem tradução: {result[2]} ({result[2]/result[0]*100:.1f}%)")

            print("\n" + "=" * 80)
            print("[OK] MIGRATIONS 060 e 061 APLICADAS COM SUCESSO!")
            print("=" * 80)

            print("\n📝 PRÓXIMOS PASSOS:")
            print("  1. Verificar se a tradução de 'waiting_schedule' está aparecendo")
            print("  2. Adicionar mais traduções conforme necessário usando:")
            print("     INSERT INTO motivo_status_traducao (codigo, descricao_pt, categoria)")
            print("     VALUES ('novo_codigo', 'Descrição em português', 'categoria');")
            print("  3. Exportar para Google Sheets para validação")

    except Exception as e:
        print(f"\n[ERRO] Falha ao aplicar migrations: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        engine.dispose()

    return 0

if __name__ == "__main__":
    sys.exit(main())
