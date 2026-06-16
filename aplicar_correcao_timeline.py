"""Aplica correções na timeline das 7 posições problemáticas"""
import psycopg2

# Conectar ao banco
conn = psycopg2.connect(
    host='localhost',
    database='inhire',
    user='postgres',
    password='postgres'
)

cur = conn.cursor()

print("\n" + "="*80)
print("CORRECAO DE TIMELINE - 7 POSICOES")
print("="*80)

try:
    # ETAPA 1: Remover Duplicados
    print("\n[ETAPA 1] Removendo eventos duplicados...")

    cur.execute("""
        DELETE FROM position_timeline
        WHERE id IN (
            SELECT id
            FROM (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY posicao_id, changed_at, previous_status, new_status
                        ORDER BY id
                    ) as rn
                FROM position_timeline
                WHERE posicao_id IN (
                    SELECT id FROM posicoes
                    WHERE id IN (1303, 1264, 120, 425, 1308, 759, 1261)
                )
            ) t
            WHERE t.rn > 1
        )
    """)

    duplicados_removidos = cur.rowcount
    print(f"  OK - {duplicados_removidos} eventos duplicados removidos")

    # ETAPA 2: Inverter Status
    print("\n[ETAPA 2] Invertendo previous_status <-> new_status...")

    cur.execute("""
        UPDATE position_timeline
        SET
            previous_status = new_status,
            new_status = previous_status
        WHERE posicao_id IN (
            SELECT id FROM posicoes
            WHERE id IN (1303, 1264, 120, 425, 1308, 759, 1261)
        )
    """)

    registros_atualizados = cur.rowcount
    print(f"  OK - {registros_atualizados} eventos atualizados")

    # Commit
    conn.commit()
    print("\n[COMMIT] Alteracoes gravadas com sucesso!")

    # VALIDACAO
    print("\n" + "="*80)
    print("VALIDACAO")
    print("="*80)

    # Verificar duplicados
    cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT
                posicao_id,
                changed_at,
                previous_status,
                new_status,
                COUNT(*) as total
            FROM position_timeline
            WHERE posicao_id IN (
                SELECT id FROM posicoes
                WHERE id IN (1303, 1264, 120, 425, 1308, 759, 1261)
            )
            GROUP BY posicao_id, changed_at, previous_status, new_status
            HAVING COUNT(*) > 1
        ) t
    """)

    duplicados = cur.fetchone()[0]
    print(f"\nDuplicados restantes: {duplicados}")
    if duplicados == 0:
        print("  OK - Nenhum duplicado encontrado!")
    else:
        print("  ALERTA - Ainda ha duplicados!")

    # Verificar consistência
    print("\nConsistencia (status BD vs timeline):")
    cur.execute("""
        SELECT DISTINCT ON (pt.posicao_id)
            pt.posicao_id,
            p.status as status_bd,
            pt.new_status as status_timeline
        FROM position_timeline pt
        JOIN posicoes p ON pt.posicao_id = p.id
        WHERE p.id IN (1303, 1264, 120, 425, 1308, 759, 1261)
        ORDER BY pt.posicao_id, pt.changed_at DESC
    """)

    inconsistencias = 0
    for pos_id, status_bd, status_timeline in cur.fetchall():
        if status_bd != status_timeline:
            print(f"  Pos {pos_id}: BD={status_bd}, Timeline={status_timeline} - INCONSISTENTE!")
            inconsistencias += 1
        else:
            print(f"  Pos {pos_id}: {status_bd} - OK")

    if inconsistencias == 0:
        print("\n  OK - Todas as posicoes consistentes!")
    else:
        print(f"\n  ALERTA - {inconsistencias} inconsistencias encontradas!")

    # Mostrar resultado final
    print("\n" + "="*80)
    print("RESULTADO FINAL")
    print("="*80)

    cur.execute("""
        SELECT
            p.id as posicao_id,
            v.name as vaga_nome,
            p.status as status_atual,
            pt.changed_at as ultimo_evento,
            pt.previous_status || ' -> ' || pt.new_status as transicao
        FROM posicoes p
        JOIN vagas v ON p.vaga_id = v.id
        JOIN LATERAL (
            SELECT changed_at, previous_status, new_status
            FROM position_timeline
            WHERE posicao_id = p.id
            ORDER BY changed_at DESC
            LIMIT 1
        ) pt ON true
        WHERE p.id IN (1303, 1264, 120, 425, 1308, 759, 1261)
        ORDER BY p.id
    """)

    print()
    for pos_id, vaga, status, dt, transicao in cur.fetchall():
        print(f"Pos {pos_id:4d} | {vaga[:40]:40s} | {status:10s} | {transicao}")

    print("\n" + "="*80)
    print("CORRECAO CONCLUIDA COM SUCESSO!")
    print("="*80 + "\n")

except Exception as e:
    conn.rollback()
    print(f"\nERRO: {str(e)}")
    print("\n[ROLLBACK] Alteracoes desfeitas")
    raise
finally:
    cur.close()
    conn.close()
