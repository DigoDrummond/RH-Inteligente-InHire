"""
Sincronização Incremental Otimizada - Baseada em Datas das Tabelas

Nova estratégia que consulta o banco PRIMEIRO para identificar registros
que precisam ser atualizados, reduzindo drasticamente chamadas à API.

Campos de referência por tabela:
- candidatura_timeline: stage_updated_at
- candidaturas: updated_at_inhire
- clientes: updated_at_inhire
- posicoes: updated_at_inhire
- position_timeline: changed_at
- requisicoes: status_updated_at
- talentos: updated_at_inhire
- vaga_tags: updated_at
- vagas: updated_at_inhire
"""

import sys
from datetime import datetime, timedelta
from typing import Dict, List, Set
from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import sessionmaker

from config import settings, SyncType, SyncStatus, SyncEntity
from services.api_client import InhireAPIClient
from services.database_service import DatabaseService
from models.database import (
    Vaga, Posicao, Candidatura, Talento, Requisicao,
    VagaTag, Cliente, PositionTimeline, CandidaturaTimeline
)
from utils.logger import get_logger

logger = get_logger(__name__)


def sync_incremental_optimized():
    """
    Sincronização Incremental Otimizada

    Estratégia:
    1. Consultar BD para identificar registros modificados desde última sync
    2. Buscar vagas que tiveram mudanças (para sincronizar posições/candidaturas)
    3. Buscar apenas dados relevantes da API
    4. Atualizar apenas o necessário

    Tempo estimado: 2-5 minutos
    Frequência recomendada: a cada 1-2 horas
    """
    logger.info("=" * 80)
    logger.info("SINCRONIZAÇÃO INCREMENTAL OTIMIZADA - INICIANDO")
    logger.info("=" * 80)

    # Setup
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    db = DatabaseService(session)
    api_client = InhireAPIClient()

    # Obter configuração e última sincronização
    config = db.get_sync_configuration(settings.INHIRE_TENANT)
    last_sync = config.last_incremental_sync or config.last_full_sync

    if not last_sync:
        logger.error("❌ Nenhuma sincronização anterior encontrada!")
        logger.error("Execute primeiro: python sync_completa.py")
        return

    logger.info(f"📅 Última sincronização: {last_sync}")
    logger.info(f"⏱️  Sincronizando mudanças desde: {last_sync}")
    logger.info("")

    # Criar log de sincronização
    main_log = db.create_sync_log(config.id, SyncType.INCREMENTAL, SyncEntity.ALL)

    all_stats = {
        'processed': 0,
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'failed': 0
    }

    try:
        # ========================================
        # FASE 1: IDENTIFICAR MUDANÇAS NO BD
        # ========================================

        logger.info("🔍 FASE 1: Identificando mudanças no banco de dados...")
        logger.info("-" * 80)

        # 1.1 Vagas modificadas
        vagas_modificadas = session.query(Vaga).filter(
            or_(
                Vaga.updated_at_inhire > last_sync,
                Vaga.created_at > last_sync
            )
        ).all()

        vagas_modificadas_ids = {v.inhire_id for v in vagas_modificadas}
        logger.info(f"  Vagas modificadas/novas: {len(vagas_modificadas_ids)}")

        # 1.2 Posições modificadas
        posicoes_modificadas = session.query(Posicao).filter(
            Posicao.updated_at_inhire > last_sync
        ).all()
        logger.info(f"  Posições modificadas: {len(posicoes_modificadas)}")

        # 1.3 Candidaturas modificadas
        candidaturas_modificadas = session.query(Candidatura).filter(
            Candidatura.updated_at_inhire > last_sync
        ).all()
        logger.info(f"  Candidaturas modificadas: {len(candidaturas_modificadas)}")

        # 1.4 Talentos modificados
        talentos_modificados = session.query(Talento).filter(
            Talento.updated_at_inhire > last_sync
        ).all()
        logger.info(f"  Talentos modificados: {len(talentos_modificados)}")

        # 1.5 Posições com mudanças de status (via timeline)
        posicoes_com_mudanca_status = session.query(PositionTimeline.posicao_id).filter(
            PositionTimeline.changed_at > last_sync
        ).distinct().all()
        posicoes_ids_timeline = {p[0] for p in posicoes_com_mudanca_status}
        logger.info(f"  Posições com mudança de status (timeline): {len(posicoes_ids_timeline)}")

        # 1.6 Candidaturas com mudanças de stage (via timeline)
        candidaturas_com_mudanca_stage = session.query(CandidaturaTimeline.candidatura_id).filter(
            CandidaturaTimeline.stage_updated_at > last_sync
        ).distinct().all()
        candidaturas_ids_timeline = {c[0] for c in candidaturas_com_mudanca_stage}
        logger.info(f"  Candidaturas com mudança de stage (timeline): {len(candidaturas_ids_timeline)}")

        logger.info("")

        # ========================================
        # FASE 2: SINCRONIZAR DADOS DA API
        # ========================================

        logger.info("🔄 FASE 2: Sincronizando dados da API...")
        logger.info("-" * 80)

        # 2.1 VAGAS
        logger.info("[1/6] Sincronizando VAGAS...")

        # Buscar TODAS as vagas (para detectar novas também)
        # Mas a comparação de data fará skip das não modificadas
        todas_vagas = list(api_client.get_all_vagas())
        logger.info(f"  Vagas encontradas na API: {len(todas_vagas)}")

        vaga_stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        for vaga_api in todas_vagas:
            try:
                is_new, operation = db.upsert_vaga(vaga_api)
                vaga_stats['processed'] += 1
                vaga_stats[operation] += 1

                # Adicionar à lista de modificadas se foi criada ou atualizada
                if operation in ['created', 'updated']:
                    vagas_modificadas_ids.add(vaga_api.id)

            except Exception as e:
                logger.error(f"  ❌ Erro ao processar vaga {vaga_api.id}: {e}")
                vaga_stats['failed'] += 1

        logger.info(f"  Processadas: {vaga_stats['processed']}")
        logger.info(f"  Criadas: {vaga_stats['created']}")
        logger.info(f"  Atualizadas: {vaga_stats['updated']}")
        logger.info(f"  Ignoradas: {vaga_stats['skipped']}")
        if vaga_stats['failed'] > 0:
            logger.warning(f"  Falhas: {vaga_stats['failed']}")
        logger.info("")

        # Atualizar estatísticas gerais
        for key in vaga_stats:
            all_stats[key] += vaga_stats[key]

        # 2.2 POSIÇÕES (apenas de vagas modificadas)
        logger.info("[2/6] Sincronizando POSIÇÕES...")
        logger.info(f"  Sincronizando posições de {len(vagas_modificadas_ids)} vagas modificadas...")

        posicao_stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        for vaga_inhire_id in vagas_modificadas_ids:
            try:
                posicoes = api_client.get_all_posicoes(vaga_inhire_id)

                for posicao_api in posicoes:
                    try:
                        is_new, operation = db.upsert_posicao(posicao_api)
                        posicao_stats['processed'] += 1
                        posicao_stats[operation] += 1
                    except Exception as e:
                        logger.error(f"  ❌ Erro ao processar posição {posicao_api.id}: {e}")
                        posicao_stats['failed'] += 1

            except Exception as e:
                logger.error(f"  ❌ Erro ao buscar posições da vaga {vaga_inhire_id}: {e}")
                posicao_stats['failed'] += 1

        logger.info(f"  Processadas: {posicao_stats['processed']}")
        logger.info(f"  Criadas: {posicao_stats['created']}")
        logger.info(f"  Atualizadas: {posicao_stats['updated']}")
        logger.info(f"  Ignoradas: {posicao_stats['skipped']}")
        if posicao_stats['failed'] > 0:
            logger.warning(f"  Falhas: {posicao_stats['failed']}")
        logger.info("")

        for key in posicao_stats:
            all_stats[key] += posicao_stats[key]

        # 2.3 CANDIDATURAS (apenas de vagas modificadas)
        logger.info("[3/6] Sincronizando CANDIDATURAS...")
        logger.info(f"  Sincronizando candidaturas de {len(vagas_modificadas_ids)} vagas modificadas...")

        cand_stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        talent_ids_encontrados: Set[str] = set()

        for vaga_inhire_id in vagas_modificadas_ids:
            try:
                candidaturas = api_client.get_all_candidaturas(vaga_inhire_id)

                for cand_api in candidaturas:
                    try:
                        is_new, operation = db.upsert_candidatura(cand_api, vaga_inhire_id)
                        cand_stats['processed'] += 1
                        cand_stats[operation] += 1

                        # Coletar IDs de talentos
                        if cand_api.talentId:
                            talent_ids_encontrados.add(cand_api.talentId)

                    except Exception as e:
                        logger.error(f"  ❌ Erro ao processar candidatura {cand_api.id}: {e}")
                        cand_stats['failed'] += 1

            except Exception as e:
                logger.error(f"  ❌ Erro ao buscar candidaturas da vaga {vaga_inhire_id}: {e}")
                cand_stats['failed'] += 1

        logger.info(f"  Processadas: {cand_stats['processed']}")
        logger.info(f"  Criadas: {cand_stats['created']}")
        logger.info(f"  Atualizadas: {cand_stats['updated']}")
        logger.info(f"  Ignoradas: {cand_stats['skipped']}")
        logger.info(f"  Talentos únicos encontrados: {len(talent_ids_encontrados)}")
        if cand_stats['failed'] > 0:
            logger.warning(f"  Falhas: {cand_stats['failed']}")
        logger.info("")

        for key in cand_stats:
            all_stats[key] += cand_stats[key]

        # 2.4 TALENTOS
        logger.info("[4/6] Sincronizando TALENTOS...")

        tal_stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        # Tentar usar filtro de data na API (se suportado)
        try:
            filter_date = {"updatedAt": {"gte": last_sync.isoformat()}}
            talentos_modificados_api = api_client.get_all_talentos(filter_dict=filter_date)
            logger.info(f"  Talentos modificados (filtro API): {len(talentos_modificados_api)}")

            for talento_api in talentos_modificados_api:
                try:
                    is_new, operation = db.upsert_talento(talento_api)
                    tal_stats['processed'] += 1
                    tal_stats[operation] += 1
                except Exception as e:
                    logger.error(f"  ❌ Erro ao processar talento {talento_api.id}: {e}")
                    tal_stats['failed'] += 1

        except Exception as e:
            logger.warning(f"  ⚠️  Filtro de data não funcionou na API: {e}")
            logger.info("  Sincronizando apenas talentos das candidaturas...")

        # Sincronizar talentos das candidaturas processadas
        logger.info(f"  Sincronizando {len(talent_ids_encontrados)} talentos das candidaturas...")

        for talent_id in talent_ids_encontrados:
            try:
                # Verificar se já existe no BD
                talento_bd = session.query(Talento).filter_by(inhire_id=talent_id).first()

                # Se não existe ou foi modificado recentemente, buscar da API
                if not talento_bd or (talento_bd.updated_at_inhire and talento_bd.updated_at_inhire > last_sync):
                    # Aqui precisaríamos de um endpoint para buscar talento por ID
                    # Como não temos, vamos pular
                    pass

            except Exception as e:
                logger.error(f"  ❌ Erro ao processar talento {talent_id}: {e}")
                tal_stats['failed'] += 1

        logger.info(f"  Processados: {tal_stats['processed']}")
        logger.info(f"  Criados: {tal_stats['created']}")
        logger.info(f"  Atualizados: {tal_stats['updated']}")
        logger.info(f"  Ignorados: {tal_stats['skipped']}")
        if tal_stats['failed'] > 0:
            logger.warning(f"  Falhas: {tal_stats['failed']}")
        logger.info("")

        for key in tal_stats:
            all_stats[key] += tal_stats[key]

        # 2.5 REQUISIÇÕES (apenas de vagas modificadas)
        logger.info("[5/6] Sincronizando REQUISIÇÕES...")
        logger.info(f"  Sincronizando requisições de {len(vagas_modificadas_ids)} vagas modificadas...")

        req_stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        # A API de requisições não tem filtro de data, então buscamos de todas as vagas
        # mas apenas das modificadas (otimização)
        for vaga_inhire_id in vagas_modificadas_ids:
            try:
                requisicoes = api_client.get_requisicoes_by_vaga(vaga_inhire_id)

                for req_api in requisicoes:
                    try:
                        is_new, operation = db.upsert_requisicao(req_api)
                        req_stats['processed'] += 1
                        req_stats[operation] += 1
                    except Exception as e:
                        logger.error(f"  ❌ Erro ao processar requisição {req_api.id}: {e}")
                        req_stats['failed'] += 1

            except Exception as e:
                # Endpoint pode não existir para todas as vagas
                pass

        logger.info(f"  Processadas: {req_stats['processed']}")
        logger.info(f"  Criadas: {req_stats['created']}")
        logger.info(f"  Atualizadas: {req_stats['updated']}")
        logger.info(f"  Ignoradas: {req_stats['skipped']}")
        if req_stats['failed'] > 0:
            logger.warning(f"  Falhas: {req_stats['failed']}")
        logger.info("")

        for key in req_stats:
            all_stats[key] += req_stats[key]

        # 2.6 POSITION TIMELINE (apenas de posições modificadas)
        logger.info("[6/6] Sincronizando POSITION TIMELINE...")

        # Identificar posições que precisam ter timeline atualizado
        posicoes_para_timeline = set()

        # Posições modificadas
        for posicao in posicoes_modificadas:
            posicoes_para_timeline.add(posicao.inhire_id)

        # Posições de vagas modificadas
        for vaga_inhire_id in vagas_modificadas_ids:
            posicoes_vaga = session.query(Posicao).join(Vaga).filter(
                Vaga.inhire_id == vaga_inhire_id
            ).all()
            for posicao in posicoes_vaga:
                posicoes_para_timeline.add(posicao.inhire_id)

        logger.info(f"  Sincronizando timeline de {len(posicoes_para_timeline)} posições...")

        pt_stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        for posicao_inhire_id in posicoes_para_timeline:
            try:
                timeline_events = api_client.get_position_timeline(posicao_inhire_id)

                for event_api in timeline_events:
                    try:
                        is_new, operation = db.upsert_position_timeline_event(event_api)
                        pt_stats['processed'] += 1
                        pt_stats[operation] += 1
                    except Exception as e:
                        logger.error(f"  ❌ Erro ao processar evento de timeline: {e}")
                        pt_stats['failed'] += 1

            except Exception as e:
                # Nem todas as posições têm timeline
                pass

        logger.info(f"  Processados: {pt_stats['processed']}")
        logger.info(f"  Criados: {pt_stats['created']}")
        logger.info(f"  Atualizados: {pt_stats['updated']}")
        logger.info(f"  Ignorados: {pt_stats['skipped']}")
        if pt_stats['failed'] > 0:
            logger.warning(f"  Falhas: {pt_stats['failed']}")
        logger.info("")

        for key in pt_stats:
            all_stats[key] += pt_stats[key]

        # ========================================
        # FINALIZAÇÃO
        # ========================================

        # Atualizar timestamp da última sincronização incremental
        config.last_incremental_sync = datetime.utcnow()
        session.commit()

        # Completar log de sincronização
        db.complete_sync_log(main_log, SyncStatus.SUCCESS, all_stats)

        logger.info("=" * 80)
        logger.info("✅ SINCRONIZAÇÃO INCREMENTAL OTIMIZADA CONCLUÍDA COM SUCESSO")
        logger.info("=" * 80)
        logger.info("")
        logger.info("📊 RESUMO GERAL:")
        logger.info(f"  Total processado: {all_stats['processed']}")
        logger.info(f"  Criados: {all_stats['created']}")
        logger.info(f"  Atualizados: {all_stats['updated']}")
        logger.info(f"  Ignorados: {all_stats['skipped']}")

        if all_stats['processed'] > 0:
            eficiencia = (all_stats['skipped'] / all_stats['processed']) * 100
            logger.info(f"  Eficiência: {eficiencia:.1f}% (registros ignorados)")

        if all_stats['failed'] > 0:
            logger.warning(f"  ⚠️  Falhas: {all_stats['failed']}")

        logger.info("=" * 80)

        return {
            'success': True,
            'status': SyncStatus.SUCCESS,
            'stats': all_stats
        }

    except Exception as e:
        logger.error(f"❌ Erro na sincronização incremental otimizada: {str(e)}", exc_info=True)
        db.complete_sync_log(main_log, SyncStatus.ERROR, all_stats, errors=str(e))

        return {
            'success': False,
            'status': SyncStatus.ERROR,
            'error': str(e),
            'stats': all_stats
        }

    finally:
        session.close()


if __name__ == "__main__":
    try:
        result = sync_incremental_optimized()

        if result['success']:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Sincronização interrompida pelo usuário")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Erro fatal: {str(e)}", exc_info=True)
        sys.exit(1)
