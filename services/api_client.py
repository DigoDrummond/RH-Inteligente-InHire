"""
Cliente HTTP para comunicação com API Inhire
Todos os endpoints e lógica de paginação concentrados aqui
"""
import requests
import time
from typing import Optional, Dict, Generator
from config import settings, get_default_headers, InhireEndpoints
from interfaces.i_api_client import IAPIClient
from models.api_schemas import (
    VagaAPI, VagasPaginatedRequest, VagasPaginatedResponse,
    PosicaoAPI, PosicoesPaginatedRequest, PosicoesPaginatedResponse,
    CandidaturaAPI, CandidaturasPaginatedRequest, CandidaturasPaginatedResponse,
    TalentoAPI, TalentosPaginatedRequest, TalentosPaginatedResponse
)
from models.new_api_schemas import (
    RequisicaoAPI, RequisicoesPaginatedResponse,
    VagaTagAPI, ClienteAPI,
    JobDetailsAPI, JobTalentDetailsAPI,
    PositionTimelineEventAPI, PositionTimelinePaginatedResponse,
    CustomFieldAPI
)
from services.auth_service import get_auth_service, AuthService
from utils.logger import get_logger, log_api_request
from utils.retry import retry_with_backoff, TokenExpiredException, RateLimitException
from utils.rate_limiter import INHIRE_API_LIMITER


class InhireAPIClient(IAPIClient):
    """Cliente para todos os endpoints da API Inhire"""

    def __init__(self, auth_service: Optional[AuthService] = None):
        self.logger = get_logger(__name__)
        self.auth_service = auth_service or get_auth_service()
        self.api_base_url = settings.INHIRE_BASE_URL.rstrip('/')
        self.timeout = (settings.INHIRE_TIMEOUT_CONNECT, settings.INHIRE_TIMEOUT_READ)
        self.default_batch_size = settings.SYNC_BATCH_SIZE

    def validate_tenant(self) -> bool:
        """
        Valida se o tenant configurado existe e está autorizado.

        Returns:
            True se tenant é válido

        Raises:
            ValueError se tenant não existe ou não está autorizado
        """
        try:
            # Tentar fazer uma request simples para validar tenant
            # Se tenant estiver errado, API retornará erro 403 ou 404
            tenant_id = settings.INHIRE_TENANT

            self.logger.info(f"Validando tenant: {tenant_id}")

            # Fazer request de teste - buscar vagas com limit 1
            test_data = {"tenantId": tenant_id, "limit": 1}
            response = self._request("POST", InhireEndpoints.JOBS_PAGINATED_LEAN, data=test_data)

            if response is not None:
                self.logger.info(f"✓ Tenant {tenant_id} validado com sucesso")
                return True
            else:
                raise ValueError(f"Tenant {tenant_id} retornou resposta vazia")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                raise ValueError(
                    f"Tenant {tenant_id} não autorizado. Verifique INHIRE_TENANT no .env"
                )
            elif e.response.status_code == 404:
                raise ValueError(
                    f"Tenant {tenant_id} não encontrado. Verifique INHIRE_TENANT no .env"
                )
            else:
                raise ValueError(f"Erro ao validar tenant {tenant_id}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Falha na validação do tenant {tenant_id}: {str(e)}")

    @retry_with_backoff(max_attempts=3)
    def _request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None):
        """Faz requisição HTTP com retry automático e rate limiting"""
        # RATE LIMITING: Adquirir permissão antes de fazer request
        INHIRE_API_LIMITER.acquire(wait=True)

        url = f"{self.api_base_url}{endpoint}"
        start = time.time()

        self.auth_service.ensure_authenticated()
        headers = self.auth_service.get_auth_headers()

        response = requests.request(method, url, json=data, params=params, headers=headers, timeout=self.timeout)
        duration_ms = int((time.time() - start) * 1000)

        # RATE LIMITING: Registrar duração para rate limiter adaptativo
        success = response.status_code == 200

        if response.status_code == 200:
            INHIRE_API_LIMITER.record_request(duration_ms, success=True)
            log_api_request(self.logger, method, url, 200, duration_ms)

            # VALIDAÇÃO: Verificar se resposta não é None ou vazia
            try:
                json_response = response.json()
            except ValueError as e:
                self.logger.error(f"API retornou resposta inválida (não-JSON) para {method} {url}")
                raise ValueError(f"Resposta da API não é JSON válido: {e}")

            if json_response is None:
                self.logger.warning(f"API retornou None para {method} {url}")
                return {}  # Retornar dict vazio ao invés de None para evitar crashes

            return json_response

        elif response.status_code == 401:
            INHIRE_API_LIMITER.record_request(duration_ms, success=False)
            self.auth_service.authenticate()
            return self._request(method, endpoint, data, params)  # Retry
        elif response.status_code == 429:
            INHIRE_API_LIMITER.record_request(duration_ms, success=False)
            # Rate limiter adaptativo irá reduzir automaticamente a taxa
            self.logger.warning(f"Rate limit 429 recebido. Rate limiter irá reduzir taxa automaticamente.")
            raise RateLimitException("Rate limit atingido")
        else:
            INHIRE_API_LIMITER.record_request(duration_ms, success=False)
            response.raise_for_status()

    # VAGAS
    def get_all_vagas(self, tenant_id: str = None, limit: int = None) -> Generator[VagaAPI, None, None]:
        """Itera sobre todas as vagas"""
        tenant_id = tenant_id or settings.INHIRE_TENANT
        limit = limit or self.default_batch_size
        start_key = None

        while True:
            data = {"tenantId": tenant_id, "limit": limit}
            if start_key:
                data["exclusiveStartKey"] = start_key

            response = self._request("POST", InhireEndpoints.JOBS_PAGINATED_LEAN, data=data)
            resp = VagasPaginatedResponse(**response)

            for vaga in resp.results:
                yield vaga

            if not resp.startKey:
                break
            start_key = resp.startKey

    # POSIÇÕES
    def get_all_posicoes(self, job_id: str, limit: int = None) -> Generator[PosicaoAPI, None, None]:
        """Itera sobre todas as posições de uma vaga"""
        limit = limit or self.default_batch_size
        start_key = None  # Primeira página NÃO deve incluir startKey

        while True:
            endpoint = InhireEndpoints.POSITIONS_PAGINATED.format(job_id=job_id)

            # Montar params: só incluir startKey se não for None
            params = {"limit": limit}
            if start_key is not None:
                params["startKey"] = start_key

            response = self._request("GET", endpoint, params=params)
            resp = PosicoesPaginatedResponse(**response)

            for posicao in resp.items:
                yield posicao

            if not resp.hasMore:
                break

            # Para próxima página, usar startKey numérico
            if start_key is None:
                start_key = limit
            else:
                start_key += limit

    # CANDIDATURAS
    def get_all_candidaturas(self, job_id: str, limit: int = None) -> Generator[CandidaturaAPI, None, None]:
        """Itera sobre todas as candidaturas de uma vaga"""
        limit = limit or self.default_batch_size
        start_key = None

        while True:
            endpoint = InhireEndpoints.APPLICATIONS_PAGINATED.format(job_id=job_id)
            data = {"limit": limit}
            if start_key:
                data["exclusiveStartKey"] = start_key

            response = self._request("POST", endpoint, data=data)
            resp = CandidaturasPaginatedResponse(**response)

            for cand in resp.jobTalents:
                yield cand

            if not resp.startKey:
                break
            start_key = resp.startKey

    # TALENTOS
    def get_talento_by_id(self, talent_id: str) -> Optional[TalentoAPI]:
        """Busca talento completo por ID"""
        try:
            endpoint = InhireEndpoints.TALENT_BY_ID.format(talent_id=talent_id)
            response = self._request("GET", endpoint)
            return TalentoAPI(**response)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def get_all_talentos(self, limit: int = None, filter_dict: Dict = None) -> Generator[TalentoAPI, None, None]:
        """
        Itera sobre todos os talentos

        NOTA: A API do InHire mudou e não aceita mais os parametros limit, orderBy e filter.
        Esses parâmetros são mantidos apenas para compatibilidade com código existente,
        mas são ignorados.
        """
        start_key = None

        while True:
            # API nova: payload vazio para primeira página,
            # ou só exclusiveStartKey (como objeto) para páginas seguintes
            data = {}
            if start_key:
                data["exclusiveStartKey"] = start_key

            response = self._request("POST", InhireEndpoints.TALENTS_PAGINATED, data=data)
            resp = TalentosPaginatedResponse(**response)

            for talento in resp.items:
                yield talento

            if not resp.startKey:
                break
            start_key = resp.startKey

    # TIMELINE / HISTÓRICO
    def get_candidatura_timeline(self, candidatura_id: str) -> list:
        """
        Busca o histórico de transições (timeline) de uma candidatura.

        O candidatura_id deve estar no formato: jobId*talentId
        Retorna lista de eventos do timeline ordenados cronologicamente.
        """
        try:
            endpoint = f"/job-talents/{candidatura_id}/timeline"
            response = self._request("GET", endpoint)
            return response if isinstance(response, list) else []
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.logger.warning(f"Timeline não encontrado para candidatura {candidatura_id}")
                return []
            elif e.response.status_code == 403:
                self.logger.warning(f"Acesso negado ao timeline da candidatura {candidatura_id}")
                return []
            raise

    # ALTERNATIVA - GET /talents (sem paginação)
    def get_all_talentos_simple(self) -> list:
        """
        Busca todos os talentos sem paginação (alternativa ao /paginated com erro).
        Retorna até 501 talentos de uma vez.
        """
        try:
            endpoint = "/talents"
            response = self._request("GET", endpoint)
            return [TalentoAPI(**t) for t in response] if isinstance(response, list) else []
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Erro ao buscar talentos via GET /talents: {str(e)}")
            return []

    # REQUISIÇÕES
    def get_all_requisicoes(self) -> Generator[RequisicaoAPI, None, None]:
        """
        Itera sobre todas as requisições

        Estratégia: Busca requisições através das vagas
        (não existe endpoint paginado geral de requisições)
        """
        # Buscar todas as vagas primeiro
        for vaga in self.get_all_vagas():
            # Para cada vaga, buscar suas requisições
            try:
                requisicoes = self.get_requisicoes_by_job(vaga.id)
                for req in requisicoes:
                    yield req
            except Exception as e:
                self.logger.error(f"Erro ao buscar requisições da vaga {vaga.id}: {str(e)}")
                continue

    def get_requisicoes_by_job(self, job_id: str) -> list:
        """Busca requisições de uma vaga específica"""
        try:
            endpoint = f"/requisitions/job/{job_id}"
            response = self._request("GET", endpoint)
            return [RequisicaoAPI(**r) for r in response] if isinstance(response, list) else []
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return []
            self.logger.error(f"Erro ao buscar requisições da vaga {job_id}: {str(e)}")
            return []

    def get_requisicao_completa(self, requisicao_id: str) -> Optional[RequisicaoAPI]:
        """
        Busca dados COMPLETOS de uma requisição específica

        Endpoint: GET /requisitions/{id}
        Retorna: name, description, positions, approvalWorkflow, approvers, etc.

        Este endpoint retorna MUITO mais dados que o endpoint paginado.
        Use para enriquecer dados de requisições já existentes.
        """
        try:
            endpoint = f"/requisitions/{requisicao_id}"
            response = self._request("GET", endpoint)
            return RequisicaoAPI(**response) if response else None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.logger.warning(f"Requisição {requisicao_id} não encontrada")
                return None
            self.logger.error(f"Erro ao buscar requisição completa {requisicao_id}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Erro inesperado ao buscar requisição {requisicao_id}: {str(e)}")
            return None

    def get_all_requisicoes_paginated(self) -> Generator[RequisicaoAPI, None, None]:
        """
        Itera sobre todas as requisições usando endpoint paginado (NOVO)

        Endpoint: GET /requisitions/paginated?lastEvaluatedKey={key}
        Paginação: lastEvaluatedKey (null/zero quando acabar)

        Vantagens sobre get_all_requisicoes():
        - 50-100x mais rápido
        - Reduz de ~1.138 requests para ~10-20 requests
        - Busca requisições órfãs (sem vaga vinculada)
        """
        last_key = None
        page_count = 0

        while True:
            page_count += 1
            endpoint = InhireEndpoints.REQUISITIONS_PAGINATED

            # Montar params: só incluir lastEvaluatedKey se não for None
            params = {}
            if last_key:
                params["lastEvaluatedKey"] = last_key

            try:
                response = self._request("GET", endpoint, params=params)

                # DEBUG: Log raw response
                self.logger.info(f"DEBUG - Página {page_count}: {len(response.get('items', []))} items retornados")
                if page_count == 1:
                    self.logger.info(f"DEBUG - Estrutura da resposta: {list(response.keys())}")

                resp = RequisicoesPaginatedResponse(**response)

                for requisicao in resp.items:
                    yield requisicao

                # Verificar se há próxima página
                # API retorna lastEvaluatedKey=null ou '0' ou 0 quando acabar
                if not resp.lastEvaluatedKey:
                    self.logger.info(f"Requisições paginadas concluídas: {page_count} páginas processadas")
                    break

                last_key = resp.lastEvaluatedKey

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    self.logger.warning("Endpoint /requisitions/paginated não encontrado")
                    break
                raise

    # POSITION TIMELINE (Histórico de Posições)

    @staticmethod
    def _normalize_timeline_timestamp(timestamp_str: str) -> str:
        """
        Normaliza timestamp para merge de eventos duplicados

        Remove microssegundos e garante formato consistente para matching.
        Isso resolve o problema de statusHistory.statusUpdatedAt != history.createdAt
        causando duplicatas no banco.

        Args:
            timestamp_str: Timestamp ISO 8601 da API

        Returns:
            Timestamp normalizado (sem microssegundos, formato: YYYY-MM-DD HH:MM:SS)
        """
        from dateutil import parser
        try:
            dt = parser.parse(timestamp_str)
            # Remover microssegundos e retornar formato padronizado
            return dt.replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            # Fallback: retornar original se parsing falhar
            return timestamp_str

    def _merge_timeline_events(
        self,
        position_id: str,
        job_id: str,
        status_history: list,
        history: list
    ) -> list:
        """
        Faz merge de eventos de statusHistory e history para evitar duplicatas

        PROBLEMA ORIGINAL:
        - statusHistory retorna: {status, statusUpdatedAt, userName, userId}
        - history retorna: {status, createdAt, comments, newData, previousData, userName, userId}
        - Ambos representam os MESMOS eventos, mas com campos diferentes
        - O código original processava ambos separadamente, criando duplicatas no banco

        SOLUÇÃO:
        - Consolidar ambos em memória usando chave (position_id, date_norm, status)
        - Priorizar dados do 'history' (tem mais campos, incluindo comments/notes)
        - Retornar lista única de eventos merged

        Args:
            position_id: ID da posição
            job_id: ID da vaga
            status_history: Array statusHistory da API
            history: Array history da API

        Returns:
            Lista de PositionTimelineEventAPI sem duplicatas
        """
        events_map = {}

        # PASSO 1: Processar statusHistory (dados básicos, SEM notes)
        if status_history and isinstance(status_history, list):
            for i, sh_event in enumerate(status_history):
                status = sh_event.get('status')
                timestamp = sh_event.get('statusUpdatedAt')

                if not status or not timestamp:
                    continue

                # Criar chave única: (position_id, data_normalizada, status)
                key = (position_id, self._normalize_timeline_timestamp(timestamp), status)

                # Determinar previous_status percorrendo histórico
                previous_status = status_history[i - 1]['status'] if i > 0 else None

                try:
                    events_map[key] = PositionTimelineEventAPI(
                        positionId=position_id,
                        jobId=job_id,
                        previousStatus=previous_status,
                        newStatus=status,
                        changedAt=timestamp,
                        changedBy=sh_event.get('userId'),
                        changedByName=sh_event.get('userName'),
                        # notes permanece None neste passo
                    )
                except Exception as e:
                    self.logger.warning(f"Erro ao parsear statusHistory: {str(e)}")

        # PASSO 2: Processar history (dados completos, COM notes/comments)
        if history and isinstance(history, list):
            for h_event in history:
                previous_data = h_event.get('previousData', {})
                new_data = h_event.get('newData', {})

                status = new_data.get('status') or h_event.get('status')
                timestamp = h_event.get('createdAt')

                if not status or not timestamp:
                    continue

                # Mesma chave usada no statusHistory
                key = (position_id, self._normalize_timeline_timestamp(timestamp), status)

                try:
                    # Se evento já existe (veio do statusHistory), ENRIQUECER com dados do history
                    if key in events_map:
                        # Adicionar notes e metadata ao evento existente
                        events_map[key].notes = h_event.get('comments')
                        events_map[key].eventMetadata = {
                            'newData': new_data,
                            'previousData': previous_data
                        } if new_data or previous_data else None

                        # Atualizar previous_status se não estava definido
                        if not events_map[key].previousStatus and previous_data.get('status'):
                            events_map[key].previousStatus = previous_data.get('status')
                    else:
                        # Evento só existe em history (não em statusHistory)
                        # Criar novo evento completo
                        events_map[key] = PositionTimelineEventAPI(
                            positionId=position_id,
                            jobId=job_id,
                            previousStatus=previous_data.get('status'),
                            newStatus=status,
                            changedAt=timestamp,
                            changedBy=h_event.get('userId'),
                            changedByName=h_event.get('userName'),
                            notes=h_event.get('comments'),
                            eventMetadata={
                                'newData': new_data,
                                'previousData': previous_data
                            } if new_data or previous_data else None
                        )
                except Exception as e:
                    self.logger.warning(f"Erro ao parsear history: {str(e)}")

        return list(events_map.values())

    def get_position_timeline_by_job(self, job_id: str) -> Generator[PositionTimelineEventAPI, None, None]:
        """
        Busca histórico de mudanças de status de todas as posições de uma vaga

        IMPORTANTE: O endpoint /jobs/positions/paginated/{job_id} retorna:
        - Lista de posições DA VAGA
        - Histórico de movimentações de status de cada posição

        CORREÇÃO (2026-03-20): Implementado merge de statusHistory + history para evitar
        duplicatas no banco. Anteriormente, ambos arrays eram processados separadamente,
        criando 2 eventos para cada mudança de status.

        Args:
            job_id: ID da vaga no InHire (vagas.inhire_id - UUID)

        Yields:
            Eventos de timeline de todas as posições da vaga (SEM DUPLICATAS)

        Exemplo de uso:
            for event in api.get_position_timeline_by_job('fd434658-ba35-4d68-90b0-a97a35bcc1ff'):
                print(f"{event.positionId}: {event.previousStatus} → {event.newStatus}")
        """
        try:
            # Usar o mesmo endpoint que busca posições (retorna posições + histórico)
            endpoint = InhireEndpoints.POSITIONS_PAGINATED.format(job_id=job_id)

            # Paginação similar ao get_all_posicoes
            limit = self.default_batch_size
            start_key = None

            while True:
                params = {"limit": limit}
                if start_key is not None:
                    params["startKey"] = start_key

                response = self._request("GET", endpoint, params=params)

                # A resposta contém:
                # - items: lista de posições
                # - cada posição tem: history (eventos detalhados) e statusHistory (resumo simples)

                if isinstance(response, dict) and 'items' in response:
                    for position_item in response['items']:
                        if not isinstance(position_item, dict):
                            continue

                        position_id = position_item.get('id')
                        job_id = position_item.get('jobId')

                        # NOVO (2026-03-20): Fazer merge de statusHistory + history ANTES de yield
                        # Isso evita duplicatas no banco de dados
                        status_history = position_item.get('statusHistory', [])
                        history = position_item.get('history', [])

                        # Merge em memória (retorna lista sem duplicatas)
                        merged_events = self._merge_timeline_events(
                            position_id=position_id,
                            job_id=job_id,
                            status_history=status_history,
                            history=history
                        )

                        # Yield eventos merged
                        for event in merged_events:
                            yield event

                    # Verificar paginação
                    if not response.get('hasMore', False):
                        break

                    # Atualizar startKey
                    if start_key is None:
                        start_key = limit
                    else:
                        start_key += limit
                else:
                    break

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.logger.debug(f"Histórico não encontrado para vaga {job_id}")
            else:
                self.logger.error(f"Erro ao buscar timeline da vaga {job_id}: {str(e)}")
            return

    # SCORECARDS
    def get_all_scorecard_interviews(self) -> Generator[ScorecardInterviewAPI, None, None]:
        """Itera sobre todos os templates de entrevista"""
        try:
            endpoint = "/forms/scorecards/interviews"
            response = self._request("GET", endpoint)

            if isinstance(response, list):
                for interview in response:
                    yield ScorecardInterviewAPI(**interview)
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Erro ao buscar scorecard interviews: {str(e)}")

    def get_all_scorecard_jobs(self) -> Generator[ScorecardJobAPI, None, None]:
        """Itera sobre todos os scorecards de vagas"""
        try:
            endpoint = "/forms/scorecards/jobs"
            response = self._request("GET", endpoint)

            if isinstance(response, list):
                for scorecard in response:
                    yield ScorecardJobAPI(**scorecard)
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Erro ao buscar scorecard jobs: {str(e)}")

    def get_scorecard_by_job(self, job_id: str) -> Optional[ScorecardJobAPI]:
        """Busca scorecard de uma vaga específica"""
        try:
            endpoint = f"/forms/scorecards/jobs/{job_id}"
            response = self._request("GET", endpoint)
            return ScorecardJobAPI(**response) if response else None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def get_scorecard_interviews_by_job(self, job_id: str) -> list:
        """Busca entrevistas/scorecards de uma vaga"""
        try:
            endpoint = f"/forms/scorecards/interviews/job/{job_id}"
            response = self._request("GET", endpoint)
            return [ScorecardInterviewAPI(**i) for i in response] if isinstance(response, list) else []
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return []
            raise

    def get_scorecard_avaliacao_candidato(self, candidatura_id: str) -> Optional[Dict]:
        """Busca avaliação de scorecard de um candidato"""
        try:
            endpoint = f"/forms/scorecards/jobTalent/{candidatura_id}"
            response = self._request("GET", endpoint)
            return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    # FORM RESPONSES
    def get_form_responses_by_candidato(self, candidatura_id: str) -> Optional[FormResponseAPI]:
        """Busca respostas de formulários de um candidato"""
        try:
            endpoint = f"/forms/responses/job-talent-id/{candidatura_id}"
            response = self._request("GET", endpoint)
            return FormResponseAPI(jobTalentId=candidatura_id, **response) if response else None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            self.logger.error(f"Erro ao buscar form responses do candidato {candidatura_id}: {str(e)}")
            return None

    # TAGS
    def get_vaga_tags(self, job_id: str) -> list:
        """Busca tags de uma vaga"""
        try:
            endpoint = f"/jobs/{job_id}/tags"
            response = self._request("GET", endpoint)
            return [VagaTagAPI(**tag) for tag in response] if isinstance(response, list) else []
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return []
            raise

    # AUTOMAÇÕES
    def get_all_automations(self) -> Generator[AutomationAPI, None, None]:
        """Itera sobre todas as automações"""
        try:
            endpoint = "/workflows/automations"
            response = self._request("GET", endpoint)

            if isinstance(response, list):
                for automation in response:
                    yield AutomationAPI(**automation)
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Erro ao buscar automações: {str(e)}")

    # CLIENTES
    def get_all_clientes(self) -> Generator[ClienteAPI, None, None]:
        """Itera sobre todos os clientes"""
        try:
            endpoint = "/tenants/clients"
            response = self._request("GET", endpoint)

            if isinstance(response, list):
                for cliente in response:
                    yield ClienteAPI(**cliente)
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Erro ao buscar clientes: {str(e)}")

    # CUSTOM FIELDS
    def get_custom_fields(self, entity_type: str) -> list:
        """Busca custom fields de uma entidade (job, talent, jobTalent)"""
        try:
            endpoint = f"/custom-data-manager/custom-fields/entity/{entity_type}"
            response = self._request("GET", endpoint)
            return [CustomFieldAPI(entityType=entity_type, **field) for field in response] if isinstance(response, list) else []
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return []
            raise

    # DETALHES COMPLETOS
    def get_job_details(self, job_id: str) -> Optional[JobDetailsAPI]:
        """Busca detalhes completos de uma vaga"""
        try:
            endpoint = f"/jobs/{job_id}"
            response = self._request("GET", endpoint)
            return JobDetailsAPI(**response) if response else None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def get_job_talent_details(self, job_id: str, talent_id: str) -> Optional[JobTalentDetailsAPI]:
        """Busca detalhes completos de uma candidatura"""
        try:
            endpoint = f"/job-talents/{job_id}/talents/{talent_id}"
            response = self._request("GET", endpoint)
            if response:
                response['id'] = f"{job_id}*{talent_id}"
                response['jobId'] = job_id
                response['talentId'] = talent_id
                return JobTalentDetailsAPI(**response)
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
