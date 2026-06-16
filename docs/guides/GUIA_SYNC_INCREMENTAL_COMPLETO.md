# Guia Completo: Sincronização Incremental 100% Sem Timeout

**Versão:** 1.0
**Data:** 2026-02-27
**Autor:** Sistema de Sincronização Inhire

---

## Índice

- [1. Visão Geral](#1-visão-geral)
- [2. Características](#2-características)
- [3. Quando Usar](#3-quando-usar)
- [4. Pré-requisitos](#4-pré-requisitos)
- [5. Instalação e Configuração](#5-instalação-e-configuração)
- [6. Uso](#6-uso)
- [7. Modos de Operação](#7-modos-de-operação)
- [8. Interpretando os Resultados](#8-interpretando-os-resultados)
- [9. Troubleshooting](#9-troubleshooting)
- [10. Perguntas Frequentes](#10-perguntas-frequentes)
- [11. Referências](#11-referências)

---

## 1. Visão Geral

A **Sincronização Incremental Completa** é uma solução robusta para manter 100% dos dados do banco de dados atualizados com a API Inhire, sem risco de timeout.

### O Que é Sincronização Incremental?

Diferente da sincronização completa (que busca e processa TODOS os registros), a sincronização incremental:
- Busca apenas registros modificados desde a última sincronização
- Compara datas `updated_at` da API com o banco de dados
- Atualiza apenas registros que mudaram
- **Skip** em registros que já estão atualizados (98% dos casos)

### Benefícios

✅ **Rápida:** 10-25 minutos vs 55 minutos da sincronização completa
✅ **Sem timeout:** Timeouts estendidos e batch processing
✅ **100% de cobertura:** Todas as tabelas são sincronizadas
✅ **Robusta:** Sistema de alertas e interrupção em falhas
✅ **Validada:** Validações pré e pós-execução
✅ **Detalhada:** Relatório completo ao final

---

## 2. Características

### 2.1 Validações Automáticas

#### Pré-Execução
- ✓ Conexão com API Inhire
- ✓ Conexão com Banco de Dados PostgreSQL
- ✓ Configuração de sincronização existe
- ✓ Última sincronização válida

#### Pós-Execução
- ✓ Pelo menos 1 registro processado
- ✓ Taxa de falhas < 10%
- ✓ Integridade referencial (candidaturas → vagas/talentos)

### 2.2 Proteções Contra Timeout

| Proteção | Descrição | Valor |
|----------|-----------|-------|
| **Timeout Conectar** | Tempo para estabelecer conexão | 30s (vs 15s padrão) |
| **Timeout Leitura** | Tempo para ler resposta da API | 120s (vs 45s padrão) |
| **Batch Commits** | Commit a cada N registros | 50 registros |
| **Checkpoints** | Log de progresso a cada N | 100 registros |

### 2.3 Sistema de Alertas

- 🔴 **Falha Crítica:** Interrompe sincronização após N erros por entidade (padrão: 5)
- 🟡 **Aviso:** Registra erros não-críticos e continua
- 📊 **Relatório:** Resumo detalhado ao final com todas as estatísticas

### 2.4 Tabelas Sincronizadas

#### Dados de Negócio (Críticos)
1. **Vagas** - Jobs/Vagas abertas e fechadas
2. **Posições** - Posições dentro de cada vaga
3. **Position Timeline** - Histórico de mudanças de status das posições
4. **Candidaturas** - Aplicações de talentos às vagas
5. **Talentos** - Candidatos/Profissionais

#### Dados Complementares
6. **Requisições** - Aprovações de requisições
7. **Scorecard Interviews** - Avaliações de entrevistas
8. **Scorecard Jobs** - Avaliações de vagas
9. **Vaga Tags** - Tags associadas às vagas
10. **Clientes** - Clientes do tenant
11. **Custom Fields** - Campos personalizados

#### Dados Opcionais (Desabilitados por padrão)
- ~~Candidatura Timeline~~ (muito lento, problemas na API)
- ~~Talento Arquivos~~ (acesso direto no ATS é mais eficiente)
- ~~Form Responses~~ (dados complexos, baixo valor para BI)
- ~~Automations~~ (configuração do sistema, não dados de negócio)

---

## 3. Quando Usar

### Use Sincronização Incremental Completa Quando:

✅ Precisa de **100% dos dados atualizados**
✅ Tem pelo menos **1 sincronização completa** prévia
✅ Quer **garantir cobertura total** sem risco de timeout
✅ Precisa de **validações e alertas** robustos
✅ Quer **relatório detalhado** ao final

### NÃO Use Quando:

❌ É a **primeira sincronização** (use `sync_full()` primeiro)
❌ Precisa de **atualização em tempo real** (use `sync_express()`)
❌ Não se importa com **dados antigos** (use `sync_express()`)

### Comparação com Outros Tipos

| Tipo | Tempo | Cobertura | Quando Usar |
|------|-------|-----------|-------------|
| **Completa** | 55 min | 100% | 1ª carga, 1x/semana |
| **Incremental Completa** | 15-25 min | 100% | Manutenção geral |
| **Express** | 3-5 min | Vagas ativas | Atualização frequente |

---

## 4. Pré-requisitos

### 4.1 Software

- Python 3.8+
- PostgreSQL 12+
- Acesso à API Inhire

### 4.2 Credenciais

Configurar no arquivo `.env`:

```env
# API Inhire
INHIRE_EMAIL=seu_email@empresa.com
INHIRE_PASSWORD=sua_senha
INHIRE_TENANT=seu_tenant_id

# Banco de Dados
DB_HOST=localhost
DB_PORT=5432
DB_NAME=inhire
DB_USER=postgres
DB_PASSWORD=sua_senha_bd
```

### 4.3 Sincronização Prévia

**IMPORTANTE:** Deve ter executado pelo menos 1 sincronização completa antes:

```bash
# Primeira vez (obrigatório)
python run_sync.py --full

# Depois pode usar incremental completa
python sync_incremental_completo.py --completa
```

---

## 5. Instalação e Configuração

### 5.1 Verificar Instalação

```bash
# 1. Verificar Python
python --version  # Deve ser 3.8+

# 2. Verificar dependências
pip install -r requirements.txt

# 3. Validar configurações
python config.py

# 4. Testar conexão BD
python health_check.py
```

### 5.2 Configurações Opcionais

Editar `.env` para ajustar timeouts e limites:

```env
# Timeouts estendidos (padrão já é robusto)
SYNC_INCREMENTAL_TIMEOUT_CONNECT=30      # 30 segundos para conectar
SYNC_INCREMENTAL_TIMEOUT_READ=120        # 120 segundos para ler resposta
SYNC_INCREMENTAL_TIMEOUT_TOTAL=180       # 180 segundos timeout total

# Batch processing (ajustar se necessário)
SYNC_INCREMENTAL_COMMIT_BATCH=50         # Commit a cada 50 registros
SYNC_INCREMENTAL_LOG_PROGRESS_EVERY=100  # Log a cada 100 registros

# Sistema de alertas
SYNC_INCREMENTAL_FAIL_ON_ERROR=True               # Interromper em erro crítico
SYNC_INCREMENTAL_VALIDATE_INTEGRITY=True          # Validar integridade pós-sync
SYNC_INCREMENTAL_MAX_ERRORS_PER_ENTITY=5          # Máx erros por entidade
```

---

## 6. Uso

### 6.1 Uso Básico

```bash
# Sincronização completa 100% (RECOMENDADO)
python sync_incremental_completo.py --completa

# Com confirmação automática (sem prompt)
python sync_incremental_completo.py --completa --yes
```

### 6.2 Opções Disponíveis

```bash
# Ver ajuda
python sync_incremental_completo.py --help

# Modo express (mais rápido, pula entidades secundárias)
python sync_incremental_completo.py --express

# Simulação (dry-run) - não grava dados
python sync_incremental_completo.py --completa --dry-run

# Sem validações (NÃO RECOMENDADO)
python sync_incremental_completo.py --completa --no-validation
```

### 6.3 Exemplos de Uso

#### Exemplo 1: Sincronização Completa Padrão

```bash
$ python sync_incremental_completo.py --completa

╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║        SINCRONIZAÇÃO INCREMENTAL COMPLETA - INHIRE API → BD              ║
║                                                                          ║
║  Cobertura: 100% de todas as tabelas                                    ║
║  Timeout: Estendido (sem timeout)                                       ║
║  Alertas: Interrompe em caso de falha crítica                           ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝

Validando configurações...
✓ Configurações válidas

================================================================================
INFORMAÇÕES DA SINCRONIZAÇÃO
================================================================================
Modo:              COMPLETA 100%
Tenant:            seu_tenant_id
Ambiente:          production
Banco de Dados:    localhost:5432/inhire
API Base URL:      https://api.inhire.app/
Timeout Conectar:  30s
Timeout Leitura:   120s
Batch Size:        50
Max Erros/Entid.:  5
================================================================================

Última sincronização: 2026-02-27 10:30:00 UTC (2.5h atrás)

Duração estimada: 15-25 minutos

ATENÇÃO: Esta sincronização irá:
  1. Conectar à API Inhire
  2. Buscar dados de TODAS as tabelas
  3. Atualizar o banco de dados
  4. Interromper em caso de falha crítica

Deseja continuar? (sim/não): sim

================================================================================
EXECUTANDO SINCRONIZAÇÃO
================================================================================

[...logs detalhados de progresso...]

================================================================================
✓ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO
================================================================================
Duração real: 1234.56s (20.58 minutos)
Status: SUCCESS
Estatísticas: {'processed': 15243, 'created': 52, 'updated': 387, 'skipped': 14804, 'failed': 0}
================================================================================
```

#### Exemplo 2: Dry-Run (Simulação)

```bash
$ python sync_incremental_completo.py --completa --dry-run

[...banner e informações...]

================================================================================
MODO DRY-RUN - Simulando sincronização...
================================================================================

Neste modo, a sincronização seria executada com:
  - Modo: COMPLETA 100%
  - Validações: Habilitadas
  - Cobertura: 100% de todas as tabelas
  - Duração estimada: 15-25 minutos

Nenhum dado foi gravado no banco de dados.
```

---

## 7. Modos de Operação

### 7.1 Modo COMPLETA (Recomendado)

```bash
python sync_incremental_completo.py --completa
```

**Características:**
- Sincroniza **100% de todas as tabelas**
- Validações pré e pós-execução
- Timeouts estendidos
- Sistema de alertas robusto
- Duração: 15-25 minutos

**Quando usar:**
- Manutenção geral dos dados
- Garantir 100% de cobertura
- Após alterações estruturais
- 1-2x por dia

### 7.2 Modo EXPRESS

```bash
python sync_incremental_completo.py --express
```

**Características:**
- Sincroniza apenas **entidades críticas**
- Pula entidades secundárias (scorecards, tags, clientes)
- Validações opcionais
- Duração: 10-15 minutos

**Quando usar:**
- Atualização rápida
- Foco em vagas e candidaturas
- Execução frequente (a cada 2-4h)

### 7.3 Comparação de Modos

| Característica | COMPLETA | EXPRESS |
|----------------|----------|---------|
| Vagas | ✅ | ✅ |
| Posições | ✅ | ✅ |
| Position Timeline | ✅ | ✅ |
| Candidaturas | ✅ | ✅ |
| Talentos | ✅ | ✅ |
| Requisições | ✅ | ✅ |
| Scorecards | ✅ | ✅ |
| Tags | ✅ | ❌ |
| Clientes | ✅ | ❌ |
| Custom Fields | ✅ | ❌ |
| **Duração** | 15-25 min | 10-15 min |
| **Cobertura** | 100% | ~85% |

---

## 8. Interpretando os Resultados

### 8.1 Relatório de Sucesso

```
================================================================================
RELATÓRIO DE SINCRONIZAÇÃO INCREMENTAL COMPLETA
================================================================================

Duração: 1234.56 segundos (20.58 minutos)

ESTATÍSTICAS:
  Total Processado: 15,243
  Criados:          52
  Atualizados:      387
  Pulados (skip):   14,804
  Falhas:           0

Taxa de Skip:     97.12%
Taxa de Falhas:   0.00%

================================================================================
```

### 8.2 Interpretação das Estatísticas

| Métrica | Significado | Valor Esperado |
|---------|-------------|----------------|
| **Total Processado** | Registros analisados | Depende do volume de dados |
| **Criados** | Novos registros inseridos | Baixo (apenas novos itens) |
| **Atualizados** | Registros modificados | Variável (0-10%) |
| **Pulados (skip)** | Registros já atualizados | Alto (90-99%) |
| **Falhas** | Erros durante processamento | 0 (ideal) ou < 1% |

### 8.3 Taxa de Skip

**Taxa de Skip Alta (95-99%)** = 🟢 **BOM**
- Poucas mudanças desde última sync
- Banco de dados já está atualizado
- Sincronização eficiente

**Taxa de Skip Média (50-94%)** = 🟡 **NORMAL**
- Mudanças moderadas
- Primeira sync após muito tempo
- Válido

**Taxa de Skip Baixa (0-49%)** = 🟠 **ATENÇÃO**
- Muitas mudanças ou primeira sync incremental
- Considerar se sync completa seria mais adequada

### 8.4 Relatório de Erro

```
================================================================================
✗ SINCRONIZAÇÃO FALHOU
================================================================================
Duração até falha: 456.78s (7.61 minutos)
Erro: Muitos erros em CANDIDATURAS (>5). Interrompendo sincronização.

ERROS ENCONTRADOS (8 total):
CANDIDATURAS: 6 erros
  1. Timeout ao buscar candidaturas da vaga 1234
  2. Erro de validação: talent_id não encontrado
  [...]

VAGAS: 2 erros
  1. Erro ao processar custom_fields da vaga 5678
  2. Timeout na API
================================================================================
```

---

## 9. Troubleshooting

### 9.1 Erro: "Nenhuma sincronização anterior encontrada"

**Causa:** Nunca executou sincronização completa antes.

**Solução:**
```bash
# Execute sincronização completa primeiro
python run_sync.py --full

# Depois pode usar incremental
python sync_incremental_completo.py --completa
```

### 9.2 Erro: "Falha na conexão com API"

**Possíveis causas:**
1. Credenciais inválidas
2. Token expirado
3. API Inhire fora do ar

**Solução:**
```bash
# 1. Verificar credenciais no .env
cat .env | grep INHIRE_

# 2. Testar autenticação
python -c "from services.api_client import InhireAPIClient; client = InhireAPIClient(); client.authenticate(); print('✓ OK')"

# 3. Verificar status da API
curl https://api.inhire.app/health
```

### 9.3 Erro: "Timeout ao buscar dados"

**Causa:** API lenta ou muitos dados.

**Solução:**
```bash
# 1. Aumentar timeouts no .env
SYNC_INCREMENTAL_TIMEOUT_READ=180  # 3 minutos

# 2. Reduzir batch size
SYNC_BATCH_SIZE=25  # Processar menos de cada vez

# 3. Tentar novamente (API pode ter ficado mais rápida)
python sync_incremental_completo.py --completa
```

### 9.4 Erro: "Taxa de falhas muito alta: 15%"

**Causa:** Muitos erros durante sincronização.

**Solução:**
```bash
# 1. Ver logs detalhados
tail -f logs/inhire_sync.log

# 2. Identificar tabela problemática
grep "ERROR" logs/inhire_sync.log | sort | uniq -c

# 3. Sincronizar apenas tabela problemática
python run_sync.py --entity vagas  # exemplo

# 4. Se persistir, executar sync completa
python run_sync.py --full
```

### 9.5 Erro: "Integridade referencial: candidaturas sem vaga"

**Causa:** Dados inconsistentes entre tabelas.

**Solução:**
```bash
# 1. Executar sync completa para corrigir
python run_sync.py --full

# 2. Verificar integridade manualmente
python scripts/debug/verificar_integridade.py

# 3. Limpar dados órfãos (cuidado!)
python scripts/cleanup/limpar_orfaos.py --dry-run
```

### 9.6 Performance Lenta (>30 minutos)

**Possíveis causas:**
1. API Inhire lenta
2. Banco de dados lento
3. Muitos dados para processar

**Solução:**
```bash
# 1. Verificar performance da API
python scripts/debug/test_api_performance.py

# 2. Verificar índices do banco
python scripts/debug/check_database_indexes.py

# 3. Usar modo express temporariamente
python sync_incremental_completo.py --express

# 4. Aumentar workers (cuidado com rate limit)
# No .env:
SYNC_MAX_WORKERS=10  # Processar mais em paralelo
```

---

## 10. Perguntas Frequentes

### Q1: Qual a diferença entre sync incremental e sync completa?

**R:**
- **Sync Completa:** Busca e processa TODOS os registros (100% sempre, 55 min)
- **Sync Incremental:** Busca todos, mas compara datas e pula registros já atualizados (98% skip, 15-25 min)

### Q2: Posso executar sync incremental sem ter feito sync completa antes?

**R:** Não. A sync incremental depende de ter uma data de referência (`last_sync`). Na primeira vez, execute:
```bash
python run_sync.py --full
```

### Q3: Com que frequência devo executar?

**R:**
- **Sync Incremental Completa:** 1-2x por dia
- **Sync Express:** A cada 2-4 horas
- **Sync Completa:** 1x por semana (validação)

### Q4: E se a sincronização falhar no meio?

**R:** O sistema possui:
- ✅ Batch commits (registros já processados são salvos)
- ✅ Logs detalhados (pode identificar onde parou)
- ✅ Pode reexecutar (só processará o que falta)

### Q5: Posso executar em horário comercial?

**R:** Sim, mas:
- ✅ Modo EXPRESS é seguro a qualquer hora
- ⚠️ Modo COMPLETA pode gerar carga no BD (preferir horário de baixo uso)

### Q6: Como agendar execução automática?

**R:** Use o scheduler integrado ou cron:

```bash
# Opção 1: Scheduler integrado (recomendado)
# Editar scheduler.py e adicionar:
scheduler.add_job(
    lambda: run_sync_incremental_completo(),
    'cron',
    hour='8,14,20',  # 08:00, 14:00, 20:00
    id='sync_incremental_completa'
)

# Opção 2: Cron (Linux/Mac)
crontab -e
# Adicionar:
0 8,14,20 * * * cd /path/to/inhire && python sync_incremental_completo.py --completa --yes >> logs/cron.log 2>&1
```

### Q7: O que fazer se taxa de skip for muito baixa?

**R:** Taxa de skip baixa (<50%) indica:
- Primeira sync incremental após muito tempo
- Muitas mudanças nos dados
- Problema com comparação de datas

**Solução:** Execute sync completa para "resetar":
```bash
python run_sync.py --full
```

### Q8: Posso cancelar durante execução (Ctrl+C)?

**R:** Sim, é seguro. O sistema:
- ✅ Captura Ctrl+C gracefully
- ✅ Salva progresso até o ponto atual (batch commits)
- ✅ Pode reexecutar depois (continuará do último batch)

### Q9: Como ver o progresso em tempo real?

**R:**
```bash
# Terminal 1: Executar sync
python sync_incremental_completo.py --completa

# Terminal 2: Acompanhar logs
tail -f logs/inhire_sync.log
```

### Q10: Qual o consumo de recursos?

**R:**
- **CPU:** Baixo (5-10% durante execução)
- **Memória:** ~500MB-1GB
- **Rede:** ~100-500MB download da API
- **Banco:** Baixo (batch commits, índices otimizados)

---

## 11. Referências

### Documentação Relacionada

- [Guia de 3 Tipos de Sync](./GUIA_3_TIPOS_SYNC.md)
- [Estratégia Sync Baseada em Tabelas](./ESTRATEGIA_SYNC_BASEADA_EM_TABELAS.md)
- [Comparação dos 3 Tipos de Sync](../analysis/COMPARACAO_3_TIPOS_SYNC.md)
- [Changelog Sync Incremental Otimizada](../changelogs/CHANGELOG_2026-02-11_SYNC_INCREMENTAL_OTIMIZADA.md)

### Arquivos do Sistema

- `sync_incremental_completo.py` - Script de execução manual
- `services/sync_service.py` - Lógica de sincronização
- `config.py` - Configurações do sistema
- `.env` - Credenciais e configurações

### Comandos Úteis

```bash
# Validar configurações
python config.py

# Verificar saúde do sistema
python health_check.py

# Ver logs
tail -f logs/inhire_sync.log

# Testar conexão API
python -c "from services.api_client import InhireAPIClient; InhireAPIClient().authenticate()"

# Verificar última sincronização
python -c "from services.database_service import DatabaseService; from models.database import get_session; session = get_session(); db = DatabaseService(session); config = db.get_sync_configuration('seu_tenant'); print(f'Última sync: {config.last_incremental_sync}')"
```

---

## Suporte

Para problemas não cobertos por este guia:

1. Verifique os logs em `logs/inhire_sync.log`
2. Consulte a documentação adicional em `docs/`
3. Execute diagnósticos com scripts em `scripts/debug/`

---

**Última atualização:** 2026-02-27
**Versão do Sistema:** 2.0
