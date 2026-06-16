"""
Serviço de Sincronização - Orquestrador Central
Coordena sincronização de todas as entidades respeitando ordem de dependências
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from interfaces.i_api_client import IAPIClient
from interfaces.i_database_service import IDatabaseService
from services.api_client import InhireAPIClient
from services.database_service import DatabaseService
from config import settings, SyncType, SyncStatus, SyncEntity
from utils.logger import get_logger, log_sync_start, log_sync_end
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class SyncService:
    """
    Orquestrador central de sincronização

    Ordem OBRIGATÓRIA:
    1. Vagas (independente)
    2. Posições (depende de Vagas)
    3. Candidaturas (depende de Vagas)
    4. Talentos (otimizado com IDs das Candidaturas)
    """

    def __init__(
        self,
        session: Session,
        api_client: Optional[IAPIClient] = None,
        db_service: Optional[IDatabaseService] = None
    ):
        """
        Inicializa SyncService com Dependency Injection

        Args:
            session: SQLAlchemy session
            api_client: Implementação de IAPIClient (default: InhireAPIClient)
            db_service: Implementação de IDatabaseService (default: DatabaseService)
        """
        self.logger = get_logger(__name__)
        self.session = session
        self.db = db_service or DatabaseService(session)
        self.api_client = api_client or InhireAPIClient()
        self.tenant_id = settings.INHIRE_TENANT

    # ========================================
    # MÉTODOS AUXILIARES PARA SINCRONIZAÇÃO INCREMENTAL ROBUSTA
    # ========================================

    def _validate_pre_sync(self) -> tuple[bool, str]:
        """
        Valida condições pré-sincronização.

        Returns:
            Tuple (success, message)
        """
        try:
            # 1. Verificar conexão com API (autenticação acontece automaticamente quando necessário)
            self.logger.info("Validando conexão com API Inhire...")
            try:
                # Verificar se auth_service está disponível
                if not hasattr(self.api_client, 'auth_service') or not self.api_client.auth_service:
                    return False, "Auth service não disponível"
                self.logger.info("✓ Conexão com API OK")
            except Exception as e:
                return False, f"Falha na conexão com API: {str(e)}"

            # 2. Verificar conexão com Banco de Dados
            self.logger.info("Validando conexão com Banco de Dados...")
            try:
                self.session.execute(text("SELECT 1"))
                self.logger.info("✓ Conexão com BD OK")
            except Exception as e:
                return False, f"Falha na conexão com BD: {str(e)}"

            # 3. Verificar sync_configuration existe
            self.logger.info("Validando configuração de sincronização...")
            try:
                config = self.db.get_sync_configuration(self.tenant_id)
                if not config:
                    return False, "Configuração de sincronização não encontrada"
                self.logger.info("✓ Configuração de sincronização OK")
            except Exception as e:
                return False, f"Erro ao obter configuração: {str(e)}"

            return True, "Todas as validações pré-sync passaram"

        except Exception as e:
            return False, f"Erro inesperado na validação: {str(e)}"

    def _configure_extended_timeouts(self):
        """
        Configura timeouts estendidos no API client para sincronização incremental.
        """
        self.logger.info("Configurando timeouts estendidos para sincronização incremental...")
        original_timeout = self.api_client.timeout
        extended_timeout = (
            settings.SYNC_INCREMENTAL_TIMEOUT_CONNECT,
            settings.SYNC_INCREMENTAL_TIMEOUT_READ
        )
        self.api_client.timeout = extended_timeout
        self.logger.info(f"Timeouts ajustados: {original_timeout} → {extended_timeout}")
        return original_timeout

    def _restore_timeouts(self, original_timeout: tuple):
        """
        Restaura timeouts originais do API client.
        """
        self.api_client.timeout = original_timeout
        self.logger.info(f"Timeouts restaurados: {original_timeout}")

    class _ErrorCounter:
        """Contador de erros por entidade para controle de falhas críticas"""

        def __init__(self, max_errors: int = 5):
            self.max_errors = max_errors
            self.errors = {}
            self.lock = threading.Lock()

        def add_error(self, entity: str, error: str) -> bool:
            """
            Adiciona erro para entidade. Retorna True se deve continuar, False se deve parar.
            """
            with self.lock:
                if entity not in self.errors:
                    self.errors[entity] = []
                self.errors[entity].append(error)

                if len(self.errors[entity]) >= self.max_errors:
                    return False  # Deve parar
                return True  # Pode continuar

        def get_total_errors(self) -> int:
            """Retorna total de erros acumulados"""
            return sum(len(errs) for errs in self.errors.values())

        def get_error_summary(self) -> str:
            """Retorna resumo dos erros"""
            if not self.errors:
                return "Nenhum erro registrado"

            summary = []
            for entity, errs in self.errors.items():
                summary.append(f"{entity}: {len(errs)} erros")
                for i, err in enumerate(errs, 1):
                    summary.append(f"  {i}. {err[:100]}")
            return "\n".join(summary)

    class _EntityTimer:
        """Rastreador de tempo de sincronização por entidade"""

        def __init__(self):
            self.timings = {}  # {entity_name: {'start': datetime, 'end': datetime, 'duration': float, 'stats': dict}}
            self.lock = threading.Lock()

        def start_entity(self, entity_name: str):
            """
            Marca início da sincronização de uma entidade.

            Args:
                entity_name: Nome da entidade sendo sincronizada
            """
            with self.lock:
                self.timings[entity_name] = {
                    'start': datetime.utcnow(),
                    'end': None,
                    'duration': 0.0,
                    'stats': {}
                }

        def end_entity(self, entity_name: str, stats: Dict):
            """
            Marca fim da sincronização de uma entidade.

            Args:
                entity_name: Nome da entidade que foi sincronizada
                stats: Estatísticas da sincronização (processed, created, updated, skipped, failed)
            """
            with self.lock:
                if entity_name in self.timings:
                    self.timings[entity_name]['end'] = datetime.utcnow()
                    self.timings[entity_name]['duration'] = (
                        self.timings[entity_name]['end'] - self.timings[entity_name]['start']
                    ).total_seconds()
                    self.timings[entity_name]['stats'] = stats

        def get_timings(self) -> Dict:
            """
            Retorna todas as medições de tempo.

            Returns:
                Dict com timings de todas as entidades
            """
            return self.timings

        def get_total_duration(self) -> float:
            """
            Retorna duração total de todas as entidades.

            Returns:
                Float com soma de todas as durações em segundos
            """
            return sum(t['duration'] for t in self.timings.values())

    def _validate_post_sync(self, all_stats: Dict) -> tuple[bool, str]:
        """
        Valida integridade após sincronização.

        Args:
            all_stats: Estatísticas da sincronização

        Returns:
            Tuple (success, message)
        """
        try:
            self.logger.info("Validando integridade pós-sincronização...")

            # 1. Verificar se processou algum registro
            if all_stats['processed'] == 0:
                return False, "Nenhum registro foi processado durante a sincronização"

            # 2. Verificar taxa de falhas
            fail_rate = (all_stats['failed'] / all_stats['processed'] * 100) if all_stats['processed'] > 0 else 0
            if fail_rate > 10:  # Mais de 10% de falhas
                return False, f"Taxa de falhas muito alta: {fail_rate:.2f}% ({all_stats['failed']}/{all_stats['processed']})"

            # 3. Verificar integridade referencial básica
            # Verificar se existem candidaturas sem vaga ou sem talento
            try:
                from models.database import Candidatura, Vaga, Talento

                candidaturas_sem_vaga = self.session.query(Candidatura).filter(
                    ~Candidatura.vaga_id.in_(self.session.query(Vaga.id))
                ).count()

                if candidaturas_sem_vaga > 0:
                    self.logger.warning(f"Encontradas {candidaturas_sem_vaga} candidaturas sem vaga correspondente")

                candidaturas_sem_talento = self.session.query(Candidatura).filter(
                    ~Candidatura.talento_id.in_(self.session.query(Talento.id))
                ).count()

                if candidaturas_sem_talento > 0:
                    self.logger.warning(f"Encontradas {candidaturas_sem_talento} candidaturas sem talento correspondente")

            except Exception as e:
                self.logger.warning(f"Não foi possível validar integridade referencial: {str(e)}")

            self.logger.info("✓ Validação de integridade OK")
            return True, "Integridade validada com sucesso"

        except Exception as e:
            return False, f"Erro na validação pós-sync: {str(e)}"

    def _generate_sync_report(self, all_stats: Dict, error_counter: _ErrorCounter, duration_seconds: float, entity_timer: _EntityTimer = None) -> str:
        """
        Gera relatório detalhado da sincronização.

        Args:
            all_stats: Estatísticas da sincronização
            error_counter: Contador de erros
            duration_seconds: Duração da sincronização em segundos
            entity_timer: Rastreador de tempo por entidade (opcional)

        Returns:
            String com relatório formatado
        """
        report_lines = [
            "\n" + "=" * 80,
            "RELATÓRIO DE SINCRONIZAÇÃO INCREMENTAL COMPLETA",
            "=" * 80,
            "",
            f"Duração Total: {duration_seconds:.2f} segundos ({duration_seconds/60:.2f} minutos)",
            "",
        ]

        # === NOVA SEÇÃO: TEMPO POR TABELA ===
        if entity_timer:
            timings = entity_timer.get_timings()
            if timings:
                report_lines.extend([
                    "TEMPO POR TABELA:",
                    "-" * 80,
                    f"{'Entidade':<30} {'Tempo (s)':<12} {'% Total':<10} {'Processados':<12} {'Skip Rate':<10}",
                    "-" * 80,
                ])

                # Ordenar por tempo (mais lento primeiro)
                sorted_timings = sorted(timings.items(), key=lambda x: x[1]['duration'], reverse=True)
                total_duration = duration_seconds

                for entity_name, timing in sorted_timings:
                    stats = timing['stats']
                    duration = timing['duration']
                    pct_total = (duration / total_duration * 100) if total_duration > 0 else 0
                    processed = stats.get('processed', 0)
                    skipped = stats.get('skipped', 0)
                    skip_rate = (skipped / processed * 100) if processed > 0 else 0

                    report_lines.append(
                        f"{entity_name:<30} {duration:>10.2f}s  {pct_total:>8.1f}%  {processed:>10,}  {skip_rate:>8.1f}%"
                    )

                report_lines.extend(["", "-" * 80, ""])

        # === ESTATÍSTICAS GERAIS ===
        report_lines.extend([
            "ESTATÍSTICAS GERAIS:",
            f"  Total Processado: {all_stats['processed']:,}",
            f"  Criados:          {all_stats['created']:,}",
            f"  Atualizados:      {all_stats['updated']:,}",
            f"  Pulados (skip):   {all_stats['skipped']:,}",
            f"  Falhas:           {all_stats['failed']:,}",
            "",
            f"Taxa de Skip:     {(all_stats['skipped'] / all_stats['processed'] * 100) if all_stats['processed'] > 0 else 0:.2f}%",
            f"Taxa de Falhas:   {(all_stats['failed'] / all_stats['processed'] * 100) if all_stats['processed'] > 0 else 0:.2f}%",
            "",
        ])

        # Adicionar erros se houver
        total_errors = error_counter.get_total_errors()
        if total_errors > 0:
            report_lines.extend([
                f"ERROS ENCONTRADOS ({total_errors} total):",
                error_counter.get_error_summary(),
                ""
            ])

        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def sync_full(self) -> Dict:
        """
        Sincronização completa - importa TODOS os dados

        Returns:
            Dict com resultado da sincronização
        """
        self.logger.info("=== INICIANDO SINCRONIZAÇÃO COMPLETA ===")

        config = self.db.get_sync_configuration(self.tenant_id)
        main_log = self.db.create_sync_log(config.id, SyncType.FULL, SyncEntity.ALL)

        all_stats = {
            'processed': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'failed': 0
        }
        errors = []

        try:
            # 1. VAGAS (PRIMEIRO - OBRIGATÓRIO)
            if settings.SYNC_VAGAS_ENABLED:
                self.logger.info(">>> Sincronizando VAGAS...")
                vaga_stats = self._sync_vagas_full()
                self._merge_stats(all_stats, vaga_stats)

            # 2. POSIÇÕES (SEGUNDO - DEPENDE DE VAGAS)
            if settings.SYNC_POSICOES_ENABLED:
                self.logger.info(">>> Sincronizando POSIÇÕES...")
                pos_stats = self._sync_posicoes_full()
                self._merge_stats(all_stats, pos_stats)

            # 2.1 POSITION TIMELINE (DEPENDE DE POSIÇÕES)
            self.logger.info(">>> Sincronizando POSITION TIMELINE...")
            pt_stats = self._sync_position_timeline_full()
            self._merge_stats(all_stats, pt_stats)

            # 3. CANDIDATURAS (TERCEIRO - DEPENDE DE VAGAS)
            talent_ids = set()
            if settings.SYNC_CANDIDATURAS_ENABLED:
                self.logger.info(">>> Sincronizando CANDIDATURAS...")
                cand_stats, talent_ids = self._sync_candidaturas_full()
                self._merge_stats(all_stats, cand_stats)

            # 4. TALENTOS (QUARTO - OTIMIZADO COM IDs DAS CANDIDATURAS)
            if settings.SYNC_TALENTOS_ENABLED:
                self.logger.info(">>> Sincronizando TALENTOS...")
                tal_stats = self._sync_talentos_full(talent_ids)
                self._merge_stats(all_stats, tal_stats)

            # 5. NOVAS ENTIDADES (APÓS ENTIDADES PRINCIPAIS)

            # 5.1 REQUISIÇÕES (DEPENDE DE VAGAS)
            self.logger.info(">>> Sincronizando REQUISIÇÕES...")
            req_stats = self._sync_requisicoes()
            self._merge_stats(all_stats, req_stats)

            # 5.2 SCORECARD INTERVIEWS (INDEPENDENTE)
            self.logger.info(">>> Sincronizando SCORECARD INTERVIEWS...")
            si_stats = self._sync_scorecard_interviews()
            self._merge_stats(all_stats, si_stats)

            # 5.3 SCORECARD JOBS (DEPENDE DE VAGAS)
            self.logger.info(">>> Sincronizando SCORECARD JOBS...")
            sj_stats = self._sync_scorecard_jobs()
            self._merge_stats(all_stats, sj_stats)

            # 5.4 FORM RESPONSES (DESABILITADO - dados complexos, baixo valor analítico)
            # self.logger.info(">>> Sincronizando FORM RESPONSES...")
            # fr_stats = self._sync_form_responses()
            # self._merge_stats(all_stats, fr_stats)
            self.logger.info(">>> FORM RESPONSES: DESABILITADO (dados complexos, baixo valor para BI)")

            # 5.5 TAGS DE VAGAS (DEPENDE DE VAGAS)
            self.logger.info(">>> Sincronizando TAGS DE VAGAS...")
            tag_stats = self._sync_vaga_tags()
            self._merge_stats(all_stats, tag_stats)

            # 5.6 AUTOMAÇÕES (DESABILITADO - configuração do sistema, não dados de negócio)
            # self.logger.info(">>> Sincronizando AUTOMAÇÕES...")
            # auto_stats = self._sync_automations()
            # self._merge_stats(all_stats, auto_stats)
            self.logger.info(">>> AUTOMATIONS: DESABILITADO (configuração do sistema, não relevante para BI)")

            # 5.7 CLIENTES (INDEPENDENTE)
            self.logger.info(">>> Sincronizando CLIENTES...")
            cli_stats = self._sync_clientes()
            self._merge_stats(all_stats, cli_stats)

            # 5.8 CUSTOM FIELDS (INDEPENDENTE)
            self.logger.info(">>> Sincronizando CUSTOM FIELDS...")
            cf_stats = self._sync_custom_fields()
            self._merge_stats(all_stats, cf_stats)

            # Finalizar
            config.last_full_sync = datetime.utcnow()
            self.session.commit()

            self.db.complete_sync_log(main_log, SyncStatus.SUCCESS, all_stats)

            self.logger.info("=== SINCRONIZAÇÃO COMPLETA FINALIZADA COM SUCESSO ===")
            return {
                'success': True,
                'status': SyncStatus.SUCCESS,
                'stats': all_stats
            }

        except Exception as e:
            self.logger.error(f"Erro na sincronização completa: {str(e)}", exc_info=True)
            self.db.complete_sync_log(main_log, SyncStatus.ERROR, all_stats, errors=str(e))
            return {
                'success': False,
                'status': SyncStatus.ERROR,
                'error': str(e),
                'stats': all_stats
            }

    def sync_express(self) -> Dict:
        """
        Sincronização EXPRESS - apenas dados críticos operacionais

        Estratégia:
        1. Busca vagas com posições abertas (do BD)
        2. Sincroniza candidaturas apenas dessas vagas
        3. Sincroniza talentos vinculados às candidaturas
        4. Sincroniza timeline das posições abertas

        Tempo estimado: ~3-5 minutos
        Volume: ~20% dos dados (vagas ativas + candidatos ativos)
        Frequência recomendada: a cada 2-4 horas

        Returns:
            Dict com resultado da sincronização
        """
        self.logger.info("=== INICIANDO SINCRONIZAÇÃO EXPRESS ===")

        config = self.db.get_sync_configuration(self.tenant_id)
        # TEMPORÁRIO: usar INCREMENTAL até reiniciar aplicação Python
        # Após reiniciar, SQLAlchemy recarregará ENUMs e EXPRESS estará disponível
        # TODO: Voltar para SyncType.EXPRESS após reinício
        main_log = self.db.create_sync_log(config.id, SyncType.INCREMENTAL, SyncEntity.ALL)

        all_stats = {
            'processed': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'failed': 0
        }
        errors = []

        try:
            # 1. Buscar vagas com posições abertas (do BD - super rápido)
            self.logger.info(">>> Buscando vagas com posições abertas...")
            vagas_ativas = self.db.get_vagas_com_posicoes_abertas()
            self.logger.info(f"Encontradas {len(vagas_ativas)} vagas com posições abertas")

            if not vagas_ativas:
                self.logger.warning("Nenhuma vaga com posições abertas encontrada")
                return {
                    'success': True,
                    'status': SyncStatus.SUCCESS,
                    'stats': all_stats,
                    'message': 'Nenhuma vaga ativa para sincronizar'
                }

            # 2. Sincronizar candidaturas dessas vagas
            self.logger.info(f">>> Sincronizando candidaturas de {len(vagas_ativas)} vagas ativas...")
            talent_ids = set()

            for idx, vaga in enumerate(vagas_ativas, 1):
                try:
                    # Log de progresso a cada 50 vagas
                    if idx % 50 == 0:
                        self.logger.info(f"   Processando vaga {idx}/{len(vagas_ativas)}")

                    # Buscar candidaturas via API
                    candidaturas = list(self.api_client.get_all_candidaturas(vaga.inhire_id))

                    for cand in candidaturas:
                        try:
                            # Salvar candidatura (passar job_id como segundo parâmetro)
                            success, action = self.db.upsert_candidatura(cand, vaga.inhire_id, commit=False)

                            if success:
                                all_stats['processed'] += 1
                                if action == 'created':
                                    all_stats['created'] += 1
                                elif action == 'updated':
                                    all_stats['updated'] += 1
                                else:
                                    all_stats['skipped'] += 1

                                # Coletar talent_id para buscar depois
                                if cand.talentId:
                                    talent_ids.add(cand.talentId)

                        except Exception as e:
                            all_stats['failed'] += 1
                            self.logger.error(f"Erro ao processar candidatura {cand.id}: {e}")
                            errors.append(f"Candidatura {cand.id}: {str(e)}")

                    # Commit a cada 50 candidaturas
                    if idx % 50 == 0:
                        self.db.batch_commit()

                except Exception as e:
                    all_stats['failed'] += 1
                    self.logger.error(f"Erro ao processar vaga {vaga.inhire_id}: {e}")
                    errors.append(f"Vaga {vaga.inhire_id}: {str(e)}")

            # Commit final
            self.db.batch_commit()
            self.logger.info(f"✓ Candidaturas sincronizadas. {len(talent_ids)} talentos únicos encontrados")

            # 3. Sincronizar talentos vinculados
            self.logger.info(f">>> Sincronizando {len(talent_ids)} talentos vinculados...")

            for idx, talent_id in enumerate(talent_ids, 1):
                try:
                    if idx % 100 == 0:
                        self.logger.info(f"   Processando talento {idx}/{len(talent_ids)}")

                    talento = self.api_client.get_talento_by_id(talent_id)

                    if talento:
                        success, action = self.db.upsert_talento(talento, commit=False)

                        if success:
                            all_stats['processed'] += 1
                            if action == 'created':
                                all_stats['created'] += 1
                            elif action == 'updated':
                                all_stats['updated'] += 1
                            else:
                                all_stats['skipped'] += 1

                    # Commit a cada 100 talentos
                    if idx % 100 == 0:
                        self.db.batch_commit()

                except Exception as e:
                    all_stats['failed'] += 1
                    self.logger.error(f"Erro ao processar talento {talent_id}: {e}")
                    errors.append(f"Talento {talent_id}: {str(e)}")

            # Commit final
            self.db.batch_commit()
            self.logger.info(f"✓ Talentos sincronizados")

            # Atualizar configuração de sync
            config.last_incremental_sync = datetime.utcnow()
            self.session.commit()

            # Finalizar log
            status = SyncStatus.SUCCESS if all_stats['failed'] == 0 else SyncStatus.PARTIAL
            error_msg = "\n".join(errors[:100]) if errors else None
            self.db.complete_sync_log(main_log, status, all_stats, errors=error_msg)

            self.logger.info(f"=== SYNC EXPRESS CONCLUÍDO: {all_stats} ===")

            return {
                'success': True,
                'status': status,
                'stats': all_stats,
                'errors': errors if errors else None
            }

        except Exception as e:
            self.logger.error(f"ERRO CRÍTICO no sync_express: {str(e)}")
            import traceback
            traceback.print_exc()

            self.session.rollback()
            self.db.complete_sync_log(main_log, SyncStatus.ERROR, all_stats, errors=str(e))

            return {
                'success': False,
                'status': SyncStatus.ERROR,
                'error': str(e),
                'stats': all_stats
            }

    def sync_incremental(self, express_mode: bool = True, completa_100_pct: bool = False) -> Dict:
        """
        Sincronização incremental OTIMIZADA - compara datas BD vs API

        Estratégia:
        1. Busca registros da API filtrando por status (quando aplicável)
        2. Compara updated_at do BD com updated_at da API
        3. Atualiza apenas se API tem versão mais recente
        4. Pula tabelas vazias que não têm dados disponíveis na API

        Args:
            express_mode: Se True, sincroniza Vagas + Posições + Talentos + Scorecards (~10 min)
                         Se False, sincroniza tudo incluindo Candidaturas (pode demorar 20+ min)
            completa_100_pct: Se True, ativa modo robusto com validações e timeouts estendidos

        Returns:
            Dict com resultado
        """
        start_time = datetime.utcnow()
        mode_name = "EXPRESS" if express_mode else "COMPLETA"
        if completa_100_pct:
            mode_name += " (100% ROBUSTA)"

        self.logger.info(f"=== INICIANDO SINCRONIZAÇÃO INCREMENTAL OTIMIZADA {mode_name} ===")

        # === VALIDAÇÕES PRÉ-SYNC (se modo robusto) ===
        if completa_100_pct:
            self.logger.info("Executando validações pré-sincronização...")
            validation_ok, validation_msg = self._validate_pre_sync()
            if not validation_ok:
                error_msg = f"VALIDAÇÃO PRÉ-SYNC FALHOU: {validation_msg}"
                self.logger.error(error_msg)
                return {'success': False, 'status': SyncStatus.ERROR, 'error': error_msg}
            self.logger.info(f"✓ {validation_msg}")

        # === CONFIGURAR TIMEOUTS ESTENDIDOS (se modo robusto) ===
        original_timeout = None
        if completa_100_pct:
            original_timeout = self._configure_extended_timeouts()

        config = self.db.get_sync_configuration(self.tenant_id)
        last_sync = config.last_incremental_sync or config.last_full_sync

        if not last_sync:
            self.logger.warning("Nenhuma sincronização anterior, executando full sync")
            if original_timeout:
                self._restore_timeouts(original_timeout)
            return self.sync_full()

        main_log = self.db.create_sync_log(config.id, SyncType.INCREMENTAL, SyncEntity.ALL)
        all_stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        # === INICIALIZAR CONTADOR DE ERROS (se modo robusto) ===
        error_counter = self._ErrorCounter(max_errors=settings.SYNC_INCREMENTAL_MAX_ERRORS_PER_ENTITY) if completa_100_pct else None

        # === INICIALIZAR RASTREADOR DE TEMPO (se modo robusto) ===
        entity_timer = self._EntityTimer() if completa_100_pct else None

        try:
            # === ENTIDADES CRÍTICAS (SEMPRE SINCRONIZADAS) ===

            # 1. VAGAS (comparação de datas - captura mudanças de status)
            if settings.SYNC_VAGAS_ENABLED:
                self.logger.info(">>> Sincronizando VAGAS (comparação de datas)...")
                try:
                    if entity_timer:
                        entity_timer.start_entity("VAGAS")
                    vaga_stats = self._sync_vagas_incremental()
                    self._merge_stats(all_stats, vaga_stats)
                    if entity_timer:
                        entity_timer.end_entity("VAGAS", vaga_stats)
                except Exception as e:
                    error_msg = f"Erro ao sincronizar VAGAS: {str(e)}"
                    self.logger.error(error_msg, exc_info=True)
                    if completa_100_pct and error_counter:
                        if not error_counter.add_error("VAGAS", error_msg):
                            raise Exception(f"Muitos erros em VAGAS (>{settings.SYNC_INCREMENTAL_MAX_ERRORS_PER_ENTITY}). Interrompendo sincronização.") from e
                    if settings.SYNC_INCREMENTAL_FAIL_ON_ERROR:
                        raise

            # === EXPRESS MODE: TODAS AS ENTIDADES COM COMPARACAO DE DATAS ===
            if express_mode:
                self.logger.info("Modo EXPRESS: Sincronizando TODAS as entidades com comparacao de datas")

                # 2. POSIÇÕES (comparação de datas - captura mudanças de status)
                if settings.SYNC_POSICOES_ENABLED:
                    try:
                        self.logger.info(">>> Sincronizando POSICOES (comparação de datas)...")
                        if entity_timer:
                            entity_timer.start_entity("POSIÇÕES")
                        pos_stats = self._sync_posicoes_incremental()
                        self._merge_stats(all_stats, pos_stats)
                        if entity_timer:
                            entity_timer.end_entity("POSIÇÕES", pos_stats)
                    except Exception as e:
                        self.logger.error(f"Erro ao sincronizar POSICOES: {str(e)}")

                # 2.1 POSITION TIMELINE (DEPENDE DE POSIÇÕES)
                try:
                    self.logger.info(">>> Sincronizando POSITION TIMELINE (incremental)...")
                    if entity_timer:
                        entity_timer.start_entity("POSITION_TIMELINE")
                    pt_stats = self._sync_position_timeline_incremental()
                    self._merge_stats(all_stats, pt_stats)
                    if entity_timer:
                        entity_timer.end_entity("POSITION_TIMELINE", pt_stats)
                except Exception as e:
                    self.logger.error(f"Erro ao sincronizar POSITION TIMELINE: {str(e)}")

                # 3. CANDIDATURAS (comparação de datas - captura mudanças de status)
                if settings.SYNC_CANDIDATURAS_ENABLED:
                    try:
                        self.logger.info(">>> Sincronizando CANDIDATURAS (comparação de datas)...")
                        if entity_timer:
                            entity_timer.start_entity("CANDIDATURAS")
                        cand_stats = self._sync_candidaturas_incremental()
                        self._merge_stats(all_stats, cand_stats)
                        if entity_timer:
                            entity_timer.end_entity("CANDIDATURAS", cand_stats)
                    except Exception as e:
                        self.logger.error(f"Erro ao sincronizar CANDIDATURAS: {str(e)}")

                # 4. CANDIDATURA TIMELINE (DESABILITADO temporariamente - muito lento)
                # try:
                #     self.logger.info(">>> Sincronizando CANDIDATURA TIMELINE...")
                #     ctl_stats = self._sync_candidatura_timeline_incremental()
                #     self._merge_stats(all_stats, ctl_stats)
                # except Exception as e:
                #     self.logger.error(f"Erro ao sincronizar CANDIDATURA TIMELINE: {str(e)}")
                self.logger.info(">>> CANDIDATURA TIMELINE: DESABILITADO (problemas de performance na API)")

                # 5. TALENTOS (comparação de datas)
                if settings.SYNC_TALENTOS_ENABLED:
                    try:
                        self.logger.info(">>> Sincronizando TALENTOS...")
                        if entity_timer:
                            entity_timer.start_entity("TALENTOS")
                        tal_stats = self._sync_talentos_incremental_optimized()
                        self._merge_stats(all_stats, tal_stats)
                        if entity_timer:
                            entity_timer.end_entity("TALENTOS", tal_stats)
                    except Exception as e:
                        self.logger.warning(f"Erro ao sincronizar talentos: {str(e)}")

                # 5.1 TALENTOS FALTANTES (apenas os que não existem na tabela)
                if settings.SYNC_TALENTOS_ENABLED:
                    try:
                        self.logger.info(">>> Sincronizando TALENTOS FALTANTES...")
                        if entity_timer:
                            entity_timer.start_entity("TALENTOS_FALTANTES")
                        missing_tal_stats = self._sync_missing_talentos()
                        self._merge_stats(all_stats, missing_tal_stats)
                        if entity_timer:
                            entity_timer.end_entity("TALENTOS_FALTANTES", missing_tal_stats)
                    except Exception as e:
                        self.logger.warning(f"Erro ao sincronizar talentos faltantes: {str(e)}")

                # 6. TALENTO ARQUIVOS (DESABILITADO - muito lento, faz 1 chamada API por talento)
                # Pode acessar CVs diretamente no ATS quando necessário
                # try:
                #     self.logger.info(">>> Sincronizando TALENTO ARQUIVOS (otimizado)...")
                #     ta_stats = self._sync_talento_arquivos_incremental_optimized()
                #     self._merge_stats(all_stats, ta_stats)
                # except Exception as e:
                #     self.logger.error(f"Erro ao sincronizar TALENTO ARQUIVOS: {str(e)}")
                self.logger.info(">>> TALENTO ARQUIVOS: DESABILITADO (acessar CVs diretamente no ATS)")

                # 7. SCORECARD INTERVIEWS (comparação de datas)
                try:
                    self.logger.info(">>> Sincronizando SCORECARD INTERVIEWS...")
                    if entity_timer:
                        entity_timer.start_entity("SCORECARD_INTERVIEWS")
                    si_stats = self._sync_scorecard_interviews_incremental()
                    self._merge_stats(all_stats, si_stats)
                    if entity_timer:
                        entity_timer.end_entity("SCORECARD_INTERVIEWS", si_stats)
                except Exception as e:
                    self.logger.error(f"Erro ao sincronizar SCORECARD INTERVIEWS: {str(e)}")

                # 8. SCORECARD JOBS (comparação de datas)
                try:
                    self.logger.info(">>> Sincronizando SCORECARD JOBS...")
                    if entity_timer:
                        entity_timer.start_entity("SCORECARD_JOBS")
                    sj_stats = self._sync_scorecard_jobs_incremental()
                    self._merge_stats(all_stats, sj_stats)
                    if entity_timer:
                        entity_timer.end_entity("SCORECARD_JOBS", sj_stats)
                except Exception as e:
                    self.logger.error(f"Erro ao sincronizar SCORECARD JOBS: {str(e)}")

                # 9. FORM RESPONSES (DESABILITADO - dados complexos, baixo valor analítico)
                # try:
                #     self.logger.info(">>> Sincronizando FORM RESPONSES (últimos 7 dias)...")
                #     fr_stats = self._sync_form_responses_incremental()
                #     self._merge_stats(all_stats, fr_stats)
                # except Exception as e:
                #     self.logger.error(f"Erro ao sincronizar FORM RESPONSES: {str(e)}")
                self.logger.info(">>> FORM RESPONSES: DESABILITADO (dados complexos, pouco estruturados, baixo valor para BI)")

                # 10. VAGA TAGS (cria se não existir - tags não têm updatedAt)
                try:
                    self.logger.info(">>> Sincronizando VAGA TAGS...")
                    if entity_timer:
                        entity_timer.start_entity("VAGA_TAGS")
                    vt_stats = self._sync_vaga_tags_incremental()
                    self._merge_stats(all_stats, vt_stats)
                    if entity_timer:
                        entity_timer.end_entity("VAGA_TAGS", vt_stats)
                except Exception as e:
                    self.logger.error(f"Erro ao sincronizar VAGA TAGS: {str(e)}")

                # 11. REQUISIÇÕES (comparação de datas)
                try:
                    self.logger.info(">>> Sincronizando REQUISIÇÕES...")
                    if entity_timer:
                        entity_timer.start_entity("REQUISIÇÕES")
                    req_stats = self._sync_requisicoes_incremental()
                    self._merge_stats(all_stats, req_stats)
                    if entity_timer:
                        entity_timer.end_entity("REQUISIÇÕES", req_stats)
                except Exception as e:
                    self.logger.error(f"Erro ao sincronizar REQUISIÇÕES: {str(e)}")

                # 12. AUTOMATIONS (DESABILITADO - configuração do sistema, não dados de negócio)
                # try:
                #     self.logger.info(">>> Sincronizando AUTOMATIONS...")
                #     aut_stats = self._sync_automations_incremental()
                #     self._merge_stats(all_stats, aut_stats)
                # except Exception as e:
                #     self.logger.error(f"Erro ao sincronizar AUTOMATIONS: {str(e)}")
                self.logger.info(">>> AUTOMATIONS: DESABILITADO (configuração do sistema, não relevante para BI)")

                # 13. CLIENTES (comparação de datas)
                try:
                    self.logger.info(">>> Sincronizando CLIENTES...")
                    if entity_timer:
                        entity_timer.start_entity("CLIENTES")
                    cli_stats = self._sync_clientes_incremental()
                    self._merge_stats(all_stats, cli_stats)
                    if entity_timer:
                        entity_timer.end_entity("CLIENTES", cli_stats)
                except Exception as e:
                    self.logger.error(f"Erro ao sincronizar CLIENTES: {str(e)}")

                # 14. CUSTOM FIELDS (comparação de datas)
                try:
                    self.logger.info(">>> Sincronizando CUSTOM FIELDS...")
                    if entity_timer:
                        entity_timer.start_entity("CUSTOM_FIELDS")
                    cf_stats = self._sync_custom_fields_incremental()
                    self._merge_stats(all_stats, cf_stats)
                    if entity_timer:
                        entity_timer.end_entity("CUSTOM_FIELDS", cf_stats)
                except Exception as e:
                    self.logger.error(f"Erro ao sincronizar CUSTOM FIELDS: {str(e)}")

            # === MODO COMPLETO: Inclui Candidaturas e outras entidades pesadas ===
            else:
                self.logger.info("Modo COMPLETO: Sincronizando todas as entidades incluindo Candidaturas")

                # 2. POSIÇÕES (comparação de datas - captura mudanças de status)
                if settings.SYNC_POSICOES_ENABLED:
                    try:
                        self.logger.info(">>> Sincronizando POSIÇÕES (comparação de datas)...")
                        pos_stats = self._sync_posicoes_incremental()
                        self._merge_stats(all_stats, pos_stats)
                    except Exception as e:
                        self.logger.error(f"Erro ao sincronizar POSIÇÕES: {str(e)}")

                # 2.1 POSITION TIMELINE (DEPENDE DE POSIÇÕES)
                try:
                    self.logger.info(">>> Sincronizando POSITION TIMELINE (incremental)...")
                    if entity_timer:
                        entity_timer.start_entity("POSITION_TIMELINE")
                    pt_stats = self._sync_position_timeline_incremental()
                    self._merge_stats(all_stats, pt_stats)
                    if entity_timer:
                        entity_timer.end_entity("POSITION_TIMELINE", pt_stats)
                except Exception as e:
                    self.logger.error(f"Erro ao sincronizar POSITION TIMELINE: {str(e)}")

                # 3. CANDIDATURAS (comparação de datas - captura mudanças de status)
                if settings.SYNC_CANDIDATURAS_ENABLED:
                    try:
                        self.logger.info(">>> Sincronizando CANDIDATURAS (comparação de datas)...")
                        cand_stats = self._sync_candidaturas_incremental()
                        self._merge_stats(all_stats, cand_stats)
                    except Exception as e:
                        self.logger.error(f"Erro ao sincronizar CANDIDATURAS: {str(e)}")

                # 4. CANDIDATURA_TIMELINE (comparação de datas individuais)
                try:
                    self.logger.info(">>> Sincronizando CANDIDATURA TIMELINE...")
                    ctl_stats = self._sync_candidatura_timeline_incremental()
                    self._merge_stats(all_stats, ctl_stats)
                except Exception as e:
                    self.logger.error(f"Erro ao sincronizar CANDIDATURA TIMELINE: {str(e)}")

                # 5. TALENTOS (comparação de datas)
                if settings.SYNC_TALENTOS_ENABLED:
                    try:
                        self.logger.info(">>> Sincronizando TALENTOS...")
                        if entity_timer:
                            entity_timer.start_entity("TALENTOS")
                        tal_stats = self._sync_talentos_incremental_optimized()
                        self._merge_stats(all_stats, tal_stats)
                        if entity_timer:
                            entity_timer.end_entity("TALENTOS", tal_stats)
                    except Exception as e:
                        self.logger.warning(f"Erro ao sincronizar talentos: {str(e)}")

                # 5.1 TALENTOS FALTANTES (apenas os que não existem na tabela)
                if settings.SYNC_TALENTOS_ENABLED:
                    try:
                        self.logger.info(">>> Sincronizando TALENTOS FALTANTES...")
                        if entity_timer:
                            entity_timer.start_entity("TALENTOS_FALTANTES")
                        missing_tal_stats = self._sync_missing_talentos()
                        self._merge_stats(all_stats, missing_tal_stats)
                        if entity_timer:
                            entity_timer.end_entity("TALENTOS_FALTANTES", missing_tal_stats)
                    except Exception as e:
                        self.logger.warning(f"Erro ao sincronizar talentos faltantes: {str(e)}")

                # 6. TALENTO_ARQUIVOS (DESABILITADO - muito lento, faz 1 chamada API por talento)
                # Pode acessar CVs diretamente no ATS quando necessário
                # try:
                #     self.logger.info(">>> Sincronizando TALENTO ARQUIVOS...")
                #     ta_stats = self._sync_talento_arquivos_incremental_optimized()
                #     self._merge_stats(all_stats, ta_stats)
                # except Exception as e:
                #     self.logger.error(f"Erro ao sincronizar TALENTO ARQUIVOS: {str(e)}")
                self.logger.info(">>> TALENTO ARQUIVOS: DESABILITADO (acessar CVs diretamente no ATS)")

                # 7. SCORECARD INTERVIEWS (comparação de datas)
                try:
                    self.logger.info(">>> Sincronizando SCORECARD INTERVIEWS...")
                    if entity_timer:
                        entity_timer.start_entity("SCORECARD_INTERVIEWS")
                    si_stats = self._sync_scorecard_interviews_incremental()
                    self._merge_stats(all_stats, si_stats)
                    if entity_timer:
                        entity_timer.end_entity("SCORECARD_INTERVIEWS", si_stats)
                except Exception as e:
                    self.logger.error(f"Erro ao sincronizar SCORECARD INTERVIEWS: {str(e)}")

                # 8. SCORECARD JOBS (comparação de datas)
                try:
                    self.logger.info(">>> Sincronizando SCORECARD JOBS...")
                    if entity_timer:
                        entity_timer.start_entity("SCORECARD_JOBS")
                    sj_stats = self._sync_scorecard_jobs_incremental()
                    self._merge_stats(all_stats, sj_stats)
                    if entity_timer:
                        entity_timer.end_entity("SCORECARD_JOBS", sj_stats)
                except Exception as e:
                    self.logger.error(f"Erro ao sincronizar SCORECARD JOBS: {str(e)}")

                # 9. FORM RESPONSES (DESABILITADO - dados complexos, baixo valor analítico)
                # try:
                #     self.logger.info(">>> Sincronizando FORM RESPONSES (últimos 7 dias)...")
                #     fr_stats = self._sync_form_responses_incremental()
                #     self._merge_stats(all_stats, fr_stats)
                # except Exception as e:
                #     self.logger.error(f"Erro ao sincronizar FORM RESPONSES: {str(e)}")
                self.logger.info(">>> FORM RESPONSES: DESABILITADO (dados complexos, pouco estruturados, baixo valor para BI)")

                # 10. VAGA TAGS (cria se não existir - tags não têm updatedAt)
                try:
                    self.logger.info(">>> Sincronizando VAGA TAGS...")
                    if entity_timer:
                        entity_timer.start_entity("VAGA_TAGS")
                    vt_stats = self._sync_vaga_tags_incremental()
                    self._merge_stats(all_stats, vt_stats)
                    if entity_timer:
                        entity_timer.end_entity("VAGA_TAGS", vt_stats)
                except Exception as e:
                    self.logger.error(f"Erro ao sincronizar VAGA TAGS: {str(e)}")

                # 11. REQUISIÇÕES (comparação de datas)
                try:
                    self.logger.info(">>> Sincronizando REQUISIÇÕES...")
                    if entity_timer:
                        entity_timer.start_entity("REQUISIÇÕES")
                    req_stats = self._sync_requisicoes_incremental()
                    self._merge_stats(all_stats, req_stats)
                    if entity_timer:
                        entity_timer.end_entity("REQUISIÇÕES", req_stats)
                except Exception as e:
                    self.logger.error(f"Erro ao sincronizar REQUISIÇÕES: {str(e)}")

                # 12. AUTOMATIONS (DESABILITADO - configuração do sistema, não dados de negócio)
                # try:
                #     self.logger.info(">>> Sincronizando AUTOMATIONS...")
                #     aut_stats = self._sync_automations_incremental()
                #     self._merge_stats(all_stats, aut_stats)
                # except Exception as e:
                #     self.logger.error(f"Erro ao sincronizar AUTOMATIONS: {str(e)}")
                self.logger.info(">>> AUTOMATIONS: DESABILITADO (configuração do sistema, não relevante para BI)")

                # 13. CLIENTES (comparação de datas)
                try:
                    self.logger.info(">>> Sincronizando CLIENTES...")
                    if entity_timer:
                        entity_timer.start_entity("CLIENTES")
                    cli_stats = self._sync_clientes_incremental()
                    self._merge_stats(all_stats, cli_stats)
                    if entity_timer:
                        entity_timer.end_entity("CLIENTES", cli_stats)
                except Exception as e:
                    self.logger.error(f"Erro ao sincronizar CLIENTES: {str(e)}")

                # 14. CUSTOM FIELDS (comparação de datas)
                try:
                    self.logger.info(">>> Sincronizando CUSTOM FIELDS...")
                    if entity_timer:
                        entity_timer.start_entity("CUSTOM_FIELDS")
                    cf_stats = self._sync_custom_fields_incremental()
                    self._merge_stats(all_stats, cf_stats)
                    if entity_timer:
                        entity_timer.end_entity("CUSTOM_FIELDS", cf_stats)
                except Exception as e:
                    self.logger.error(f"Erro ao sincronizar CUSTOM FIELDS: {str(e)}")

            # === SINCRONIZAÇÃO COMPLETA ===
            # Todas as entidades foram sincronizadas com comparação de datas:
            # - Vagas, Posições, Candidaturas, Talentos, Talento Arquivos
            # - Scorecard Interviews, Scorecard Jobs, Form Responses
            # - Vaga Tags, Requisições, Automations, Clientes, Custom Fields

            # === VALIDAÇÃO PÓS-SYNC (se modo robusto) ===
            if completa_100_pct and settings.SYNC_INCREMENTAL_VALIDATE_INTEGRITY:
                self.logger.info("Executando validações pós-sincronização...")
                validation_ok, validation_msg = self._validate_post_sync(all_stats)
                if not validation_ok:
                    error_msg = f"VALIDAÇÃO PÓS-SYNC FALHOU: {validation_msg}"
                    self.logger.error(error_msg)
                    self.db.complete_sync_log(main_log, SyncStatus.ERROR, all_stats, errors=error_msg)
                    if original_timeout:
                        self._restore_timeouts(original_timeout)
                    return {'success': False, 'status': SyncStatus.ERROR, 'error': error_msg}
                self.logger.info(f"✓ {validation_msg}")

            config.last_incremental_sync = datetime.utcnow()
            self.session.commit()

            self.db.complete_sync_log(main_log, SyncStatus.SUCCESS, all_stats)

            # === RESTAURAR TIMEOUTS (se foram alterados) ===
            if original_timeout:
                self._restore_timeouts(original_timeout)

            # === GERAR RELATÓRIO DETALHADO (se modo robusto) ===
            if completa_100_pct and error_counter:
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                report = self._generate_sync_report(all_stats, error_counter, duration, entity_timer)
                self.logger.info(report)

            self.logger.info("=== SINCRONIZAÇÃO INCREMENTAL FINALIZADA ===")
            return {'success': True, 'status': SyncStatus.SUCCESS, 'stats': all_stats}

        except Exception as e:
            self.logger.error(f"Erro na sincronização incremental: {str(e)}", exc_info=True)
            self.db.complete_sync_log(main_log, SyncStatus.ERROR, all_stats, errors=str(e))

            # === RESTAURAR TIMEOUTS EM CASO DE ERRO ===
            if original_timeout:
                self._restore_timeouts(original_timeout)

            # === GERAR RELATÓRIO DE ERRO (se modo robusto) ===
            if completa_100_pct and error_counter:
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                report = self._generate_sync_report(all_stats, error_counter, duration, entity_timer)
                self.logger.error(report)

            return {'success': False, 'status': SyncStatus.ERROR, 'error': str(e)}

    def sync_manual(self, entity: str = 'all') -> Dict:
        """Sincronização manual de entidade específica"""
        self.logger.info(f"=== SINCRONIZAÇÃO MANUAL: {entity.upper()} ===")

        if entity == 'all':
            return self.sync_full()

        config = self.db.get_sync_configuration(self.tenant_id)
        main_log = self.db.create_sync_log(config.id, SyncType.MANUAL, entity.upper())
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        try:
            if entity == 'vagas':
                stats = self._sync_vagas_full()
            elif entity == 'posicoes':
                stats = self._sync_posicoes_full()
            elif entity == 'candidaturas':
                stats, _ = self._sync_candidaturas_full()
            elif entity == 'talentos':
                stats = self._sync_talentos_full()
            elif entity == 'requisicoes':
                stats = self._sync_requisicoes()
            elif entity == 'scorecard_interviews':
                stats = self._sync_scorecard_interviews()
            elif entity == 'scorecard_jobs':
                stats = self._sync_scorecard_jobs()
            elif entity == 'form_responses':
                stats = self._sync_form_responses()
            elif entity == 'vaga_tags':
                stats = self._sync_vaga_tags()
            elif entity == 'automations':
                stats = self._sync_automations()
            elif entity == 'clientes':
                stats = self._sync_clientes()
            elif entity == 'custom_fields':
                stats = self._sync_custom_fields()

            self.db.complete_sync_log(main_log, SyncStatus.SUCCESS, stats)
            return {'success': True, 'status': SyncStatus.SUCCESS, 'stats': stats}

        except Exception as e:
            self.db.complete_sync_log(main_log, SyncStatus.ERROR, stats, errors=str(e))
            return {'success': False, 'status': SyncStatus.ERROR, 'error': str(e)}

    # ========================================
    # MÉTODO GENÉRICO DE SINCRONIZAÇÃO
    # DRY: Elimina duplicação de código
    # ========================================

    def _sync_entity_generic(
        self,
        entity_name: str,
        api_fetcher,
        db_upsert_func,
        batch_size: int = 50,
        additional_args: tuple = ()
    ) -> Dict:
        """
        Método genérico para sincronizar qualquer entidade com bulk commits.

        Args:
            entity_name: Nome da entidade para logging
            api_fetcher: Generator ou iterable que retorna registros da API
            db_upsert_func: Função de upsert (recebe registro + commit=False + additional_args)
            batch_size: Tamanho do batch para commits
            additional_args: Args adicionais para db_upsert_func (ex: job_id para candidaturas)

        Returns:
            Dict com estatísticas (processed, created, updated, skipped, failed)

        Example:
            stats = self._sync_entity_generic(
                entity_name="vagas",
                api_fetcher=self.api_client.get_all_vagas(),
                db_upsert_func=self.db.upsert_vaga,
                batch_size=50
            )
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        for record in api_fetcher:
            try:
                # Chamar upsert com commit=False
                is_new, operation = db_upsert_func(record, *additional_args, commit=False)
                stats['processed'] += 1
                stats[operation] += 1

                # Batch commit a cada N registros
                if stats['processed'] % batch_size == 0:
                    self.db.batch_commit()
                    self.logger.info(f"{entity_name} processados: {stats['processed']} (batch commit)")

            except Exception as e:
                stats['failed'] += 1
                record_id = getattr(record, 'id', 'unknown')
                self.logger.error(f"Erro ao processar {entity_name} {record_id}: {str(e)}")

        # Commit final para registros remanescentes
        if stats['processed'] % batch_size != 0:
            self.db.batch_commit()

        self.logger.info(f"✓ {entity_name} sincronizados: {stats}")
        return stats

    # ========================================
    # MÉTODOS DE SINCRONIZAÇÃO COMPLETA (FULL)
    # Importam TODOS os dados sem filtros de data
    # ========================================

    def _sync_vagas_full(self) -> Dict:
        """Sincroniza todas as vagas (refatorado para usar método genérico)"""
        return self._sync_entity_generic(
            entity_name="vagas",
            api_fetcher=self.api_client.get_all_vagas(),
            db_upsert_func=self.db.upsert_vaga
        )

    def _sync_posicoes_full(self) -> Dict:
        """
        Sincroniza todas as posições de todas as vagas com bulk commits
        OTIMIZADO: Usa ThreadPoolExecutor para paralelizar chamadas de API
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from models.database import Vaga

        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        BATCH_SIZE = 50
        MAX_WORKERS = 5  # Paralelização moderada para não sobrecarregar API

        # Buscar todas as vagas do banco
        vagas = self.session.query(Vaga).all()
        self.logger.info(f"Sincronizando posições de {len(vagas)} vagas em paralelo (workers={MAX_WORKERS})")

        def fetch_and_process_posicoes(vaga):
            """Helper para processar posições de uma vaga"""
            local_stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
            try:
                for posicao in self.api_client.get_all_posicoes(vaga.inhire_id):
                    try:
                        is_new, operation = self.db.upsert_posicao(posicao, commit=False)
                        local_stats['processed'] += 1
                        local_stats[operation] += 1
                    except Exception as e:
                        local_stats['failed'] += 1
                        self.logger.error(f"Erro ao processar posição {posicao.id}: {str(e)}")
            except Exception as e:
                self.logger.error(f"Erro ao buscar posições da vaga {vaga.inhire_id}: {str(e)}")
            return local_stats

        # Processar vagas em paralelo
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(fetch_and_process_posicoes, vaga): vaga for vaga in vagas}

            for future in as_completed(futures):
                vaga = futures[future]
                try:
                    local_stats = future.result()
                    # Acumular estatísticas
                    for key in stats:
                        stats[key] += local_stats[key]

                    # Batch commit periodicamente
                    if stats['processed'] % BATCH_SIZE == 0:
                        self.db.batch_commit()
                        self.logger.info(f"Posições processadas: {stats['processed']} (batch commit)")

                except Exception as e:
                    stats['failed'] += 1
                    self.logger.error(f"Erro ao processar vaga {vaga.inhire_id}: {str(e)}")

        # Commit final
        if stats['processed'] % BATCH_SIZE != 0:
            self.db.batch_commit()

        self.logger.info(f"✓ Posições sincronizadas: {stats}")
        return stats

    def _sync_candidaturas_full(self) -> tuple[Dict, set]:
        """Sincroniza candidaturas e coleta IDs dos talentos com bulk commits"""
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        timeline_stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        talent_ids = set()
        BATCH_SIZE = 50

        from models.database import Vaga, Candidatura
        vagas = self.session.query(Vaga).all()

        for vaga in vagas:
            try:
                for cand in self.api_client.get_all_candidaturas(vaga.inhire_id):
                    try:
                        is_new, operation = self.db.upsert_candidatura(cand, vaga.inhire_id, commit=False)
                        stats['processed'] += 1
                        stats[operation] += 1

                        # Coletar ID do talento para sincronização posterior
                        if cand.talentId:
                            talent_ids.add(cand.talentId)

                        # Batch commit a cada 50 registros
                        if stats['processed'] % BATCH_SIZE == 0:
                            self.db.batch_commit()
                            self.logger.info(f"Candidaturas processadas: {stats['processed']} (batch commit)")

                            # NOVO: Sincronizar timeline da candidatura
                            # Buscar a candidatura no banco para pegar o ID interno
                            candidatura_db = self.session.query(Candidatura).filter_by(
                                inhire_id=cand.id
                            ).first()

                            if candidatura_db:
                                tl_stats = self._sync_candidatura_timeline(cand.id, candidatura_db.id)
                                self._merge_stats(timeline_stats, tl_stats)

                    except Exception as e:
                        stats['failed'] += 1
                        self.logger.error(f"Erro ao processar candidatura {cand.id}: {str(e)}")

            except Exception as e:
                self.logger.error(f"Erro ao buscar candidaturas da vaga {vaga.inhire_id}: {str(e)}")

        # Commit final
        if stats['processed'] % BATCH_SIZE != 0:
            self.db.batch_commit()

        self.logger.info(f"✓ Candidaturas sincronizadas: {stats}")
        self.logger.info(f"✓ Timeline sincronizado: {timeline_stats}")
        self.logger.info(f"✓ {len(talent_ids)} talentos únicos coletados")
        return stats, talent_ids

    def _sync_talentos_full(self, talent_ids: set = None) -> Dict:
        """Sincroniza talentos (refatorado para usar método genérico)"""
        if talent_ids:
            # Generator que busca talentos por IDs específicos
            self.logger.info(f"Sincronizando {len(talent_ids)} talentos específicos...")
            def talent_fetcher():
                for talent_id in talent_ids:
                    talento = self.api_client.get_talento_by_id(talent_id)
                    if talento:
                        yield talento

            return self._sync_entity_generic(
                entity_name="talentos",
                api_fetcher=talent_fetcher(),
                db_upsert_func=self.db.upsert_talento
            )
        else:
            # Sincronizar todos os talentos
            self.logger.info("Sincronizando todos os talentos...")
            return self._sync_entity_generic(
                entity_name="talentos",
                api_fetcher=self.api_client.get_all_talentos(),
                db_upsert_func=self.db.upsert_talento
            )

    def _sync_talentos_incremental(self, filter_dict: Dict) -> Dict:
        """Sincroniza apenas talentos modificados (refatorado)"""
        return self._sync_entity_generic(
            entity_name="talentos",
            api_fetcher=self.api_client.get_all_talentos(filter_dict=filter_dict),
            db_upsert_func=self.db.upsert_talento
        )

    def _sync_candidatura_timeline(self, candidatura_inhire_id: str, candidatura_db_id: int) -> Dict:
        """
        Sincroniza o timeline/histórico de uma candidatura específica

        Args:
            candidatura_inhire_id: ID da candidatura no formato InHire (jobId*talentId)
            candidatura_db_id: ID interno da candidatura no banco

        Returns:
            Dict com estatísticas da sincronização
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        try:
            # Buscar timeline da API
            timeline_events = self.api_client.get_candidatura_timeline(candidatura_inhire_id)

            if not timeline_events:
                # Timeline vazio ou não acessível
                return stats

            # Processar cada evento do timeline
            for event in timeline_events:
                try:
                    is_new, operation = self.db.upsert_candidatura_timeline(
                        event,
                        candidatura_inhire_id,
                        candidatura_db_id
                    )
                    stats['processed'] += 1
                    stats[operation] += 1

                except Exception as e:
                    stats['failed'] += 1
                    self.logger.error(
                        f"Erro ao processar evento de timeline da candidatura {candidatura_inhire_id}: {str(e)}"
                    )

        except Exception as e:
            stats['failed'] += 1
            self.logger.error(
                f"Erro ao buscar timeline da candidatura {candidatura_inhire_id}: {str(e)}"
            )

        return stats

    def _sync_requisicoes(self) -> Dict:
        """
        Sincroniza todas as requisições com dados completos

        Estratégia:
        1. Busca lista de requisições via endpoint paginado (rápido)
        2. Para cada requisição, busca dados completos via endpoint direto
        3. Dados completos incluem: name, description, positions, approvalWorkflow
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0, 'enriched': 0}

        for req_basico in self.api_client.get_all_requisicoes_paginated():
            try:
                # ETAPA 1: Buscar dados COMPLETOS da requisição
                req_completo = self.api_client.get_requisicao_completa(req_basico.id)

                if req_completo:
                    req = req_completo  # Usar dados completos
                    stats['enriched'] += 1
                else:
                    req = req_basico  # Fallback para dados básicos se endpoint falhar
                    self.logger.warning(f"Usando dados básicos para requisição {req_basico.id}")

                # ETAPA 2: Buscar vaga_db_id se jobId existir
                vaga_db_id = None
                if req.jobId:
                    from models.database import Vaga
                    vaga = self.session.query(Vaga).filter_by(inhire_id=req.jobId).first()
                    if vaga:
                        vaga_db_id = vaga.id
                    else:
                        self.logger.warning(f"Vaga {req.jobId} não encontrada para requisição {req.id}")

                # ETAPA 3: Salvar requisição com dados completos
                is_new, operation = self.db.upsert_requisicao(req, vaga_db_id)
                stats['processed'] += 1
                stats[operation] += 1

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Erro ao processar requisição {req_basico.id}: {str(e)}")

        self.logger.info(f"✓ Requisições sincronizadas: {stats} (enriquecidas: {stats['enriched']})")
        return stats

    def _sync_scorecard_interviews(self) -> Dict:
        """Sincroniza todos os templates de entrevista"""
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        for interview in self.api_client.get_all_scorecard_interviews():
            try:
                is_new, operation = self.db.upsert_scorecard_interview(interview)
                stats['processed'] += 1
                stats[operation] += 1

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Erro ao processar scorecard interview {interview.id}: {str(e)}")

        self.logger.info(f"✓ Scorecard interviews sincronizados: {stats}")
        return stats

    def _sync_scorecard_jobs(self) -> Dict:
        """Sincroniza todos os scorecards de vagas"""
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        for scorecard in self.api_client.get_all_scorecard_jobs():
            try:
                # Buscar vaga_db_id se jobId existir
                vaga_db_id = None
                if scorecard.jobId:
                    from models.database import Vaga
                    vaga = self.session.query(Vaga).filter_by(inhire_id=scorecard.jobId).first()
                    if vaga:
                        vaga_db_id = vaga.id

                is_new, operation = self.db.upsert_scorecard_job(scorecard, vaga_db_id)
                stats['processed'] += 1
                stats[operation] += 1

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Erro ao processar scorecard job {scorecard.id}: {str(e)}")

        self.logger.info(f"✓ Scorecard jobs sincronizados: {stats}")
        return stats

    def _sync_form_responses(self) -> Dict:
        """Sincroniza respostas de formulários de todos os candidatos"""
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        from models.database import Candidatura
        candidaturas = self.session.query(Candidatura).all()

        for cand in candidaturas:
            try:
                form = self.api_client.get_form_responses_by_candidato(cand.inhire_id)
                if form:
                    is_new, operation = self.db.upsert_form_response(form, cand.id)
                    stats['processed'] += 1
                    stats[operation] += 1

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Erro ao processar form response do candidato {cand.inhire_id}: {str(e)}")

        self.logger.info(f"✓ Form responses sincronizados: {stats}")
        return stats

    def _sync_vaga_tags(self) -> Dict:
        """Sincroniza tags de todas as vagas"""
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        from models.database import Vaga
        vagas = self.session.query(Vaga).all()

        for vaga in vagas:
            try:
                tags = self.api_client.get_vaga_tags(vaga.inhire_id)
                for tag in tags:
                    try:
                        is_new, operation = self.db.upsert_vaga_tag(tag, vaga.id)
                        stats['processed'] += 1
                        stats[operation] += 1
                    except Exception as e:
                        stats['failed'] += 1
                        self.logger.error(f"Erro ao processar tag {tag.id} da vaga {vaga.inhire_id}: {str(e)}")

            except Exception as e:
                self.logger.error(f"Erro ao buscar tags da vaga {vaga.inhire_id}: {str(e)}")

        self.logger.info(f"✓ Tags de vagas sincronizadas: {stats}")
        return stats

    def _sync_automations(self) -> Dict:
        """Sincroniza todas as automações/workflows"""
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        for auto in self.api_client.get_all_automations():
            try:
                is_new, operation = self.db.upsert_automation(auto)
                stats['processed'] += 1
                stats[operation] += 1

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Erro ao processar automation {auto.id}: {str(e)}")

        self.logger.info(f"✓ Automações sincronizadas: {stats}")
        return stats

    def _sync_clientes(self) -> Dict:
        """Sincroniza todos os clientes"""
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        for cliente in self.api_client.get_all_clientes():
            try:
                is_new, operation = self.db.upsert_cliente(cliente)
                stats['processed'] += 1
                stats[operation] += 1

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Erro ao processar cliente {cliente.id}: {str(e)}")

        self.logger.info(f"✓ Clientes sincronizados: {stats}")
        return stats

    def _sync_custom_fields(self) -> Dict:
        """
        Sincroniza custom fields de todas as entidades

        ATUALIZAÇÃO 2026-02-10: API mudou comportamento
        - ❌ Chamadas individuais (job, talent, etc) retornam HTTP 400
        - ✅ Apenas 'ALL' funciona agora
        - Reduz de 4 chamadas para 1 chamada (75% mais eficiente)
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

        try:
            # Buscar TODOS os custom fields de uma vez (API só suporta 'ALL' agora)
            fields = self.api_client.get_custom_fields('ALL')
            self.logger.info(f"Buscados {len(fields)} custom fields da API")

            for field in fields:
                try:
                    is_new, operation = self.db.upsert_custom_field(field)
                    stats['processed'] += 1
                    stats[operation] += 1
                except Exception as e:
                    stats['failed'] += 1
                    field_name = getattr(field, 'name', getattr(field, 'fieldName', 'unknown'))
                    self.logger.error(f"Erro ao processar custom field {field_name}: {str(e)}")

        except Exception as e:
            self.logger.error(f"Erro ao buscar custom fields: {str(e)}")

        self.logger.info(f"✓ Custom fields sincronizados: {stats}")
        return stats

    # ========================================
    # MÉTODOS DE SINCRONIZAÇÃO INCREMENTAL
    # Comparam updated_at do BD com API e atualizam apenas registros modificados
    # REGRA: Sempre comparar datas, NUNCA filtrar por status antes da comparação
    # ========================================

    @staticmethod
    def _normalize_datetime_for_comparison(dt):
        """Normaliza datetime para comparação (adiciona UTC se não tem timezone)"""
        from datetime import timezone
        if dt and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def _sync_vagas_incremental(self) -> Dict:
        """
        SINCRONIZAÇÃO INCREMENTAL DE VAGAS

        Estratégia:
        1. Busca TODAS as vagas da API (sem filtro de status)
        2. Para cada vaga, busca no BD
        3. Se não existe no BD: cria
        4. Se existe no BD com status final (CLOSED, CANCELED): pula (otimização - não sofrem mais alterações)
        5. Se existe no BD: compara updated_at_inhire (BD) com updatedAt (API)
           - Se API é mais recente: atualiza (incluindo mudanças de status)
           - Se BD é mais recente ou igual: pula

        IMPORTANTE: Processamos até a vaga chegar no status final para capturar a mudança.
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import Vaga

        for vaga_api in self.api_client.get_all_vagas():
            try:
                # Buscar vaga existente no BD
                vaga_bd = self.session.query(Vaga).filter_by(inhire_id=vaga_api.id).first()

                # Se não existe, criar
                if not vaga_bd:
                    is_new, operation = self.db.upsert_vaga(vaga_api)
                    stats['processed'] += 1
                    stats[operation] += 1
                else:
                    # Comparar datas - atualizar apenas se API é mais recente
                    if vaga_api.updatedAt and vaga_bd.updated_at_inhire:
                        api_date = self._normalize_datetime_for_comparison(vaga_api.updatedAt)
                        bd_date = self._normalize_datetime_for_comparison(vaga_bd.updated_at_inhire)

                        if api_date <= bd_date:
                            stats['skipped'] += 1
                            continue

                    # Atualizar (incluindo mudanças de status)
                    is_new, operation = self.db.upsert_vaga(vaga_api)
                    stats['processed'] += 1
                    stats[operation] += 1

                if stats['processed'] % 50 == 0:
                    self.logger.info(f"Vagas processadas: {stats['processed']}")

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Erro ao processar vaga {vaga_api.id}: {str(e)}")

        self.logger.info(f"✓ Vagas sincronizadas (incremental): {stats}")
        return stats

    def _sync_posicoes_incremental(self) -> Dict:
        """
        SINCRONIZAÇÃO INCREMENTAL DE POSIÇÕES

        Estratégia:
        1. Busca TODAS as vagas do BD (sem filtro de status)
        2. Para cada vaga, busca suas posições na API
        3. Para cada posição:
           - Se não existe no BD: cria
           - Se existe no BD com status final (canceled, closed): pula (otimização - não sofrem mais alterações)
           - Se existe no BD: compara updated_at_inhire (BD) com updatedAt (API)
             * Se API é mais recente: atualiza (incluindo mudanças de status)
             * Se BD é mais recente ou igual: pula

        IMPORTANTE: Processamos até a posição chegar no status final para capturar a mudança.
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import Vaga, Posicao

        # Buscar TODAS as vagas do banco (não apenas OPEN)
        vagas = self.session.query(Vaga).all()

        for vaga in vagas:
            try:
                for posicao_api in self.api_client.get_all_posicoes(vaga.inhire_id):
                    try:
                        # Buscar posição existente no BD
                        posicao_bd = self.session.query(Posicao).filter_by(inhire_id=posicao_api.id).first()

                        # Se não existe, criar
                        if not posicao_bd:
                            is_new, operation = self.db.upsert_posicao(posicao_api)
                            stats['processed'] += 1
                            stats[operation] += 1
                        else:
                            # Comparar datas - atualizar apenas se API é mais recente
                            if posicao_api.updatedAt and posicao_bd.updated_at_inhire:
                                api_date = self._normalize_datetime_for_comparison(posicao_api.updatedAt)
                                bd_date = self._normalize_datetime_for_comparison(posicao_bd.updated_at_inhire)

                                if api_date <= bd_date:
                                    stats['skipped'] += 1
                                    continue

                            # Atualizar (incluindo mudanças de status)
                            is_new, operation = self.db.upsert_posicao(posicao_api)
                            stats['processed'] += 1
                            stats[operation] += 1

                    except Exception as e:
                        stats['failed'] += 1
                        self.logger.error(f"Erro ao processar posição {posicao_api.id}: {str(e)}")

            except Exception as e:
                self.logger.error(f"Erro ao buscar posições da vaga {vaga.inhire_id}: {str(e)}")

        self.logger.info(f"✓ Posições sincronizadas (incremental): {stats}")
        return stats

    def _sync_position_timeline_full(self) -> Dict:
        """
        Sincroniza histórico completo de todas as posições de todas as vagas

        Estratégia:
        1. Busca todas as vagas do banco
        2. Para cada vaga, busca o histórico de TODAS suas posições via API
        3. Insere/atualiza eventos no banco

        IMPORTANTE: Este método pode ser lento pois faz 1 chamada API por vaga
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from models.database import Vaga

        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        BATCH_SIZE = 50
        MAX_WORKERS = 3  # Reduzido para não sobrecarregar API com timeline

        # Buscar todas as vagas do banco
        vagas = self.session.query(Vaga).all()
        self.logger.info(f"Sincronizando position timeline de {len(vagas)} vagas em paralelo (workers={MAX_WORKERS})")

        def fetch_and_process_timeline(vaga):
            """Helper para processar timeline de uma vaga"""
            local_stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
            try:
                for event in self.api_client.get_position_timeline_by_job(vaga.inhire_id):
                    try:
                        is_new, operation = self.db.upsert_position_timeline(
                            event,
                            vaga_db_id=vaga.id,
                            commit=False
                        )
                        local_stats['processed'] += 1
                        local_stats[operation] += 1
                    except Exception as e:
                        local_stats['failed'] += 1
                        self.logger.error(f"Erro ao processar evento timeline da posição {event.positionId}: {str(e)}")
            except Exception as e:
                self.logger.error(f"Erro ao buscar timeline da vaga {vaga.inhire_id}: {str(e)}")
            return local_stats

        # Processar vagas em paralelo
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(fetch_and_process_timeline, vaga): vaga for vaga in vagas}

            for future in as_completed(futures):
                vaga = futures[future]
                try:
                    local_stats = future.result()
                    # Acumular estatísticas
                    for key in stats:
                        stats[key] += local_stats[key]

                    # Batch commit periodicamente
                    if stats['processed'] % BATCH_SIZE == 0:
                        self.db.batch_commit()
                        self.logger.info(f"Position timeline processados: {stats['processed']} eventos (batch commit)")

                except Exception as e:
                    stats['failed'] += 1
                    self.logger.error(f"Erro ao processar timeline da vaga {vaga.inhire_id}: {str(e)}")

        # Commit final
        if stats['processed'] % BATCH_SIZE != 0:
            self.db.batch_commit()

        self.logger.info(f"✓ Position timeline sincronizados: {stats}")
        return stats

    def _sync_position_timeline_incremental(self) -> Dict:
        """
        SINCRONIZAÇÃO INCREMENTAL DE POSITION TIMELINE

        Estratégia:
        1. Busca TODAS as vagas do BD
        2. Para cada vaga, busca o histórico de suas posições na API
        3. Para cada evento:
           - Se a posição já está em status final (canceled, closed): pula (otimização - timeline não muda mais)
           - Verifica se já existe no BD (posicao_id + changed_at + new_status)
           - Se não existe: cria
           - Se existe: atualiza apenas se houver diferenças

        OTIMIZAÇÃO: Timeline não tem campo updatedAt, então comparamos pela existência
        do evento (unique constraint na migration). Além disso, pulamos eventos de posições em status final.
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import Vaga, PositionTimeline, Posicao

        # Buscar TODAS as vagas do banco
        vagas = self.session.query(Vaga).all()
        self.logger.info(f"Sincronizando position timeline (incremental) de {len(vagas)} vagas")

        for vaga in vagas:
            try:
                for event in self.api_client.get_position_timeline_by_job(vaga.inhire_id):
                    try:
                        # Buscar posição para obter o ID do banco
                        posicao_bd = self.session.query(Posicao).filter_by(inhire_id=event.positionId).first()

                        if not posicao_bd:
                            stats['skipped'] += 1
                            self.logger.debug(f"Posição {event.positionId} não encontrada no banco, pulando evento")
                            continue

                        # Verificar se evento já existe
                        existing_event = self.session.query(PositionTimeline).filter_by(
                            posicao_id=posicao_bd.id,
                            changed_at=self._normalize_datetime_for_comparison(event.changedAt),
                            new_status=event.newStatus
                        ).first()

                        if existing_event:
                            # Evento já existe - pular
                            stats['skipped'] += 1
                        else:
                            # Criar novo evento
                            is_new, operation = self.db.upsert_position_timeline(
                                event,
                                posicao_db_id=posicao_bd.id,
                                vaga_db_id=vaga.id,
                                commit=False
                            )
                            stats['processed'] += 1
                            stats[operation] += 1

                    except Exception as e:
                        stats['failed'] += 1
                        self.logger.error(f"Erro ao processar evento timeline: {str(e)}")

                # Batch commit por vaga
                if stats['processed'] % 50 == 0:
                    self.db.batch_commit()

            except Exception as e:
                self.logger.error(f"Erro ao buscar timeline da vaga {vaga.inhire_id}: {str(e)}")

        # Commit final
        self.db.batch_commit()

        self.logger.info(f"✓ Position timeline sincronizados (incremental): {stats}")
        return stats

    def _sync_candidaturas_incremental(self) -> Dict:
        """
        SINCRONIZAÇÃO INCREMENTAL DE CANDIDATURAS

        Estratégia:
        1. Busca TODAS as vagas do BD (sem filtro de status)
        2. Para cada vaga, busca suas candidaturas na API
        3. Para cada candidatura:
           - Se não existe no BD: cria
           - Se existe no BD com status final (REJECTED, DECLINED): pula (otimização - não sofrem mais alterações)
           - Se existe no BD: compara updated_at_inhire (BD) com updatedAt (API)
             * Se API é mais recente: atualiza (incluindo mudanças de status)
             * Se BD é mais recente ou igual: pula

        IMPORTANTE: Processamos até a candidatura chegar no status final para capturar a mudança.
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import Vaga, Candidatura

        # Buscar TODAS as vagas do banco (não apenas OPEN)
        vagas = self.session.query(Vaga).all()

        for vaga in vagas:
            try:
                for cand_api in self.api_client.get_all_candidaturas(vaga.inhire_id):
                    try:
                        # Buscar candidatura existente no BD
                        cand_bd = self.session.query(Candidatura).filter_by(inhire_id=cand_api.id).first()

                        # Se não existe, criar
                        if not cand_bd:
                            is_new, operation = self.db.upsert_candidatura(cand_api, vaga.inhire_id)
                            stats['processed'] += 1
                            stats[operation] += 1
                        else:
                            # Comparar datas - atualizar apenas se API é mais recente
                            if cand_api.updatedAt and cand_bd.updated_at_inhire:
                                api_date = self._normalize_datetime_for_comparison(cand_api.updatedAt)
                                bd_date = self._normalize_datetime_for_comparison(cand_bd.updated_at_inhire)

                                if api_date <= bd_date:
                                    stats['skipped'] += 1
                                    continue

                            # Atualizar (incluindo mudanças de status)
                            is_new, operation = self.db.upsert_candidatura(cand_api, vaga.inhire_id)
                            stats['processed'] += 1
                            stats[operation] += 1

                    except Exception as e:
                        stats['failed'] += 1
                        self.logger.error(f"Erro ao processar candidatura {cand_api.id}: {str(e)}")

            except Exception as e:
                self.logger.error(f"Erro ao buscar candidaturas da vaga {vaga.inhire_id}: {str(e)}")

        self.logger.info(f"✓ Candidaturas sincronizadas (incremental): {stats}")
        return stats

    def _sync_candidatura_timeline_incremental(self) -> Dict:
        """
        Sincroniza timeline de candidaturas ACTIVE com otimizações:
        1. Filtro por última sincronização (compara data do BD com API)
        2. Paralelização com ThreadPoolExecutor
        3. Sessões independentes por thread

        Compara updated_at de cada evento: BD < API = atualiza
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        stats_lock = threading.Lock()

        from models.database import Candidatura, CandidaturaTimeline
        from sqlalchemy import func

        # OTIMIZAÇÃO 1: Filtro inteligente - apenas candidaturas modificadas desde última sync
        # Buscar a data da última sincronização de timeline no banco
        last_sync_date = self.session.query(func.max(CandidaturaTimeline.updated_at)).scalar()

        if last_sync_date:
            # Se já existe timeline no banco, buscar apenas candidaturas atualizadas depois
            self.logger.info(f"Última sincronização de timeline: {last_sync_date}")
            candidaturas = self.session.query(Candidatura).filter(
                Candidatura.status == 'active',
                Candidatura.updated_at_inhire > last_sync_date
            ).all()
            self.logger.info(f"Sincronizando timeline de {len(candidaturas)} candidaturas ACTIVE atualizadas após {last_sync_date}")
        else:
            # Primeira sincronização - usar fallback de 30 dias
            days_lookback = int(getattr(settings, 'TIMELINE_DAYS_LOOKBACK', 30))
            cutoff_date = datetime.now() - timedelta(days=days_lookback)
            candidaturas = self.session.query(Candidatura).filter(
                Candidatura.status == 'active',
                Candidatura.updated_at_inhire >= cutoff_date
            ).all()
            self.logger.info(f"Primeira sincronização de timeline: processando {len(candidaturas)} candidaturas ACTIVE (últimos {days_lookback} dias)")

        def process_candidatura_timeline(cand):
            """Processa timeline de uma candidatura (para execução paralela)"""
            local_stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

            # Criar nova sessão para esta thread (thread-safe)
            from sqlalchemy.orm import sessionmaker
            from config import settings
            from sqlalchemy import create_engine

            database_url = (
                f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
                f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
                f"?client_encoding=utf8"
            )
            thread_engine = create_engine(database_url, poolclass=None)  # Sem pool para threads
            ThreadSession = sessionmaker(bind=thread_engine)
            thread_session = ThreadSession()
            thread_db = DatabaseService(thread_session)

            try:
                timeline_events = self.api_client.get_candidatura_timeline(cand.inhire_id)

                if not timeline_events:
                    return local_stats

                for event_api in timeline_events:
                    try:
                        # O upsert já verifica se existe e decide criar/atualizar/pular
                        is_new, operation = thread_db.upsert_candidatura_timeline(
                            event_api, cand.inhire_id, cand.id
                        )
                        local_stats['processed'] += 1
                        local_stats[operation] += 1

                    except Exception as e:
                        local_stats['failed'] += 1
                        self.logger.error(f"Erro ao processar timeline event: {str(e)}")

                # Commit dos dados desta thread
                thread_session.commit()

            except Exception as e:
                local_stats['failed'] += 1
                self.logger.error(f"Erro ao buscar timeline da candidatura {cand.inhire_id}: {str(e)}")
                thread_session.rollback()

            finally:
                # Fechar sessão e engine da thread
                thread_session.close()
                thread_engine.dispose()

            return local_stats

        # OTIMIZAÇÃO 2: Paralelização com ThreadPoolExecutor
        # Processar até 10 candidaturas simultaneamente (configurável)
        max_workers = int(getattr(settings, 'TIMELINE_MAX_WORKERS', 10))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submeter todas as tarefas
            futures = {executor.submit(process_candidatura_timeline, cand): cand for cand in candidaturas}

            # Processar resultados conforme completam
            completed = 0
            for future in as_completed(futures):
                completed += 1
                try:
                    local_stats = future.result()

                    # Merge stats de forma thread-safe
                    with stats_lock:
                        for key in local_stats:
                            stats[key] += local_stats[key]

                    # Log de progresso a cada 100 candidaturas
                    if completed % 100 == 0:
                        self.logger.info(f"Timeline: {completed}/{len(candidaturas)} candidaturas processadas")

                except Exception as e:
                    self.logger.error(f"Erro ao processar future: {str(e)}")
                    stats['failed'] += 1

        self.logger.info(f"✓ Timeline sincronizado (incremental): {stats}")
        return stats

    def _sync_talentos_incremental_optimized(self) -> Dict:
        """
        SINCRONIZAÇÃO INCREMENTAL DE TALENTOS

        Estratégia:
        1. Busca TODOS os talentos da API
        2. Para cada talento:
           - Se não existe no BD: cria
           - Se existe no BD: compara updated_at_inhire (BD) com updatedAt (API)
             * Se API é mais recente: atualiza
             * Se BD é mais recente ou igual: pula
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import Talento

        for talento_api in self.api_client.get_all_talentos():
            try:
                # Buscar talento existente no BD
                talento_bd = self.session.query(Talento).filter_by(inhire_id=talento_api.id).first()

                # Se não existe, criar
                if not talento_bd:
                    is_new, operation = self.db.upsert_talento(talento_api)
                    stats['processed'] += 1
                    stats[operation] += 1
                else:
                    # Filtro: Comparar datas - atualizar apenas se API é mais recente
                    if talento_api.updatedAt and talento_bd.updated_at_inhire:
                        api_date = self._normalize_datetime_for_comparison(talento_api.updatedAt)
                        bd_date = self._normalize_datetime_for_comparison(talento_bd.updated_at_inhire)

                        if api_date <= bd_date:
                            stats['skipped'] += 1
                            continue

                    # Atualizar
                    is_new, operation = self.db.upsert_talento(talento_api)
                    stats['processed'] += 1
                    stats[operation] += 1

                if stats['processed'] % 50 == 0:
                    self.logger.info(f"Talentos processados: {stats['processed']}")

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Erro ao processar talento {talento_api.id}: {str(e)}")

        self.logger.info(f"✓ Talentos sincronizados (incremental): {stats}")
        return stats

    def _sync_missing_talentos(self) -> Dict:
        """
        SINCRONIZAÇÃO DE TALENTOS FALTANTES

        Busca talent_inhire_id que existem em candidaturas mas não na tabela talentos,
        e os sincroniza da API.

        Útil para:
        - Talentos criados recentemente que ainda não foram sincronizados
        - Talentos antigos que podem ter sido pulados em syncs anteriores
        - Garantir que todos os talentos em candidaturas existam na tabela
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import Talento, Candidatura
        from sqlalchemy import func

        try:
            # 1. Buscar talent_inhire_id que existem em candidaturas mas não em talentos
            self.logger.info("   Identificando talentos faltantes...")

            subquery = self.session.query(Talento.inhire_id).subquery()

            missing_talent_ids = self.session.query(
                func.distinct(Candidatura.talent_inhire_id)
            ).filter(
                Candidatura.talent_inhire_id.isnot(None),
                ~Candidatura.talent_inhire_id.in_(subquery)
            ).all()

            missing_ids = [row[0] for row in missing_talent_ids]

            if not missing_ids:
                self.logger.info("   Nenhum talento faltante encontrado")
                return stats

            self.logger.info(f"   Encontrados {len(missing_ids)} talentos faltantes")

            # 2. Buscar cada talento faltante da API
            for i, talent_id in enumerate(missing_ids, 1):
                try:
                    # Buscar talento individual da API
                    talento_api = self.api_client.get_talento_by_id(talent_id)

                    if talento_api:
                        # Inserir na tabela
                        is_new, operation = self.db.upsert_talento(talento_api)
                        stats['processed'] += 1
                        stats[operation] += 1
                    else:
                        # Talento não encontrado na API (pode ter sido deletado)
                        stats['skipped'] += 1

                    # Log de progresso a cada 50 talentos
                    if i % 50 == 0:
                        self.logger.info(f"   Talentos faltantes sincronizados: {i}/{len(missing_ids)}")

                except Exception as e:
                    stats['failed'] += 1
                    self.logger.warning(f"   Erro ao sincronizar talento faltante {talent_id}: {str(e)}")

            self.logger.info(f"   Talentos faltantes sincronizados: {stats}")
            return stats

        except Exception as e:
            self.logger.error(f"Erro ao sincronizar talentos faltantes: {str(e)}")
            return stats

    def _sync_talento_arquivos_incremental(self) -> Dict:
        """
        Sincroniza arquivos de talentos comparando datas BD vs API
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import Talento, TalentoArquivo

        # Buscar talentos que têm arquivos no BD
        talentos = self.session.query(Talento).all()

        for talento in talentos:
            try:
                # Buscar arquivos do talento na API
                talento_completo = self.api_client.get_talento_by_id(talento.inhire_id)

                if not talento_completo or not hasattr(talento_completo, 'files'):
                    continue

                for arquivo_api in talento_completo.files or []:
                    try:
                        arquivo_id = arquivo_api.get('id')
                        if not arquivo_id:
                            continue

                        # Buscar arquivo existente no BD
                        arquivo_bd = self.session.query(TalentoArquivo).filter_by(
                            inhire_id=arquivo_id
                        ).first()

                        # Se não existe, criar
                        if not arquivo_bd:
                            is_new, operation = self.db.upsert_talento_arquivo(arquivo_api, talento.id)
                            stats['processed'] += 1
                            stats[operation] += 1
                        else:
                            # Filtro: Comparar datas - atualizar apenas se API é mais recente
                            arquivo_updated_at = arquivo_api.get('updatedAt')
                            if arquivo_updated_at and arquivo_bd.updated_at_inhire:
                                api_date = self._normalize_datetime_for_comparison(arquivo_updated_at)
                                bd_date = self._normalize_datetime_for_comparison(arquivo_bd.updated_at_inhire)

                                if api_date <= bd_date:
                                    stats['skipped'] += 1
                                    continue

                            # Atualizar
                            is_new, operation = self.db.upsert_talento_arquivo(arquivo_api, talento.id)
                            stats['processed'] += 1
                            stats[operation] += 1

                    except Exception as e:
                        stats['failed'] += 1
                        self.logger.error(f"Erro ao processar arquivo: {str(e)}")

            except Exception as e:
                self.logger.error(f"Erro ao buscar arquivos do talento {talento.inhire_id}: {str(e)}")

        self.logger.info(f"✓ Arquivos de talentos sincronizados (incremental): {stats}")
        return stats

    def _sync_scorecard_interviews_incremental(self) -> Dict:
        """
        SINCRONIZAÇÃO INCREMENTAL DE SCORECARD INTERVIEWS

        Estratégia:
        1. Busca TODOS os scorecard interviews da API
        2. Para cada interview:
           - Se não existe no BD: cria
           - Se existe no BD: compara updated_at_inhire (BD) com updatedAt (API)
             * Se API é mais recente: atualiza
             * Se BD é mais recente ou igual: pula
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import ScorecardInterview

        for interview_api in self.api_client.get_all_scorecard_interviews():
            try:
                # Buscar interview existente no BD
                interview_bd = self.session.query(ScorecardInterview).filter_by(
                    inhire_id=interview_api.id
                ).first()

                # Se não existe, criar
                if not interview_bd:
                    is_new, operation = self.db.upsert_scorecard_interview(interview_api)
                    stats['processed'] += 1
                    stats[operation] += 1
                else:
                    # Filtro: Comparar datas - atualizar apenas se API é mais recente
                    if interview_api.updatedAt and interview_bd.updated_at_inhire:
                        api_date = self._normalize_datetime_for_comparison(interview_api.updatedAt)
                        bd_date = self._normalize_datetime_for_comparison(interview_bd.updated_at_inhire)

                        if api_date <= bd_date:
                            stats['skipped'] += 1
                            continue

                    # Atualizar
                    is_new, operation = self.db.upsert_scorecard_interview(interview_api)
                    stats['processed'] += 1
                    stats[operation] += 1

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Erro ao processar scorecard interview {interview_api.id}: {str(e)}")

        self.logger.info(f"✓ Scorecard interviews sincronizados (incremental): {stats}")
        return stats

    def _sync_scorecard_jobs_incremental(self) -> Dict:
        """
        SINCRONIZAÇÃO INCREMENTAL DE SCORECARD JOBS

        Estratégia:
        1. Busca TODOS os scorecard jobs da API
        2. Para cada scorecard:
           - Se não existe no BD: cria
           - Se existe no BD: compara updated_at_inhire (BD) com updatedAt (API)
             * Se API é mais recente: atualiza
             * Se BD é mais recente ou igual: pula
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import ScorecardJob, Vaga

        for scorecard_api in self.api_client.get_all_scorecard_jobs():
            try:
                # Buscar scorecard existente no BD
                scorecard_bd = self.session.query(ScorecardJob).filter_by(
                    inhire_id=scorecard_api.id
                ).first()

                # Buscar vaga_db_id se jobId existir
                vaga_db_id = None
                if scorecard_api.jobId:
                    vaga = self.session.query(Vaga).filter_by(inhire_id=scorecard_api.jobId).first()
                    if vaga:
                        vaga_db_id = vaga.id

                # Se não existe, criar
                if not scorecard_bd:
                    is_new, operation = self.db.upsert_scorecard_job(scorecard_api, vaga_db_id)
                    stats['processed'] += 1
                    stats[operation] += 1
                else:
                    # Filtro: Comparar datas - atualizar apenas se API é mais recente
                    if scorecard_api.updatedAt and scorecard_bd.updated_at_inhire:
                        api_date = self._normalize_datetime_for_comparison(scorecard_api.updatedAt)
                        bd_date = self._normalize_datetime_for_comparison(scorecard_bd.updated_at_inhire)

                        if api_date <= bd_date:
                            stats['skipped'] += 1
                            continue

                    # Atualizar
                    is_new, operation = self.db.upsert_scorecard_job(scorecard_api, vaga_db_id)
                    stats['processed'] += 1
                    stats[operation] += 1

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Erro ao processar scorecard job {scorecard_api.id}: {str(e)}")

        self.logger.info(f"✓ Scorecard jobs sincronizados (incremental): {stats}")
        return stats

    def _sync_talento_arquivos_incremental_optimized(self) -> Dict:
        """
        Sincroniza arquivos de talentos com candidaturas ACTIVE
        Compara updated_at de cada arquivo: BD < API = atualiza
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import Talento, TalentoArquivo, Candidatura

        # Buscar IDs de TODOS os talentos com candidaturas ACTIVE (sem filtro de data)
        talentos_ids = self.session.query(Candidatura.talent_inhire_id).filter(
            Candidatura.status == 'active',
            Candidatura.talent_inhire_id.isnot(None)
        ).distinct().all()

        talent_inhire_ids = [tid[0] for tid in talentos_ids if tid[0]]

        if not talent_inhire_ids:
            self.logger.info("Nenhum talento com candidaturas ACTIVE")
            return stats

        # Buscar talentos
        talentos = self.session.query(Talento).filter(
            Talento.inhire_id.in_(talent_inhire_ids)
        ).all()

        self.logger.info(f"Sincronizando arquivos de {len(talentos)} talentos (com candidaturas ACTIVE)")

        for talento in talentos:
            try:
                # Buscar arquivos do talento na API
                talento_completo = self.api_client.get_talento_by_id(talento.inhire_id)

                if not talento_completo or not hasattr(talento_completo, 'files'):
                    continue

                for arquivo_api in talento_completo.files or []:
                    try:
                        arquivo_id = arquivo_api.get('id')
                        if not arquivo_id:
                            continue

                        # Buscar arquivo existente no BD
                        arquivo_bd = self.session.query(TalentoArquivo).filter_by(
                            inhire_id=arquivo_id
                        ).first()

                        # Se não existe, criar
                        if not arquivo_bd:
                            is_new, operation = self.db.upsert_talento_arquivo(arquivo_api, talento.id)
                            stats['processed'] += 1
                            stats[operation] += 1
                        else:
                            # Comparar datas
                            arquivo_updated_at = arquivo_api.get('updatedAt')
                            if arquivo_updated_at and arquivo_bd.updated_at_inhire:
                                api_date = self._normalize_datetime_for_comparison(arquivo_updated_at)
                                bd_date = self._normalize_datetime_for_comparison(arquivo_bd.updated_at_inhire)

                                if api_date <= bd_date:
                                    stats['skipped'] += 1
                                    continue

                            # Atualizar
                            is_new, operation = self.db.upsert_talento_arquivo(arquivo_api, talento.id)
                            stats['processed'] += 1
                            stats[operation] += 1

                    except Exception as e:
                        stats['failed'] += 1
                        self.logger.error(f"Erro ao processar arquivo {arquivo_id}: {str(e)}")

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Erro ao sincronizar arquivos do talento {talento.inhire_id}: {str(e)}")

        self.logger.info(f"Talento arquivos sincronizados (otimizado): {stats}")
        return stats

    def _sync_form_responses_incremental(self) -> Dict:
        """
        Sincroniza form responses de candidaturas ACTIVE atualizadas recentemente
        OTIMIZADO: Sincroniza apenas candidaturas dos últimos 7 dias + rate limiting
        """
        import time
        from datetime import timedelta
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import Candidatura, FormResponse

        # Buscar apenas candidaturas ACTIVE atualizadas nos últimos 7 dias
        cutoff_date = datetime.now() - timedelta(days=7)
        candidaturas = self.session.query(Candidatura).filter(
            Candidatura.status == 'active',
            Candidatura.updated_at_inhire >= cutoff_date
        ).all()

        total = len(candidaturas)
        self.logger.info(f"Sincronizando form responses de {total} candidaturas ACTIVE atualizadas nos últimos 7 dias")

        for idx, candidatura in enumerate(candidaturas, 1):
            try:
                # Buscar form response da API
                form_response_api = self.api_client.get_form_responses_by_candidato(candidatura.inhire_id)

                if not form_response_api:
                    stats['skipped'] += 1
                    continue

                # Buscar form response existente no BD
                form_bd = self.session.query(FormResponse).filter_by(
                    candidatura_id=candidatura.id
                ).first()

                # Se não existe, criar
                if not form_bd:
                    is_new, operation = self.db.upsert_form_response(form_response_api, candidatura.id)
                    stats['processed'] += 1
                    stats[operation] += 1
                else:
                    # Comparar datas se existirem
                    if hasattr(form_response_api, 'updatedAt') and form_response_api.updatedAt and form_bd.updated_at_inhire:
                        api_date = self._normalize_datetime_for_comparison(form_response_api.updatedAt)
                        bd_date = self._normalize_datetime_for_comparison(form_bd.updated_at_inhire)

                        if api_date <= bd_date:
                            stats['skipped'] += 1
                            continue

                    # Atualizar
                    is_new, operation = self.db.upsert_form_response(form_response_api, candidatura.id)
                    stats['processed'] += 1
                    stats[operation] += 1

                # Rate limiting: 0.2s entre requisições (300 req/min)
                time.sleep(0.2)

                # Log de progresso a cada 50 candidaturas
                if idx % 50 == 0:
                    self.logger.info(f"Form responses: {idx}/{total} candidaturas processadas")

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Erro ao sincronizar form response da candidatura {candidatura.inhire_id}: {str(e)}")

        self.logger.info(f"✓ Form responses sincronizados (incremental): {stats}")
        return stats

    def _sync_vaga_tags_incremental(self) -> Dict:
        """
        Sincroniza tags de vagas ativas (excluindo CLOSED e CANCELED)
        Tags geralmente não têm updatedAt, então cria se não existir
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import Vaga, VagaTag

        # Buscar vagas ativas (excluindo status finais: CLOSED, CANCELED)
        vagas = self.session.query(Vaga).filter(
            ~Vaga.status.in_(['CLOSED', 'CANCELED'])
        ).all()

        self.logger.info(f"Sincronizando tags de {len(vagas)} vagas ativas (excluindo CLOSED, CANCELED)")

        for vaga in vagas:
            try:
                # Buscar tags da vaga usando método correto
                tags_api = self.api_client.get_vaga_tags(vaga.inhire_id)

                if not tags_api:
                    continue

                for tag_api in tags_api:
                    try:
                        # Tags são VagaTagAPI objects
                        tag_id = tag_api.id if hasattr(tag_api, 'id') else None
                        if not tag_id:
                            continue

                        # Buscar tag existente no BD
                        tag_bd = self.session.query(VagaTag).filter_by(
                            tag_inhire_id=tag_id,
                            vaga_id=vaga.id
                        ).first()

                        # Se não existe, criar
                        if not tag_bd:
                            is_new, operation = self.db.upsert_vaga_tag(tag_api, vaga.id)
                            stats['processed'] += 1
                            stats[operation] += 1
                        else:
                            # Tags geralmente não têm updatedAt, então pular se já existe
                            stats['skipped'] += 1

                    except Exception as e:
                        stats['failed'] += 1
                        self.logger.error(f"Erro ao processar tag {tag_id}: {str(e)}")

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Erro ao sincronizar tags da vaga {vaga.inhire_id}: {str(e)}")

        self.logger.info(f"Vaga tags sincronizados (incremental): {stats}")
        return stats

    def _sync_requisicoes_incremental(self) -> Dict:
        """
        SINCRONIZAÇÃO INCREMENTAL DE REQUISIÇÕES

        Estratégia:
        1. Busca TODAS as requisições da API
        2. Para cada requisição:
           - Se não existe no BD: cria
           - Se existe no BD com status final (approved, canceled, rejected): pula (otimização - não sofrem mais alterações)
           - Se existe no BD: compara updated_at_inhire (BD) com updatedAt (API)
             * Se API é mais recente: atualiza
             * Se BD é mais recente ou igual: pula

        IMPORTANTE: Processamos até a requisição chegar no status final para capturar a mudança.
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import Requisicao, Vaga

        for req_api in self.api_client.get_all_requisicoes_paginated():
            try:
                # Buscar vaga_db_id se jobId existir
                vaga_db_id = None
                if req_api.jobId:
                    vaga = self.session.query(Vaga).filter_by(inhire_id=req_api.jobId).first()
                    if vaga:
                        vaga_db_id = vaga.id

                # Buscar requisição existente no BD
                req_bd = self.session.query(Requisicao).filter_by(inhire_id=req_api.id).first()

                # Se não existe, criar
                if not req_bd:
                    is_new, operation = self.db.upsert_requisicao(req_api, vaga_db_id)
                    stats['processed'] += 1
                    stats[operation] += 1
                else:
                    # Filtro: Comparar datas - atualizar apenas se API é mais recente
                    if req_api.updatedAt and req_bd.updated_at_inhire:
                        api_date = self._normalize_datetime_for_comparison(req_api.updatedAt)
                        bd_date = self._normalize_datetime_for_comparison(req_bd.updated_at_inhire)

                        if api_date <= bd_date:
                            stats['skipped'] += 1
                            continue

                    # Atualizar
                    is_new, operation = self.db.upsert_requisicao(req_api, vaga_db_id)
                    stats['processed'] += 1
                    stats[operation] += 1

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Erro ao processar requisição {req_api.id}: {str(e)}")

        self.logger.info(f"✓ Requisições sincronizadas (incremental): {stats}")
        return stats

    def _sync_automations_incremental(self) -> Dict:
        """
        Sincroniza automations/workflows comparando datas BD vs API
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import Automation

        for auto_api in self.api_client.get_all_automations():
            try:
                # Buscar automation existente no BD
                auto_bd = self.session.query(Automation).filter_by(inhire_id=auto_api.id).first()

                # Se não existe, criar
                if not auto_bd:
                    is_new, operation = self.db.upsert_automation(auto_api)
                    stats['processed'] += 1
                    stats[operation] += 1
                else:
                    # Filtro: Comparar datas - atualizar apenas se API é mais recente
                    if auto_api.updatedAt and auto_bd.updated_at_inhire:
                        api_date = self._normalize_datetime_for_comparison(auto_api.updatedAt)
                        bd_date = self._normalize_datetime_for_comparison(auto_bd.updated_at_inhire)

                        if api_date <= bd_date:
                            stats['skipped'] += 1
                            continue

                    # Atualizar
                    is_new, operation = self.db.upsert_automation(auto_api)
                    stats['processed'] += 1
                    stats[operation] += 1

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Erro ao processar automation {auto_api.id}: {str(e)}")

        self.logger.info(f"✓ Automations sincronizadas (incremental): {stats}")
        return stats

    def _sync_clientes_incremental(self) -> Dict:
        """
        SINCRONIZAÇÃO INCREMENTAL DE CLIENTES

        Estratégia:
        1. Busca TODOS os clientes da API
        2. Para cada cliente:
           - Se não existe no BD: cria
           - Se existe no BD: compara updated_at_inhire (BD) com updatedAt (API)
             * Se API é mais recente: atualiza
             * Se BD é mais recente ou igual: pula
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import Cliente

        for cliente_api in self.api_client.get_all_clientes():
            try:
                # Buscar cliente existente no BD
                cliente_bd = self.session.query(Cliente).filter_by(inhire_id=cliente_api.id).first()

                # Se não existe, criar
                if not cliente_bd:
                    is_new, operation = self.db.upsert_cliente(cliente_api)
                    stats['processed'] += 1
                    stats[operation] += 1
                else:
                    # Filtro: Comparar datas - atualizar apenas se API é mais recente
                    if cliente_api.updatedAt and cliente_bd.updated_at_inhire:
                        api_date = self._normalize_datetime_for_comparison(cliente_api.updatedAt)
                        bd_date = self._normalize_datetime_for_comparison(cliente_bd.updated_at_inhire)

                        if api_date <= bd_date:
                            stats['skipped'] += 1
                            continue

                    # Atualizar
                    is_new, operation = self.db.upsert_cliente(cliente_api)
                    stats['processed'] += 1
                    stats[operation] += 1

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Erro ao processar cliente {cliente_api.id}: {str(e)}")

        self.logger.info(f"✓ Clientes sincronizados (incremental): {stats}")
        return stats

    def _sync_custom_fields_incremental(self) -> Dict:
        """
        SINCRONIZAÇÃO INCREMENTAL DE CUSTOM FIELDS

        Estratégia:
        1. Busca TODOS os custom fields da API (job, talent, jobTalent)
        2. Para cada custom field:
           - Se não existe no BD: cria
           - Se existe no BD: compara updated_at_inhire (BD) com updatedAt (API)
             * Se API é mais recente: atualiza
             * Se BD é mais recente ou igual: pula
        """
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        from models.database import CustomField

        # Buscar custom fields de cada tipo de entidade
        # ATUALIZADO: Adicionado 'requisition' para sincronizar custom fields de requisições
        for entity_type in ['job', 'talent', 'jobTalent', 'requisition']:
            try:
                fields = self.api_client.get_custom_fields(entity_type)
                for field_api in fields:
                    try:
                        # Buscar field existente no BD
                        field_bd = self.session.query(CustomField).filter_by(inhire_id=field_api.id).first()

                        # Se não existe, criar
                        if not field_bd:
                            is_new, operation = self.db.upsert_custom_field(field_api)
                            stats['processed'] += 1
                            stats[operation] += 1
                        else:
                            # Filtro: Comparar datas - atualizar apenas se API é mais recente
                            if field_api.updatedAt and field_bd.updated_at_inhire:
                                api_date = self._normalize_datetime_for_comparison(field_api.updatedAt)
                                bd_date = self._normalize_datetime_for_comparison(field_bd.updated_at_inhire)

                                if api_date <= bd_date:
                                    stats['skipped'] += 1
                                    continue

                            # Atualizar
                            is_new, operation = self.db.upsert_custom_field(field_api)
                            stats['processed'] += 1
                            stats[operation] += 1

                    except Exception as e:
                        stats['failed'] += 1
                        self.logger.error(f"Erro ao processar custom field {field_api.id}: {str(e)}")

            except Exception as e:
                self.logger.error(f"Erro ao buscar custom fields de {entity_type}: {str(e)}")

        self.logger.info(f"✓ Custom fields sincronizados (incremental): {stats}")
        return stats

    @staticmethod
    def _merge_stats(target: Dict, source: Dict):
        """Merge estatísticas"""
        for key in source:
            target[key] = target.get(key, 0) + source.get(key, 0)
