"""
Métricas Avançadas para Observabilidade Detalhada
Extensão do sistema de métricas básico com análises mais profundas
"""
from prometheus_client import Gauge, Histogram, Counter, Summary
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# MÉTRICAS DE FUNIL DE RECRUTAMENTO
# ============================================================================

# Candidatos por estágio do funil
candidates_by_stage = Gauge(
    'inhire_candidates_by_stage',
    'Número de candidatos por estágio do processo',
    ['stage_name', 'vaga_id', 'vaga_name']
)

# Tempo médio por estágio
stage_duration_days = Gauge(
    'inhire_stage_duration_days',
    'Tempo médio em dias que candidatos passam em cada estágio',
    ['stage_name', 'vaga_id']
)

# Taxa de conversão entre estágios
stage_conversion_rate = Gauge(
    'inhire_stage_conversion_rate',
    'Taxa de conversão percentual entre estágios consecutivos',
    ['from_stage', 'to_stage', 'vaga_id']
)

# Time to hire (dias desde aplicação até contratação)
time_to_hire_days = Histogram(
    'inhire_time_to_hire_days',
    'Tempo em dias desde aplicação até contratação',
    ['vaga_id', 'vaga_name'],
    buckets=[7, 14, 21, 30, 45, 60, 90, 120, 180]
)


# ============================================================================
# MÉTRICAS DE QUALIDADE DE DADOS
# ============================================================================

# Completude dos dados (% campos preenchidos)
data_completeness_pct = Gauge(
    'inhire_data_completeness_pct',
    'Percentual de completude dos dados',
    ['entity', 'field_category']  # field_category: required, optional, custom
)

# Registros com dados inconsistentes
data_inconsistencies_total = Counter(
    'inhire_data_inconsistencies_total',
    'Total de inconsistências detectadas nos dados',
    ['entity', 'inconsistency_type']
)

# Tamanho médio dos campos JSON
json_field_size_bytes = Gauge(
    'inhire_json_field_size_bytes',
    'Tamanho médio em bytes dos campos JSON',
    ['entity', 'field_name']
)


# ============================================================================
# MÉTRICAS DE PERFORMANCE DE SINCRONIZAÇÃO
# ============================================================================

# Taxa de throughput (registros/segundo)
sync_throughput_records_per_second = Gauge(
    'inhire_sync_throughput_records_per_second',
    'Taxa de processamento em registros por segundo',
    ['entity', 'sync_type']
)

# Lag de sincronização (diferença entre updated_at API e última sync)
sync_lag_minutes = Gauge(
    'inhire_sync_lag_minutes',
    'Lag em minutos entre atualização na API e última sincronização',
    ['entity']
)

# Registros pendentes de sincronização
sync_pending_records = Gauge(
    'inhire_sync_pending_records',
    'Número de registros com atualizações pendentes',
    ['entity']
)


# ============================================================================
# MÉTRICAS DE TENDÊNCIAS E SAZONALIDADE
# ============================================================================

# Novas aplicações por período
new_applications_by_period = Gauge(
    'inhire_new_applications_by_period',
    'Número de novas aplicações por período',
    ['period', 'vaga_id']  # period: hour, day, week, month
)

# Taxa de crescimento (% mudança vs período anterior)
growth_rate_pct = Gauge(
    'inhire_growth_rate_pct',
    'Taxa de crescimento percentual vs período anterior',
    ['entity', 'period']
)


# ============================================================================
# MÉTRICAS DE DIVERSIDADE
# ============================================================================

# Distribuição por gênero
diversity_gender_distribution = Gauge(
    'inhire_diversity_gender_distribution',
    'Distribuição percentual por gênero',
    ['gender', 'vaga_id']
)

# Distribuição por PCD
diversity_pcd_distribution = Gauge(
    'inhire_diversity_pcd_distribution',
    'Distribuição percentual de pessoas com deficiência',
    ['is_pcd', 'vaga_id']
)


# ============================================================================
# MÉTRICAS DE SAÚDE DO SISTEMA
# ============================================================================

# Tamanho do banco de dados
database_size_mb = Gauge(
    'inhire_database_size_mb',
    'Tamanho total do banco de dados em MB'
)

# Tamanho por tabela
table_size_mb = Gauge(
    'inhire_table_size_mb',
    'Tamanho de cada tabela em MB',
    ['table_name']
)

# Número de conexões ativas
database_connections_active = Gauge(
    'inhire_database_connections_active',
    'Número de conexões ativas ao banco'
)

# Taxa de cache hit (se implementado)
cache_hit_rate_pct = Gauge(
    'inhire_cache_hit_rate_pct',
    'Taxa de acerto do cache em percentual',
    ['cache_type']
)


# ============================================================================
# MÉTRICAS DE NEGÓCIO/KPIs
# ============================================================================

# Custo por contratação (se disponível)
cost_per_hire = Gauge(
    'inhire_cost_per_hire',
    'Custo médio por contratação',
    ['vaga_id', 'department']
)

# Qualidade das contratações (score médio)
hire_quality_score = Gauge(
    'inhire_hire_quality_score',
    'Score médio de qualidade das contratações',
    ['vaga_id', 'period']
)

# Taxa de oferta aceita
offer_acceptance_rate = Gauge(
    'inhire_offer_acceptance_rate',
    'Percentual de ofertas aceitas vs enviadas',
    ['vaga_id']
)


# ============================================================================
# FUNÇÕES DE COLETA DE MÉTRICAS AVANÇADAS
# ============================================================================

def collect_recruitment_funnel_metrics(session: Session):
    """
    Coleta métricas do funil de recrutamento

    Args:
        session: Sessão SQLAlchemy
    """
    from models.database import Candidatura, Vaga

    try:
        # Candidatos por estágio
        stage_counts = (
            session.query(
                Candidatura.stage_name,
                Vaga.inhire_id,
                Vaga.name,
                func.count(Candidatura.id).label('count')
            )
            .join(Vaga, Candidatura.vaga_id == Vaga.id)
            .filter(Candidatura.stage_name.isnot(None))
            .group_by(Candidatura.stage_name, Vaga.inhire_id, Vaga.name)
            .all()
        )

        for stage in stage_counts:
            candidates_by_stage.labels(
                stage_name=stage.stage_name,
                vaga_id=str(stage.inhire_id),
                vaga_name=stage.name
            ).set(stage.count)

        logger.debug(f"Métricas de funil coletadas: {len(stage_counts)} estágios")

    except Exception as e:
        logger.error(f"Erro ao coletar métricas de funil: {str(e)}")


def collect_time_to_hire_metrics(session: Session):
    """
    Calcula time-to-hire para candidatos contratados

    Args:
        session: Sessão SQLAlchemy
    """
    from models.database import Candidatura, Vaga, CandidaturaStatusEnum
    from sqlalchemy import extract

    try:
        # Candidatos contratados nos últimos 90 dias
        cutoff_date = datetime.now() - timedelta(days=90)

        hired_candidates = (
            session.query(
                Candidatura.created_at,
                Candidatura.updated_at_inhire,
                Vaga.inhire_id,
                Vaga.name
            )
            .join(Vaga, Candidatura.vaga_id == Vaga.id)
            .filter(
                and_(
                    Candidatura.status == CandidaturaStatusEnum.HIRED,
                    Candidatura.created_at >= cutoff_date,
                    Candidatura.updated_at_inhire.isnot(None)
                )
            )
            .all()
        )

        for candidate in hired_candidates:
            days_to_hire = (candidate.updated_at_inhire - candidate.created_at).days
            time_to_hire_days.labels(
                vaga_id=str(candidate.inhire_id),
                vaga_name=candidate.name
            ).observe(days_to_hire)

        logger.debug(f"Time-to-hire calculado para {len(hired_candidates)} contratações")

    except Exception as e:
        logger.error(f"Erro ao calcular time-to-hire: {str(e)}")


def collect_data_quality_metrics(session: Session):
    """
    Analisa qualidade e completude dos dados

    Args:
        session: Sessão SQLAlchemy
    """
    from models.database import Candidatura, Talento, Vaga

    try:
        # Completude de candidaturas
        total_candidaturas = session.query(Candidatura).count()
        if total_candidaturas > 0:
            # Campos obrigatórios
            with_talento = session.query(Candidatura).filter(
                Candidatura.talento_id.isnot(None)
            ).count()
            with_vaga = session.query(Candidatura).filter(
                Candidatura.vaga_id.isnot(None)
            ).count()

            data_completeness_pct.labels(
                entity='candidatura',
                field_category='required'
            ).set((with_talento + with_vaga) / (total_candidaturas * 2) * 100)

            # Campos opcionais
            with_stage = session.query(Candidatura).filter(
                Candidatura.stage_name.isnot(None)
            ).count()
            with_source = session.query(Candidatura).filter(
                Candidatura.source.isnot(None)
            ).count()

            data_completeness_pct.labels(
                entity='candidatura',
                field_category='optional'
            ).set((with_stage + with_source) / (total_candidaturas * 2) * 100)

        # Completude de talentos
        total_talentos = session.query(Talento).count()
        if total_talentos > 0:
            with_email = session.query(Talento).filter(
                Talento.email.isnot(None)
            ).count()
            with_phone = session.query(Talento).filter(
                Talento.phone.isnot(None)
            ).count()

            data_completeness_pct.labels(
                entity='talento',
                field_category='required'
            ).set((with_email + with_phone) / (total_talentos * 2) * 100)

        logger.debug("Métricas de qualidade de dados coletadas")

    except Exception as e:
        logger.error(f"Erro ao coletar métricas de qualidade: {str(e)}")


def collect_sync_performance_metrics(session: Session):
    """
    Calcula métricas de performance de sincronização

    Args:
        session: Sessão SQLAlchemy
    """
    from models.database import Candidatura, Vaga, Posicao, Talento

    try:
        entities = {
            'candidatura': Candidatura,
            'vaga': Vaga,
            'posicao': Posicao,
            'talento': Talento
        }

        for entity_name, entity_class in entities.items():
            # Calcular lag de sincronização
            now = datetime.now()
            recent_updates = (
                session.query(entity_class.updated_at_inhire)
                .filter(entity_class.updated_at_inhire.isnot(None))
                .order_by(entity_class.updated_at_inhire.desc())
                .limit(100)
                .all()
            )

            if recent_updates:
                avg_lag_minutes = sum(
                    (now - record.updated_at_inhire).total_seconds() / 60
                    for record in recent_updates
                ) / len(recent_updates)

                sync_lag_minutes.labels(entity=entity_name).set(avg_lag_minutes)

        logger.debug("Métricas de performance de sync coletadas")

    except Exception as e:
        logger.error(f"Erro ao coletar métricas de performance: {str(e)}")


def collect_trend_metrics(session: Session):
    """
    Coleta métricas de tendências e sazonalidade

    Args:
        session: Sessão SQLAlchemy
    """
    from models.database import Candidatura, Vaga

    try:
        # Novas aplicações nas últimas 24 horas
        last_24h = datetime.now() - timedelta(hours=24)

        applications_by_job = (
            session.query(
                Vaga.inhire_id,
                func.count(Candidatura.id).label('count')
            )
            .join(Candidatura, Candidatura.vaga_id == Vaga.id)
            .filter(Candidatura.created_at >= last_24h)
            .group_by(Vaga.inhire_id)
            .all()
        )

        for job in applications_by_job:
            new_applications_by_period.labels(
                period='24h',
                vaga_id=str(job.inhire_id)
            ).set(job.count)

        logger.debug(f"Métricas de tendência coletadas para {len(applications_by_job)} vagas")

    except Exception as e:
        logger.error(f"Erro ao coletar métricas de tendência: {str(e)}")


def collect_diversity_metrics(session: Session):
    """
    Coleta métricas de diversidade

    Args:
        session: Sessão SQLAlchemy
    """
    from models.database import Candidatura, Talento, Vaga

    try:
        # Distribuição por gênero
        gender_dist = (
            session.query(
                Vaga.inhire_id,
                Talento.gender,
                func.count(Candidatura.id).label('count')
            )
            .join(Candidatura, Candidatura.vaga_id == Vaga.id)
            .join(Talento, Candidatura.talento_id == Talento.id)
            .filter(Talento.gender.isnot(None))
            .group_by(Vaga.inhire_id, Talento.gender)
            .all()
        )

        # Calcular percentuais por vaga
        vaga_totals = {}
        for row in gender_dist:
            vaga_totals[row.inhire_id] = vaga_totals.get(row.inhire_id, 0) + row.count

        for row in gender_dist:
            if vaga_totals[row.inhire_id] > 0:
                pct = (row.count / vaga_totals[row.inhire_id]) * 100
                diversity_gender_distribution.labels(
                    gender=row.gender or 'not_specified',
                    vaga_id=str(row.inhire_id)
                ).set(pct)

        # Distribuição PCD
        pcd_dist = (
            session.query(
                Vaga.inhire_id,
                Talento.is_pcd,
                func.count(Candidatura.id).label('count')
            )
            .join(Candidatura, Candidatura.vaga_id == Vaga.id)
            .join(Talento, Candidatura.talento_id == Talento.id)
            .filter(Talento.is_pcd.isnot(None))
            .group_by(Vaga.inhire_id, Talento.is_pcd)
            .all()
        )

        for row in pcd_dist:
            if vaga_totals.get(row.inhire_id, 0) > 0:
                pct = (row.count / vaga_totals[row.inhire_id]) * 100
                diversity_pcd_distribution.labels(
                    is_pcd=str(row.is_pcd),
                    vaga_id=str(row.inhire_id)
                ).set(pct)

        logger.debug("Métricas de diversidade coletadas")

    except Exception as e:
        logger.error(f"Erro ao coletar métricas de diversidade: {str(e)}")


def collect_database_health_metrics(session: Session):
    """
    Coleta métricas de saúde do banco de dados

    Args:
        session: Sessão SQLAlchemy
    """
    try:
        # Tamanho do banco de dados
        result = session.execute(
            "SELECT pg_database_size(current_database()) / (1024*1024) as size_mb"
        ).fetchone()

        if result:
            database_size_mb.set(result[0])

        # Tamanho por tabela
        tables = [
            'vagas', 'posicoes', 'candidaturas', 'talentos',
            'candidatura_timeline', 'talento_arquivos', 'requisicoes'
        ]

        for table in tables:
            result = session.execute(
                f"SELECT pg_total_relation_size('{table}') / (1024*1024) as size_mb"
            ).fetchone()

            if result:
                table_size_mb.labels(table_name=table).set(result[0])

        # Conexões ativas
        result = session.execute(
            "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
        ).fetchone()

        if result:
            database_connections_active.set(result[0])

        logger.debug("Métricas de saúde do banco coletadas")

    except Exception as e:
        logger.error(f"Erro ao coletar métricas de saúde do banco: {str(e)}")


def collect_all_advanced_metrics(session: Session):
    """
    Coleta todas as métricas avançadas de uma vez

    Args:
        session: Sessão SQLAlchemy
    """
    logger.info("Iniciando coleta de métricas avançadas...")

    collect_recruitment_funnel_metrics(session)
    collect_time_to_hire_metrics(session)
    collect_data_quality_metrics(session)
    collect_sync_performance_metrics(session)
    collect_trend_metrics(session)
    collect_diversity_metrics(session)
    collect_database_health_metrics(session)

    logger.info("Coleta de métricas avançadas concluída")
