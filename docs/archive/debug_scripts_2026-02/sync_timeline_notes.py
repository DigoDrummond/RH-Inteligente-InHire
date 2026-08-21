"""
Script focado para re-sincronizar o campo 'notes' (Motivo) na position_timeline.

Problema resolvido: api_client.py usava 'elif' causando 'history[].comments'
ser ignorado quando 'statusHistory' tambem existia. Corrigido para 'if'.

Este script percorre todas as vagas e re-sincroniza os eventos de timeline,
enriquecendo registros existentes com o campo 'notes' onde disponivel.
"""
import sys
import time
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Suprimir logs para output limpo
logging.disable(logging.WARNING)

from config import settings
from services.api_client import InhireAPIClient
from services.database_service import DatabaseService


def sync_vaga_timeline(vaga_inhire_id: str, vaga_db_id: int) -> dict:
    """
    Sincroniza timeline de uma vaga. Retorna estatisticas.
    Cada thread usa sua propria sessao de banco.
    """
    engine = create_engine(settings.DATABASE_URL, poolclass=NullPool)
    SessionLocal = sessionmaker(bind=engine)

    stats = {'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0, 'with_notes': 0}

    try:
        client = InhireAPIClient()
        events = list(client.get_position_timeline_by_job(vaga_inhire_id))

        if not events:
            return stats

        with SessionLocal() as session:
            db = DatabaseService(session)
            for ev in events:
                try:
                    _, op = db.upsert_position_timeline(ev, commit=True)
                    stats[op] = stats.get(op, 0) + 1
                    if ev.notes:
                        stats['with_notes'] += 1
                except Exception:
                    stats['errors'] += 1

    except Exception:
        stats['errors'] += 1
    finally:
        engine.dispose()

    return stats


def main():
    print("=" * 70)
    print("SYNC TIMELINE NOTES - Re-sincronizacao do campo 'notes' (Motivo)")
    print("=" * 70)

    # Buscar todas as vagas do banco
    engine = create_engine(settings.DATABASE_URL, poolclass=NullPool)
    with engine.connect() as conn:
        conn.execute(text("SET statement_timeout = 30000"))
        rows = conn.execute(text(
            "SELECT id, inhire_id FROM vagas ORDER BY id"
        )).fetchall()
    engine.dispose()

    total_vagas = len(rows)
    print(f"\nTotal de vagas a processar: {total_vagas}")
    print(f"Workers paralelos: 5")
    print(f"Inicio: {time.strftime('%H:%M:%S')}\n")

    # Estatisticas globais
    total_created = 0
    total_updated = 0
    total_skipped = 0
    total_errors = 0
    total_with_notes = 0
    vagas_processed = 0

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_vaga = {
            executor.submit(sync_vaga_timeline, row[1], row[0]): row
            for row in rows
        }

        for future in as_completed(future_to_vaga):
            row = future_to_vaga[future]
            vagas_processed += 1

            try:
                stats = future.result()
                total_created += stats.get('created', 0)
                total_updated += stats.get('updated', 0)
                total_skipped += stats.get('skipped', 0)
                total_errors += stats.get('errors', 0)
                total_with_notes += stats.get('with_notes', 0)
            except Exception as e:
                total_errors += 1

            # Progress a cada 50 vagas
            if vagas_processed % 50 == 0 or vagas_processed == total_vagas:
                elapsed = time.time() - start_time
                pct = vagas_processed / total_vagas * 100
                rate = vagas_processed / elapsed if elapsed > 0 else 0
                eta = (total_vagas - vagas_processed) / rate if rate > 0 else 0
                print(
                    f"  [{vagas_processed:4}/{total_vagas}] {pct:5.1f}% | "
                    f"created={total_created} updated={total_updated} "
                    f"notes={total_with_notes} | "
                    f"ETA: {eta/60:.1f}min"
                )

    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)
    print(f"  Vagas processadas : {vagas_processed}")
    print(f"  Eventos criados   : {total_created}")
    print(f"  Eventos atualizados (com notes): {total_updated}")
    print(f"  Eventos ignorados : {total_skipped}")
    print(f"  Erros             : {total_errors}")
    print(f"  Tempo total       : {elapsed/60:.1f} minutos")

    # Verificar no banco quantos eventos tem notes
    engine = create_engine(settings.DATABASE_URL, poolclass=NullPool)
    with engine.connect() as conn:
        conn.execute(text("SET statement_timeout = 30000"))
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(notes) as com_notes,
                COUNT(DISTINCT notes) as valores_distintos
            FROM position_timeline
        """)).fetchone()

        if result:
            total = result[0]
            com_notes = result[1]
            distintos = result[2]
            print(f"\n[Banco] position_timeline:")
            print(f"  Total eventos     : {total}")
            print(f"  Com notes (Motivo): {com_notes} ({com_notes/total*100:.1f}%)")
            print(f"  Valores distintos : {distintos}")

        # Mostrar valores distintos de notes
        if com_notes > 0:
            rows_notes = conn.execute(text("""
                SELECT notes, COUNT(*) as count
                FROM position_timeline
                WHERE notes IS NOT NULL
                GROUP BY notes
                ORDER BY count DESC
                LIMIT 20
            """)).fetchall()

            print(f"\n[Valores de notes encontrados]")
            print(f"  {'Codigo (notes)':<40} {'Count':>8}")
            print("  " + "-" * 50)
            for r in rows_notes:
                print(f"  {r[0]:<40} {r[1]:>8}")

    engine.dispose()

    print("\n" + "=" * 70)
    print("[OK] Sincronizacao de notes concluida!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
