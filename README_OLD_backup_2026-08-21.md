# Sistema de Sincronização Inhire → PostgreSQL

Sistema completo em Python para sincronização automática de dados entre a plataforma Inhire e banco de dados PostgreSQL.

> **📚 Documentação Completa:** Consulte o **[Índice de Documentação](docs/README.md)** para navegação completa por toda a documentação do projeto.

---

## 📌 Status Atual do Projeto

### 🆕 Atualização 08/01/2026 - Integração Google Sheets + Bug Fix Posições

**✅ INTEGRAÇÃO GOOGLE SHEETS OPERACIONAL:**
- ✅ **Exportação Automática** - Script `export_posicoes_gspread.py` 100% funcional
- ✅ **Autenticação OAuth2** - Desktop App configurado e testado
- ✅ **20 Posições Exportadas** - Primeira exportação bem-sucedida
- ✅ **231 Células Atualizadas** - Dados completos na aba "Teste_API"
- ✅ **Token Caching** - Autenticação salva em `token.json` (reutilizável)

**🐛 BUG CRÍTICO CORRIGIDO:**
- ✅ Posições agora sincronizam corretamente (problema: `startKey=0`)
- ✅ 2 posições faltantes sincronizadas (vagas 1122 e 1124)
- ✅ Total de posições abertas: **20** (antes: 18)

**📊 DADOS EXPORTADOS:**
- 11 colunas de informações por posição
- Link direto para cada vaga no InHire
- Timestamp de última atualização
- Formato compatível com análises e dashboards

**🔧 CONFIGURAÇÃO NECESSÁRIA:**
- OAuth2 Client ID (Desktop app)
- Credenciais em `credentials.json`
- Token salvo automaticamente em `token.json`
- ID da planilha no arquivo `.env`

**📖 DOCUMENTAÇÃO:**
- [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md) - Guia completo de configuração
- [FIX_POSICOES_STARTKEY_2026-01-08.md](FIX_POSICOES_STARTKEY_2026-01-08.md) - Detalhes técnicos do bug fix
- [RELATORIO_SINCRONIZACAO_2026-01-08.md](RELATORIO_SINCRONIZACAO_2026-01-08.md) - Relatório completo

**🚀 COMANDO DE EXPORTAÇÃO:**
```bash
python export_posicoes_gspread.py
```

### 🚀 Atualização 08/01/2026 - Otimização de Timeline Implementada

**✅ OTIMIZAÇÕES DE PERFORMANCE:**
- ✅ **Timeline Inteligente** - Processa apenas candidaturas modificadas após última sync
- ✅ **Paralelização** - 10 threads paralelas (10x mais rápido)
- ✅ **Sessões Thread-Safe** - Cada thread com sua própria conexão ao banco
- ✅ **Filtro Automático** - Detecta última sincronização e filtra automaticamente

**📊 RESULTADOS REAIS:**
- ✅ Tempo sync incremental: **1.6 minutos** (vs 6+ horas antes)
- ✅ Timeline instantâneo quando não há mudanças (0 candidaturas processadas)
- ✅ Ganho: **120-720x mais rápido** em syncs subsequentes
- ✅ Total processado: **1.480 registros em 96.5 segundos**

**📖 DOCUMENTAÇÃO ATUALIZADA:**
- [OTIMIZACOES_TIMELINE.md](OTIMIZACOES_TIMELINE.md) - Detalhes completos das otimizações
- [ESTRATEGIA_SYNC_FINAL.md](docs/ESTRATEGIA_SYNC_FINAL.md) - Estratégia definitiva de sincronização
- [relatorio_cobertura_sync.md](docs/relatorio_cobertura_sync.md) - Cobertura completa

### 🎉 Atualização 04/12/2025 - Sincronização Incremental 100% Funcional

**✅ CORREÇÕES CRÍTICAS APLICADAS:**
- ✅ **Filtros de 7 dias REMOVIDOS** - Agora busca TODOS os registros ativos
- ✅ **Comparação individual implementada** - Cada registro comparado `BD < API`
- ✅ **Vaga Tags CORRIGIDO** - 31 tags sincronizadas com sucesso
- ✅ **Form Responses HABILITADO** - 310 respostas sincronizadas
- ✅ **Todas as 10 entidades no EXPRESS** - Sincronização completa

### 🗑️ Atualização 06/02/2026 - Otimização do Banco de Dados

**✅ LIMPEZA DE TABELAS OBSOLETAS:**
- ✅ **8 tabelas removidas** - Redução de 42% no número de tabelas
- ✅ **Banco focado em BI** - Apenas dados relevantes para análise
- ✅ **Models atualizados** - Código sincronizado com estrutura do BD
- ✅ **Migration criada** - Documentação completa das exclusões

**Tabelas Removidas:**
1. `custom_fields` - Tabela vazia, nunca foi populada
2. `talento_arquivos` - CVs em binário, não relevante para BI
3. `talento_tags` - Sem dados ou obsoleto
4. `scorecard_interviews` - Sem dados populados
5. `scorecard_jobs` - Sem dados populados
6. `scorecard_avaliacoes` - Sem dados populados
7. `form_responses` - Dados complexos, baixo valor analítico
8. `automations` - Configuração do sistema, não dados de negócio

**Estado Final:**
- **11 tabelas ativas** + 2 views de análise
- **287.777 registros** em produção
- **Integridade 100%** - Todas as dependências respeitadas

**📖 DOCUMENTAÇÃO:**
- [Migration 023](migrations/023_remove_obsolete_tables.sql) - Script de remoção
- `models/database.py.backup` - Backup do arquivo original

### Atualizações Anteriores

- **02/12/2025**: Dashboard v2 & Filtros Completos - [Detalhes](docs/reports/RELATORIO_MUDANCAS_2025-12-02.md)
- **19/11/2025**: Problema do enum "declined" corrigido - [Detalhes](docs/TROUBLESHOOTING_ENUM_DECLINED.md)
- **27/11/2025**: Projeto reorganizado - [Changelog](docs/changelogs/CHANGELOG_2025-11-27.md)

---

## 🎯 Características

- **Sincronização Completa**: Importa todos os dados históricos
- **Sincronização Incremental Otimizada**: Compara cada registro individualmente (`updated_at_bd < updated_at_api`)
- **Timeline Inteligente**: Filtro automático por última sincronização (processa apenas candidaturas modificadas)
- **Paralelização**: 10 threads paralelas para sincronização de timeline (10x mais rápido)
- **Autenticação JWT**: Renovação automática de tokens
- **Retry Automático**: Tratamento de falhas temporárias com backoff exponencial
- **Paginação Automática**: Processa grandes volumes de dados
- **Logs Estruturados**: Auditoria completa de todas as operações
- **Ordem de Dependências**: Respeita relacionamentos críticos entre entidades
- **Comparação Individual**: Cada registro verificado antes de atualizar (sem filtros temporais)

---

## 📦 Instalação Rápida

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# 3. Inicializar banco de dados
python init_database.py
```

---

## 🚀 Uso Básico

### Verificar Status
```bash
python scripts/utilities/check_sync_status.py
```

### Executar Sincronização

```bash
# EXPRESS (recomendado - ~9.5 min)
python run_sync.py --incremental

# COMPLETO (~20 min - inclui timeline completo)
python run_sync.py --incremental-complete

# FULL (~55 min - sincronização histórica completa)
python run_sync.py --full
```

### Modos de Sincronização (ATUALIZADO 04/12/2025)

#### 1. EXPRESS Mode (~9.5 minutos) ⭐ **RECOMENDADO**
- **Frequência**: A cada 1-2 horas
- **Entidades**: 10 entidades principais
- **Lógica**: Compara TODOS os registros ativos, atualiza apenas se `BD < API`
- **Uso**: `python run_sync.py --incremental`

**Entidades sincronizadas (otimizadas para BI/Analytics):**

**✅ ESSENCIAIS (Análise de Dados):**
1. **Candidaturas** (status='ACTIVE') - Funil de recrutamento
2. **Candidatura Timeline** - Tempo em cada etapa
3. **Vagas** (status='OPEN') - Posições abertas/fechadas
4. **Posições** (status='open') - Múltiplas vagas por posição
5. **Talentos** - Pool de candidatos
6. **Scorecard Interviews** - Avaliações de entrevistas
7. **Scorecard Jobs** - Avaliações de vagas

**🟡 SECUNDÁRIAS (Contexto):**
8. **Requisições** - Aprovações de vagas
9. **Vaga Tags** - Categorização
10. **Clientes** - Contexto empresarial

**❌ DESABILITADAS (Não relevantes para BI):**
- ~~Automations~~ - Configuração do sistema, não dados de negócio
- ~~Form Responses~~ - Dados complexos, pouco estruturados, baixo valor analítico
- ~~Talento Arquivos~~ - CVs (binários), acessar diretamente no ATS quando necessário

#### 2. COMPLETO Mode (~20 minutos)
- **Frequência**: A cada 4 horas ou quando necessário
- **Entidades**: Idêntico ao EXPRESS
- **Diferença**: Mantido para compatibilidade
- **Uso**: `python run_sync.py --incremental-complete`

#### 3. FULL Mode (~55 minutos)
- **Frequência**: Domingos às 02:00
- **Entidades**: Todas + dados históricos
- **Uso**: `python run_sync.py --full`

### Agendamento Automático
```bash
# Iniciar scheduler (mantém rodando)
python scheduler.py
```

---

## ⚙️ Lógica de Sincronização (ATUALIZADA)

### ✅ Estratégia Correta Implementada

Para **TODAS** as entidades, a lógica é:

1. **Buscar TODOS os registros ativos da API** (sem filtro temporal)
   - Vagas: `status = 'OPEN'`
   - Posições: `status = 'open'`
   - Candidaturas: `status = 'ACTIVE'`

2. **Para cada registro da API:**
   ```python
   # Buscar registro correspondente no BD
   if not exists:
       CREATE  # Criar novo registro
   else:
       # Comparar datas
       if updated_at_bd < updated_at_api:
           UPDATE  # Atualizar registro
       else:
           SKIP  # BD já está atualizado
   ```

3. **Sem filtros temporais arbitrários**
   - ❌ NÃO usa "últimos 7 dias"
   - ❌ NÃO usa "últimos 30 dias"
   - ✅ Compara CADA registro individualmente

**Resultado:** Performance otimizada + dados sempre atualizados

---

## 📁 Estrutura do Projeto

> 📖 **Documentação detalhada:** [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

```
Inhire/
├── 📄 Arquivos principais
│   ├── config.py                    # Configurações centralizadas
│   ├── run_sync.py                  # Script principal de sincronização
│   ├── scheduler.py                 # Agendador de tarefas
│   ├── init_database.py             # Inicialização do banco
│   ├── requirements.txt             # Dependências
│   ├── .env                         # Variáveis de ambiente (não versionado)
│   └── README.md                    # Este arquivo
│
├── 📊 Dashboard
│   ├── dashboard_funil.html         # Frontend do dashboard
│   ├── dashboard_funil_api.py       # Backend Flask (API REST)
│   └── DASHBOARD_FUNIL_README.md    # Documentação do dashboard
│
├── 📂 models/                       # Modelos de dados SQLAlchemy
│   ├── database.py                  # Definições de tabelas
│   └── api_schemas.py               # Schemas da API
│
├── 📂 services/                     # Serviços de negócio
│   ├── auth_service.py              # Autenticação JWT
│   ├── api_client.py                # Cliente HTTP API Inhire
│   ├── database_service.py          # Operações banco de dados
│   └── sync_service.py              # Orquestrador de sincronização
│
├── 📂 utils/                        # Utilitários
│   ├── logger.py                    # Sistema de logs
│   └── retry.py                     # Mecanismo de retry
│
├── 📂 migrations/                   # Migrações do banco de dados
├── 📂 scripts/                      # Scripts auxiliares
│   ├── diagnostics/                 # Scripts de diagnóstico
│   ├── maintenance/                 # Scripts de manutenção
│   ├── utilities/                   # Utilitários
│   └── tests/                       # Scripts de teste
│
├── 📂 docs/                         # Documentação completa
│   ├── README.md                    # Índice da documentação
│   ├── reports/                     # Relatórios de sessões
│   ├── guides/                      # Guias de uso
│   ├── analysis/                    # Análises técnicas
│   ├── changelogs/                  # Histórico de mudanças
│   └── resources/                   # Recursos (PDFs, ZIPs)
│
├── 📂 deprecated/                   # Arquivos obsoletos
├── 📂 tests/                        # Testes automatizados (pytest)
├── 📂 logs/                         # Arquivos de log
└── 📂 relatorios/                   # Relatórios gerados
```

---

## ⚙️ Configuração

### Arquivo .env

```env
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=inhire
DB_USER=postgres
DB_PASSWORD=sua_senha

# Inhire API
INHIRE_EMAIL=seu_email@inhire.app
INHIRE_PASSWORD=sua_senha
INHIRE_TENANT=seu_tenant

# Sincronização
SYNC_INCREMENTAL_FREQUENCY_MINUTES=60  # 1 hora
SYNC_FULL_FREQUENCY_HOURS=24           # 1 dia
SCHEDULER_FULL_SYNC_HOUR=2             # 02:00 AM

# Otimizações de Timeline (08/01/2026)
TIMELINE_DAYS_LOOKBACK=30              # Fallback para primeira sync (dias)
TIMELINE_MAX_WORKERS=10                # Threads paralelas (10x mais rápido)
```

---

## 🔧 Scripts Disponíveis

### Utilitários (scripts/utilities/)
- **check_sync_status.py** - Verifica status completo da sincronização
- **count_all_positions.py** - Conta posições por vaga
- **estimate_sync.py** - Estima tempo de sincronização

### Manutenção (scripts/maintenance/)
- **fix_candidatura_enum.py** - Corrige enum de status
- **fix_stuck_sync.py** - Corrige sincronizações travadas
- **verify_database_state.py** - Verifica integridade do banco
- **backup_tables_direct.py** - Backup de tabelas
- **fix_timezone_candidaturas.py** - Corrige timezone de candidaturas
- **check_inactive_candidaturas.py** - Verifica mudanças de status

### Testes (scripts/tests/)
- **test_db_connection.py** - Testa conexão com banco
- **test_inhire_auth.py** - Testa autenticação API
- **test_db_tables.py** - Verifica estrutura das tabelas

### Debug (scripts/diagnostics/)
- **debug_api.py** - Debug de chamadas API
- **analyze_positions.py** - Análise de posições

---

## 🔍 Monitoramento

### Ver Logs em Tempo Real
```bash
# Windows PowerShell
Get-Content "G:\Meu Drive\Framework_Data\Inhire\logs\inhire_sync.log" -Tail 50 -Wait

# Linux/Mac
tail -f logs/inhire_sync.log
```

### Consultas SQL Úteis

```sql
-- Últimas sincronizações
SELECT sync_type, sync_entity, status, start_time, records_processed
FROM sync_log
ORDER BY start_time DESC
LIMIT 10;

-- Total de registros por entidade
SELECT 'Vagas' as entidade, COUNT(*) FROM vagas
UNION ALL SELECT 'Posições', COUNT(*) FROM posicoes
UNION ALL SELECT 'Candidaturas', COUNT(*) FROM candidaturas
UNION ALL SELECT 'Talentos', COUNT(*) FROM talentos
UNION ALL SELECT 'Vaga Tags', COUNT(*) FROM vaga_tags
UNION ALL SELECT 'Form Responses', COUNT(*) FROM form_responses;

-- Candidaturas por status
SELECT status, COUNT(*) as total
FROM candidaturas
GROUP BY status
ORDER BY total DESC;
```

---

## 🔄 Ordem de Sincronização (Otimizada para BI)

O sistema **SEMPRE** respeita esta ordem para manter integridade referencial:

```
1º → VAGAS (independente)
      ↓
2º → POSIÇÕES (requer vagaId)
      ↓
3º → CANDIDATURAS (requer vagaId, fornece talentIds)
      ↓
4º → TIMELINE (requer candidatura)
      ↓
5º → TALENTOS (otimizado com talentIds)
      ↓
6º → SCORECARDS (requer candidatura)
      ↓
7º → VAGA TAGS (requer vaga)
      ↓
8º → REQUISIÇÕES (independente)
      ↓
9º → CLIENTES (independente)

❌ DESABILITADAS:
   • Talento Arquivos (CVs - não relevante para BI)
   • Form Responses (dados complexos, baixo valor analítico)
   • Automations (configuração do sistema, não dados de negócio)
```

**⚠️ IMPORTANTE**: Nunca altere esta ordem! As dependências devem ser respeitadas.

---

## 📚 Documentação Completa

**📖 Índice Completo:** [docs/README.md](docs/README.md)

### Documentação Principal (04/12/2025)
- **[Estratégia de Sincronização Final](docs/ESTRATEGIA_SYNC_FINAL.md)** - ⭐ Lógica definitiva implementada
- **[Relatório de Cobertura](docs/relatorio_cobertura_sync.md)** - Cobertura completa de todas as entidades
- **[Estrutura do Projeto](docs/PROJECT_STRUCTURE.md)** - Arquitetura detalhada
- **[Dashboard de Funil](DASHBOARD_FUNIL_README.md)** - Guia do dashboard

### Relatórios e Análises
- **[Mudanças 02/12/2025](docs/reports/RELATORIO_MUDANCAS_2025-12-02.md)** - Dashboard v2
- **[Organização Completa](docs/reports/ORGANIZATION_COMPLETE.md)** - Reorganização (19/11/2025)
- **[Correções Aplicadas](docs/reports/RELATORIO_CORRECOES.md)** - Histórico de correções

### Guias Técnicos
- **[Arquitetura do Sistema](docs/guides/ARQUITETURA_SISTEMA_INTEGRADO.md)** - Visão geral
- **[Guia de 3 Tipos de Sync](docs/guides/GUIA_3_TIPOS_SYNC.md)** - Comparação detalhada
- **[Deploy AWS](docs/guides/AWS_DEPLOY_GUIDE.md)** - Guia de produção

---

## ✅ Correções e Implementações Recentes

### 04/12/2025 - Sincronização Incremental Corrigida ⭐

**Problema Identificado:**
- ❌ Filtro de "últimos 7 dias" aplicado incorretamente
- ❌ Registros mais antigos não eram atualizados mesmo se mudassem
- ❌ Vaga Tags com erro de API method
- ❌ Form Responses desabilitado

**Correções Aplicadas:**
- ✅ **REMOVIDO**: Todos os filtros temporais arbitrários
- ✅ **IMPLEMENTADO**: Comparação individual `BD < API` para cada registro
- ✅ **CORRIGIDO**: Método API de Vaga Tags (`get_vaga_tags()`)
- ✅ **CORRIGIDO**: Campo do modelo (`tag_inhire_id` vs `inhire_id`)
- ✅ **HABILITADO**: Form Responses no EXPRESS mode
- ✅ **HABILITADO**: Todas as 10 entidades principais

**Resultado:**
- ✅ 1.953 registros processados em 9.5 minutos
- ✅ 31 tags criadas com sucesso
- ✅ 310 form responses sincronizados
- ✅ Taxa de sucesso 99.95%

📖 **Documentação:** [docs/ESTRATEGIA_SYNC_FINAL.md](docs/ESTRATEGIA_SYNC_FINAL.md)

### 02/12/2025 - Dashboard v2 & Filtros Completos

- ✅ Filtros de mês implementados (16/16 endpoints)
- ✅ Problema de datas resolvido (`updated_at_inhire`)
- ✅ Dashboard de Funil v2 com análises temporais

### 19/11/2025 - Enum "declined" e Reorganização

- ✅ Erro de enum "declined" corrigido
- ✅ Projeto completamente reorganizado
- ✅ Redução de 96% de arquivos .md na raiz

---

## 🚨 Solução de Problemas

### Sincronização não inicia
```bash
# 1. Verificar configuração
python -c "from config import settings; print(f'Sync Enabled: {settings.SYNC_ENABLED}')"

# 2. Testar autenticação
python scripts/tests/test_inhire_auth.py

# 3. Verificar status
python scripts/utilities/check_sync_status.py
```

### Sincronização travada
```bash
# Corrigir automaticamente
python scripts/maintenance/fix_stuck_sync.py
```

### Dados desatualizados
```bash
# Forçar sincronização completa
python run_sync.py --full
```

### Verificar Entidade Específica
```bash
# Exemplo: verificar candidaturas
python scripts/maintenance/verify_candidaturas_sync.py
```

---

## 📊 Performance

### Resultados Reais (08/01/2026)

| Modo | Tempo | Registros | Entidades | Uso |
|------|-------|-----------|-----------|-----|
| EXPRESS | **9.5 min** | 1.953 | 10 | Diário/horário |
| COMPLETO | **1.6 min** | 1.480 | 10 | A cada hora |
| FULL | ~55 min | ~100.000 | Todas | Mensal |

### Otimizações Implementadas
1. ✅ Comparação de datas ANTES de processar
2. ✅ Skip automático de registros não alterados
3. ✅ Filtro por status (apenas ativos)
4. ✅ UPSERT inteligente (create vs update)
5. ✅ Pool de conexões de banco
6. ✅ Índices otimizados
7. ✅ **Timeline Inteligente** - Processa apenas candidaturas modificadas após última sync
8. ✅ **Paralelização** - 10 threads paralelas para timeline (10x mais rápido)

### Volumes Esperados por Entidade
- **Vagas**: ~1.100 (25 processados, 1 atualizado)
- **Posições**: ~30 (6 processados, 0 atualizados)
- **Candidaturas**: ~3.300 (456 processados, 2 atualizados)
- **Timeline**: ~600 eventos (599 processados, 5 criados)
- **Talentos**: ~650 (145 processados, 0 atualizados)
- **Scorecards**: ~400 (381 processados, 0 atualizados)
- **Form Responses**: ~310 (310 processados, 309 atualizados)
- **Vaga Tags**: ~370 (31 processados, 31 criados)

---

## 🔒 Segurança

- Tokens JWT armazenados apenas em memória
- Senhas nunca logadas
- Conexão PostgreSQL com SSL (opcional)
- Validação de dados com Pydantic
- Variáveis sensíveis em `.env` (não versionado)

---

## 📞 Suporte

Para problemas:
1. ✅ Verificar `logs/inhire_sync.log`
2. ✅ Executar `python scripts/utilities/check_sync_status.py`
3. ✅ Revisar [docs/ESTRATEGIA_SYNC_FINAL.md](docs/ESTRATEGIA_SYNC_FINAL.md)
4. ✅ Consultar tabela `sync_log` no banco de dados

---

## 📝 Licença

Framework Digital - Uso Interno

---

## 🎯 Próximos Passos Sugeridos

1. ⏰ Configurar agendamento automático com `scheduler.py`
2. 📊 Ativar dashboard de métricas
3. 🔔 Configurar alertas de falha (opcional)
4. 📈 Monitorar performance por 1 semana
5. 🔧 Ajustar frequência de sincronização conforme necessidade

---

**Última atualização:** 08/01/2026
**Versão do Sistema:** 2.1 (Timeline Inteligente + Paralelização)
**Status:** ✅ Produção - 100% Funcional
