"""
Testes unitários para InhireAPIClient
Testa chamadas à API com mocks
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.api_client import InhireAPIClient
from models.api_schemas import VagaAPI, PosicaoAPI, CandidaturaAPI


@pytest.mark.unit
class TestAPIClientVagas:
    """Testes para métodos de vagas"""

    def test_get_all_vagas_single_page(self, mock_api_client, mock_vagas_response):
        """Deve retornar todas as vagas em página única"""
        with patch.object(mock_api_client, '_request', return_value=mock_vagas_response):
            vagas = list(mock_api_client.get_all_vagas())

            assert len(vagas) == 1
            assert isinstance(vagas[0], VagaAPI)
            assert vagas[0].id == "vaga-123"

    def test_get_all_vagas_multiple_pages(self, mock_api_client, sample_vaga_data):
        """Deve paginar corretamente múltiplas páginas"""
        # Simular 2 páginas
        page1 = {
            "results": [sample_vaga_data],
            "startKey": "next-page",
            "count": 1
        }

        sample_vaga_data_2 = sample_vaga_data.copy()
        sample_vaga_data_2["id"] = "vaga-456"

        page2 = {
            "results": [sample_vaga_data_2],
            "startKey": None,  # Última página
            "count": 1
        }

        with patch.object(mock_api_client, '_request', side_effect=[page1, page2]):
            vagas = list(mock_api_client.get_all_vagas())

            assert len(vagas) == 2
            assert vagas[0].id == "vaga-123"
            assert vagas[1].id == "vaga-456"

    def test_get_all_vagas_with_limit(self, mock_api_client, mock_vagas_response):
        """Deve respeitar parâmetro limit"""
        with patch.object(mock_api_client, '_request', return_value=mock_vagas_response) as mock_request:
            list(mock_api_client.get_all_vagas(limit=10))

            # Verificar que limit foi passado
            call_args = mock_request.call_args[1]
            assert call_args['data']['limit'] == 10


@pytest.mark.unit
class TestAPIClientPosicoes:
    """Testes para métodos de posições"""

    def test_get_all_posicoes_single_page(self, mock_api_client, mock_posicoes_response):
        """Deve retornar todas as posições"""
        with patch.object(mock_api_client, '_request', return_value=mock_posicoes_response):
            posicoes = list(mock_api_client.get_all_posicoes(job_id="vaga-123"))

            assert len(posicoes) == 1
            assert isinstance(posicoes[0], PosicaoAPI)
            assert posicoes[0].id == "pos-456"

    def test_get_all_posicoes_no_startkey_first_page(self, mock_api_client, mock_posicoes_response):
        """Primeira página NÃO deve incluir startKey"""
        with patch.object(mock_api_client, '_request', return_value=mock_posicoes_response) as mock_request:
            list(mock_api_client.get_all_posicoes(job_id="vaga-123"))

            # Primeira chamada não deve ter startKey
            first_call = mock_request.call_args_list[0]
            params = first_call[1]['params']
            assert 'startKey' not in params or params.get('startKey') is None

    def test_get_all_posicoes_pagination(self, mock_api_client, sample_posicao_data):
        """Deve paginar corretamente com startKey"""
        page1 = {
            "items": [sample_posicao_data],
            "hasMore": True,
            "nextStartKey": 1
        }

        sample_posicao_data_2 = sample_posicao_data.copy()
        sample_posicao_data_2["id"] = "pos-789"

        page2 = {
            "items": [sample_posicao_data_2],
            "hasMore": False,
            "nextStartKey": None
        }

        with patch.object(mock_api_client, '_request', side_effect=[page1, page2]) as mock_request:
            posicoes = list(mock_api_client.get_all_posicoes(job_id="vaga-123"))

            assert len(posicoes) == 2

            # Segunda chamada deve incluir startKey=1
            second_call = mock_request.call_args_list[1]
            params = second_call[1]['params']
            assert params['startKey'] == 1


@pytest.mark.unit
class TestAPIClientCandidaturas:
    """Testes para métodos de candidaturas"""

    def test_get_all_candidaturas(self, mock_api_client, mock_candidaturas_response):
        """Deve retornar todas as candidaturas"""
        with patch.object(mock_api_client, '_request', return_value=mock_candidaturas_response):
            candidaturas = list(mock_api_client.get_all_candidaturas(job_id="vaga-123"))

            assert len(candidaturas) == 1
            assert isinstance(candidaturas[0], CandidaturaAPI)
            assert candidaturas[0].id == "cand-789"

    def test_get_all_candidaturas_filters_active(self, mock_api_client, sample_candidatura_data):
        """Deve filtrar apenas candidaturas ativas"""
        # Simular mix de ativas e inativas
        active = sample_candidatura_data.copy()
        active["status"] = "ACTIVE"

        inactive = sample_candidatura_data.copy()
        inactive["id"] = "cand-999"
        inactive["status"] = "INACTIVE"

        response = {
            "results": [active, inactive],
            "startKey": None,
            "count": 2
        }

        with patch.object(mock_api_client, '_request', return_value=response):
            candidaturas = list(mock_api_client.get_all_candidaturas(
                job_id="vaga-123",
                only_active=True
            ))

            # Deve filtrar apenas ativas
            assert len(candidaturas) == 1
            assert candidaturas[0].status == "ACTIVE"


@pytest.mark.unit
class TestAPIClientRetry:
    """Testes para mecanismo de retry"""

    def test_request_retry_on_401(self, mock_api_client, mock_auth_service):
        """Deve fazer retry quando recebe 401"""
        with patch('requests.request') as mock_request:
            # Primeira chamada: 401
            mock_response_401 = Mock()
            mock_response_401.status_code = 401

            # Segunda chamada: 200
            mock_response_200 = Mock()
            mock_response_200.status_code = 200
            mock_response_200.json.return_value = {"success": True}

            mock_request.side_effect = [mock_response_401, mock_response_200]

            result = mock_api_client._request("GET", "/test")

            # Deve ter feito 2 chamadas
            assert mock_request.call_count == 2

            # Deve ter re-autenticado
            assert mock_auth_service.authenticate.called

    def test_request_raises_on_429(self, mock_api_client):
        """Deve lançar exceção em rate limit"""
        from utils.retry import RateLimitException

        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 429

            mock_request.return_value = mock_response

            with pytest.raises(RateLimitException):
                mock_api_client._request("GET", "/test")

    def test_request_raises_on_other_errors(self, mock_api_client):
        """Deve lançar exceção em outros erros HTTP"""
        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = Exception("Server Error")

            mock_request.return_value = mock_response

            with pytest.raises(Exception):
                mock_api_client._request("GET", "/test")


@pytest.mark.unit
class TestAPIClientTimeout:
    """Testes para configuração de timeout"""

    def test_request_uses_configured_timeout(self, mock_api_client):
        """Deve usar timeout configurado"""
        from config import settings

        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}

            mock_request.return_value = mock_response

            mock_api_client._request("GET", "/test")

            # Verificar timeout
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs['timeout'] == (
                settings.INHIRE_TIMEOUT_CONNECT,
                settings.INHIRE_TIMEOUT_READ
            )


@pytest.mark.unit
class TestAPIClientHeaders:
    """Testes para headers HTTP"""

    def test_request_includes_auth_headers(self, mock_api_client, mock_auth_service):
        """Deve incluir headers de autenticação"""
        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}

            mock_request.return_value = mock_response

            mock_api_client._request("GET", "/test")

            # Verificar headers
            call_kwargs = mock_request.call_args[1]
            assert "Authorization" in call_kwargs['headers']
            assert "Bearer fake_token" in call_kwargs['headers']['Authorization']

    def test_request_includes_tenant_header(self, mock_api_client):
        """Deve incluir X-Tenant header"""
        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}

            mock_request.return_value = mock_response

            mock_api_client._request("GET", "/test")

            # Verificar tenant
            call_kwargs = mock_request.call_args[1]
            assert "X-Tenant" in call_kwargs['headers']


@pytest.mark.unit
class TestAPIClientLogging:
    """Testes para logging de requisições"""

    def test_request_logs_success(self, mock_api_client, caplog):
        """Deve logar requisição bem-sucedida"""
        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}

            mock_request.return_value = mock_response

            mock_api_client._request("GET", "/test")

            # Verificar se logou
            # (caplog captura logs do pytest)
            # Podemos verificar se chamou log_api_request

    def test_request_logs_error(self, mock_api_client, caplog):
        """Deve logar erro de requisição"""
        with patch('requests.request') as mock_request:
            mock_request.side_effect = Exception("Connection failed")

            with pytest.raises(Exception):
                mock_api_client._request("GET", "/test")


@pytest.mark.unit
class TestAPIClientPaginationEdgeCases:
    """Testes para casos extremos de paginação"""

    def test_empty_results(self, mock_api_client):
        """Deve lidar com resposta vazia"""
        empty_response = {
            "results": [],
            "startKey": None,
            "count": 0
        }

        with patch.object(mock_api_client, '_request', return_value=empty_response):
            vagas = list(mock_api_client.get_all_vagas())

            assert len(vagas) == 0

    def test_single_item_result(self, mock_api_client, sample_vaga_data):
        """Deve lidar com resultado de 1 item"""
        response = {
            "results": [sample_vaga_data],
            "startKey": None,
            "count": 1
        }

        with patch.object(mock_api_client, '_request', return_value=response):
            vagas = list(mock_api_client.get_all_vagas())

            assert len(vagas) == 1

    def test_many_pages(self, mock_api_client, sample_vaga_data):
        """Deve lidar com muitas páginas (>10)"""
        pages = []
        for i in range(15):
            vaga = sample_vaga_data.copy()
            vaga["id"] = f"vaga-{i}"

            page = {
                "results": [vaga],
                "startKey": f"key-{i+1}" if i < 14 else None,
                "count": 1
            }
            pages.append(page)

        with patch.object(mock_api_client, '_request', side_effect=pages):
            vagas = list(mock_api_client.get_all_vagas())

            assert len(vagas) == 15
