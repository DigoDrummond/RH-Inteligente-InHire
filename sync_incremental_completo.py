# -*- coding: utf-8 -*-
"""
Script de Sincronizacao Incremental Completa - Execucao Manual

Este script executa sincronizacao incremental robusta com:
- Cobertura de 100% de todas as tabelas
- Validacoes pre e pos-execucao
- Timeouts estendidos (sem timeout)
- Sistema de alertas e interrupcao em caso de falha
- Relatorio detalhado ao final

USO:
    python sync_incremental_completo.py

OPCOES:
    --express          Modo express (mais rapido, 10-15 min)
    --completa         Modo completo (cobertura 100%, 15-25 min)
    --dry-run          Simula execucao sem gravar dados
    --no-validation    Pula validacoes (nao recomendado)

EXEMPLOS:
    # Sincronizacao completa 100% (recomendado)
    python sync_incremental_completo.py --completa

    # Sincronizacao express
    python sync_incremental_completo.py --express

    # Simulacao (dry-run)
    python sync_incremental_completo.py --completa --dry-run
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings, validate_settings, SyncStatus
from services.sync_service import SyncService
from utils.logger import get_logger

logger = get_logger(__name__)


def print_banner():
    """Imprime banner do script"""
    banner = """
================================================================================

        SINCRONIZACAO INCREMENTAL COMPLETA - INHIRE API -> BD

  Cobertura: 100% de todas as tabelas
  Timeout: Estendido (sem timeout)
  Alertas: Interrompe em caso de falha critica

================================================================================
"""
    print(banner)


def print_pre_sync_info(mode: str):
    """Imprime informações pré-sincronização"""
    logger.info("\n" + "=" * 80)
    logger.info("INFORMAÇÕES DA SINCRONIZAÇÃO")
    logger.info("=" * 80)
    logger.info(f"Modo:              {mode}")
    logger.info(f"Tenant:            {settings.INHIRE_TENANT}")
    logger.info(f"Ambiente:          {settings.ENVIRONMENT}")
    logger.info(f"Banco de Dados:    {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    logger.info(f"API Base URL:      {settings.INHIRE_BASE_URL}")
    logger.info(f"Timeout Conectar:  {settings.SYNC_INCREMENTAL_TIMEOUT_CONNECT}s")
    logger.info(f"Timeout Leitura:   {settings.SYNC_INCREMENTAL_TIMEOUT_READ}s")
    logger.info(f"Batch Size:        {settings.SYNC_BATCH_SIZE}")
    logger.info(f"Max Erros/Entid.:  {settings.SYNC_INCREMENTAL_MAX_ERRORS_PER_ENTITY}")
    logger.info("=" * 80 + "\n")


def confirm_execution(dry_run: bool = False) -> bool:
    """
    Solicita confirmacao do usuario para executar sincronizacao.

    Args:
        dry_run: Se True, nao solicita confirmacao

    Returns:
        True se usuario confirmar ou for dry-run, False caso contrario
    """
    if dry_run:
        logger.warning("MODO DRY-RUN: Nenhum dado sera gravado no banco de dados")
        return True

    logger.warning("\nATENCAO: Esta sincronizacao ira:")
    logger.warning("  1. Conectar a API Inhire")
    logger.warning("  2. Buscar dados de TODAS as tabelas")
    logger.warning("  3. Atualizar o banco de dados")
    logger.warning("  4. Interromper em caso de falha critica")

    try:
        response = input("\nDeseja continuar? (sim/nao): ").lower().strip()
        return response in ['sim', 's', 'yes', 'y']
    except KeyboardInterrupt:
        logger.info("\n\nSincronizacao cancelada pelo usuario")
        return False
    except Exception:
        return False


def check_last_sync(session) -> dict:
    """
    Verifica ultima sincronizacao e retorna informacoes.

    Args:
        session: SQLAlchemy session

    Returns:
        Dict com informacoes da ultima sync
    """
    from models.database import SyncConfiguration

    try:
        config = session.query(SyncConfiguration).filter_by(
            tenant_id=settings.INHIRE_TENANT
        ).first()

        if not config:
            return {
                'exists': False,
                'message': 'Nenhuma sincronizacao anterior encontrada'
            }

        last_sync = config.last_incremental_sync or config.last_full_sync
        if not last_sync:
            return {
                'exists': False,
                'message': 'Nenhuma sincronizacao anterior registrada'
            }

        time_since_sync = datetime.utcnow() - last_sync
        hours = time_since_sync.total_seconds() / 3600

        return {
            'exists': True,
            'last_sync': last_sync,
            'hours_ago': hours,
            'message': f'Ultima sincronizacao: {last_sync.strftime("%Y-%m-%d %H:%M:%S UTC")} ({hours:.1f}h atras)'
        }

    except Exception as e:
        return {
            'exists': False,
            'error': str(e),
            'message': f'Erro ao verificar ultima sincronizacao: {str(e)}'
        }


def estimate_duration(express_mode: bool) -> str:
    """
    Estima duracao da sincronizacao.

    Args:
        express_mode: Se True, modo express, senao modo completo

    Returns:
        String com estimativa de duracao
    """
    if express_mode:
        return "10-15 minutos"
    else:
        return "15-25 minutos"


def run_sync(express_mode: bool = False, dry_run: bool = False, skip_validation: bool = False) -> dict:
    """
    Executa sincronizacao incremental completa.

    Args:
        express_mode: Se True, executa modo express (mais rapido)
        dry_run: Se True, simula execucao sem gravar dados
        skip_validation: Se True, pula validacoes (nao recomendado)

    Returns:
        Dict com resultado da sincronizacao
    """
    mode_name = "EXPRESS" if express_mode else "COMPLETA"
    logger.info(f"\n{'=' * 80}")
    logger.info(f"INICIANDO SINCRONIZACAO INCREMENTAL {mode_name}")
    logger.info(f"{'=' * 80}\n")

    start_time = datetime.utcnow()

    # Criar engine e sessão
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        echo=False
    )
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Verificar última sincronização
        last_sync_info = check_last_sync(session)
        logger.info(last_sync_info['message'])

        if not last_sync_info['exists'] and not dry_run:
            logger.warning("\nAVISO: Nenhuma sincronização anterior encontrada.")
            logger.warning("Recomenda-se executar uma sincronização COMPLETA primeiro.")
            response = input("Deseja continuar mesmo assim? (sim/não): ").lower().strip()
            if response not in ['sim', 's', 'yes', 'y']:
                return {'success': False, 'message': 'Sincronização cancelada pelo usuário'}

        # Estimar duração
        duration_estimate = estimate_duration(express_mode)
        logger.info(f"\nDuração estimada: {duration_estimate}")

        if dry_run:
            logger.info("\n" + "=" * 80)
            logger.info("MODO DRY-RUN - Simulando sincronização...")
            logger.info("=" * 80)
            logger.info("\nNeste modo, a sincronização seria executada com:")
            logger.info(f"  - Modo: {mode_name}")
            logger.info(f"  - Validações: {'Desabilitadas' if skip_validation else 'Habilitadas'}")
            logger.info(f"  - Cobertura: 100% de todas as tabelas")
            logger.info(f"  - Duração estimada: {duration_estimate}")
            logger.info("\nNenhum dado foi gravado no banco de dados.")
            return {'success': True, 'message': 'Dry-run concluído', 'dry_run': True}

        # Executar sincronização
        sync_service = SyncService(session)

        logger.info("\n" + "=" * 80)
        logger.info("EXECUTANDO SINCRONIZAÇÃO")
        logger.info("=" * 80 + "\n")

        result = sync_service.sync_incremental(
            express_mode=express_mode,
            completa_100_pct=not skip_validation  # Ativa modo robusto se validações habilitadas
        )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        if result['success']:
            logger.info("\n" + "=" * 80)
            logger.info("✓ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO")
            logger.info("=" * 80)
            logger.info(f"Duração real: {duration:.2f}s ({duration/60:.2f} minutos)")
            logger.info(f"Status: {result['status']}")
            logger.info(f"Estatísticas: {result.get('stats', {})}")
            logger.info("=" * 80 + "\n")
        else:
            logger.error("\n" + "=" * 80)
            logger.error("✗ SINCRONIZAÇÃO FALHOU")
            logger.error("=" * 80)
            logger.error(f"Duração até falha: {duration:.2f}s ({duration/60:.2f} minutos)")
            logger.error(f"Erro: {result.get('error', 'Erro desconhecido')}")
            logger.error("=" * 80 + "\n")

        return result

    except KeyboardInterrupt:
        logger.warning("\n\nSincronização interrompida pelo usuário (Ctrl+C)")
        return {'success': False, 'message': 'Interrompido pelo usuário'}

    except Exception as e:
        logger.error(f"\n\nErro inesperado durante sincronização: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}

    finally:
        session.close()
        engine.dispose()


def main():
    """Funcao principal do script"""
    # Configurar encoding para UTF-8 no Windows
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(
        description="Sincronizacao Incremental Completa - Inhire API -> BD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXEMPLOS:
  # Sincronizacao completa 100%% (recomendado)
  python sync_incremental_completo.py --completa

  # Sincronizacao express (mais rapida)
  python sync_incremental_completo.py --express

  # Simulacao (dry-run)
  python sync_incremental_completo.py --completa --dry-run

  # Sem validacoes (nao recomendado)
  python sync_incremental_completo.py --completa --no-validation
        """
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--express',
        action='store_true',
        help='Modo express (10-15 min, pula algumas entidades secundárias)'
    )
    mode_group.add_argument(
        '--completa',
        action='store_true',
        help='Modo completo (15-25 min, cobertura 100%%) - RECOMENDADO'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simula execução sem gravar dados'
    )
    parser.add_argument(
        '--no-validation',
        action='store_true',
        help='Pula validações pré/pós-sync (não recomendado)'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Confirma automaticamente (não solicita confirmação)'
    )

    args = parser.parse_args()

    # Se nenhum modo especificado, usar completo
    express_mode = args.express
    if not args.express and not args.completa:
        logger.info("Nenhum modo especificado, usando --completa (recomendado)")
        express_mode = False

    # Imprimir banner
    print_banner()

    # Validar configurações
    logger.info("Validando configurações...")
    if not validate_settings():
        logger.error("\n✗ Configurações inválidas. Verifique o arquivo .env")
        logger.error("Execute: python config.py para ver detalhes")
        sys.exit(1)
    logger.info("✓ Configurações válidas\n")

    # Imprimir informações
    mode_name = "EXPRESS" if express_mode else "COMPLETA 100%"
    print_pre_sync_info(mode_name)

    # Confirmar execução (se não for --yes ou --dry-run)
    if not args.yes and not args.dry_run:
        if not confirm_execution(args.dry_run):
            logger.info("\nSincronização cancelada pelo usuário")
            sys.exit(0)

    # Executar sincronização
    result = run_sync(
        express_mode=express_mode,
        dry_run=args.dry_run,
        skip_validation=args.no_validation
    )

    # Retornar código de saída apropriado
    if result['success']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
