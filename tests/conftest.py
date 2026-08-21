"""
Configuração global de testes - pytest
Fixtures compartilhadas entre todos os testes
"""
import os
import sys
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, MagicMock

# Adicionar projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import settings
from models.database import Base
from services.api_client import InhireAPIClient
from services.database_service import DatabaseService
from services.sync_service import SyncService


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_db_engine():
    """
    Engine de banco de dados para testes
    Usa database separado para não afetar produção
    """
    test_db_url = (
        f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/inhire_test"
        f"?client_encoding=utf8"
    )

    engine = create_engine(test_db_url, echo=False)

    # Criar todas as tabelas
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup após todos os testes
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db_engine):
    """
    Session de banco de dados para cada teste
    Rollback automático após cada teste
    """
    connection = test_db_engine.connect()
    transaction = connection.begin()

    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def database_service(db_session):
    """DatabaseService com session de teste"""
    return DatabaseService(db_session)


# ============================================================================
# API MOCKS
# ============================================================================

@pytest.fixture
def mock_auth_service():
    """Mock do AuthService"""
    mock = Mock()
    mock.ensure_authenticated.return_value = True
    mock.get_auth_headers.return_value = {
        "Authorization": "Bearer fake_token",
        "X-Tenant": "test-tenant"
    }
    return mock


@pytest.fixture
def mock_api_client(mock_auth_service):
    """Mock do InhireAPIClient"""
    client = InhireAPIClient(auth_service=mock_auth_service)
    return client


# ============================================================================
# SAMPLE DATA
# ============================================================================

@pytest.fixture
def sample_vaga_data():
    """Dados de exemplo de uma vaga"""
    return {
        "id": "vaga-123",
        "name": "Desenvolvedor Python",
        "status": "OPEN",
        "department": "Engenharia",
        "location": "São Paulo",
        "seniority": "senior",
        "createdAt": "2025-01-01T10:00:00Z",
        "updatedAt": "2025-01-15T15:30:00Z",
        "description": "Vaga para desenvolvedor Python",
        "requirements": ["Python 3.x", "Django", "PostgreSQL"],
        "customFields": {"area": "Backend"}
    }


@pytest.fixture
def sample_posicao_data():
    """Dados de exemplo de uma posição"""
    return {
        "id": "pos-456",
        "jobId": "vaga-123",
        "requisitionId": "req-789",
        "status": "open",
        "createdAt": "2025-01-01T10:00:00Z",
        "updatedAt": "2025-01-15T15:30:00Z"
    }


@pytest.fixture
def sample_candidatura_data():
    """Dados de exemplo de uma candidatura"""
    return {
        "id": "cand-789",
        "jobId": "vaga-123",
        "talentId": "talent-111",
        "status": "ACTIVE",
        "stageName": "Triagem",
        "source": "linkedin",
        "createdAt": "2025-01-10T09:00:00Z",
        "updatedAt": "2025-01-15T14:00:00Z",
        "appliedAt": "2025-01-10T09:00:00Z"
    }


@pytest.fixture
def sample_talento_data():
    """Dados de exemplo de um talento"""
    return {
        "id": "talent-111",
        "name": "João Silva",
        "email": "joao.silva@example.com",
        "phone": "+5511999999999",
        "createdAt": "2025-01-01T10:00:00Z",
        "updatedAt": "2025-01-15T15:30:00Z",
        "attributes": {
            "skills": ["Python", "Django", "PostgreSQL"],
            "experience_years": 5
        }
    }


@pytest.fixture
def sample_timeline_event():
    """Dados de exemplo de um evento de timeline"""
    return {
        "candidaturaId": "cand-789",
        "fromStage": "Novo",
        "toStage": "Triagem",
        "stageType": "screening",
        "createdAt": "2025-01-11T10:00:00Z",
        "updatedBy": "user-123"
    }


# ============================================================================
# MOCK RESPONSES
# ============================================================================

@pytest.fixture
def mock_vagas_response(sample_vaga_data):
    """Mock de resposta da API de vagas"""
    return {
        "results": [sample_vaga_data],
        "startKey": None,
        "count": 1
    }


@pytest.fixture
def mock_posicoes_response(sample_posicao_data):
    """Mock de resposta da API de posições"""
    return {
        "items": [sample_posicao_data],
        "hasMore": False,
        "nextStartKey": None
    }


@pytest.fixture
def mock_candidaturas_response(sample_candidatura_data):
    """Mock de resposta da API de candidaturas"""
    return {
        "results": [sample_candidatura_data],
        "startKey": None,
        "count": 1
    }


# ============================================================================
# SYNC SERVICE FIXTURES
# ============================================================================

@pytest.fixture
def sync_service(db_session, mock_api_client):
    """SyncService com mocks"""
    service = SyncService(db_session)
    service.api_client = mock_api_client
    return service


# ============================================================================
# UTILITIES
# ============================================================================

@pytest.fixture
def freeze_time():
    """Congela o tempo para testes determinísticos"""
    frozen_time = datetime(2026, 1, 16, 12, 0, 0)

    class FrozenTime:
        @staticmethod
        def now():
            return frozen_time

        @staticmethod
        def utcnow():
            return frozen_time

    return FrozenTime


@pytest.fixture
def cleanup_test_data(db_session):
    """
    Limpa dados de teste após execução
    Uso: Use como dependency em testes que criam dados
    """
    yield

    # Limpar tabelas após teste
    from models.database import (
        Vaga, Posicao, Candidatura, Talento,
        CandidaturaTimeline, SyncLog
    )

    db_session.query(CandidaturaTimeline).delete()
    db_session.query(Candidatura).delete()
    db_session.query(Posicao).delete()
    db_session.query(Vaga).delete()
    db_session.query(Talento).delete()
    db_session.query(SyncLog).delete()
    db_session.commit()


# ============================================================================
# MARKERS
# ============================================================================

def pytest_configure(config):
    """Configurar markers customizados"""
    config.addinivalue_line(
        "markers", "unit: Testes unitários (rápidos, sem dependências externas)"
    )
    config.addinivalue_line(
        "markers", "integration: Testes de integração (banco de dados, APIs)"
    )
    config.addinivalue_line(
        "markers", "slow: Testes lentos (> 1 segundo)"
    )
    config.addinivalue_line(
        "markers", "requires_db: Requer banco de dados de teste"
    )
    config.addinivalue_line(
        "markers", "requires_api: Requer API InHire disponível"
    )


# ============================================================================
# HOOKS
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """Modificar items coletados"""
    # Adicionar marker 'unit' por padrão se não tiver markers
    for item in items:
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unit)
