#!/usr/bin/env python3
"""
Script de Limpeza: Remover Duplicatas de position_timeline

Objetivo:
    Remover eventos duplicados na tabela position_timeline criados pelo bug
    de processamento dual de statusHistory + history.

Problema:
    - Cada mudança de status cria 2 eventos: um COM notes, outro SEM notes
    - Mesma data, mesmo status, mesma posição
    - 85 posições afetadas com ~170 eventos duplicados

Solução:
    - Identificar duplicatas: (posicao_id, DATE(changed_at), new_status)
    - Manter evento COM notes (se existir)
    - Deletar evento SEM notes
    - Se ambos têm notes, manter o com mais informação

Data: 2026-03-20
Autor: Sistema de Sincronização Inhire
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings
from utils.logger import get_logger
import json

logger = get_logger(__name__)


def print_banner():
    """Exibe banner informativo"""
    print()
    print("=" * 80)
    print("LIMPEZA: Remover Duplicatas de position_timeline")
    print("=" * 80)
    print()
    print("Este script remove eventos duplicados na tabela position_timeline.")
    print()
    print("PROBLEMA:")
    print("  - Cada status change criava 2 eventos (statusHistory + history)")
    print("  - Um evento COM notes, outro SEM notes")
    print("  - ~170 eventos duplicados nas 85 posições afetadas")
    print()
    print("SOLUÇÃO:")
    print("  - Identificar duplicatas: mesmo (posicao_id, date, status)")
    print("  - Manter evento COM notes")
    print("  - Deletar evento SEM notes")
    print()
    print("SEGURANÇA:")
    print("  - Operação dentro de transação (rollback se erro)")
    print("  - Backup automático dos eventos deletados")
    print("  - Log detalhado de todas as operações")
    print()
    print("=" * 80)
    print()


def find_duplicates(session, position_ids=None):
    """
    Identifica eventos duplicados na position_timeline

    Args:
        session: SQLAlchemy session
        position_ids: Lista de IDs de posições (None = todas)

    Returns:
        Lista de dicts com informações das duplicatas
    """
    logger.info("Identificando duplicatas...")

    # Query para encontrar duplicatas
    query = text("""
        WITH duplicates AS (
            SELECT
                posicao_id,
                DATE(changed_at) as event_date,
                new_status,
                COUNT(*) as dup_count,
                json_agg(
                    json_build_object(
                        'id', id,
                        'inhire_id', inhire_id,
                        'notes', notes,
                        'reason', reason,
                        'changed_at', changed_at,
                        'created_at', created_at,
                        'changed_by_name', changed_by_name
                    )
                    ORDER BY
                        -- Prioridade: 1) COM notes, 2) Mais antigo
                        CASE WHEN notes IS NOT NULL AND notes != '' THEN 0 ELSE 1 END,
                        created_at
                ) as events
            FROM position_timeline
            WHERE 1=1
                {:position_filter}
            GROUP BY posicao_id, DATE(changed_at), new_status
            HAVING COUNT(*) > 1
        )
        SELECT
            posicao_id,
            event_date,
            new_status,
            dup_count,
            events
        FROM duplicates
        ORDER BY posicao_id, event_date;
    """)

    # Adicionar filtro de posições se fornecido
    if position_ids:
        position_filter = f"AND posicao_id IN ({','.join(map(str, position_ids))})"
        query_str = str(query).replace("{:position_filter}", position_filter)
    else:
        query_str = str(query).replace("{:position_filter}", "")

    result = session.execute(text(query_str))
    duplicates = []

    for row in result:
        duplicates.append({
            'posicao_id': row[0],
            'event_date': row[1],
            'new_status': row[2],
            'dup_count': row[3],
            'events': row[4]  # JSON array
        })

    logger.info(f"Encontradas {len(duplicates)} grupos de duplicatas")
    return duplicates


def backup_events(session, event_ids):
    """
    Cria backup dos eventos que serão deletados

    Args:
        session: SQLAlchemy session
        event_ids: Lista de IDs de eventos a fazer backup

    Returns:
        Path do arquivo de backup
    """
    if not event_ids:
        return None

    logger.info(f"Criando backup de {len(event_ids)} eventos...")

    # Buscar dados completos dos eventos
    query = text("""
        SELECT
            id, inhire_id, posicao_id, vaga_id,
            previous_status, new_status, changed_at,
            changed_by, changed_by_name, reason, notes,
            metadata, created_at, updated_at
        FROM position_timeline
        WHERE id IN :event_ids
        ORDER BY id
    """)

    result = session.execute(query, {"event_ids": tuple(event_ids)})

    backup_data = []
    for row in result:
        backup_data.append({
            'id': row[0],
            'inhire_id': row[1],
            'posicao_id': row[2],
            'vaga_id': row[3],
            'previous_status': row[4],
            'new_status': row[5],
            'changed_at': row[6].isoformat() if row[6] else None,
            'changed_by': row[7],
            'changed_by_name': row[8],
            'reason': row[9],
            'notes': row[10],
            'metadata': row[11],
            'created_at': row[12].isoformat() if row[12] else None,
            'updated_at': row[13].isoformat() if row[13] else None,
        })

    # Salvar backup em arquivo
    backup_dir = project_root / 'logs' / 'backups'
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f'position_timeline_backup_{timestamp}.json'

    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_events': len(backup_data),
            'events': backup_data
        }, f, indent=2, ensure_ascii=False)

    logger.info(f"Backup salvo em: {backup_file}")
    return backup_file


def delete_duplicates(session, duplicates, dry_run=False):
    """
    Deleta eventos duplicados, mantendo o melhor de cada grupo

    Args:
        session: SQLAlchemy session
        duplicates: Lista de duplicatas (output de find_duplicates)
        dry_run: Se True, apenas simula (não deleta)

    Returns:
        Dict com estatísticas da operação
    """
    stats = {
        'total_groups': len(duplicates),
        'total_events_analyzed': 0,
        'events_to_keep': 0,
        'events_to_delete': 0,
        'events_deleted': 0,
        'events_with_notes_kept': 0,
        'events_without_notes_deleted': 0,
    }

    events_to_delete = []

    for dup in duplicates:
        events = dup['events']
        stats['total_events_analyzed'] += len(events)

        # Primeiro evento (índice 0) é o MELHOR (ordenado por notes DESC, created_at ASC)
        best_event = events[0]
        to_delete = events[1:]  # Todos os outros

        stats['events_to_keep'] += 1
        stats['events_to_delete'] += len(to_delete)

        if best_event.get('notes'):
            stats['events_with_notes_kept'] += 1

        # Coletar IDs para deleção
        for event in to_delete:
            events_to_delete.append(event['id'])
            if not event.get('notes'):
                stats['events_without_notes_deleted'] += 1

        # Log da decisão
        logger.debug(f"Posição {dup['posicao_id']} - {dup['event_date']} - {dup['new_status']}:")
        logger.debug(f"  KEEP: ID={best_event['id']}, notes={best_event.get('notes', '(empty)')}")
        for event in to_delete:
            logger.debug(f"  DELETE: ID={event['id']}, notes={event.get('notes', '(empty)')}")

    # Fazer backup antes de deletar
    if events_to_delete and not dry_run:
        backup_file = backup_events(session, events_to_delete)
        logger.info(f"Backup criado: {backup_file}")

    # Deletar eventos
    if events_to_delete:
        if dry_run:
            logger.info(f"[DRY-RUN] Deletaria {len(events_to_delete)} eventos")
            logger.info(f"[DRY-RUN] IDs: {events_to_delete[:10]}...")  # Mostrar primeiros 10
        else:
            delete_query = text("""
                DELETE FROM position_timeline
                WHERE id IN :event_ids
            """)

            result = session.execute(delete_query, {"event_ids": tuple(events_to_delete)})
            stats['events_deleted'] = result.rowcount

            logger.info(f"Deletados {stats['events_deleted']} eventos duplicados")

    return stats


def validate_cleanup(session, position_ids=None):
    """
    Valida que não existem mais duplicatas após a limpeza

    Args:
        session: SQLAlchemy session
        position_ids: Lista de IDs de posições (None = todas)

    Returns:
        Bool indicando se validação passou
    """
    logger.info("Validando limpeza...")

    remaining_duplicates = find_duplicates(session, position_ids)

    if remaining_duplicates:
        logger.error(f"FALHA: Ainda existem {len(remaining_duplicates)} duplicatas!")
        return False
    else:
        logger.info("SUCESSO: Nenhuma duplicata encontrada")
        return True


def print_stats(stats):
    """Exibe estatísticas da operação"""
    print()
    print("=" * 80)
    print("ESTATÍSTICAS DA LIMPEZA")
    print("=" * 80)
    print()
    print(f"Grupos de duplicatas:           {stats['total_groups']}")
    print(f"Total de eventos analisados:    {stats['total_events_analyzed']}")
    print(f"Eventos mantidos (melhores):    {stats['events_to_keep']}")
    print(f"Eventos deletados (duplicatas): {stats['events_deleted']}")
    print()
    print(f"Eventos com notes mantidos:     {stats['events_with_notes_kept']}")
    print(f"Eventos sem notes deletados:    {stats['events_without_notes_deleted']}")
    print()
    print("=" * 80)
    print()


def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Remove duplicatas de eventos na position_timeline'
    )
    parser.add_argument(
        '--positions',
        type=str,
        help='IDs de posições separados por vírgula (ex: 386,311,85). Se omitido, processa todas.'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Apenas simula, não deleta eventos'
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='Não pede confirmação (uso em scripts)'
    )

    args = parser.parse_args()

    # Parse position IDs
    position_ids = None
    if args.positions:
        try:
            position_ids = [int(x.strip()) for x in args.positions.split(',')]
        except ValueError:
            print("[ERROR] IDs de posições inválidos. Use números separados por vírgula.")
            return 1

    # Banner
    print_banner()

    if args.dry_run:
        print("[DRY-RUN MODE] Nenhum dado será modificado.")
        print()

    # Confirmação
    if not args.yes and not args.dry_run:
        try:
            confirm = input("Deseja continuar com a limpeza? (s/N): ").strip().lower()
            if confirm not in ['s', 'sim', 'y', 'yes']:
                print("\n[CANCEL] Limpeza cancelada pelo usuário.\n")
                return 0
        except (EOFError, KeyboardInterrupt):
            print("\n\n[CANCEL] Limpeza cancelada.\n")
            return 0

    print()
    print("[>>>] Iniciando limpeza...\n")

    # Criar conexão
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # STEP 1: Identificar duplicatas
        print("[STEP 1] Identificando duplicatas...")
        duplicates = find_duplicates(session, position_ids)

        if not duplicates:
            print()
            print("[SUCCESS] Nenhuma duplicata encontrada! Banco já está limpo.")
            print()
            return 0

        print(f"   Encontrados {len(duplicates)} grupos de duplicatas")
        print()

        # STEP 2: Deletar duplicatas
        print("[STEP 2] Removendo duplicatas...")
        stats = delete_duplicates(session, duplicates, dry_run=args.dry_run)
        print()

        # STEP 3: Validar
        if not args.dry_run:
            print("[STEP 3] Validando limpeza...")
            if validate_cleanup(session, position_ids):
                session.commit()
                print("   Transação commitada com sucesso")
            else:
                session.rollback()
                print("   [ERROR] Validação falhou - Rollback executado")
                return 1
        else:
            print("[DRY-RUN] Pulando validação e commit")

        # Estatísticas
        print_stats(stats)

        print("[SUCCESS] Limpeza concluída!")
        print()

        return 0

    except Exception as e:
        logger.error(f"Erro durante limpeza: {str(e)}")
        session.rollback()
        print(f"\n[ERROR] {str(e)}\n")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        session.close()


if __name__ == '__main__':
    sys.exit(main())
