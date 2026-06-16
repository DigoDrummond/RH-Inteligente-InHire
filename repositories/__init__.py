"""
Repositories - Camada de Acesso a Dados
Separa a lógica de persistência da lógica de negócio
"""
from repositories.base_repository import BaseRepository
from repositories.vaga_repository import VagaRepository
from repositories.posicao_repository import PosicaoRepository
from repositories.candidatura_repository import CandidaturaRepository
from repositories.talento_repository import TalentoRepository

__all__ = [
    'BaseRepository',
    'VagaRepository',
    'PosicaoRepository',
    'CandidaturaRepository',
    'TalentoRepository'
]
