"""
Posicao Repository - Operações de persistência para Posições
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from repositories.base_repository import BaseRepository
from models.database import Posicao


class PosicaoRepository(BaseRepository[Posicao]):
    """Repository para entidade Posicao"""

    @property
    def model_class(self):
        return Posicao

    def get_by_vaga_id(self, vaga_id: int) -> List[Posicao]:
        """
        Busca todas as posições de uma vaga

        Args:
            vaga_id: ID da vaga (FK)

        Returns:
            Lista de posições
        """
        try:
            return self.session.query(Posicao).filter_by(vaga_id=vaga_id).all()
        except Exception as e:
            self.logger.error(f"Erro ao buscar posições da vaga {vaga_id}: {e}")
            return []

    def get_all_open(self) -> List[Posicao]:
        """
        Busca todas as posições abertas

        Returns:
            Lista de posições com status 'open'
        """
        try:
            return self.session.query(Posicao).filter(Posicao.status == 'open').all()
        except Exception as e:
            self.logger.error(f"Erro ao buscar posições abertas: {e}")
            return []

    def count_by_vaga(self, vaga_id: int) -> int:
        """
        Conta posições de uma vaga

        Args:
            vaga_id: ID da vaga

        Returns:
            Quantidade de posições
        """
        try:
            return self.session.query(Posicao).filter_by(vaga_id=vaga_id).count()
        except Exception as e:
            self.logger.error(f"Erro ao contar posições da vaga {vaga_id}: {e}")
            return 0

    def get_open_by_vaga(self, vaga_id: int) -> List[Posicao]:
        """
        Busca posições abertas de uma vaga específica

        Args:
            vaga_id: ID da vaga

        Returns:
            Lista de posições abertas
        """
        try:
            return self.session.query(Posicao).filter(
                Posicao.vaga_id == vaga_id,
                Posicao.status == 'open'
            ).all()
        except Exception as e:
            self.logger.error(f"Erro ao buscar posições abertas da vaga {vaga_id}: {e}")
            return []

    def get_by_requisition_id(self, requisition_id: str) -> Optional[Posicao]:
        """
        Busca posição por ID de requisição

        Args:
            requisition_id: ID da requisição

        Returns:
            Posição encontrada ou None
        """
        try:
            return self.session.query(Posicao).filter_by(requisition_id=requisition_id).first()
        except Exception as e:
            self.logger.error(f"Erro ao buscar posição por requisition_id {requisition_id}: {e}")
            return None
