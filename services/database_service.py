"""
Serviço de Banco de Dados
Gerencia todas as operações de persistência (UPSERT) no PostgreSQL
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from interfaces.i_database_service import IDatabaseService
from repositories.vaga_repository import VagaRepository
from repositories.posicao_repository import PosicaoRepository
from repositories.candidatura_repository import CandidaturaRepository
from repositories.talento_repository import TalentoRepository
from models.database import (
    Vaga, Posicao, Candidatura, Talento,
    SyncConfiguration, SyncLog, CandidaturaTimeline, PositionTimeline,
    Requisicao, VagaTag, Cliente
)
from models.api_schemas import VagaAPI, PosicaoAPI, CandidaturaAPI, TalentoAPI
from models.new_api_schemas import (
    RequisicaoAPI, VagaTagAPI, ClienteAPI,
    PositionTimelineEventAPI
)
from utils.logger import get_logger, log_database_operation
from config import SyncType, SyncStatus, SyncEntity


class DatabaseService(IDatabaseService):
    """Serviço para operações de banco de dados"""

    def __init__(self, session: Session):
        self.session = session
        self.logger = get_logger(__name__)

        # REPOSITORIES: Camada de acesso a dados
        self.vaga_repo = VagaRepository(session)
        self.posicao_repo = PosicaoRepository(session)
        self.candidatura_repo = CandidaturaRepository(session)
        self.talento_repo = TalentoRepository(session)

        # CACHE: Dicionários para FK lookups (reduz queries de N para 1)
        self._vaga_cache: Dict[str, int] = {}  # {inhire_id: db_id}
        self._talento_cache: Dict[str, int] = {}  # {inhire_id: db_id}
        self._cache_populated = False

    @staticmethod
    def _convert_custom_fields_to_dict(custom_fields: Any) -> Optional[Dict[str, Any]]:
        """
        Converte custom_fields da API para o formato de dicionário esperado.

        A API pode retornar:
        - Dict[str, Any]: Formato correto {field_id: [valores]}
        - List[Dict]: Formato antigo [{"id": "field_id", "value": ["valores"]}]
        - None: Sem custom fields

        Returns:
            Dict no formato {field_id: [valores]} ou None
        """
        if not custom_fields:
            return None

        # Se já é um dicionário, retornar como está
        if isinstance(custom_fields, dict):
            return custom_fields

        # Se é uma lista, converter para dicionário
        if isinstance(custom_fields, list):
            result = {}
            for field in custom_fields:
                if isinstance(field, dict):
                    field_id = field.get('id') or field.get('name')
                    field_value = field.get('value', [])

                    # Garantir que value é uma lista
                    if not isinstance(field_value, list):
                        field_value = [field_value] if field_value else []

                    if field_id:
                        result[field_id] = field_value

            return result if result else None

        # Formato desconhecido, retornar None
        return None

    def populate_fk_cache(self) -> None:
        """
        Popula cache de FKs com todas as vagas e talentos do banco.
        Chame isso antes de sync em massa para otimizar performance.

        Reduz queries de ~300+ para 2 (1 para vagas, 1 para talentos).
        """
        if self._cache_populated:
            return

        self.logger.info("Populando cache de FK lookups...")

        # Usar repositories para popular cache
        self._vaga_cache = self.vaga_repo.get_all_id_mappings()
        self._talento_cache = self.talento_repo.get_all_id_mappings()

        self._cache_populated = True
        self.logger.info(
            f"✓ Cache populado: {len(self._vaga_cache)} vagas, "
            f"{len(self._talento_cache)} talentos"
        )

    def clear_fk_cache(self) -> None:
        """Limpa cache de FKs. Útil após inserções de novas vagas/talentos."""
        self._vaga_cache.clear()
        self._talento_cache.clear()
        self._cache_populated = False
        self.logger.debug("Cache de FK limpo")

    def batch_commit(self, batch_size: int = 50) -> None:
        """
        Faz commit em batch para otimizar performance.

        Args:
            batch_size: Número de operações antes de fazer commit (padrão: 50)

        Usage:
            # Processar 100 registros com batch de 50
            for i, record in enumerate(records):
                db_service.upsert_vaga(record, commit=False)
                if (i + 1) % 50 == 0:
                    db_service.batch_commit()
            # Commit final para registros remanescentes
            db_service.batch_commit()
        """
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao fazer batch commit: {str(e)}")
            raise

    # ========================================
    # SAVEPOINTS: Transações Aninhadas
    # ========================================

    def create_savepoint(self, name: str) -> None:
        """
        Cria um savepoint (checkpoint) na transação atual.

        Savepoints permitem rollback parcial sem perder toda a transação.
        Útil para sincronizações longas onde queremos manter progresso.

        Args:
            name: Nome do savepoint (ex: 'after_vagas', 'after_posicoes')

        Usage:
            db.create_savepoint('after_vagas')
            # ... processar posições ...
            if error:
                db.rollback_to_savepoint('after_vagas')  # Volta só posições

        Note:
            SQLAlchemy usa begin_nested() para criar SAVEPOINTs
        """
        try:
            self.session.begin_nested()
            self.logger.info(f"Savepoint criado: {name}")
        except Exception as e:
            self.logger.error(f"Erro ao criar savepoint {name}: {str(e)}")
            raise

    def rollback_to_savepoint(self, name: str = None) -> None:
        """
        Faz rollback para o último savepoint.

        Args:
            name: Nome do savepoint (apenas para logging, SQLAlchemy gerencia automaticamente)

        Usage:
            db.create_savepoint('checkpoint1')
            # ... operações ...
            if error:
                db.rollback_to_savepoint('checkpoint1')
        """
        try:
            self.session.rollback()  # Rollback do nested transaction
            log_msg = f"Rollback para savepoint: {name}" if name else "Rollback para último savepoint"
            self.logger.warning(log_msg)
        except Exception as e:
            self.logger.error(f"Erro ao fazer rollback para savepoint {name}: {str(e)}")
            raise

    def release_savepoint(self, name: str = None) -> None:
        """
        Libera um savepoint (confirma as mudanças desde o savepoint).

        Args:
            name: Nome do savepoint (apenas para logging)

        Usage:
            db.create_savepoint('checkpoint1')
            # ... operações bem-sucedidas ...
            db.release_savepoint('checkpoint1')  # Confirma mudanças
        """
        try:
            self.session.commit()  # Commit do nested transaction
            log_msg = f"Savepoint liberado: {name}" if name else "Savepoint liberado"
            self.logger.debug(log_msg)
        except Exception as e:
            self.logger.error(f"Erro ao liberar savepoint {name}: {str(e)}")
            raise

    def get_vaga_id_cached(self, inhire_id: str) -> Optional[int]:
        """
        Busca vaga_id usando cache. Se cache vazio, faz query no banco.

        Args:
            inhire_id: ID da vaga na API InHire

        Returns:
            ID interno do banco ou None se não encontrado
        """
        # Tentar cache primeiro
        if inhire_id in self._vaga_cache:
            return self._vaga_cache[inhire_id]

        # Cache miss: buscar no banco e atualizar cache
        vaga = self.session.query(Vaga).filter_by(inhire_id=inhire_id).first()
        if vaga:
            self._vaga_cache[inhire_id] = vaga.id
            return vaga.id

        return None

    def get_talento_id_cached(self, inhire_id: str) -> Optional[int]:
        """
        Busca talento_id usando cache. Se cache vazio, faz query no banco.

        Args:
            inhire_id: ID do talento na API InHire

        Returns:
            ID interno do banco ou None se não encontrado
        """
        # Tentar cache primeiro
        if inhire_id in self._talento_cache:
            return self._talento_cache[inhire_id]

        # Cache miss: buscar no banco e atualizar cache
        talento = self.session.query(Talento).filter_by(inhire_id=inhire_id).first()
        if talento:
            self._talento_cache[inhire_id] = talento.id
            return talento.id

        return None

    @staticmethod
    @staticmethod
    def _convert_datetime_to_str(obj: Any) -> Any:
        """
        Converte recursivamente objetos datetime para strings ISO 8601.
        Necessário porque PostgreSQL JSON não aceita objetos datetime Python.
        """
        from datetime import datetime
        from uuid import UUID
        from decimal import Decimal

        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (UUID, Decimal)):
            return str(obj)
        elif isinstance(obj, dict):
            return {key: DatabaseService._convert_datetime_to_str(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [DatabaseService._convert_datetime_to_str(item) for item in obj]
        else:
            return obj

    def _serialize_pydantic_to_dict(self, obj: Any) -> Optional[Dict]:
        """
        Converte objeto Pydantic ou lista de objetos Pydantic para dicionário compatível com PostgreSQL JSONB.

        IMPORTANTE: Usa model_dump(exclude_none=True) para performance, depois converte datetime->str
        para compatibilidade com PostgreSQL JSON (não aceita objetos datetime Python).
        """
        if obj is None:
            return None

        if isinstance(obj, list):
            result = [item.model_dump(exclude_none=True) if hasattr(item, 'model_dump') else item for item in obj]
            return DatabaseService._convert_datetime_to_str(result)
        elif isinstance(obj, dict):
            # Se já é um dict, converter valores que são Pydantic
            result = {}
            for key, value in obj.items():
                if isinstance(value, list):
                    result[key] = [v.model_dump(exclude_none=True) if hasattr(v, 'model_dump') else v for v in value]
                elif hasattr(value, 'model_dump'):
                    result[key] = value.model_dump(exclude_none=True)
                else:
                    result[key] = value
            return DatabaseService._convert_datetime_to_str(result)
        elif hasattr(obj, 'model_dump'):
            result = obj.model_dump(exclude_none=True)
            return DatabaseService._convert_datetime_to_str(result)

        return obj

    @staticmethod
    def _normalize_datetime(dt: Optional[datetime]) -> Optional[datetime]:
        """
        Normaliza datetime para timezone-naive em horário de São Paulo
        Converte para America/Sao_Paulo e remove timezone info para salvar no banco
        Aceita datetime objects ou strings ISO 8601
        """
        if dt is None:
            return None

        # Se for string, converter para datetime primeiro
        if isinstance(dt, str):
            from dateutil import parser
            try:
                dt = parser.isoparse(dt)
            except Exception:
                return None

        if dt.tzinfo is not None:
            # Converter para timezone de São Paulo
            import pytz
            sp_tz = pytz.timezone('America/Sao_Paulo')
            dt_sp = dt.astimezone(sp_tz)
            # Remover timezone info mantendo horário de São Paulo
            return dt_sp.replace(tzinfo=None)

        # Se já é naive, assume que está em São Paulo
        return dt

    def _fix_date_inconsistency(self, created_at, updated_at, entity_name: str, entity_id: str) -> tuple:
        """
        Valida e corrige inconsistências de datas onde created_at > updated_at

        Args:
            created_at: Data de criação
            updated_at: Data de atualização
            entity_name: Nome da entidade (para log)
            entity_id: ID da entidade (para log)

        Returns:
            tuple[datetime, datetime]: (created_at_corrigido, updated_at_corrigido)
        """
        # Normalizar as datas
        created_normalized = self._normalize_datetime(created_at) if created_at else None
        updated_normalized = self._normalize_datetime(updated_at) if updated_at else None

        # Se alguma data estiver ausente, retornar as normalizadas
        if not created_normalized or not updated_normalized:
            return created_normalized, updated_normalized

        # Verificar se created_at > updated_at (inconsistência lógica)
        if created_normalized > updated_normalized:
            self.logger.warning(
                f"INCONSISTÊNCIA DE DATAS detectada em {entity_name} {entity_id}: "
                f"created_at ({created_normalized}) > updated_at ({updated_normalized}). "
                f"Ajustando: ambas as datas serão definidas como updated_at ({updated_normalized})."
            )
            # Usar a data mais recente (updated_at) para ambas
            # Isso mantém a lógica de que a entidade foi "criada e atualizada" no mesmo momento
            return updated_normalized, updated_normalized

        return created_normalized, updated_normalized

    def upsert_vaga(self, vaga_api: VagaAPI, commit=True) -> tuple[bool, str]:
        """
        Insere ou atualiza vaga no banco

        Args:
            vaga_api: Dados da vaga da API
            commit: Se True, faz commit imediato. Se False, acumula para batch commit.

        Returns:
            (is_new, operation) - (True/False, 'created'/'updated'/'skipped')
        """
        try:
            existing = self.session.query(Vaga).filter_by(inhire_id=vaga_api.id).first()

            if existing:
                # Verificar se precisa atualizar
                if vaga_api.updatedAt and existing.updated_at_inhire:
                    updated_at_normalized = self._normalize_datetime(vaga_api.updatedAt)
                    if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
                        return False, 'skipped'

                # Atualizar
                existing.name = vaga_api.name
                existing.description = vaga_api.description
                existing.area = vaga_api.area
                existing.status = vaga_api.status
                existing.seniority = vaga_api.seniority
                existing.accepted_seniority = vaga_api.acceptedSeniority
                existing.location_required = vaga_api.locationRequired
                existing.talent_suggestions = vaga_api.talentSuggestions
                existing.salary_max = vaga_api.salaryMax
                existing.sla = vaga_api.sla
                existing.sla_days_goal = vaga_api.slaDaysGoal
                existing.active_talents = vaga_api.activeTalents
                existing.open_positions = vaga_api.openPositions
                existing.user_id = vaga_api.userId
                existing.user_name = vaga_api.userName
                existing.manager_id = vaga_api.managerId
                existing.recruiter_id = vaga_api.recruiterId
                existing.evaluator_ids = vaga_api.evaluatorIds
                existing.tenant_client_id = vaga_api.tenantClientId
                existing.origin_id = vaga_api.originId

                # Migration 051: Campos opcionais
                existing.specialization = vaga_api.specialization
                existing.vaga_metadata = {
                    'duplicateFrom': vaga_api.duplicateFrom,
                    'duplication': vaga_api.duplication
                } if (vaga_api.duplicateFrom or vaga_api.duplication) else None

                # Validar que updated_at não seja menor que created_at
                new_updated_at = self._normalize_datetime(vaga_api.updatedAt)
                if new_updated_at and existing.created_at_inhire and new_updated_at < existing.created_at_inhire:
                    self.logger.warning(
                        f"INCONSISTÊNCIA DE DATAS detectada ao atualizar Vaga {vaga_api.id}: "
                        f"novo updated_at ({new_updated_at}) < created_at existente ({existing.created_at_inhire}). "
                        f"Ajustando updated_at para created_at."
                    )
                    existing.updated_at_inhire = existing.created_at_inhire
                else:
                    existing.updated_at_inhire = new_updated_at

                existing.updated_at = datetime.utcnow()

                if commit:
                    self.session.commit()
                return False, 'updated'

            # Criar nova
            # Validar e corrigir datas inconsistentes antes de criar
            created_at_fixed, updated_at_fixed = self._fix_date_inconsistency(
                vaga_api.createdAt,
                vaga_api.updatedAt,
                "Vaga",
                vaga_api.id
            )

            nova_vaga = Vaga(
                inhire_id=vaga_api.id,
                name=vaga_api.name,
                description=vaga_api.description,
                area=vaga_api.area,
                status=vaga_api.status,
                seniority=vaga_api.seniority,
                accepted_seniority=vaga_api.acceptedSeniority,
                location_required=vaga_api.locationRequired,
                talent_suggestions=vaga_api.talentSuggestions,
                salary_max=vaga_api.salaryMax,
                sla=vaga_api.sla,
                sla_days_goal=vaga_api.slaDaysGoal,
                active_talents=vaga_api.activeTalents,
                open_positions=vaga_api.openPositions,
                user_id=vaga_api.userId,
                user_name=vaga_api.userName,
                manager_id=vaga_api.managerId,
                recruiter_id=vaga_api.recruiterId,
                evaluator_ids=vaga_api.evaluatorIds,
                tenant_client_id=vaga_api.tenantClientId,
                origin_id=vaga_api.originId,
                # Migration 051: Campos opcionais
                specialization=vaga_api.specialization,
                vaga_metadata={
                    'duplicateFrom': vaga_api.duplicateFrom,
                    'duplication': vaga_api.duplication
                } if (vaga_api.duplicateFrom or vaga_api.duplication) else None,
                created_at_inhire=created_at_fixed,
                updated_at_inhire=updated_at_fixed
            )

            self.session.add(nova_vaga)
            if commit:
                self.session.commit()
            return True, 'created'

        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao upsert vaga {vaga_api.id}: {str(e)}")
            raise

    def upsert_posicao(self, posicao_api: PosicaoAPI, commit=True) -> tuple[bool, str]:
        """
        Insere ou atualiza posição
        VERSÃO MELHORADA: Compara campos específicos (status, hired_at, approved_at, opened_at)
        """
        try:
            # OTIMIZAÇÃO: Buscar vaga pai usando cache
            vaga_id = self.get_vaga_id_cached(posicao_api.jobId)
            if not vaga_id:
                self.logger.warning(
                    f"FK órfão detectado: Vaga {posicao_api.jobId} não encontrada para posição {posicao_api.id}. "
                    f"Sincronize vagas antes de posições."
                )
                return False, 'skipped'

            existing = self.session.query(Posicao).filter_by(inhire_id=posicao_api.id).first()

            if existing:
                # ETAPA 1: Comparar updated_at_inhire (campo principal)
                api_updated_at = self._normalize_datetime(posicao_api.updatedAt)

                if api_updated_at and existing.updated_at_inhire:
                    # Se API está desatualizada, SKIP
                    if api_updated_at < existing.updated_at_inhire:
                        return False, 'skipped'

                # ETAPA 2: Comparar campos específicos CRÍTICOS
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

                # Se updated_at E campos críticos são iguais → SKIP
                if (api_updated_at == existing.updated_at_inhire and campos_criticos_iguais):
                    return False, 'skipped'

                # ETAPA 3: Atualizar (pelo menos um campo mudou)
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

            # Criar nova posição
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

    def upsert_position_timeline(
        self,
        event_api: PositionTimelineEventAPI,
        posicao_db_id: int = None,
        vaga_db_id: int = None,
        commit=True
    ) -> tuple[bool, str]:
        """
        Insere ou atualiza evento de timeline de posição

        Args:
            event_api: Dados do evento da API
            posicao_db_id: ID da posição no banco (opcional, será buscado se não fornecido)
            vaga_db_id: ID da vaga no banco (opcional, será buscado se não fornecido)
            commit: Se deve fazer commit

        Returns:
            Tupla (is_new, operation) onde operation é 'created', 'updated' ou 'skipped'
        """
        try:
            # Buscar posição pelo inhire_id se não fornecido
            if not posicao_db_id:
                posicao_bd = self.session.query(Posicao).filter_by(inhire_id=event_api.positionId).first()
                if not posicao_bd:
                    self.logger.warning(
                        f"Posição {event_api.positionId} não encontrada para evento de timeline. "
                        f"Sincronize posições antes de timeline."
                    )
                    return False, 'skipped'
                posicao_db_id = posicao_bd.id

            # Buscar vaga pelo inhire_id se não fornecido
            if not vaga_db_id:
                vaga_bd = self.session.query(Vaga).filter_by(inhire_id=event_api.jobId).first()
                if vaga_bd:
                    vaga_db_id = vaga_bd.id

            # Gerar um ID único para o evento (combinação de positionId + changedAt + newStatus)
            # Isso previne duplicatas quando o mesmo evento é sincronizado múltiplas vezes
            event_unique_key = f"{event_api.positionId}_{event_api.changedAt.isoformat()}_{event_api.newStatus}"

            # Verificar se já existe um evento idêntico
            # Como não temos inhire_id para eventos de timeline, usamos campos únicos
            existing = self.session.query(PositionTimeline).filter_by(
                posicao_id=posicao_db_id,
                changed_at=self._normalize_datetime(event_api.changedAt),
                new_status=event_api.newStatus
            ).first()

            if existing:
                # Evento já existe - atualizar apenas se houver novos dados
                updated = False

                if event_api.changedBy and existing.changed_by != event_api.changedBy:
                    existing.changed_by = event_api.changedBy
                    updated = True

                if event_api.changedByName and existing.changed_by_name != event_api.changedByName:
                    existing.changed_by_name = event_api.changedByName
                    updated = True

                if event_api.reason and existing.reason != event_api.reason:
                    existing.reason = event_api.reason
                    updated = True

                if event_api.notes and existing.notes != event_api.notes:
                    existing.notes = event_api.notes
                    updated = True

                if event_api.previousStatus and existing.previous_status != event_api.previousStatus:
                    existing.previous_status = event_api.previousStatus
                    updated = True

                if event_api.eventMetadata and existing.event_metadata != event_api.eventMetadata:
                    existing.event_metadata = event_api.eventMetadata
                    updated = True

                if updated:
                    if commit:
                        self.session.commit()
                    return False, 'updated'
                else:
                    return False, 'skipped'

            # Criar novo evento
            novo_evento = PositionTimeline(
                posicao_id=posicao_db_id,
                vaga_id=vaga_db_id,
                previous_status=event_api.previousStatus,
                new_status=event_api.newStatus,
                changed_at=self._normalize_datetime(event_api.changedAt),
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

        except IntegrityError as e:
            self.session.rollback()
            # Duplicate - provavelmente evento já existe
            self.logger.debug(f"Evento de timeline duplicado para posição {event_api.positionId}: {str(e)}")
            return False, 'skipped'

        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao upsert position timeline para posição {event_api.positionId}: {str(e)}")
            raise

    def upsert_candidatura(self, cand_api: CandidaturaAPI, job_id: str, commit=True) -> tuple[bool, str]:
        """
        Insere ou atualiza candidatura
        VERSÃO MELHORADA: Compara campos específicos (status, stage_id/name, phase_id/name)
        """
        try:
            # OTIMIZAÇÃO: Buscar vaga usando cache
            vaga_id = self.get_vaga_id_cached(job_id)
            if not vaga_id:
                # LOG WARNING: Vaga não encontrada (FK órfão)
                self.logger.warning(
                    f"FK órfão detectado: Vaga {job_id} não encontrada para candidatura {cand_api.id}. "
                    f"Sincronize vagas antes de candidaturas."
                )
                return False, 'skipped'

            # Normalizar status para lowercase (API retorna uppercase, enum espera lowercase)
            status_normalized = cand_api.status.lower() if cand_api.status else None

            # OTIMIZAÇÃO: Lookup do talento usando cache
            talento_id = None
            if cand_api.talentId:
                talento_id = self.get_talento_id_cached(cand_api.talentId)

                # LOG WARNING: Talento não encontrado (FK órfão opcional)
                if not talento_id:
                    self.logger.warning(
                        f"FK órfão detectado: Talento {cand_api.talentId} não encontrado para candidatura {cand_api.id}. "
                        f"FK será None até sincronização de talentos."
                    )

            existing = self.session.query(Candidatura).filter_by(inhire_id=cand_api.id).first()

            if existing:
                # ETAPA 1: Comparar updated_at_inhire
                api_updated_at = self._normalize_datetime(cand_api.updatedAt)

                if api_updated_at and existing.updated_at_inhire:
                    if api_updated_at < existing.updated_at_inhire:
                        return False, 'skipped'

                # ETAPA 2: Comparar campos específicos CRÍTICOS
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

                # Se updated_at E campos críticos são iguais → SKIP
                if (api_updated_at == existing.updated_at_inhire and campos_criticos_iguais):
                    return False, 'skipped'

                # ETAPA 3: Atualizar (pelo menos um campo mudou)
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

                # Dados do talento embutidos na candidatura (corrigido em 2026-02-18)
                # Atualiza talent_name e talent_email se a API retornar dados do talento,
                # mantendo o valor existente caso a API retorne None (para não sobrescrever com NULL)
                if cand_api.talent:
                    if cand_api.talent.name:
                        existing.talent_name = cand_api.talent.name
                    if cand_api.talent.email:
                        existing.talent_email = cand_api.talent.email

                # Migration 051: Metadados completos de stage e phase
                existing.stage_metadata = self._serialize_pydantic_to_dict(cand_api.stage) if cand_api.stage else None
                existing.phase_metadata = self._serialize_pydantic_to_dict(cand_api.phase) if cand_api.phase else None

                # Migration 069: Custom fields responses (JOB_TALENTS)
                if hasattr(cand_api, 'customFields') and cand_api.customFields:
                    existing.custom_fields = self._convert_custom_fields_to_dict(cand_api.customFields)

                if commit:
                    self.session.commit()
                return False, 'updated'

            # Normalizar updated_at_inhire
            updated_at_inhire = self._normalize_datetime(cand_api.updatedAt)

            # IMPORTANTE: Definir created_at para respeitar constraint chk_candidatura_dates_logical
            # created_at deve ser <= updated_at_inhire para satisfazer a constraint
            # Usar o menor valor entre updated_at_inhire e NOW()
            from datetime import datetime
            created_at = updated_at_inhire if updated_at_inhire else datetime.utcnow()

            nova_cand = Candidatura(
                inhire_id=cand_api.id,
                vaga_id=vaga_id,  # Usando cache
                talento_id=talento_id,  # FK para talentos (usando cache)
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
                created_at=created_at,  # Definir explicitamente para respeitar constraint
                # Migration 051: Metadados completos de stage e phase
                stage_metadata=self._serialize_pydantic_to_dict(cand_api.stage) if cand_api.stage else None,
                phase_metadata=self._serialize_pydantic_to_dict(cand_api.phase) if cand_api.phase else None,
                # Migration 069: Custom fields responses (JOB_TALENTS)
                custom_fields=self._convert_custom_fields_to_dict(cand_api.customFields) if hasattr(cand_api, 'customFields') else None
            )

            self.session.add(nova_cand)
            if commit:
                self.session.commit()
            return True, 'created'

        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao upsert candidatura {cand_api.id}: {str(e)}")
            raise

    def upsert_talento(self, talento_api: TalentoAPI, commit=True) -> tuple[bool, str]:
        """Insere ou atualiza talento completo"""
        try:
            existing = self.session.query(Talento).filter_by(inhire_id=talento_api.id).first()

            if existing:
                if talento_api.updatedAt and existing.updated_at_inhire:
                    updated_at_normalized = self._normalize_datetime(talento_api.updatedAt)
                    if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
                        return False, 'skipped'

                existing.name = talento_api.name
                existing.email = talento_api.email
                existing.phone = talento_api.phone
                existing.headline = talento_api.headline
                existing.company = talento_api.company
                existing.location = talento_api.location
                existing.picture = talento_api.picture
                existing.linkedin_username = talento_api.linkedinUsername
                existing.contact_method = talento_api.contactMethod
                existing.status = talento_api.status
                existing.user_id = talento_api.userId
                existing.user_name = talento_api.userName
                existing.resume = talento_api.resume

                # Extrair e salvar dados de diversidade em colunas dedicadas
                attributes_dict = self._serialize_pydantic_to_dict(talento_api.attributes)
                existing.diversity_black = self._extract_diversity_value(attributes_dict, 'diversityBlack')
                existing.diversity_woman = self._extract_diversity_value(attributes_dict, 'diversityWoman')
                existing.diversity_lgbt = self._extract_diversity_value(attributes_dict, 'diversityLgbt')
                existing.diversity_disability = self._extract_diversity_value(attributes_dict, 'diversityDisability')
                existing.diversity_trans = self._extract_diversity_value(attributes_dict, 'diversityTrans')

                existing.attributes = attributes_dict
                existing.jobs = self._serialize_pydantic_to_dict(talento_api.jobs)
                existing.updated_at_inhire = self._normalize_datetime(talento_api.updatedAt)

                # Atualizar arquivos e tags se necessário
                if talento_api.files:
                    self._sync_talento_arquivos(existing, talento_api.files)
                if talento_api.tags:
                    self._sync_talento_tags(existing, talento_api.tags)

                if commit:
                    self.session.commit()
                return False, 'updated'

            # Extrair dados de diversidade
            attributes_dict = self._serialize_pydantic_to_dict(talento_api.attributes)

            # Normalizar datas da API
            created_at_inhire = self._normalize_datetime(talento_api.createdAt)
            updated_at_inhire = self._normalize_datetime(talento_api.updatedAt)

            # IMPORTANTE: Definir created_at para respeitar constraint chk_talento_dates_logical
            # created_at deve ser <= updated_at_inhire (e created_at_inhire) para satisfazer a constraint
            # Usar o menor valor entre as datas da API e NOW()
            from datetime import datetime
            if created_at_inhire:
                created_at = created_at_inhire
            elif updated_at_inhire:
                created_at = updated_at_inhire
            else:
                created_at = datetime.utcnow()

            novo_talento = Talento(
                inhire_id=talento_api.id,
                name=talento_api.name,
                email=talento_api.email,
                phone=talento_api.phone,
                headline=talento_api.headline,
                company=talento_api.company,
                location=talento_api.location,
                picture=talento_api.picture,
                linkedin_username=talento_api.linkedinUsername,
                contact_method=talento_api.contactMethod,
                status=talento_api.status,
                user_id=talento_api.userId,
                user_name=talento_api.userName,
                resume=talento_api.resume,
                # Campos de diversidade extraídos
                diversity_black=self._extract_diversity_value(attributes_dict, 'diversityBlack'),
                diversity_woman=self._extract_diversity_value(attributes_dict, 'diversityWoman'),
                diversity_lgbt=self._extract_diversity_value(attributes_dict, 'diversityLgbt'),
                diversity_disability=self._extract_diversity_value(attributes_dict, 'diversityDisability'),
                diversity_trans=self._extract_diversity_value(attributes_dict, 'diversityTrans'),
                # JSON completo
                attributes=attributes_dict,
                jobs=self._serialize_pydantic_to_dict(talento_api.jobs),
                created_at_inhire=created_at_inhire,
                updated_at_inhire=updated_at_inhire,
                created_at=created_at  # Definir explicitamente para respeitar constraint
            )

            self.session.add(novo_talento)
            self.session.flush()

            if talento_api.files:
                self._sync_talento_arquivos(novo_talento, talento_api.files)
            if talento_api.tags:
                self._sync_talento_tags(novo_talento, talento_api.tags)

            if commit:
                self.session.commit()
            return True, 'created'

        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao upsert talento {talento_api.id}: {str(e)}")
            raise

    def _extract_diversity_value(self, attributes: dict, field_name: str) -> bool | None:
        """
        Extrai valor de diversidade do campo attributes

        Args:
            attributes: Dicionário de attributes do talento
            field_name: Nome do campo (ex: 'diversityBlack')

        Returns:
            bool ou None se campo não existir ou não tiver valor
        """
        if not attributes or field_name not in attributes:
            return None

        field_data = attributes.get(field_name)
        if not field_data or not isinstance(field_data, list) or len(field_data) == 0:
            return None

        # Pegar o primeiro item (mais recente)
        first_item = field_data[0]
        if isinstance(first_item, dict) and 'value' in first_item:
            value = first_item['value']
            # Converter para boolean se for string
            if isinstance(value, str):
                return value.lower() == 'true'
            return bool(value) if value is not None else None

        return None

    def _sync_talento_arquivos(self, talento: Talento, files: list):
        """Sincroniza arquivos do talento"""
        # Remover arquivos que não existem mais
        existing_ids = {f.file_inhire_id for f in talento.arquivos}
        new_ids = {f.id for f in files}

        for arquivo in list(talento.arquivos):
            if arquivo.file_inhire_id not in new_ids:
                self.session.delete(arquivo)

        # Adicionar/atualizar arquivos
        for file in files:
            arquivo = next((a for a in talento.arquivos if a.file_inhire_id == file.id), None)
            if not arquivo:
                arquivo = TalentoArquivo(
                    talento_id=talento.id,
                    file_inhire_id=file.id,
                    name=file.name,
                    url=file.url,
                    file_type=file.type
                )
                self.session.add(arquivo)

    def _sync_talento_tags(self, talento: Talento, tags: list):
        """Sincroniza tags do talento"""
        existing_ids = {t.tag_inhire_id for t in talento.tags}
        new_ids = {t.id for t in tags}

        for tag in list(talento.tags):
            if tag.tag_inhire_id not in new_ids:
                self.session.delete(tag)

        for tag_data in tags:
            tag = next((t for t in talento.tags if t.tag_inhire_id == tag_data.id), None)
            if not tag:
                tag = TalentoTag(
                    talento_id=talento.id,
                    tag_inhire_id=tag_data.id,
                    name=tag_data.name,
                    category=tag_data.category
                )
                self.session.add(tag)

    def upsert_candidatura_timeline(
        self,
        timeline_event: dict,
        candidatura_inhire_id: str,
        candidatura_db_id: int,
        commit: bool = True
    ) -> tuple[bool, str]:
        """
        Insere ou atualiza um evento de timeline da candidatura

        Args:
            timeline_event: Dicionário com dados do evento de timeline da API
            candidatura_inhire_id: ID da candidatura no formato InHire (jobId*talentId)
            candidatura_db_id: ID interno da candidatura no banco

        Returns:
            tuple[bool, str]: (is_new, operation) onde operation é 'created', 'updated' ou 'skipped'
        """
        from models.database import CandidaturaTimeline

        try:
            # Extrair dados do evento
            transition_at = self._normalize_datetime(timeline_event.get('createdAt'))
            if not transition_at:
                return False, 'skipped'

            talent_id = timeline_event.get('talentId')
            user_id = timeline_event.get('userId')
            user_name = timeline_event.get('userName')

            # Extrair dados do stage
            stage = timeline_event.get('stage', {})
            stage_id = stage.get('id') if stage else None
            stage_name = stage.get('name') if stage else None
            stage_order = stage.get('order') if stage else None
            stage_type = stage.get('type') if stage else None
            stage_created_at = self._normalize_datetime(stage.get('createdAt')) if stage else None
            stage_updated_at = self._normalize_datetime(stage.get('updatedAt')) if stage else None

            # Extrair dados do phase (dentro do stage)
            phase = stage.get('phase', {}) if stage else None
            phase_id = phase.get('id') if phase else None
            phase_name = phase.get('name') if phase else None
            phase_order = phase.get('order') if phase else None
            phase_type = phase.get('type') if phase else None
            phase_created_at = self._normalize_datetime(phase.get('createdAt')) if phase else None
            phase_updated_at = self._normalize_datetime(phase.get('updatedAt')) if phase else None

            # Verificar se já existe um evento idêntico
            # Usamos candidatura_id + transition_at como chave única
            existing = self.session.query(CandidaturaTimeline).filter_by(
                candidatura_id=candidatura_db_id,
                transition_at=transition_at
            ).first()

            if existing:
                # Atualizar se houver mudanças
                updated = False

                if existing.stage_id != stage_id:
                    existing.stage_id = stage_id
                    updated = True
                if existing.stage_name != stage_name:
                    existing.stage_name = stage_name
                    updated = True
                if existing.phase_id != phase_id:
                    existing.phase_id = phase_id
                    updated = True
                if existing.phase_name != phase_name:
                    existing.phase_name = phase_name
                    updated = True

                if updated:
                    existing.stage_order = stage_order
                    existing.stage_type = stage_type
                    existing.stage_created_at = stage_created_at
                    existing.stage_updated_at = stage_updated_at
                    existing.phase_order = phase_order
                    existing.phase_type = phase_type
                    existing.phase_created_at = phase_created_at
                    existing.phase_updated_at = phase_updated_at
                    existing.user_id = user_id
                    existing.user_name = user_name

                    if commit:
                        self.session.commit()
                    return False, 'updated'
                else:
                    return False, 'skipped'

            # Criar novo evento de timeline
            novo_timeline = CandidaturaTimeline(
                candidatura_id=candidatura_db_id,
                candidatura_inhire_id=candidatura_inhire_id,
                stage_id=stage_id,
                stage_name=stage_name,
                stage_order=stage_order,
                stage_type=stage_type,
                stage_created_at=stage_created_at,
                stage_updated_at=stage_updated_at,
                phase_id=phase_id,
                phase_name=phase_name,
                phase_order=phase_order,
                phase_type=phase_type,
                phase_created_at=phase_created_at,
                phase_updated_at=phase_updated_at,
                talent_inhire_id=talent_id,
                user_id=user_id,
                user_name=user_name,
                transition_at=transition_at
            )

            self.session.add(novo_timeline)
            if commit:
                self.session.commit()
            return True, 'created'

        except Exception as e:
            self.session.rollback()
            self.logger.error(
                f"Erro ao upsert timeline da candidatura {candidatura_inhire_id}: {str(e)}"
            )
            raise

    def get_vagas_com_posicoes_abertas(self) -> list:
        """
        Busca vagas que têm pelo menos 1 posição aberta
        Wrapper para VagaRepository.get_vagas_com_posicoes_abertas()
        """
        return self.vaga_repo.get_vagas_com_posicoes_abertas()

    def get_vagas_ativas_ou_recentes(self, days: int = 7) -> list:
        """
        Busca vagas ativas (status=OPEN) OU atualizadas nos últimos N dias
        Wrapper para VagaRepository.get_vagas_ativas_ou_recentes()
        """
        return self.vaga_repo.get_vagas_ativas_ou_recentes(days=days)

    def get_sync_configuration(self, tenant_id: str, commit: bool = True) -> SyncConfiguration:
        """Busca ou cria configuração de sincronização"""
        config = self.session.query(SyncConfiguration).filter_by(tenant_id=tenant_id).first()

        if not config:
            config = SyncConfiguration(tenant_id=tenant_id)
            self.session.add(config)
            if commit:
                self.session.commit()

        return config

    def create_sync_log(self, config_id: int, sync_type: str, entity: str, commit: bool = True) -> SyncLog:
        """Cria registro de log de sincronização"""
        log = SyncLog(
            config_id=config_id,
            sync_type=sync_type,
            sync_entity=entity,
            status=SyncStatus.RUNNING,
            start_time=datetime.utcnow()
        )

        self.session.add(log)
        if commit:
            self.session.commit()
        return log

    def complete_sync_log(self, log: SyncLog, status: str, stats: Dict[str, int], errors: str = None, commit: bool = True):
        """Finaliza log de sincronização"""
        log.status = status
        log.end_time = datetime.utcnow()
        log.duration_ms = int((log.end_time - log.start_time).total_seconds() * 1000)
        log.records_processed = stats.get('processed', 0)
        log.records_created = stats.get('created', 0)
        log.records_updated = stats.get('updated', 0)
        log.records_skipped = stats.get('skipped', 0)
        log.records_failed = stats.get('failed', 0)

        if errors:
            log.error_messages = errors

        if commit:
            self.session.commit()

    # ========================================
    # MÉTODOS UPSERT PARA NOVAS ENTIDADES
    # ========================================

    def _extract_approval_data_from_json(self, req_api: RequisicaoAPI):
        """
        Extrai dados de aprovação/rejeição do JSON approvers
        quando os campos não vêm populados pela API

        Returns:
            dict com approved_at, rejected_at, approver_name, status_updated_at
        """
        result = {
            'approved_at': None,
            'rejected_at': None,
            'approver_name': None,
            'status_updated_at': None
        }

        # Verificar se approvers existe no schema (campo foi removido em versões mais recentes)
        try:
            approvers = req_api.approvers
            if not approvers:
                return result
        except AttributeError:
            # Campo não existe mais no modelo Pydantic
            return result

        # Buscar aprovador/rejeitador no JSON
        for aprov in approvers:
            if not isinstance(aprov, dict):
                continue

            aprov_status = aprov.get('status')
            status_updated_str = aprov.get('statusUpdatedAt')
            aprov_name = aprov.get('name')

            # Extrair data de aprovação
            if aprov_status == 'approved' and status_updated_str:
                try:
                    from datetime import datetime
                    result['approved_at'] = datetime.fromisoformat(status_updated_str.replace('Z', '+00:00'))
                    result['status_updated_at'] = result['approved_at']
                    if aprov_name:
                        result['approver_name'] = aprov_name
                except:
                    pass

            # Extrair data de rejeição
            elif aprov_status == 'rejected' and status_updated_str:
                try:
                    from datetime import datetime
                    result['rejected_at'] = datetime.fromisoformat(status_updated_str.replace('Z', '+00:00'))
                    result['status_updated_at'] = result['rejected_at']
                    if aprov_name:
                        result['approver_name'] = aprov_name
                except:
                    pass

        return result

    def upsert_requisicao(self, req_api: RequisicaoAPI, vaga_db_id: int = None, commit=True) -> tuple[bool, str]:
        """
        Insere ou atualiza requisição no banco
        Extrai dados do JSON approvers quando campos não vêm populados

        Returns:
            (is_new, operation) - (True/False, 'created'/'updated'/'skipped')
        """
        try:
            existing = self.session.query(Requisicao).filter_by(inhire_id=req_api.id).first()

            # Extrair dados do JSON approvers
            approval_data = self._extract_approval_data_from_json(req_api)

            if existing:
                # Verificar se precisa atualizar
                if req_api.updatedAt and existing.updated_at_inhire:
                    updated_at_normalized = self._normalize_datetime(req_api.updatedAt)
                    if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
                        return False, 'skipped'

                # Atualizar
                if vaga_db_id:
                    existing.vaga_id = vaga_db_id
                existing.job_inhire_id = req_api.jobId
                existing.client_id = req_api.clientId
                existing.status = req_api.status
                existing.reason = req_api.reason

                # Novos campos do endpoint direto /requisitions/{id}
                if hasattr(req_api, 'name') and req_api.name:
                    existing.name = req_api.name
                if hasattr(req_api, 'description') and req_api.description:
                    existing.description = req_api.description
                if hasattr(req_api, 'positions') and req_api.positions:
                    existing.positions = self._serialize_pydantic_to_dict(req_api.positions)
                if hasattr(req_api, 'approvalWorkflow') and req_api.approvalWorkflow:
                    existing.approval_workflow = self._serialize_pydantic_to_dict(req_api.approvalWorkflow)
                if hasattr(req_api, 'approvers') and req_api.approvers:
                    existing.approvers = self._serialize_pydantic_to_dict(req_api.approvers)

                # position_amount: usar do JSON positions se não vier da API
                existing.position_amount = req_api.positionAmount
                if existing.position_amount is None and hasattr(req_api, 'positions') and req_api.positions:
                    existing.position_amount = len(req_api.positions)

                existing.requester_id = req_api.requesterId
                existing.requester_name = req_api.requesterName
                existing.approver_id = req_api.approverId

                # approver_name: usar do JSON se não vier da API
                existing.approver_name = req_api.approverName or approval_data['approver_name']

                existing.custom_fields = self._serialize_pydantic_to_dict(req_api.customFields)

                # requested_at: usar created_at_inhire se não vier da API
                existing.requested_at = self._normalize_datetime(req_api.requestedAt)
                if not existing.requested_at and req_api.createdAt:
                    existing.requested_at = self._normalize_datetime(req_api.createdAt)

                # status_updated_at: usar do JSON se não vier da API
                if hasattr(req_api, 'statusUpdatedAt') and req_api.statusUpdatedAt:
                    existing.status_updated_at = self._normalize_datetime(req_api.statusUpdatedAt)
                elif approval_data['status_updated_at']:
                    existing.status_updated_at = approval_data['status_updated_at']

                # approved_at: usar do JSON ou status_updated_at baseado no status
                existing.approved_at = (
                    self._normalize_datetime(req_api.approvedAt) or
                    approval_data['approved_at'] or
                    (existing.status_updated_at if req_api.status == 'approved' else None)
                )

                # rejected_at: usar do JSON ou status_updated_at baseado no status
                existing.rejected_at = (
                    self._normalize_datetime(req_api.rejectedAt) or
                    approval_data['rejected_at'] or
                    (existing.status_updated_at if req_api.status == 'rejected' else None)
                )

                existing.updated_at_inhire = self._normalize_datetime(req_api.updatedAt)

                if commit:
                    self.session.commit()
                return False, 'updated'

            # Criar novo
            # Calcular status_updated_at primeiro (usado como fallback)
            status_updated_at = (
                self._normalize_datetime(req_api.statusUpdatedAt) if hasattr(req_api, 'statusUpdatedAt') else None or
                approval_data['status_updated_at']
            )

            nova_req = Requisicao(
                inhire_id=req_api.id,
                vaga_id=vaga_db_id,
                job_inhire_id=req_api.jobId,
                client_id=req_api.clientId,
                status=req_api.status,
                reason=req_api.reason,

                # Campos do endpoint direto /requisitions/{id}
                name=req_api.name if hasattr(req_api, 'name') else None,
                description=req_api.description if hasattr(req_api, 'description') else None,
                positions=self._serialize_pydantic_to_dict(req_api.positions) if hasattr(req_api, 'positions') and req_api.positions else None,
                approval_workflow=self._serialize_pydantic_to_dict(req_api.approvalWorkflow) if hasattr(req_api, 'approvalWorkflow') and req_api.approvalWorkflow else None,
                approvers=self._serialize_pydantic_to_dict(req_api.approvers) if hasattr(req_api, 'approvers') and req_api.approvers else None,

                position_amount=req_api.positionAmount if req_api.positionAmount else (len(req_api.positions) if hasattr(req_api, 'positions') and req_api.positions else None),
                requester_id=req_api.requesterId,
                requester_name=req_api.requesterName,
                approver_id=req_api.approverId,
                approver_name=req_api.approverName or approval_data['approver_name'],
                custom_fields=self._serialize_pydantic_to_dict(req_api.customFields),
                requested_at=self._normalize_datetime(req_api.requestedAt) or self._normalize_datetime(req_api.createdAt),
                approved_at=(
                    self._normalize_datetime(req_api.approvedAt) or
                    approval_data['approved_at'] or
                    (status_updated_at if req_api.status == 'approved' else None)
                ),
                rejected_at=(
                    self._normalize_datetime(req_api.rejectedAt) or
                    approval_data['rejected_at'] or
                    (status_updated_at if req_api.status == 'rejected' else None)
                ),
                status_updated_at=status_updated_at,
                created_at_inhire=self._normalize_datetime(req_api.createdAt),
                updated_at_inhire=self._normalize_datetime(req_api.updatedAt)
            )

            self.session.add(nova_req)
            if commit:
                self.session.commit()
            return True, 'created'

        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao fazer upsert de requisição {req_api.id}: {str(e)}")
            raise

    def upsert_scorecard_interview(self, interview_api: ScorecardInterviewAPI, commit=True) -> tuple[bool, str]:
        """
        Insere ou atualiza template de entrevista/scorecard
        """
        try:
            existing = self.session.query(ScorecardInterview).filter_by(inhire_id=interview_api.id).first()

            if existing:
                if interview_api.updatedAt and existing.updated_at_inhire:
                    updated_at_normalized = self._normalize_datetime(interview_api.updatedAt)
                    if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
                        return False, 'skipped'

                existing.name = interview_api.name
                existing.description = interview_api.description
                existing.type = interview_api.type
                existing.questions = self._serialize_pydantic_to_dict(interview_api.questions)
                existing.skill_categories = self._serialize_pydantic_to_dict(interview_api.skillCategories)
                existing.user_id = interview_api.userId
                existing.user_name = interview_api.userName
                existing.tenant_id = interview_api.tenantId
                existing.updated_at_inhire = self._normalize_datetime(interview_api.updatedAt)

                if commit:
                    self.session.commit()
                return False, 'updated'

            novo_interview = ScorecardInterview(
                inhire_id=interview_api.id,
                name=interview_api.name,
                description=interview_api.description,
                type=interview_api.type,
                questions=self._serialize_pydantic_to_dict(interview_api.questions),
                skill_categories=self._serialize_pydantic_to_dict(interview_api.skillCategories),
                user_id=interview_api.userId,
                user_name=interview_api.userName,
                tenant_id=interview_api.tenantId,
                created_at_inhire=self._normalize_datetime(interview_api.createdAt),
                updated_at_inhire=self._normalize_datetime(interview_api.updatedAt)
            )

            self.session.add(novo_interview)
            if commit:
                self.session.commit()
            return True, 'created'

        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao fazer upsert de scorecard interview {interview_api.id}: {str(e)}")
            raise

    def upsert_scorecard_job(self, scorecard_api: ScorecardJobAPI, vaga_db_id: int = None, commit=True) -> tuple[bool, str]:
        """
        Insere ou atualiza scorecard de vaga
        """
        try:
            # Usar jobId como fallback quando id for None (API retorna id=None em alguns casos)
            scorecard_id = scorecard_api.id or scorecard_api.jobId

            if not scorecard_id:
                self.logger.warning(f"Scorecard job sem ID (id={scorecard_api.id}, jobId={scorecard_api.jobId}). Ignorando.")
                return False, 'skipped'

            existing = self.session.query(ScorecardJob).filter_by(inhire_id=scorecard_id).first()

            if existing:
                if scorecard_api.updatedAt and existing.updated_at_inhire:
                    updated_at_normalized = self._normalize_datetime(scorecard_api.updatedAt)
                    if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
                        return False, 'skipped'

                if vaga_db_id:
                    existing.vaga_id = vaga_db_id
                existing.job_inhire_id = scorecard_api.jobId
                existing.skill_categories = self._serialize_pydantic_to_dict(scorecard_api.skillCategories)
                existing.criteria = self._serialize_pydantic_to_dict(scorecard_api.criteria)
                existing.user_id = scorecard_api.userId
                existing.user_name = scorecard_api.userName
                existing.tenant_id = scorecard_api.tenantId
                existing.updated_at_inhire = self._normalize_datetime(scorecard_api.updatedAt)

                if commit:
                    self.session.commit()
                return False, 'updated'

            novo_scorecard = ScorecardJob(
                inhire_id=scorecard_id,
                vaga_id=vaga_db_id,
                job_inhire_id=scorecard_api.jobId,
                skill_categories=self._serialize_pydantic_to_dict(scorecard_api.skillCategories),
                criteria=self._serialize_pydantic_to_dict(scorecard_api.criteria),
                user_id=scorecard_api.userId,
                user_name=scorecard_api.userName,
                tenant_id=scorecard_api.tenantId,
                created_at_inhire=self._normalize_datetime(scorecard_api.createdAt),
                updated_at_inhire=self._normalize_datetime(scorecard_api.updatedAt)
            )

            self.session.add(novo_scorecard)
            if commit:
                self.session.commit()
            return True, 'created'

        except Exception as e:
            self.session.rollback()
            scorecard_id = scorecard_api.id or scorecard_api.jobId
            self.logger.error(f"Erro ao fazer upsert de scorecard job {scorecard_id}: {str(e)}")
            raise

    def upsert_form_response(self, form_api: FormResponseAPI, candidatura_db_id: int, commit=True) -> tuple[bool, str]:
        """
        Insere ou atualiza respostas de formulário de candidato
        """
        try:
            existing = self.session.query(FormResponse).filter_by(
                candidatura_id=candidatura_db_id,
                candidatura_inhire_id=form_api.jobTalentId
            ).first()

            if existing:
                # Sempre atualizar form responses (não têm updatedAt)
                existing.talent_inhire_id = form_api.talentId
                existing.job_inhire_id = form_api.jobId
                existing.form_type = form_api.formType
                existing.form_id = form_api.formId
                existing.forms_answers = self._serialize_pydantic_to_dict(form_api.formsAnswers)
                existing.personality_answers = self._serialize_pydantic_to_dict(form_api.personalityAnswers)
                existing.disc_interpretation = self._serialize_pydantic_to_dict(form_api.discInterpretation)
                existing.generic_form_responses = self._serialize_pydantic_to_dict(form_api.genericFormResponses)
                existing.submitted_at = self._normalize_datetime(form_api.submittedAt)

                if commit:
                    self.session.commit()
                return False, 'updated'

            novo_form = FormResponse(
                candidatura_id=candidatura_db_id,
                candidatura_inhire_id=form_api.jobTalentId,
                talent_inhire_id=form_api.talentId,
                job_inhire_id=form_api.jobId,
                form_type=form_api.formType,
                form_id=form_api.formId,
                forms_answers=self._serialize_pydantic_to_dict(form_api.formsAnswers),
                personality_answers=self._serialize_pydantic_to_dict(form_api.personalityAnswers),
                disc_interpretation=self._serialize_pydantic_to_dict(form_api.discInterpretation),
                generic_form_responses=self._serialize_pydantic_to_dict(form_api.genericFormResponses),
                submitted_at=self._normalize_datetime(form_api.submittedAt)
            )

            self.session.add(novo_form)
            if commit:
                self.session.commit()
            return True, 'created'

        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao fazer upsert de form response {form_api.jobTalentId}: {str(e)}")
            raise

    def upsert_vaga_tag(self, tag_api: VagaTagAPI, vaga_db_id: int, commit=True) -> tuple[bool, str]:
        """
        Insere ou atualiza tag de vaga
        """
        try:
            existing = self.session.query(VagaTag).filter_by(
                vaga_id=vaga_db_id,
                tag_inhire_id=tag_api.id
            ).first()

            if existing:
                existing.name = tag_api.name
                existing.category = tag_api.category
                existing.color = tag_api.color

                if commit:
                    self.session.commit()
                return False, 'updated'

            nova_tag = VagaTag(
                vaga_id=vaga_db_id,
                tag_inhire_id=tag_api.id,
                name=tag_api.name,
                category=tag_api.category,
                color=tag_api.color
            )

            self.session.add(nova_tag)
            if commit:
                self.session.commit()
            return True, 'created'

        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao fazer upsert de vaga tag {tag_api.id}: {str(e)}")
            raise

    def upsert_automation(self, auto_api: AutomationAPI, commit=True) -> tuple[bool, str]:
        """
        Insere ou atualiza automação/workflow
        """
        try:
            existing = self.session.query(Automation).filter_by(inhire_id=auto_api.id).first()

            if existing:
                if auto_api.updatedAt and existing.updated_at_inhire:
                    updated_at_normalized = self._normalize_datetime(auto_api.updatedAt)
                    if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
                        return False, 'skipped'

                existing.name = auto_api.name
                existing.description = auto_api.description
                existing.type = auto_api.type
                existing.trigger = self._serialize_pydantic_to_dict(auto_api.trigger)
                existing.conditions = self._serialize_pydantic_to_dict(auto_api.conditions)
                existing.actions = self._serialize_pydantic_to_dict(auto_api.actions)
                existing.is_active = auto_api.isActive
                existing.tenant_id = auto_api.tenantId
                existing.updated_at_inhire = self._normalize_datetime(auto_api.updatedAt)

                if commit:
                    self.session.commit()
                return False, 'updated'

            nova_auto = Automation(
                inhire_id=auto_api.id,
                name=auto_api.name,
                description=auto_api.description,
                type=auto_api.type,
                trigger=self._serialize_pydantic_to_dict(auto_api.trigger),
                conditions=self._serialize_pydantic_to_dict(auto_api.conditions),
                actions=self._serialize_pydantic_to_dict(auto_api.actions),
                is_active=auto_api.isActive,
                tenant_id=auto_api.tenantId,
                created_at_inhire=self._normalize_datetime(auto_api.createdAt),
                updated_at_inhire=self._normalize_datetime(auto_api.updatedAt)
            )

            self.session.add(nova_auto)
            if commit:
                self.session.commit()
            return True, 'created'

        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao fazer upsert de automation {auto_api.id}: {str(e)}")
            raise

    def upsert_cliente(self, cliente_api: ClienteAPI, commit=True) -> tuple[bool, str]:
        """
        Insere ou atualiza cliente
        """
        try:
            existing = self.session.query(Cliente).filter_by(inhire_id=cliente_api.id).first()

            if existing:
                if cliente_api.updatedAt and existing.updated_at_inhire:
                    updated_at_normalized = self._normalize_datetime(cliente_api.updatedAt)
                    if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
                        return False, 'skipped'

                existing.name = cliente_api.name
                existing.email = cliente_api.email
                existing.phone = cliente_api.phone
                existing.address = cliente_api.address
                existing.city = cliente_api.city
                existing.state = cliente_api.state
                existing.country = cliente_api.country
                existing.is_active = cliente_api.isActive
                existing.tenant_id = cliente_api.tenantId
                existing.updated_at_inhire = self._normalize_datetime(cliente_api.updatedAt)

                if commit:
                    self.session.commit()
                return False, 'updated'

            novo_cliente = Cliente(
                inhire_id=cliente_api.id,
                name=cliente_api.name,
                email=cliente_api.email,
                phone=cliente_api.phone,
                address=cliente_api.address,
                city=cliente_api.city,
                state=cliente_api.state,
                country=cliente_api.country,
                is_active=cliente_api.isActive,
                tenant_id=cliente_api.tenantId,
                created_at_inhire=self._normalize_datetime(cliente_api.createdAt),
                updated_at_inhire=self._normalize_datetime(cliente_api.updatedAt)
            )

            self.session.add(novo_cliente)
            if commit:
                self.session.commit()
            return True, 'created'

        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao fazer upsert de cliente {cliente_api.id}: {str(e)}")
            raise

    def upsert_custom_field(self, field_api: CustomFieldAPI, commit=True) -> tuple[bool, str]:
        """
        Insere ou atualiza custom field
        """
        try:
            existing = self.session.query(CustomField).filter_by(inhire_id=field_api.id).first()

            if existing:
                if field_api.updatedAt and existing.updated_at_inhire:
                    updated_at_normalized = self._normalize_datetime(field_api.updatedAt)
                    if updated_at_normalized and updated_at_normalized <= existing.updated_at_inhire:
                        return False, 'skipped'

                existing.entity_type = field_api.entityType
                existing.field_name = field_api.fieldName
                existing.field_label = field_api.fieldLabel
                existing.field_type = field_api.fieldType
                existing.field_options = self._serialize_pydantic_to_dict(field_api.fieldOptions)
                existing.validation_rules = self._serialize_pydantic_to_dict(field_api.validationRules)
                existing.is_required = field_api.isRequired
                existing.is_active = field_api.isActive
                existing.display_order = field_api.displayOrder
                existing.tenant_id = field_api.tenantId
                existing.updated_at_inhire = self._normalize_datetime(field_api.updatedAt)

                if commit:
                    self.session.commit()
                return False, 'updated'

            novo_field = CustomField(
                inhire_id=field_api.id,
                entity_type=field_api.entityType,
                field_name=field_api.fieldName,
                field_label=field_api.fieldLabel,
                field_type=field_api.fieldType,
                field_options=self._serialize_pydantic_to_dict(field_api.fieldOptions),
                validation_rules=self._serialize_pydantic_to_dict(field_api.validationRules),
                is_required=field_api.isRequired,
                is_active=field_api.isActive,
                display_order=field_api.displayOrder,
                tenant_id=field_api.tenantId,
                created_at_inhire=self._normalize_datetime(field_api.createdAt),
                updated_at_inhire=self._normalize_datetime(field_api.updatedAt)
            )

            self.session.add(novo_field)
            if commit:
                self.session.commit()
            return True, 'created'

        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao fazer upsert de custom field {field_api.id}: {str(e)}")
            raise
