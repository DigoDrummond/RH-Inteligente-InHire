"""
Métodos UPSERT Melhorados - Comparação com Campos Específicos

Este arquivo contém versões melhoradas dos métodos upsert que comparam
campos específicos de cada tabela em vez de apenas updated_at_inhire.

COMO USAR:
1. Fazer backup de database_service.py
2. Copiar os métodos deste arquivo
3. Substituir os métodos correspondentes em database_service.py
4. Testar com dados reais

CAMPOS CRÍTICOS POR TABELA:
- Posições: status, hired_at, approved_at, opened_at, updated_at_inhire
- Candidaturas: status, stage_id/name, phase_id/name, updated_at_inhire
- Position Timeline: changed_at, new_status, previous_status, metadados
- Requisições: status, status_updated_at, approved_at, rejected_at
"""

from datetime import datetime
from typing import Optional, Dict, Any, tuple
from sqlalchemy.orm import Session

from models.database import (
    Vaga, Posicao, Candidatura, Talento, Requisicao,
    PositionTimeline, CandidaturaTimeline
)
from models.api_schemas import VagaAPI, PosicaoAPI, CandidaturaAPI, TalentoAPI
from models.new_api_schemas import RequisicaoAPI, PositionTimelineEventAPI


# ============================================================================
# MÉTODO 1: upsert_posicao (MELHORADO)
# ============================================================================

def upsert_posicao_improved(
    self,
    posicao_api: PosicaoAPI,
    commit=True
) -> tuple[bool, str]:
    """
    VERSÃO MELHORADA: Insere ou atualiza posição

    Compara campos específicos críticos:
    - status
    - hired_at
    - approved_at
    - opened_at
    - updated_at_inhire

    Lógica:
    1. Comparar updated_at_inhire (se API < BD ’ SKIP)
    2. Comparar campos críticos (se todos iguais ’ SKIP)
    3. Atualizar apenas se houve mudança real

    Returns:
        (is_new, operation) - (True/False, 'created'/'updated'/'skipped')
    """
    try:
        # Buscar vaga pai usando cache
        vaga_id = self.get_vaga_id_cached(posicao_api.jobId)
        if not vaga_id:
            self.logger.warning(
                f"FK órfão: Vaga {posicao_api.jobId} não encontrada "
                f"para posição {posicao_api.id}."
            )
            return False, 'skipped'

        existing = self.session.query(Posicao).filter_by(
            inhire_id=posicao_api.id
        ).first()

        if existing:
            # =================================================================
            # ETAPA 1: Comparar updated_at_inhire (campo principal)
            # =================================================================
            api_updated_at = self._normalize_datetime(posicao_api.updatedAt)

            if api_updated_at and existing.updated_at_inhire:
                # Se API está desatualizada, SKIP
                if api_updated_at < existing.updated_at_inhire:
                    return False, 'skipped'

            # =================================================================
            # ETAPA 2: Comparar campos específicos CRÍTICOS
            # =================================================================
            api_hired_at = self._normalize_datetime(posicao_api.hiredAt)
            api_opened_at = self._normalize_datetime(posicao_api.openedAt)
            api_approved_at = self._normalize_datetime(posicao_api.approvedAt)
            api_status = posicao_api.status

            # Verificar se TODOS os campos críticos são iguais
            campos_criticos_iguais = (
                api_hired_at == existing.hired_at and
                api_opened_at == existing.opened_at and
                api_approved_at == existing.approved_at and
                api_status == existing.status
            )

            # Se updated_at E campos críticos são iguais ’ SKIP
            if (api_updated_at == existing.updated_at_inhire and
                campos_criticos_iguais):
                return False, 'skipped'

            # =================================================================
            # ETAPA 3: Atualizar (pelo menos um campo mudou)
            # =================================================================

            # Campos críticos
            existing.status = api_status
            existing.hired_at = api_hired_at
            existing.opened_at = api_opened_at
            existing.approved_at = api_approved_at
            existing.updated_at_inhire = api_updated_at

            # Outros campos
            existing.requisition_id = posicao_api.requisitionId
            existing.reason = posicao_api.reason
            existing.talent_id = posicao_api.talentId
            existing.time_in_current_stage = posicao_api.timeInCurrentStage
            existing.user_id = posicao_api.userId
            existing.user_name = posicao_api.userName

            if commit:
                self.session.commit()
            return False, 'updated'

        # =================================================================
        # Criar nova posição
        # =================================================================
        nova_posicao = Posicao(
            inhire_id=posicao_api.id,
            vaga_id=vaga_id,
            requisition_id=posicao_api.requisitionId,
            reason=posicao_api.reason,
            status=posicao_api.status,
            talent_id=posicao_api.talentId,
            time_in_current_stage=posicao_api.timeInCurrentStage,
            approved_at=self._normalize_datetime(posicao_api.approvedAt),
            hired_at=self._normalize_datetime(posicao_api.hiredAt),
            opened_at=self._normalize_datetime(posicao_api.openedAt),
            user_id=posicao_api.userId,
            user_name=posicao_api.userName,
            created_at_inhire=self._normalize_datetime(posicao_api.createdAt),
            updated_at_inhire=self._normalize_datetime(posicao_api.updatedAt)
        )

        self.session.add(nova_posicao)
        if commit:
            self.session.commit()
        return True, 'created'

    except Exception as e:
        self.session.rollback()
        self.logger.error(f"Erro ao upsert posição {posicao_api.id}: {str(e)}")
        raise


# ============================================================================
# MÉTODO 2: upsert_candidatura (MELHORADO)
# ============================================================================

def upsert_candidatura_improved(
    self,
    cand_api: CandidaturaAPI,
    job_id: str,
    commit=True
) -> tuple[bool, str]:
    """
    VERSÃO MELHORADA: Insere ou atualiza candidatura

    Compara campos específicos críticos:
    - status
    - stage_id, stage_name
    - phase_id, phase_name
    - updated_at_inhire

    Lógica:
    1. Comparar updated_at_inhire
    2. Comparar stage/phase (mudanças críticas)
    3. Atualizar apenas se houve mudança

    Returns:
        (is_new, operation) - (True/False, 'created'/'updated'/'skipped')
    """
    try:
        # Buscar vaga usando cache
        vaga_id = self.get_vaga_id_cached(job_id)
        if not vaga_id:
            self.logger.warning(
                f"FK órfão: Vaga {job_id} não encontrada "
                f"para candidatura {cand_api.id}."
            )
            return False, 'skipped'

        # Normalizar status
        status_normalized = cand_api.status.lower() if cand_api.status else None

        # Lookup do talento
        talento_id = None
        if cand_api.talentId:
            talento_id = self.get_talento_id_cached(cand_api.talentId)

        existing = self.session.query(Candidatura).filter_by(
            inhire_id=cand_api.id
        ).first()

        if existing:
            # =================================================================
            # ETAPA 1: Comparar updated_at_inhire
            # =================================================================
            api_updated_at = self._normalize_datetime(cand_api.updatedAt)

            if api_updated_at and existing.updated_at_inhire:
                if api_updated_at < existing.updated_at_inhire:
                    return False, 'skipped'

            # =================================================================
            # ETAPA 2: Comparar campos específicos CRÍTICOS
            # =================================================================
            api_stage_id = cand_api.stage.id if cand_api.stage else None
            api_stage_name = cand_api.stage.name if cand_api.stage else None
            api_phase_id = cand_api.phase.id if cand_api.phase else None
            api_phase_name = cand_api.phase.name if cand_api.phase else None

            # Verificar se campos críticos são iguais
            campos_criticos_iguais = (
                status_normalized == existing.status and
                api_stage_id == existing.stage_id and
                api_stage_name == existing.stage_name and
                api_phase_id == existing.phase_id and
                api_phase_name == existing.phase_name
            )

            # Se updated_at E campos críticos são iguais ’ SKIP
            if (api_updated_at == existing.updated_at_inhire and
                campos_criticos_iguais):
                return False, 'skipped'

            # =================================================================
            # ETAPA 3: Atualizar (pelo menos um campo mudou)
            # =================================================================

            # Campos críticos
            existing.status = status_normalized
            existing.stage_id = api_stage_id
            existing.stage_name = api_stage_name
            existing.stage_order = cand_api.stage.order if cand_api.stage else None
            existing.phase_id = api_phase_id
            existing.phase_name = api_phase_name
            existing.phase_order = cand_api.phase.order if cand_api.phase else None
            existing.updated_at_inhire = api_updated_at

            # Outros campos
            existing.talento_id = talento_id
            existing.source = cand_api.source
            existing.time_in_current_stage = cand_api.timeInCurrentStage
            existing.user_id = cand_api.userId
            existing.user_name = cand_api.userName

            if commit:
                self.session.commit()
            return False, 'updated'

        # =================================================================
        # Criar nova candidatura
        # =================================================================
        updated_at_inhire = self._normalize_datetime(cand_api.updatedAt)
        created_at = updated_at_inhire if updated_at_inhire else datetime.utcnow()

        nova_cand = Candidatura(
            inhire_id=cand_api.id,
            vaga_id=vaga_id,
            talento_id=talento_id,
            talent_inhire_id=cand_api.talentId,
            source=cand_api.source,
            status=status_normalized,
            stage_id=cand_api.stage.id if cand_api.stage else None,
            stage_name=cand_api.stage.name if cand_api.stage else None,
            stage_order=cand_api.stage.order if cand_api.stage else None,
            phase_id=cand_api.phase.id if cand_api.phase else None,
            phase_name=cand_api.phase.name if cand_api.phase else None,
            phase_order=cand_api.phase.order if cand_api.phase else None,
            time_in_current_stage=cand_api.timeInCurrentStage,
            talent_name=cand_api.talent.name if cand_api.talent else None,
            talent_email=cand_api.talent.email if cand_api.talent else None,
            talent_headline=cand_api.talent.headline if cand_api.talent else None,
            talent_company=cand_api.talent.company if cand_api.talent else None,
            talent_location=cand_api.talent.location if cand_api.talent else None,
            user_id=cand_api.userId,
            user_name=cand_api.userName,
            updated_at_inhire=updated_at_inhire,
            created_at=created_at
        )

        self.session.add(nova_cand)
        if commit:
            self.session.commit()
        return True, 'created'

    except Exception as e:
        self.session.rollback()
        self.logger.error(f"Erro ao upsert candidatura {cand_api.id}: {str(e)}")
        raise


# ============================================================================
# MÉTODO 3: upsert_position_timeline (MELHORADO)
# ============================================================================

def upsert_position_timeline_improved(
    self,
    event_api: PositionTimelineEventAPI,
    posicao_db_id: int = None,
    vaga_db_id: int = None,
    commit=True
) -> tuple[bool, str]:
    """
    VERSÃO MELHORADA: Insere ou atualiza evento de timeline

    Compara campos específicos:
    - changed_at (identificação única do evento)
    - new_status
    - previous_status
    - Metadados (changed_by, reason, notes)

    Returns:
        (is_new, operation) - (True/False, 'created'/'updated'/'skipped')
    """
    try:
        # Buscar posição se não fornecido
        if not posicao_db_id:
            posicao_bd = self.session.query(Posicao).filter_by(
                inhire_id=event_api.positionId
            ).first()
            if not posicao_bd:
                self.logger.warning(
                    f"Posição {event_api.positionId} não encontrada."
                )
                return False, 'skipped'
            posicao_db_id = posicao_bd.id

        # Buscar vaga se não fornecido
        if not vaga_db_id:
            vaga_bd = self.session.query(Vaga).filter_by(
                inhire_id=event_api.jobId
            ).first()
            if vaga_bd:
                vaga_db_id = vaga_bd.id

        # =================================================================
        # ETAPA 1: Verificar se evento já existe (campos únicos)
        # =================================================================
        api_changed_at = self._normalize_datetime(event_api.changedAt)

        existing = self.session.query(PositionTimeline).filter_by(
            posicao_id=posicao_db_id,
            changed_at=api_changed_at,
            new_status=event_api.newStatus
        ).first()

        if existing:
            # =============================================================
            # ETAPA 2: Comparar metadados do evento
            # =============================================================
            metadados_iguais = (
                existing.changed_by == event_api.changedBy and
                existing.changed_by_name == event_api.changedByName and
                existing.reason == event_api.reason and
                existing.notes == event_api.notes and
                existing.previous_status == event_api.previousStatus
            )

            # Se metadados iguais ’ SKIP
            if metadados_iguais:
                return False, 'skipped'

            # =============================================================
            # ETAPA 3: Atualizar metadados
            # =============================================================
            existing.changed_by = event_api.changedBy
            existing.changed_by_name = event_api.changedByName
            existing.reason = event_api.reason
            existing.notes = event_api.notes
            existing.previous_status = event_api.previousStatus
            existing.event_metadata = event_api.eventMetadata

            if commit:
                self.session.commit()
            return False, 'updated'

        # =================================================================
        # Criar novo evento
        # =================================================================
        novo_evento = PositionTimeline(
            posicao_id=posicao_db_id,
            vaga_id=vaga_db_id,
            previous_status=event_api.previousStatus,
            new_status=event_api.newStatus,
            changed_at=api_changed_at,
            changed_by=event_api.changedBy,
            changed_by_name=event_api.changedByName,
            reason=event_api.reason,
            notes=event_api.notes,
            event_metadata=event_api.eventMetadata
        )

        self.session.add(novo_evento)
        if commit:
            self.session.commit()
        return True, 'created'

    except Exception as e:
        self.session.rollback()
        self.logger.error(
            f"Erro ao upsert timeline: {str(e)}"
        )
        raise


# ============================================================================
# RESUMO DAS MELHORIAS
# ============================================================================

"""
ANTES (Lógica Atual):
  if API.updatedAt <= BD.updated_at_inhire:
      return 'skipped'

DEPOIS (Lógica Melhorada):
  if API.updatedAt < BD.updated_at_inhire:
      return 'skipped'

  if API.updatedAt == BD.updated_at_inhire AND
     campos_criticos_iguais:
      return 'skipped'

  # Atualizar (houve mudança real)

CAMPOS CRÍTICOS POR TABELA:
  Posições: status, hired_at, approved_at, opened_at
  Candidaturas: status, stage_id/name, phase_id/name
  Position Timeline: changed_at, new_status, metadados
  Requisições: status, status_updated_at, approved_at, rejected_at

BENEFÍCIOS:
 Detecção mais precisa de mudanças
 Redução de updates desnecessários
 Campos críticos sempre atualizados
 Melhor performance (menos writes)
"""
