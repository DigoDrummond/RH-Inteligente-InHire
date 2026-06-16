"""
SyncStatistics: Modelo para rastrear e agregar estatísticas de sincronização
Extrai lógica de stats do SyncService
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional
from utils.logger import get_logger


@dataclass
class EntityStats:
    """Estatísticas de sincronização para uma entidade"""
    processed: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0

    def to_dict(self) -> Dict[str, int]:
        """Converte para dicionário"""
        return asdict(self)

    def total_successful(self) -> int:
        """Total de operações bem-sucedidas"""
        return self.created + self.updated + self.skipped

    def success_rate(self) -> float:
        """Taxa de sucesso em percentual"""
        if self.processed == 0:
            return 100.0
        return (self.total_successful() / self.processed) * 100

    def merge(self, other: 'EntityStats') -> 'EntityStats':
        """
        Mescla estatísticas de outra EntityStats.

        Args:
            other: Outra instância de EntityStats

        Returns:
            Nova EntityStats com valores somados
        """
        return EntityStats(
            processed=self.processed + other.processed,
            created=self.created + other.created,
            updated=self.updated + other.updated,
            skipped=self.skipped + other.skipped,
            failed=self.failed + other.failed
        )

    def __str__(self) -> str:
        """Representação legível"""
        return (
            f"processed={self.processed}, created={self.created}, "
            f"updated={self.updated}, skipped={self.skipped}, failed={self.failed}"
        )


@dataclass
class SyncStatistics:
    """
    Agregador de estatísticas de sincronização.

    Rastreia estatísticas por entidade e fornece métricas agregadas.
    """
    entity_stats: Dict[str, EntityStats] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.logger = get_logger(__name__)
        if self.start_time is None:
            self.start_time = datetime.now()

    def get_stats(self, entity_name: str) -> EntityStats:
        """
        Retorna estatísticas para uma entidade.

        Args:
            entity_name: Nome da entidade (ex: 'vagas', 'candidaturas')

        Returns:
            EntityStats da entidade
        """
        if entity_name not in self.entity_stats:
            self.entity_stats[entity_name] = EntityStats()
        return self.entity_stats[entity_name]

    def record_operation(
        self,
        entity_name: str,
        operation: str,
        success: bool = True
    ):
        """
        Registra uma operação de sincronização.

        Args:
            entity_name: Nome da entidade
            operation: Tipo de operação ('created', 'updated', 'skipped', 'failed')
            success: Se operação foi bem-sucedida
        """
        stats = self.get_stats(entity_name)
        stats.processed += 1

        if operation in ('created', 'updated', 'skipped', 'failed'):
            setattr(stats, operation, getattr(stats, operation) + 1)
        else:
            self.logger.warning(f"Operação desconhecida: {operation}")

        if not success:
            stats.failed += 1

    def merge_entity_stats(self, entity_name: str, stats_dict: Dict[str, int]):
        """
        Mescla estatísticas de um dicionário.

        Args:
            entity_name: Nome da entidade
            stats_dict: Dicionário com chaves (processed, created, updated, skipped, failed)
        """
        current = self.get_stats(entity_name)
        current.processed += stats_dict.get('processed', 0)
        current.created += stats_dict.get('created', 0)
        current.updated += stats_dict.get('updated', 0)
        current.skipped += stats_dict.get('skipped', 0)
        current.failed += stats_dict.get('failed', 0)

    def add_error(self, error: str):
        """
        Adiciona um erro à lista de erros.

        Args:
            error: Mensagem de erro
        """
        self.errors.append(error)
        self.logger.error(f"Sync error: {error}")

    def finish(self):
        """Marca fim da sincronização"""
        self.end_time = datetime.now()

    def duration_seconds(self) -> float:
        """
        Duração da sincronização em segundos.

        Returns:
            Duração em segundos
        """
        if self.start_time is None:
            return 0.0

        end = self.end_time or datetime.now()
        delta = end - self.start_time
        return delta.total_seconds()

    def duration_formatted(self) -> str:
        """
        Duração formatada legível.

        Returns:
            String formatada (ex: "2m 30s", "45s", "1h 15m")
        """
        seconds = int(self.duration_seconds())

        if seconds < 60:
            return f"{seconds}s"

        minutes = seconds // 60
        remaining_seconds = seconds % 60

        if minutes < 60:
            return f"{minutes}m {remaining_seconds}s"

        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"{hours}h {remaining_minutes}m"

    def total_processed(self) -> int:
        """Total de registros processados em todas as entidades"""
        return sum(stats.processed for stats in self.entity_stats.values())

    def total_created(self) -> int:
        """Total de registros criados em todas as entidades"""
        return sum(stats.created for stats in self.entity_stats.values())

    def total_updated(self) -> int:
        """Total de registros atualizados em todas as entidades"""
        return sum(stats.updated for stats in self.entity_stats.values())

    def total_failed(self) -> int:
        """Total de falhas em todas as entidades"""
        return sum(stats.failed for stats in self.entity_stats.values())

    def overall_success_rate(self) -> float:
        """Taxa de sucesso geral em percentual"""
        total = self.total_processed()
        if total == 0:
            return 100.0
        failed = self.total_failed()
        return ((total - failed) / total) * 100

    def to_dict(self) -> Dict:
        """
        Converte estatísticas para dicionário.

        Returns:
            Dicionário com todas as estatísticas
        """
        return {
            'entities': {name: stats.to_dict() for name, stats in self.entity_stats.items()},
            'totals': {
                'processed': self.total_processed(),
                'created': self.total_created(),
                'updated': self.total_updated(),
                'failed': self.total_failed(),
                'success_rate_pct': round(self.overall_success_rate(), 2)
            },
            'duration': {
                'seconds': round(self.duration_seconds(), 2),
                'formatted': self.duration_formatted()
            },
            'errors': self.errors,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }

    def log_summary(self):
        """Loga sumário das estatísticas"""
        self.logger.info("=" * 60)
        self.logger.info(f"SYNC SUMMARY - Duration: {self.duration_formatted()}")
        self.logger.info("=" * 60)

        for entity_name, stats in self.entity_stats.items():
            self.logger.info(
                f"{entity_name:20s}: {stats.processed:5d} processed, "
                f"{stats.created:4d} created, {stats.updated:4d} updated, "
                f"{stats.skipped:4d} skipped, {stats.failed:4d} failed "
                f"({stats.success_rate():.1f}% success)"
            )

        self.logger.info("-" * 60)
        self.logger.info(
            f"{'TOTAL':20s}: {self.total_processed():5d} processed, "
            f"{self.total_created():4d} created, {self.total_updated():4d} updated, "
            f"{self.total_failed():4d} failed "
            f"({self.overall_success_rate():.1f}% success)"
        )

        if self.errors:
            self.logger.warning(f"\n{len(self.errors)} errors occurred during sync")
            for i, error in enumerate(self.errors[:5], 1):  # Log primeiros 5 erros
                self.logger.warning(f"  {i}. {error}")
            if len(self.errors) > 5:
                self.logger.warning(f"  ... and {len(self.errors) - 5} more errors")

        self.logger.info("=" * 60)

    def __str__(self) -> str:
        """Representação legível"""
        return (
            f"SyncStatistics(entities={len(self.entity_stats)}, "
            f"processed={self.total_processed()}, duration={self.duration_formatted()})"
        )


def merge_stats_dicts(dict1: Dict[str, int], dict2: Dict[str, int]) -> Dict[str, int]:
    """
    Utilitário para mesclar dois dicionários de estatísticas.

    Args:
        dict1: Primeiro dicionário
        dict2: Segundo dicionário

    Returns:
        Dicionário mesclado com valores somados
    """
    merged = dict1.copy()
    for key, value in dict2.items():
        merged[key] = merged.get(key, 0) + value
    return merged
