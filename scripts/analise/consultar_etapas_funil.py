"""
Script para consultar as etapas do funil existentes no banco
"""
import psycopg2
from config import settings


def main():
    """Consulta as etapas do funil"""
    conn = psycopg2.connect(
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT
    )

    cur = conn.cursor()

    print("=" * 80)
    print("ETAPAS DO FUNIL (STAGE_NAME)")
    print("=" * 80)

    # Etapas únicas com contagem
    cur.execute("""
        SELECT
            stage_name,
            stage_order,
            COUNT(*) as total_candidaturas,
            COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as ativos,
            COUNT(CASE WHEN status = 'HIRED' THEN 1 END) as contratados,
            COUNT(CASE WHEN status = 'REJECTED' THEN 1 END) as reprovados
        FROM candidaturas
        WHERE stage_name IS NOT NULL
        GROUP BY stage_name, stage_order
        ORDER BY stage_order, total_candidaturas DESC
    """)

    print(f"\n{'ETAPA':<45} {'ORDEM':>6} {'TOTAL':>8} {'ATIVOS':>8} {'CONTRAT':>8} {'REPROV':>8}")
    print("-" * 95)

    results = cur.fetchall()
    for etapa, ordem, total, ativos, contratados, reprovados in results:
        print(f"{etapa:<45} {ordem:>6} {total:>8,} {ativos:>8,} {contratados:>8,} {reprovados:>8,}")

    print(f"\n{'TOTAL':>45} {'':>6} {sum([r[2] for r in results]):>8,}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
