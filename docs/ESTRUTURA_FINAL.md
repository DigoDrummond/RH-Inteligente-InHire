# Estrutura Final do Projeto InHire

**Data da limpeza:** 12/01/2026

---

## Estrutura do Projeto

```
Inhire/
├── 📄 run_sync.py                           # Script principal (--full | --incremental)
├── 📄 scheduler.py                          # Agendador automático
├── 📄 init_database.py                      # Inicialização do banco
├── 📄 config.py                             # Configurações e endpoints
├── 📄 metrics_server.py                     # Servidor de métricas
│
├── 📄 debug_posicoes.py                     # Debug da API de posições
├── 📄 comparar_posicoes_abertas.py         # Comparativo API vs BD
│
├── 📋 README.md                             # Documentação principal
├── 📋 COMANDOS_RAPIDOS.md                   # Comandos úteis
│
├── ⚙️ .env                                  # Variáveis de ambiente (não versionar)
├── ⚙️ .env.example                          # Exemplo de configuração
├── ⚙️ requirements.txt                      # Dependências Python
├── ⚙️ pytest.ini                            # Configuração de testes
├── ⚙️ .gitignore                            # Arquivos ignorados pelo Git
├── ⚙️ credentials.json                      # Credenciais Google (não versionar)
│
├── 📁 models/                               # Modelos de dados
│   ├── __init__.py
│   ├── database.py                          # Modelos SQLAlchemy
│   ├── api_schemas.py                       # Schemas Pydantic
│   └── new_api_schemas.py                   # Schemas novos
│
├── 📁 services/                             # Serviços de negócio
│   ├── __init__.py
│   ├── sync_service.py                      # Orquestrador de sincronização
│   ├── auth_service.py                      # Autenticação InHire
│   ├── api_client.py                        # Cliente da API
│   ├── database_service.py                  # Operações de banco
│   └── google_sheets_service.py             # Integração Google Sheets
│
├── 📁 utils/                                # Utilitários
│   ├── __init__.py
│   ├── logger.py                            # Sistema de logs
│   ├── retry.py                             # Retry com backoff
│   └── metrics.py                           # Métricas de performance
│
├── 📁 migrations/                           # Migrações SQL
│   ├── 001_initial_schema.sql
│   ├── 002_add_timeline.sql
│   ├── 003_add_diversity.sql
│   └── ... (10 migrations)
│
├── 📁 docs/                                 # Documentação
│   ├── README.md                            # Visão geral do projeto
│   ├── PROJECT_STRUCTURE.md                 # Estrutura detalhada
│   ├── DOCUMENTATION_INDEX.md               # Índice de docs
│   ├── FLUXO_SINCRONIZACAO.md              # Fluxo de sincronização
│   └── DOCUMENTACAO_SINCRONIZACAO_POSICOES.md  # Debug de posições
│
├── 📁 logs/                                 # Logs do sistema
│   └── inhire_sync.log                      # Log de sincronização
│
└── 📁 .claude/                              # Configurações do Claude Code
    └── settings.local.json
```

---

## Arquivos Essenciais na Raiz

### Scripts Principais (5 arquivos)
✅ `run_sync.py` - Script principal de sincronização
✅ `scheduler.py` - Agendamento automático
✅ `init_database.py` - Setup do banco de dados
✅ `config.py` - Configurações centralizadas
✅ `metrics_server.py` - Servidor de métricas

### Scripts de Debug (2 arquivos)
✅ `debug_posicoes.py` - Debug da API de posições
✅ `comparar_posicoes_abertas.py` - Comparativo completo

### Documentação (2 arquivos)
✅ `README.md` - Documentação principal
✅ `COMANDOS_RAPIDOS.md` - Comandos frequentes

### Configuração (6 arquivos)
✅ `.env` - Variáveis de ambiente
✅ `.env.example` - Template de configuração
✅ `requirements.txt` - Dependências Python
✅ `pytest.ini` - Configuração de testes
✅ `.gitignore` - Exclusões do Git
✅ `credentials.json` - Credenciais Google

**Total: 15 arquivos na raiz**

---

## Diretórios Mantidos

### Core do Sistema (3 diretórios)
📁 `models/` - Modelos de dados (database, schemas)
📁 `services/` - Lógica de negócio (sync, auth, api)
📁 `utils/` - Utilitários (logger, retry, metrics)

### Dados e Configuração (3 diretórios)
📁 `migrations/` - 10 migrações SQL
📁 `logs/` - Logs de execução
📁 `.claude/` - Configurações do Claude Code

### Documentação (1 diretório)
📁 `docs/` - 5 documentos essenciais

**Total: 7 diretórios**

---

## Arquivos Removidos

### Arquivos Temporários
❌ `API_Posicao.py` - Script obsoleto/incompleto
❌ `LIMPEZA_2026-01-12.md` - Relatório de limpeza anterior
❌ `ANALISE_API_POSICAO.md` - Conteúdo incorporado em outra doc
❌ `log_comparacao.txt` - Log temporário
❌ Arquivos corrompidos (G??Meu, Drive, etc.)

### Diretórios Removidos
❌ `scripts/` - Scripts de desenvolvimento antigos
❌ `tests/` - Testes temporários
❌ `sql/` - SQLs temporários
❌ `analise/` - Análises temporárias
❌ `arquivos_antigos/` - Backups antigos
❌ `__pycache__/` - Cache Python (todos)

### Cache e Temporários
❌ Todos os `__pycache__/` em subpastas
❌ Todos os `*.pyc` e `*.pyo`
❌ Arquivos `desktop.ini`

**Total removido: ~50+ itens**

---

## Documentação Organizada

Toda documentação técnica foi movida para `docs/`:

1. **README.md** - Visão geral e quick start
2. **PROJECT_STRUCTURE.md** - Estrutura detalhada
3. **DOCUMENTATION_INDEX.md** - Índice de toda documentação
4. **FLUXO_SINCRONIZACAO.md** - Fluxo completo de sync
5. **DOCUMENTACAO_SINCRONIZACAO_POSICOES.md** - Debug de posições

---

## Como Usar o Sistema

### Sincronização
```bash
# Sincronização incremental (diária)
python run_sync.py --incremental

# Sincronização completa (setup inicial)
python run_sync.py --full
```

### Debug de Posições
```bash
# Testar API de posições
python debug_posicoes.py

# Comparar API vs Banco
python comparar_posicoes_abertas.py
```

### Agendamento
```bash
# Rodar scheduler automático
python scheduler.py
```

---

## Próximos Passos

1. ✅ Projeto limpo e organizado
2. ✅ Documentação completa
3. ✅ Scripts de debug prontos
4. ⏳ Discutir divergências com InHire
5. ⏳ Implementar correções necessárias

---

## Comandos Úteis

```bash
# Ver estrutura
tree /F

# Rodar sincronização
python run_sync.py --incremental

# Ver logs
tail -f logs/inhire_sync.log

# Consultar banco
psql -U postgres -d inhire
```

---

## Notas Importantes

⚠️ **Não versionar:**
- `.env` (contém credenciais)
- `credentials.json` (credenciais Google)
- `logs/*.log` (logs de execução)
- `__pycache__/` (cache Python)

✅ **Versionar:**
- Todos os arquivos `.py`
- `.env.example` (template)
- Documentação em `docs/`
- Migrações em `migrations/`

---

**Projeto pronto para produção! 🚀**
