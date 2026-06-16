# Guia de Testes - InHire Sync

**Data de criação:** 16/01/2026
**Versão:** 1.0

---

## 📋 Visão Geral

Sistema completo de testes automatizados para garantir qualidade e confiabilidade do InHire Sync.

### Cobertura de Testes

```
Cobertura atual: 70%+ (mínimo exigido)
Testes implementados: 50+
Tempo de execução: ~30 segundos
```

---

## 🏗️ Estrutura de Testes

```
tests/
├── conftest.py                      # Configuração global + fixtures
├── unit/                            # Testes unitários (rápidos)
│   ├── test_api_client.py           # 15 testes
│   ├── test_database_service.py     # 20 testes
│   ├── test_sync_service.py         # 10 testes
│   └── test_utils.py                # 5 testes
└── integration/                     # Testes de integração
    ├── test_sync_flow.py            # 10 testes
    └── test_database_operations.py  # 5 testes
```

---

## 🚀 Executando Testes

### Todos os Testes
```bash
pytest
```

### Testes Unitários (Rápidos)
```bash
pytest tests/unit/ -v
```

### Testes de Integração
```bash
pytest tests/integration/ -v
```

### Por Marker
```bash
# Apenas testes rápidos
pytest -m unit

# Apenas testes de banco
pytest -m requires_db

# Excluir testes lentos
pytest -m "not slow"
```

### Com Cobertura
```bash
pytest --cov=services --cov=models --cov=utils --cov-report=html
```

### Testes Específicos
```bash
# Um arquivo
pytest tests/unit/test_api_client.py

# Uma classe
pytest tests/unit/test_api_client.py::TestAPIClientVagas

# Um método
pytest tests/unit/test_api_client.py::TestAPIClientVagas::test_get_all_vagas_single_page
```

---

## 📊 Coverage Report

### Visualizar Coverage
```bash
# Rodar com coverage
pytest --cov=services --cov-report=html

# Abrir relatório HTML
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac
xdg-open htmlcov/index.html  # Linux
```

### Coverage por Módulo
```bash
pytest --cov=services --cov-report=term-missing
```

Saída esperada:
```
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
services/__init__.py                  5      0   100%
services/api_client.py              150     15    90%   45-50, 123
services/database_service.py        200     20    90%   78-85, 156-162
services/sync_service.py            180     30    83%   89-95, 145-158
---------------------------------------------------------------
TOTAL                               535     65    88%
```

---

## 🧪 Tipos de Testes

### 1. Unit Tests (@pytest.mark.unit)

**Características:**
- Rápidos (< 100ms por teste)
- Sem dependências externas
- Usam mocks e stubs
- Testam lógica isolada

**Exemplo:**
```python
@pytest.mark.unit
def test_normalize_datetime_with_timezone(database_service):
    """Deve normalizar datetime com timezone"""
    dt_with_tz = parser.isoparse("2025-01-15T15:30:00-03:00")
    dt_normalized = database_service._normalize_datetime(dt_with_tz)

    assert dt_normalized.tzinfo is None
    assert dt_normalized.hour == 15
```

### 2. Integration Tests (@pytest.mark.integration)

**Características:**
- Mais lentos (100ms - 1s)
- Requerem banco de dados de teste
- Testam interação entre componentes
- Validam fluxos completos

**Exemplo:**
```python
@pytest.mark.integration
@pytest.mark.requires_db
def test_sync_vagas_end_to_end(db_session, sample_vaga_data):
    """Deve sincronizar vagas do início ao fim"""
    sync_service = SyncService(db_session)

    with patch.object(sync_service.api_client, '_request'):
        result = sync_service._sync_vagas_full()

        assert result['processed'] == 1
        vaga = db_session.query(Vaga).first()
        assert vaga.name == "Desenvolvedor Python"
```

### 3. Smoke Tests (@pytest.mark.smoke)

**Características:**
- Testes de validação rápida
- Verificam funcionalidades críticas
- Executados a cada deploy

**Exemplo:**
```python
@pytest.mark.smoke
def test_api_client_authenticates():
    """API client deve autenticar com sucesso"""
    client = InhireAPIClient()
    assert client.auth_service.ensure_authenticated()
```

---

## 🔧 Fixtures

### Fixtures de Banco de Dados

```python
# Session de teste (rollback automático)
def test_something(db_session):
    # Usar db_session...
    pass

# DatabaseService configurado
def test_service(database_service):
    result = database_service.upsert_vaga(vaga_api)
    assert result == (True, "created")
```

### Fixtures de Dados

```python
# Dados de exemplo prontos
def test_with_sample_data(sample_vaga_data, sample_candidatura_data):
    # Usar sample_vaga_data...
    pass
```

### Fixtures de Mocks

```python
# API client mockado
def test_with_mock_api(mock_api_client):
    with patch.object(mock_api_client, '_request', return_value=...):
        # Testar...
        pass
```

---

## ✅ Boas Práticas

### 1. Nomenclatura Clara
```python
# ✅ BOM
def test_upsert_vaga_creates_new_when_not_exists():
    ...

# ❌ RUIM
def test_vaga():
    ...
```

### 2. AAA Pattern (Arrange-Act-Assert)
```python
def test_something():
    # Arrange - Preparar dados
    vaga_api = VagaAPI(**sample_data)

    # Act - Executar ação
    result = service.upsert_vaga(vaga_api)

    # Assert - Verificar resultado
    assert result == (True, "created")
```

### 3. Um Teste, Uma Asserção (quando possível)
```python
# ✅ BOM
def test_vaga_is_created():
    result = service.create_vaga(...)
    assert result is not None

def test_vaga_has_correct_name():
    vaga = service.get_vaga(...)
    assert vaga.name == "Expected Name"

# ⚠️ ACEITÁVEL (assertions relacionadas)
def test_vaga_creation():
    vaga = service.create_vaga(...)
    assert vaga.id is not None
    assert vaga.name == "Expected Name"
```

### 4. Usar Fixtures para Setup
```python
# ✅ BOM
@pytest.fixture
def vaga_in_db(db_session, sample_vaga_data):
    vaga = Vaga(**sample_vaga_data)
    db_session.add(vaga)
    db_session.commit()
    return vaga

def test_update_vaga(vaga_in_db):
    # Vaga já existe, pode testar update
    ...

# ❌ RUIM
def test_update_vaga(db_session):
    # Criar vaga manualmente em cada teste
    vaga = Vaga(...)
    db_session.add(vaga)
    ...
```

### 5. Isolar Testes
```python
# Cada teste deve ser independente
# Usar transações/rollback automático
def test_a(db_session):
    # Mudanças são revertidas após teste
    ...

def test_b(db_session):
    # Começa com banco limpo
    ...
```

---

## 🎯 Executar Localmente

### Configuração Inicial

```bash
# 1. Criar banco de teste
createdb -U postgres inhire_test

# 2. Instalar dependências de teste
pip install pytest pytest-cov pytest-mock

# 3. Configurar .env (se necessário)
DB_NAME=inhire_test
```

### Rodar Testes

```bash
# Testes rápidos (unit)
pytest tests/unit/ -v

# Testes com banco (integration)
pytest tests/integration/ -v

# Todos com coverage
pytest --cov --cov-report=html

# Watch mode (re-executa em mudanças)
pytest-watch
```

---

## 🔬 Debugging Testes

### Modo Verbose
```bash
pytest -vv  # Muito verboso
```

### Parar no Primeiro Erro
```bash
pytest -x
```

### Mostrar Print Statements
```bash
pytest -s
```

### Rodar Último Teste que Falhou
```bash
pytest --lf
```

### PDB (Python Debugger)
```python
def test_something():
    import pdb; pdb.set_trace()  # Breakpoint
    result = function_under_test()
    assert result == expected
```

### Capturar Logs
```bash
pytest --log-cli-level=DEBUG
```

---

## 📈 Métricas de Qualidade

### Cobertura Mínima
- **Unit tests:** 80%+
- **Integration tests:** 70%+
- **Overall:** 70%+

### Performance
- **Unit test:** < 100ms
- **Integration test:** < 1s
- **Suite completa:** < 60s

### Taxa de Sucesso
- **CI Pipeline:** 100%
- **Local:** 100%

---

## 🚨 Troubleshooting

### Testes Falhando

```bash
# Ver traceback completo
pytest --tb=long

# Ver variáveis locais
pytest -l

# Modo de captura desabilitado
pytest -s --capture=no
```

### Banco de Teste

```bash
# Recriar banco de teste
dropdb inhire_test
createdb inhire_test

# Verificar conexão
psql -U postgres -d inhire_test -c "SELECT 1"
```

### Fixtures Não Funcionando

```bash
# Listar fixtures disponíveis
pytest --fixtures

# Ver setup/teardown de fixtures
pytest --setup-show
```

### Coverage Incompleto

```bash
# Ver arquivos não cobertos
pytest --cov --cov-report=term-missing

# Gerar relatório detalhado
pytest --cov --cov-report=html
open htmlcov/index.html
```

---

## 🎓 Recursos

### pytest Docs
- https://docs.pytest.org/

### Best Practices
- https://docs.pytest.org/en/stable/goodpractices.html

### Fixtures Guide
- https://docs.pytest.org/en/stable/fixture.html

### Coverage.py
- https://coverage.readthedocs.io/

---

## 📝 Checklist de PR

Antes de criar Pull Request:

- [ ] Todos os testes passando
- [ ] Coverage ≥ 70%
- [ ] Novos testes para código novo
- [ ] Testes de regressão para bugs
- [ ] Sem warnings do pytest
- [ ] Code linting OK (flake8, black)

---

**Documentação criada em:** 16/01/2026
**Última atualização:** 16/01/2026
**Responsável:** Framework Digital QA Team
