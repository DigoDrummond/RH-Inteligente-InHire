import psycopg2
import sys

print("=" * 80)
print("APLICANDO MIGRATION 050 - CORRIGIR SLAs PARA DIAS UTEIS")
print("=" * 80)
print()

try:
    # Conectar ao banco
    print("1. Conectando ao banco de dados...")
    conn = psycopg2.connect(
        dbname="inhire",
        user="postgres",
        password="postgres",
        host="localhost"
    )
    conn.autocommit = False
    cur = conn.cursor()
    print("   [OK] Conectado")
    print()

    # Ler o arquivo da migration
    print("2. Lendo migration 050...")
    migration_file = "migrations/050_fix_sla_calculations_business_days.sql"

    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print(f"   [OK] Arquivo lido ({len(sql_content)} caracteres)")
    print()

    # Executar a migration
    print("3. Executando migration...")
    print("   - Recriando view vw_analise_posicoes...")
    print("   - Corrigindo calculos de SLA para dias uteis...")
    print("   - Isto pode levar alguns segundos...")
    print()

    cur.execute(sql_content)

    print("   [OK] Migration executada")
    print()

    # Commit
    print("4. Confirmando alteracoes...")
    conn.commit()
    print("   [OK] Commit realizado")
    print()

    # Verificar resultado
    print("5. Verificando resultado...")
    print()

    # Testar um exemplo de SLA
    cur.execute("""
        SELECT
            id_position,
            cargo,
            data_publicacao,
            data_encerramento_ou_atualizacao,
            sla_geral,
            sla_pendencia_cliente,
            sla_recrutamento,
            indicador_prazo
        FROM vw_analise_posicoes
        WHERE sla_recrutamento IS NOT NULL
        ORDER BY id_position DESC
        LIMIT 3
    """)

    print("   Exemplo de posicoes com SLAs calculados (dias uteis):")
    print()
    print(f"   {'ID':<6} {'Pub':<12} {'Enc':<12} {'SLA Geral':>10} {'SLA Pend':>10} {'SLA Recr':>10} {'Prazo'}")
    print("   " + "-" * 75)

    for row in cur.fetchall():
        id_pos, cargo, data_pub, data_enc, sla_g, sla_p, sla_r, prazo = row
        print(f"   {id_pos:<6} {str(data_pub):<12} {str(data_enc):<12} {sla_g or 0:>10} {sla_p or 0:>10} {sla_r or 0:>10} {prazo}")

    # Estatísticas
    print()
    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(sla_geral) as com_sla_geral,
            COUNT(sla_recrutamento) as com_sla_recr,
            ROUND(AVG(sla_geral)::numeric, 1) as media_sla_geral,
            ROUND(AVG(sla_recrutamento)::numeric, 1) as media_sla_recr
        FROM vw_analise_posicoes
    """)

    total, com_g, com_r, avg_g, avg_r = cur.fetchone()
    print(f"   Total de posicoes: {total}")
    print(f"   Com SLA Geral: {com_g} ({100*com_g/total if total > 0 else 0:.1f}%)")
    print(f"   Com SLA Recrutamento: {com_r} ({100*com_r/total if total > 0 else 0:.1f}%)")
    print(f"   Media SLA Geral: {avg_g} dias uteis")
    print(f"   Media SLA Recrutamento: {avg_r} dias uteis")

    print()
    print("=" * 80)
    print("[OK] MIGRATION 050 APLICADA COM SUCESSO!")
    print("=" * 80)
    print()
    print("SLAs agora usam DIAS UTEIS:")
    print("  - SLA Geral = data_encerramento - data_abertura (dias uteis)")
    print("  - SLA Pendencia Cliente = soma de periodos de pausa (dias uteis)")
    print("  - SLA Recrutamento = SLA Geral - SLA Pendencia Cliente")
    print()
    print("Exclui: sabados, domingos e feriados (tabela 'feriados')")
    print()

    cur.close()
    conn.close()

except FileNotFoundError:
    print(f"[ERRO] Arquivo de migration nao encontrado: {migration_file}")
    sys.exit(1)

except psycopg2.Error as e:
    print(f"[ERRO] Erro no banco de dados: {e}")
    if conn:
        conn.rollback()
        print("   Rollback realizado")
    sys.exit(1)

except Exception as e:
    print(f"[ERRO] Erro inesperado: {e}")
    if conn:
        conn.rollback()
        print("   Rollback realizado")
    sys.exit(1)
