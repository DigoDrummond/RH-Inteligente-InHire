"""
SyncOrchestrator: Orquestra sincronização de múltiplas entidades
Gerencia ordem de dependências e coordenação entre entidades
"""
from typing import Dict, List, Callable, Optional
from enum import Enum
from dataclasses import dataclass
from models.sync_statistics import SyncStatistics, EntityStats
from utils.logger import get_logger


class SyncPhase(Enum):
    """Fases de sincronização"""
    VAGAS = "vagas"
    POSICOES = "posicoes"
    CANDIDATURAS = "candidaturas"
    TALENTOS = "talentos"
    TIMELINE = "timeline"
    REQUISICOES = "requisicoes"
    METADATA = "metadata"  # Scorecards, tags, etc


@dataclass
class SyncTask:
    """
    Representa uma tarefa de sincronização.

    Attributes:
        phase: Fase da sincronização
        entity_name: Nome da entidade
        sync_func: Função que executa a sincronização
        depends_on: Lista de fases que devem ser concluídas primeiro
        optional: Se True, falha não bloqueia sync geral
    """
    phase: SyncPhase
    entity_name: str
    sync_func: Callable[[], Dict[str, int]]
    depends_on: List[SyncPhase] = None
    optional: bool = False

    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


class SyncOrchestrator:
    """
    Orquestra sincronização de múltiplas entidades respeitando dependências.

    Gerencia:
    - Ordem de execução baseada em dependências FK
    - Agregação de estatísticas
    - Tratamento de erros por entidade
    - Logging estruturado

    Example:
        orchestrator = SyncOrchestrator()

        # Adicionar tarefas
        orchestrator.add_task(SyncTask(
            phase=SyncPhase.VAGAS,
            entity_name="vagas",
            sync_func=lambda: sync_service._sync_vagas_full()
        ))

        orchestrator.add_task(SyncTask(
            phase=SyncPhase.POSICOES,
            entity_name="posicoes",
            sync_func=lambda: sync_service._sync_posicoes_full(),
            depends_on=[SyncPhase.VAGAS]
        ))

        # Executar
        stats = orchestrator.execute_all()
    """

    def __init__(self):
        self.tasks: List[SyncTask] = []
        self.completed_phases: List[SyncPhase] = []
        self.statistics = SyncStatistics()
        self.logger = get_logger(__name__)

    def add_task(self, task: SyncTask):
        """
        Adiciona uma tarefa à orquestração.

        Args:
            task: SyncTask a ser adicionada
        """
        self.tasks.append(task)
        self.logger.debug(f"Task adicionada: {task.entity_name} (phase={task.phase.value})")

    def can_execute(self, task: SyncTask) -> bool:
        """
        Verifica se task pode ser executada baseado em dependências.

        Args:
            task: Task a verificar

        Returns:
            True se todas as dependências foram satisfeitas
        """
        for dep in task.depends_on:
            if dep not in self.completed_phases:
                return False
        return True

    def execute_task(self, task: SyncTask, db_service=None, use_savepoint: bool = True) -> bool:
        """
        Executa uma task e registra resultado.

        Args:
            task: Task a executar
            db_service: Serviço de banco (para criar savepoints)
            use_savepoint: Se True, cria savepoint antes de executar

        Returns:
            True se sucesso, False se falhou
        """
        self.logger.info(f"Executando sync: {task.entity_name}")

        savepoint_name = f"after_{task.entity_name}"

        try:
            # Criar savepoint antes de executar
            if use_savepoint and db_service:
                db_service.create_savepoint(savepoint_name)

            # Executar função de sync
            stats_dict = task.sync_func()

            # Registrar estatísticas
            self.statistics.merge_entity_stats(task.entity_name, stats_dict)

            # Liberar savepoint (confirmar mudanças)
            if use_savepoint and db_service:
                db_service.release_savepoint(savepoint_name)

            # Marcar fase como completa
            if task.phase not in self.completed_phases:
                self.completed_phases.append(task.phase)

            self.logger.info(
                f"✓ {task.entity_name} sincronizado: "
                f"{stats_dict.get('processed', 0)} processados, "
                f"{stats_dict.get('failed', 0)} falhas"
            )
            return True

        except Exception as e:
            error_msg = f"Erro ao sincronizar {task.entity_name}: {str(e)}"
            self.statistics.add_error(error_msg)

            # Fazer rollback para savepoint se disponível
            if use_savepoint and db_service:
                try:
                    db_service.rollback_to_savepoint(savepoint_name)
                    self.logger.warning(f"Rollback executado para {savepoint_name}")
                except:
                    pass  # Savepoint pode não existir em alguns casos

            if task.optional:
                self.logger.warning(f"Task opcional falhou: {task.entity_name}")
                # Marcar como completa mesmo com falha (opcional)
                if task.phase not in self.completed_phases:
                    self.completed_phases.append(task.phase)
                return True
            else:
                self.logger.error(f"Task crítica falhou: {task.entity_name}")
                return False

    def get_ready_tasks(self) -> List[SyncTask]:
        """
        Retorna lista de tasks prontas para execução.

        Returns:
            Lista de tasks cujas dependências foram satisfeitas
        """
        executed_entities = {
            task.entity_name for task in self.tasks
            if task.phase in self.completed_phases
        }

        ready = []
        for task in self.tasks:
            # Pular se já executada
            if task.entity_name in executed_entities:
                continue

            # Verificar dependências
            if self.can_execute(task):
                ready.append(task)

        return ready

    def execute_all(self, fail_fast: bool = False, db_service=None, use_savepoints: bool = True) -> SyncStatistics:
        """
        Executa todas as tasks respeitando dependências.

        Args:
            fail_fast: Se True, para na primeira falha crítica
            db_service: Serviço de banco para savepoints (opcional)
            use_savepoints: Se True, usa savepoints entre tasks

        Returns:
            SyncStatistics com resultados agregados
        """
        self.logger.info("=" * 60)
        self.logger.info(f"INICIANDO ORQUESTRAÇÃO DE SYNC - {len(self.tasks)} tasks")
        self.logger.info("=" * 60)

        while True:
            # Buscar tasks prontas
            ready_tasks = self.get_ready_tasks()

            if not ready_tasks:
                # Verificar se todas foram executadas
                executed_count = len(self.completed_phases)
                total_phases = len(set(task.phase for task in self.tasks))

                if executed_count >= total_phases:
                    # Todas as fases foram concluídas
                    break
                else:
                    # Deadlock: tasks restantes têm dependências não satisfeitas
                    remaining = [
                        task for task in self.tasks
                        if task.phase not in self.completed_phases
                    ]
                    self.logger.error(
                        f"Deadlock detectado: {len(remaining)} tasks não podem ser executadas"
                    )
                    for task in remaining:
                        missing_deps = [
                            dep.value for dep in task.depends_on
                            if dep not in self.completed_phases
                        ]
                        self.statistics.add_error(
                            f"Task {task.entity_name} bloqueada. Dependências faltantes: {missing_deps}"
                        )
                    break

            # Executar tasks prontas
            for task in ready_tasks:
                success = self.execute_task(task, db_service=db_service, use_savepoint=use_savepoints)

                if not success and fail_fast:
                    self.logger.error("Fail-fast ativado. Parando orquestração.")
                    self.statistics.finish()
                    return self.statistics

        # Finalizar e logar sumário
        self.statistics.finish()
        self.statistics.log_summary()

        return self.statistics

    def get_execution_order(self) -> List[str]:
        """
        Retorna ordem de execução baseada em dependências (topological sort).

        Returns:
            Lista de entity names na ordem que serão executados
        """
        # Mapa de fase -> tasks
        phase_tasks: Dict[SyncPhase, List[SyncTask]] = {}
        for task in self.tasks:
            if task.phase not in phase_tasks:
                phase_tasks[task.phase] = []
            phase_tasks[task.phase].append(task)

        # Topological sort usando algoritmo de Kahn
        in_degree = {phase: 0 for phase in phase_tasks.keys()}
        graph = {phase: [] for phase in phase_tasks.keys()}

        # Construir grafo
        for phase, tasks_in_phase in phase_tasks.items():
            for task in tasks_in_phase:
                for dep in task.depends_on:
                    if dep in phase_tasks:
                        graph[dep].append(phase)
                        in_degree[phase] += 1

        # Kahn's algorithm
        queue = [phase for phase, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            phase = queue.pop(0)
            # Adicionar todas as tasks desta fase
            for task in phase_tasks[phase]:
                result.append(task.entity_name)

            # Remover arestas
            for neighbor in graph[phase]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return result

    def validate_dependencies(self) -> List[str]:
        """
        Valida que todas as dependências existem.

        Returns:
            Lista de erros encontrados (vazia se tudo OK)
        """
        errors = []
        available_phases = {task.phase for task in self.tasks}

        for task in self.tasks:
            for dep in task.depends_on:
                if dep not in available_phases:
                    errors.append(
                        f"Task '{task.entity_name}' depende de fase '{dep.value}' "
                        f"que não está disponível"
                    )

        return errors

    def reset(self):
        """Reseta orquestrador para nova execução"""
        self.completed_phases = []
        self.statistics = SyncStatistics()
        self.logger.debug("Orchestrator resetado")


def create_full_sync_orchestrator(sync_service) -> SyncOrchestrator:
    """
    Factory para criar orchestrator com todas as tasks de FULL sync.

    Args:
        sync_service: Instância do SyncService

    Returns:
        SyncOrchestrator configurado com todas as tasks
    """
    orchestrator = SyncOrchestrator()

    # FASE 1: Vagas (sem dependências)
    orchestrator.add_task(SyncTask(
        phase=SyncPhase.VAGAS,
        entity_name="vagas",
        sync_func=lambda: sync_service._sync_vagas_full()
    ))

    # FASE 2: Posições (depende de vagas para FK)
    orchestrator.add_task(SyncTask(
        phase=SyncPhase.POSICOES,
        entity_name="posicoes",
        sync_func=lambda: sync_service._sync_posicoes_full(),
        depends_on=[SyncPhase.VAGAS]
    ))

    # FASE 3: Candidaturas (depende de vagas)
    # Retorna tuple (stats, talent_ids), precisamos apenas stats
    def sync_candidaturas_wrapper():
        stats, _ = sync_service._sync_candidaturas_full()
        return stats

    orchestrator.add_task(SyncTask(
        phase=SyncPhase.CANDIDATURAS,
        entity_name="candidaturas",
        sync_func=sync_candidaturas_wrapper,
        depends_on=[SyncPhase.VAGAS]
    ))

    # FASE 4: Talentos (depende de candidaturas para coletar IDs)
    orchestrator.add_task(SyncTask(
        phase=SyncPhase.TALENTOS,
        entity_name="talentos",
        sync_func=lambda: sync_service._sync_talentos_full(),
        depends_on=[SyncPhase.CANDIDATURAS]
    ))

    # FASE 5: Requisições (opcional, depende de vagas)
    orchestrator.add_task(SyncTask(
        phase=SyncPhase.REQUISICOES,
        entity_name="requisicoes",
        sync_func=lambda: sync_service._sync_requisicoes_full(),
        depends_on=[SyncPhase.VAGAS],
        optional=True  # Não bloqueia se falhar
    ))

    return orchestrator
