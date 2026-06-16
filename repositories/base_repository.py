"""
Base Repository - Classe abstrata com operações CRUD comuns
Implementa Repository Pattern para separar acesso a dados
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from utils.logger import get_logger


T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Base repository com operações CRUD comuns

    Subclasses devem:
    1. Definir model_class: Type[T]
    2. Implementar métodos abstratos específicos
    """

    def __init__(self, session: Session):
        """
        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self.logger = get_logger(self.__class__.__name__)

    @property
    @abstractmethod
    def model_class(self):
        """Retorna a classe do modelo SQLAlchemy"""
        pass

    # ========== CRUD Básico ==========

    def get_by_id(self, id: int) -> Optional[T]:
        """
        Busca entidade por ID interno

        Args:
            id: ID do banco de dados

        Returns:
            Entidade encontrada ou None
        """
        try:
            return self.session.query(self.model_class).filter_by(id=id).first()
        except Exception as e:
            self.logger.error(f"Erro ao buscar {self.model_class.__name__} por ID {id}: {e}")
            return None

    def get_by_inhire_id(self, inhire_id: str) -> Optional[T]:
        """
        Busca entidade por ID do Inhire

        Args:
            inhire_id: ID da API Inhire

        Returns:
            Entidade encontrada ou None
        """
        try:
            return self.session.query(self.model_class).filter_by(inhire_id=inhire_id).first()
        except Exception as e:
            self.logger.error(f"Erro ao buscar {self.model_class.__name__} por inhire_id {inhire_id}: {e}")
            return None

    def get_all(self, limit: Optional[int] = None) -> List[T]:
        """
        Busca todas as entidades

        Args:
            limit: Limite de resultados (opcional)

        Returns:
            Lista de entidades
        """
        try:
            query = self.session.query(self.model_class)
            if limit:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            self.logger.error(f"Erro ao buscar todos {self.model_class.__name__}: {e}")
            return []

    def create(self, entity: T, commit: bool = True) -> T:
        """
        Cria nova entidade

        Args:
            entity: Entidade a ser criada
            commit: Se deve fazer commit imediato

        Returns:
            Entidade criada
        """
        try:
            self.session.add(entity)
            if commit:
                self.session.commit()
                self.session.refresh(entity)
            return entity
        except IntegrityError as e:
            self.session.rollback()
            self.logger.error(f"Erro de integridade ao criar {self.model_class.__name__}: {e}")
            raise
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao criar {self.model_class.__name__}: {e}")
            raise

    def update(self, entity: T, commit: bool = True) -> T:
        """
        Atualiza entidade existente

        Args:
            entity: Entidade a ser atualizada
            commit: Se deve fazer commit imediato

        Returns:
            Entidade atualizada
        """
        try:
            if commit:
                self.session.commit()
                self.session.refresh(entity)
            return entity
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao atualizar {self.model_class.__name__}: {e}")
            raise

    def delete(self, id: int, commit: bool = True) -> bool:
        """
        Deleta entidade por ID

        Args:
            id: ID da entidade
            commit: Se deve fazer commit imediato

        Returns:
            True se deletado com sucesso
        """
        try:
            entity = self.get_by_id(id)
            if entity:
                self.session.delete(entity)
                if commit:
                    self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao deletar {self.model_class.__name__} ID {id}: {e}")
            return False

    def exists_by_inhire_id(self, inhire_id: str) -> bool:
        """
        Verifica se entidade existe por Inhire ID

        Args:
            inhire_id: ID da API Inhire

        Returns:
            True se existe
        """
        try:
            return self.session.query(
                self.session.query(self.model_class)
                .filter_by(inhire_id=inhire_id)
                .exists()
            ).scalar()
        except Exception as e:
            self.logger.error(f"Erro ao verificar existência de {self.model_class.__name__}: {e}")
            return False

    def count(self) -> int:
        """
        Conta total de entidades

        Returns:
            Quantidade de registros
        """
        try:
            return self.session.query(self.model_class).count()
        except Exception as e:
            self.logger.error(f"Erro ao contar {self.model_class.__name__}: {e}")
            return 0

    # ========== Métodos de Batch ==========

    def bulk_create(self, entities: List[T], commit: bool = True) -> List[T]:
        """
        Cria múltiplas entidades em batch

        Args:
            entities: Lista de entidades
            commit: Se deve fazer commit

        Returns:
            Lista de entidades criadas
        """
        try:
            self.session.bulk_save_objects(entities)
            if commit:
                self.session.commit()
            return entities
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao criar em batch {self.model_class.__name__}: {e}")
            raise

    def flush(self):
        """Flush sem commit"""
        try:
            self.session.flush()
        except Exception as e:
            self.logger.error(f"Erro ao fazer flush: {e}")
            raise

    def commit(self):
        """Commit da transação"""
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erro ao fazer commit: {e}")
            raise

    def rollback(self):
        """Rollback da transação"""
        try:
            self.session.rollback()
        except Exception as e:
            self.logger.error(f"Erro ao fazer rollback: {e}")
            raise
