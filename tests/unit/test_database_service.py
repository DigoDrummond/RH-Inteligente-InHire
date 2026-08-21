"""
Testes unitários para DatabaseService
Testa operações CRUD e lógica de upsert
"""
import pytest
from datetime import datetime
from models.api_schemas import VagaAPI, PosicaoAPI, CandidaturaAPI, TalentoAPI
from models.database import Vaga, Posicao, Candidatura, Talento


@pytest.mark.unit
@pytest.mark.requires_db
class TestDatabaseServiceVagas:
    """Testes para operações de vagas"""

    def test_upsert_vaga_create_new(self, database_service, sample_vaga_data):
        """Deve criar nova vaga quando não existe"""
        vaga_api = VagaAPI(**sample_vaga_data)

        is_new, operation = database_service.upsert_vaga(vaga_api)

        assert is_new is True
        assert operation == "created"

        # Verificar no banco
        vaga_db = database_service.session.query(Vaga)\
            .filter_by(inhire_id=sample_vaga_data["id"]).first()

        assert vaga_db is not None
        assert vaga_db.name == sample_vaga_data["name"]
        assert vaga_db.department == sample_vaga_data["department"]

    def test_upsert_vaga_update_existing(self, database_service, sample_vaga_data):
        """Deve atualizar vaga existente se data mais recente"""
        # Criar vaga inicial
        vaga_api = VagaAPI(**sample_vaga_data)
        database_service.upsert_vaga(vaga_api)
        database_service.session.commit()

        # Atualizar dados
        sample_vaga_data["name"] = "Desenvolvedor Python Senior"
        sample_vaga_data["updatedAt"] = "2025-01-16T10:00:00Z"

        vaga_api_updated = VagaAPI(**sample_vaga_data)
        is_new, operation = database_service.upsert_vaga(vaga_api_updated)

        assert is_new is False
        assert operation == "updated"

        # Verificar atualização
        vaga_db = database_service.session.query(Vaga)\
            .filter_by(inhire_id=sample_vaga_data["id"]).first()

        assert vaga_db.name == "Desenvolvedor Python Senior"

    def test_upsert_vaga_skip_if_not_newer(self, database_service, sample_vaga_data):
        """Deve pular se data não for mais recente"""
        # Criar vaga
        vaga_api = VagaAPI(**sample_vaga_data)
        database_service.upsert_vaga(vaga_api)
        database_service.session.commit()

        # Tentar atualizar com data antiga
        sample_vaga_data["name"] = "Outro Nome"
        sample_vaga_data["updatedAt"] = "2025-01-01T10:00:00Z"  # Mais antiga

        vaga_api_old = VagaAPI(**sample_vaga_data)
        is_new, operation = database_service.upsert_vaga(vaga_api_old)

        assert is_new is False
        assert operation == "skipped"

        # Nome não deve ter mudado
        vaga_db = database_service.session.query(Vaga)\
            .filter_by(inhire_id=sample_vaga_data["id"]).first()

        assert vaga_db.name != "Outro Nome"


@pytest.mark.unit
@pytest.mark.requires_db
class TestDatabaseServicePosicoes:
    """Testes para operações de posições"""

    def test_upsert_posicao_create_new(self, database_service, sample_vaga_data, sample_posicao_data):
        """Deve criar nova posição"""
        # Criar vaga primeiro (FK)
        vaga_api = VagaAPI(**sample_vaga_data)
        database_service.upsert_vaga(vaga_api)
        database_service.session.commit()

        # Criar posição
        posicao_api = PosicaoAPI(**sample_posicao_data)
        is_new, operation = database_service.upsert_posicao(posicao_api)

        assert is_new is True
        assert operation == "created"

        # Verificar no banco
        posicao_db = database_service.session.query(Posicao)\
            .filter_by(inhire_id=sample_posicao_data["id"]).first()

        assert posicao_db is not None
        assert posicao_db.status == "open"

    def test_upsert_posicao_without_vaga_fails(self, database_service, sample_posicao_data):
        """Deve falhar se vaga não existir (FK constraint)"""
        posicao_api = PosicaoAPI(**sample_posicao_data)

        with pytest.raises(Exception):  # IntegrityError esperado
            database_service.upsert_posicao(posicao_api)
            database_service.session.commit()


@pytest.mark.unit
@pytest.mark.requires_db
class TestDatabaseServiceCandidaturas:
    """Testes para operações de candidaturas"""

    def test_upsert_candidatura_create_new(self, database_service, sample_vaga_data, sample_candidatura_data, sample_talento_data):
        """Deve criar nova candidatura"""
        # Criar vaga e talento (FKs)
        vaga_api = VagaAPI(**sample_vaga_data)
        database_service.upsert_vaga(vaga_api)

        talento_api = TalentoAPI(**sample_talento_data)
        database_service.upsert_talento(talento_api)

        database_service.session.commit()

        # Criar candidatura
        candidatura_api = CandidaturaAPI(**sample_candidatura_data)
        is_new, operation = database_service.upsert_candidatura(candidatura_api)

        assert is_new is True
        assert operation == "created"

        # Verificar no banco
        cand_db = database_service.session.query(Candidatura)\
            .filter_by(inhire_id=sample_candidatura_data["id"]).first()

        assert cand_db is not None
        assert cand_db.status == "ACTIVE"
        assert cand_db.stage_name == "Triagem"

    def test_upsert_candidatura_update_existing(self, database_service, sample_vaga_data, sample_candidatura_data, sample_talento_data):
        """Deve atualizar candidatura existente"""
        # Setup
        vaga_api = VagaAPI(**sample_vaga_data)
        database_service.upsert_vaga(vaga_api)

        talento_api = TalentoAPI(**sample_talento_data)
        database_service.upsert_talento(talento_api)

        candidatura_api = CandidaturaAPI(**sample_candidatura_data)
        database_service.upsert_candidatura(candidatura_api)

        database_service.session.commit()

        # Atualizar
        sample_candidatura_data["stageName"] = "Entrevista"
        sample_candidatura_data["updatedAt"] = "2025-01-16T10:00:00Z"

        candidatura_api_updated = CandidaturaAPI(**sample_candidatura_data)
        is_new, operation = database_service.upsert_candidatura(candidatura_api_updated)

        assert is_new is False
        assert operation == "updated"

        # Verificar
        cand_db = database_service.session.query(Candidatura)\
            .filter_by(inhire_id=sample_candidatura_data["id"]).first()

        assert cand_db.stage_name == "Entrevista"


@pytest.mark.unit
@pytest.mark.requires_db
class TestDatabaseServiceTalentos:
    """Testes para operações de talentos"""

    def test_upsert_talento_create_new(self, database_service, sample_talento_data):
        """Deve criar novo talento"""
        talento_api = TalentoAPI(**sample_talento_data)

        is_new, operation = database_service.upsert_talento(talento_api)

        assert is_new is True
        assert operation == "created"

        # Verificar no banco
        talento_db = database_service.session.query(Talento)\
            .filter_by(inhire_id=sample_talento_data["id"]).first()

        assert talento_db is not None
        assert talento_db.name == sample_talento_data["name"]
        assert talento_db.email == sample_talento_data["email"]

    def test_upsert_talento_handles_attributes_json(self, database_service, sample_talento_data):
        """Deve serializar attributes corretamente para JSON"""
        talento_api = TalentoAPI(**sample_talento_data)
        database_service.upsert_talento(talento_api)
        database_service.session.commit()

        # Verificar JSON
        talento_db = database_service.session.query(Talento)\
            .filter_by(inhire_id=sample_talento_data["id"]).first()

        assert talento_db.attributes is not None
        assert "skills" in talento_db.attributes
        assert "Python" in talento_db.attributes["skills"]


@pytest.mark.unit
class TestDatabaseServiceHelpers:
    """Testes para funções auxiliares"""

    def test_normalize_datetime_with_timezone(self, database_service):
        """Deve normalizar datetime com timezone para naive"""
        from dateutil import parser

        dt_with_tz = parser.isoparse("2025-01-15T15:30:00-03:00")
        dt_normalized = database_service._normalize_datetime(dt_with_tz)

        assert dt_normalized.tzinfo is None  # Deve ser naive
        assert dt_normalized.hour == 15  # Hora de São Paulo

    def test_normalize_datetime_from_string(self, database_service):
        """Deve converter string ISO para datetime"""
        dt_string = "2025-01-15T15:30:00Z"
        dt_normalized = database_service._normalize_datetime(dt_string)

        assert isinstance(dt_normalized, datetime)
        assert dt_normalized.tzinfo is None

    def test_normalize_datetime_none(self, database_service):
        """Deve retornar None para input None"""
        result = database_service._normalize_datetime(None)
        assert result is None

    def test_serialize_pydantic_to_dict(self, database_service, sample_vaga_data):
        """Deve converter Pydantic model para dict"""
        vaga_api = VagaAPI(**sample_vaga_data)
        result = database_service._serialize_pydantic_to_dict(vaga_api)

        assert isinstance(result, dict)
        assert result["id"] == sample_vaga_data["id"]
        assert result["name"] == sample_vaga_data["name"]

    def test_serialize_pydantic_list(self, database_service, sample_vaga_data):
        """Deve converter lista de Pydantic models"""
        vaga_api = VagaAPI(**sample_vaga_data)
        result = database_service._serialize_pydantic_to_dict([vaga_api, vaga_api])

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, dict) for item in result)


@pytest.mark.unit
@pytest.mark.requires_db
class TestDatabaseServiceSyncLog:
    """Testes para sync log"""

    def test_create_sync_log(self, database_service):
        """Deve criar registro de sync log"""
        from models.database import SyncConfiguration
        from config import SyncType, SyncEntity

        # Criar config
        config = SyncConfiguration(tenant_id="test-tenant")
        database_service.session.add(config)
        database_service.session.commit()

        # Criar sync log
        sync_log = database_service.create_sync_log(
            config.id,
            SyncType.FULL,
            SyncEntity.VAGA
        )

        assert sync_log is not None
        assert sync_log.sync_type == SyncType.FULL
        assert sync_log.sync_entity == SyncEntity.VAGA
        assert sync_log.status == "RUNNING"

    def test_complete_sync_log_success(self, database_service):
        """Deve completar sync log com sucesso"""
        from models.database import SyncConfiguration
        from config import SyncType, SyncEntity, SyncStatus

        # Setup
        config = SyncConfiguration(tenant_id="test-tenant")
        database_service.session.add(config)
        database_service.session.commit()

        sync_log = database_service.create_sync_log(
            config.id,
            SyncType.FULL,
            SyncEntity.VAGA
        )

        # Completar
        stats = {"processed": 100, "created": 50, "updated": 30}
        database_service.complete_sync_log(sync_log, SyncStatus.SUCCESS, stats)

        assert sync_log.status == SyncStatus.SUCCESS
        assert sync_log.records_processed == 100
        assert sync_log.end_time is not None
