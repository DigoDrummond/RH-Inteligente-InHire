"""
Interfaces abstratas para Dependency Injection
Permite injetar dependências e facilita testes com mocks
"""
from abc import ABC, abstractmethod

__all__ = [
    'IAPIClient',
    'IDatabaseService',
    'IAuthService'
]
