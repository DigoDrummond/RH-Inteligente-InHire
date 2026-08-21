# 📊 Melhorias Estruturais - InHire Database

**Data:** 19/11/2025
**Versão:** 1.0.0

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Migrations SQL](#migrations-sql)
3. [Views Materializadas](#views-materializadas)
4. [Sistema de Métricas](#sistema-de-métricas)
5. [Scripts de Relatórios](#scripts-de-relatórios)
6. [Guia de Uso](#guia-de-uso)
7. [API de Arquivos e Tags](#api-de-arquivos-e-tags)

---

## 🎯 Visão Geral

Este documento descreve as melhorias estruturais implementadas no banco de dados InHire para otimizar análises e relatórios de candidaturas, SLA, funil de conversão e taxas.

### Objetivos Alcançados

✅ Adicionar campos calculados automáticos
✅ Criar views materializadas para análises rápidas
✅ Implementar sistema de métricas pré-calculadas
✅ Desenvolver scripts Python para relatórios
✅ Criar exportador para Excel formatado
✅ Documentar estrutura e uso

---

## 🗄️ Migrations SQL

Três migrations foram criadas para aplicar as melhorias estruturais:

### Migration 001: Campos Calculados

**Arquivo:** `migrations/001_add_calculated_fields.sql`

#### Campos Adicionados:

- **`created_at_inhire`** (candidaturas): Data de criação original na API
- **`dias_no_processo`** (candidaturas): Dias desde a criação até agora
- **`dias_no_stage_atual`** (candidaturas): Dias no stage atual

#### Triggers Criados:

- **`trg_candidatura_insert_metrics`**: Calcula métricas ao inserir
- **`trg_candidatura_update_metrics`**: Recalcula ao atualizar

#### Índices Criados:

- `idx_candidatura_created_inhire`
- `idx_candidatura_tempo_metricas` (vaga_id, status, dias_no_processo)

#### Como Executar:

```bash
psql -U postgres -d inhire -f migrations/001_add_calculated_fields.sql
```

---

### Migration 002: Views Materializadas

**Arquivo:** `migrations/002_create_materialized_views.sql`

#### Views Criadas:

##### 1. `mv_funil_conversao`

Funil de conversão com taxas por stage.

**Colunas Principais:**
- `stage_order`, `stage_name`
- `total_candidatos`, `ativos`, `rejeitados`, `desistentes`, `contratados`
- `taxa_conversao_pct`, `taxa_rejeicao_pct`, `taxa_desistencia_pct`
- `media_dias_no_stage`, `mediana_dias_no_stage`

**Uso:**
```sql
SELECT * FROM mv_funil_conversao ORDER BY stage_order;
```

##### 2. `mv_kanban_dashboard`

Visão consolidada de kanban para vagas, posições e candidaturas.

**Colunas Principais:**
- `entidade` (VAGAS, POSICOES, CANDIDATURAS)
- `status`, `quantidade`
- `metrica_1`, `metrica_2`, `metrica_3`, `metrica_4`

**Uso:**
```sql
SELECT * FROM mv_kanban_dashboard WHERE entidade = 'CANDIDATURAS';
```

##### 3. `mv_sla_metrics`

Métricas de SLA para candidaturas ativas.

**Colunas Principais:**
- `candidatura_id`, `vaga_name`, `talent_name`
- `dias_no_processo`, `dias_no_stage_atual`
- `sla_days_goal`, `dias_atraso_sla`
- **`status_sla`**: OK, EM_ALERTA, ATRASADO, SEM_SLA
- `total_transicoes`, `dias_timeline_total`

**Uso:**
```sql
-- Candidaturas atrasadas
SELECT * FROM mv_sla_metrics
WHERE status_sla = 'ATRASADO'
ORDER BY dias_atraso_sla DESC;
```

##### 4. `mv_candidaturas_summary`

Resumo analítico de candidaturas agrupadas por vaga.

**Colunas Principais:**
- `vaga_id`, `vaga_name`, `vaga_area`, `vaga_seniority`
- `total_candidaturas`, `ativas`, `rejeitadas`, `desistidas`, `contratadas`
- `taxa_ativas_pct`, `taxa_rejeicao_pct`, `taxa_contratacao_pct`
- `media_dias_processo`, `mediana_dias_processo`
- **`status_performance`**: SUCESSO, EM_ANDAMENTO, FECHADA_SEM_SUCESSO, etc.

**Uso:**
```sql
-- Vagas com melhor performance
SELECT vaga_name, taxa_contratacao_pct, total_candidaturas
FROM mv_candidaturas_summary
WHERE contratadas > 0
ORDER BY taxa_contratacao_pct DESC
LIMIT 10;
```

#### Função de Refresh:

```sql
-- Atualizar todas as views de uma vez
SELECT refresh_all_materialized_views();
```

#### Como Executar:

```bash
psql -U postgres -d inhire -f migrations/002_create_materialized_views.sql
```

---

### Migration 003: Tabela de Métricas

**Arquivo:** `migrations/003_create_metrics_table.sql`

#### Tabela: `candidatura_metrics`

Armazena métricas pré-calculadas para cada candidatura.

**Estrutura:**

```sql
CREATE TABLE candidatura_metrics (
    id BIGSERIAL PRIMARY KEY,
    candidatura_id BIGINT NOT NULL UNIQUE,
    candidatura_inhire_id VARCHAR(255),
    vaga_id BIGINT,
    talento_id BIGINT,

    -- Métricas de Tempo
    dias_no_processo DECIMAL(10, 2),
    dias_no_stage_atual DECIMAL(10, 2),
    total_transicoes INTEGER,
    primeira_transicao_at TIMESTAMP,
    ultima_transicao_at TIMESTAMP,
    dias_timeline_total DECIMAL(10, 2),

    -- Métricas de Performance
    stages_percorridos INTEGER,
    tempo_medio_por_stage DECIMAL(10, 2),
    stage_com_maior_tempo VARCHAR(255),
    tempo_maior_stage DECIMAL(10, 2),

    -- SLA
    sla_days_goal INTEGER,
    dias_atraso_sla DECIMAL(10, 2),
    status_sla VARCHAR(50),  -- OK, EM_ALERTA, ATRASADO, SEM_SLA

    -- Classificação
    velocidade_processo VARCHAR(50),  -- RAPIDO, NORMAL, LENTO
    risco_abandono VARCHAR(50),       -- BAIXO, MEDIO, ALTO

    calculado_em TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Funções Criadas:

##### 1. `calculate_candidatura_metrics(candidatura_id)`

Calcula e armazena métricas para uma candidatura específica.

```sql
-- Exemplo de uso
SELECT calculate_candidatura_metrics(12345);
```

##### 2. `refresh_all_candidatura_metrics()`

Recalcula métricas para TODAS as candidaturas (usar com cautela).

```sql
-- Execução (pode demorar)
SELECT * FROM refresh_all_candidatura_metrics();
```

#### Trigger Automático:

Sempre que uma candidatura é inserida ou atualizada, as métricas são recalculadas automaticamente.

#### Como Executar:

```bash
psql -U postgres -d inhire -f migrations/003_create_metrics_table.sql
```

---

## 📊 Views Materializadas - Detalhes

### Performance e Otimização

#### Refresh Manual:

```sql
-- Refresh individual
REFRESH MATERIALIZED VIEW mv_funil_conversao;
REFRESH MATERIALIZED VIEW mv_kanban_dashboard;
REFRESH MATERIALIZED VIEW mv_sla_metrics;
REFRESH MATERIALIZED VIEW mv_candidaturas_summary;

-- Refresh concorrente (sem bloquear leitura)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_funil_conversao;
```

#### Refresh Automático:

Integrar com o `sync_service.py` para refresh após cada sincronização:

```python
# Adicionar no final do sync
db.execute("SELECT refresh_all_materialized_views();")
```

#### Índices:

Todas as views materializadas possuem índices otimizados para queries de alta performance.

---

## 🐍 Scripts de Relatórios

Cinco scripts Python foram desenvolvidos para geração de relatórios:

### 1. Funil de Candidaturas

**Arquivo:** `relatorios/funil_candidaturas.py`

**Funcionalidades:**
- Funil geral de conversão
- Funil por vaga específica
- Top vagas por conversão
- Pontos de abandono
- Resumo executivo

**Uso:**

```python
from relatorios.funil_candidaturas import FunilCandidaturasReport

report = FunilCandidaturasReport()

# Funil geral
df_funil = report.get_funil_geral()
print(df_funil)

# Resumo
summary = report.generate_summary()
print(f"Taxa de Contratação: {summary['taxa_contratacao_geral']}%")
```

**Executar via CLI:**

```bash
cd "G:\Meu Drive\Framework_Data\Inhire"
python relatorios/funil_candidaturas.py
```

---

### 2. Análise de SLA

**Arquivo:** `relatorios/analise_sla.py`

**Funcionalidades:**
- Resumo de SLA
- Candidaturas atrasadas
- Candidaturas em alerta
- Tempo médio por stage
- Performance de SLA por vaga
- Tempo entre transições

**Uso:**

```python
from relatorios.analise_sla import AnaliseSLAReport

report = AnaliseSLAReport()

# Resumo
resumo = report.get_resumo_sla()
print(f"Atrasados: {resumo['sla_atrasado']} ({resumo['pct_atrasado']}%)")

# Candidaturas atrasadas
df_atrasadas = report.get_candidaturas_atrasadas(50)
print(df_atrasadas)
```

**Executar via CLI:**

```bash
python relatorios/analise_sla.py
```

---

### 3. Taxas de Conversão

**Arquivo:** `relatorios/taxas_conversao.py`

**Funcionalidades:**
- Resumo geral de taxas
- Taxas por vaga
- Taxas por stage
- Taxas por área e senioridade
- Vagas com melhor/pior performance
- Evolução temporal

**Uso:**

```python
from relatorios.taxas_conversao import TaxasConversaoReport

report = TaxasConversaoReport()

# Resumo
resumo = report.get_resumo_geral()
print(f"Taxa de Rejeição: {resumo['taxa_rejeicao_pct']}%")

# Melhores vagas
df_melhores = report.get_vagas_melhor_performance(10)
print(df_melhores)
```

**Executar via CLI:**

```bash
python relatorios/taxas_conversao.py
```

---

### 4. Dashboard Consolidado

**Arquivo:** `relatorios/dashboard_consolidado.py`

**Funcionalidades:**
- KPIs principais
- Status de vagas
- Alertas críticos
- Top performers
- Tendências temporais
- Visão 360° integrada

**Uso:**

```python
from relatorios.dashboard_consolidado import DashboardConsolidado

dashboard = DashboardConsolidado()

# KPIs
kpis = dashboard.get_kpis_principais()
print(f"Total de Candidaturas: {kpis['total_candidaturas']:,}")

# Alertas
alertas = dashboard.get_alertas_criticos()
print(f"Candidaturas Atrasadas: {len(alertas['candidaturas_atrasadas'])}")

# Dashboard completo (JSON)
dashboard_completo = dashboard.generate_complete_dashboard()
```

**Executar via CLI:**

```bash
python relatorios/dashboard_consolidado.py
```

---

### 5. Exportador Excel

**Arquivo:** `relatorios/export_excel.py`

**Funcionalidades:**
- Exportação de relatório completo (múltiplas abas)
- Exportação de funil isolado
- Exportação de SLA isolado
- Formatação automática

**Uso:**

```python
from relatorios.export_excel import ExcelExporter

exporter = ExcelExporter(output_dir="exports")

# Relatório completo
filepath = exporter.export_relatorio_completo()
print(f"Relatório gerado: {filepath}")

# Apenas funil
filepath_funil = exporter.export_funil_only()

# Apenas SLA
filepath_sla = exporter.export_sla_only()
```

**Executar via CLI:**

```bash
python relatorios/export_excel.py
```

**Requisitos:**

```bash
pip install openpyxl
```

---

## 📖 Guia de Uso

### Passo 1: Executar Migrations

```bash
# Migration 001 - Campos Calculados
psql -U postgres -d inhire -f migrations/001_add_calculated_fields.sql

# Migration 002 - Views Materializadas
psql -U postgres -d inhire -f migrations/002_create_materialized_views.sql

# Migration 003 - Tabela de Métricas
psql -U postgres -d inhire -f migrations/003_create_metrics_table.sql
```

### Passo 2: Atualizar Views (Opcional)

```sql
-- Via SQL
SELECT refresh_all_materialized_views();
```

### Passo 3: Gerar Relatórios

```bash
# Relatório completo via CLI
python relatorios/dashboard_consolidado.py

# Exportar para Excel
python relatorios/export_excel.py
```

### Passo 4: Integrar com Sincronização

Editar `services/sync_service.py` e adicionar no final da sincronização:

```python
def sync_all(self, ...):
    # ... código existente ...

    # Refresh views materializadas após sincronização
    try:
        self.db_service.execute_raw("SELECT refresh_all_materialized_views();")
        logger.info("Views materializadas atualizadas")
    except Exception as e:
        logger.warning(f"Erro ao atualizar views: {e}")
```

---

## 🔍 API de Arquivos e Tags

### Investigação Realizada

Foi investigada a disponibilidade de endpoints para sincronizar **arquivos** (currículos) e **tags** (habilidades) dos talentos.

#### Resultados:

✅ **Estrutura existente**: Modelos `TalentoFile` e `TalentoTag` já definidos
✅ **Tabelas criadas**: `talento_arquivos` e `talento_tags`
✅ **Lógica de sync**: Função `_sync_talento_arquivos()` e `_sync_talento_tags()` implementadas

⚠️ **Status atual**: Tabelas vazias (0 registros)

#### Possíveis Causas:

1. API não retorna campos `files` e `tags` por padrão
2. Endpoint específico necessário para buscar anexos
3. Permissões de acesso podem ser necessárias
4. Dados podem não estar populados no InHire

#### Recomendação:

Verificar documentação oficial da API InHire ou entrar em contato com suporte para confirmar:
- Endpoint para buscar arquivos de talentos
- Endpoint para buscar tags/habilidades
- Parâmetros necessários nas requisições

#### Implementação Futura:

Se os endpoints forem confirmados, basta adicionar no `sync_service.py`:

```python
# Em sync_talentos()
if talento_api.files:
    self._sync_talento_arquivos(talento_db, talento_api.files)
if talento_api.tags:
    self._sync_talento_tags(talento_db, talento_api.tags)
```

---

## 📈 Indicadores Disponíveis

Com as melhorias implementadas, os seguintes indicadores estão disponíveis:

### Candidaturas
✅ Volume por vaga/período
✅ Distribuição por status
✅ Candidaturas por stage
✅ Tempo médio no processo

### Kanban
✅ Vagas por status (open, closed, canceled)
✅ Posições por status
✅ Pipeline de candidaturas (stage_name como colunas)

### Taxas
✅ Taxa de Aprovação
✅ Taxa de Rejeição
✅ Taxa de Desistência
✅ Taxa de Conversão entre stages
✅ Taxa de Contratação

### SLA
✅ Tempo total no processo
✅ Tempo por stage
✅ Tempo até aprovação/contratação
✅ Alertas de atraso
✅ Distribuição: OK, EM_ALERTA, ATRASADO

### Funil
✅ Jornada completa via timeline
✅ Conversão entre etapas
✅ Pontos de abandono
✅ Tempo em cada stage

---

## 🚀 Próximos Passos Recomendados

1. **Automatizar Refresh**: Integrar refresh de views com sincronização
2. **Dashboards Visuais**: Criar dashboards em Grafana/Metabase conectando ao PostgreSQL
3. **Alertas Automáticos**: Implementar notificações para candidaturas atrasadas
4. **APIs REST**: Expor métricas via FastAPI/Flask
5. **Popular Arquivos/Tags**: Confirmar endpoints da API InHire
6. **Testes Unitários**: Criar testes para os scripts de relatórios
7. **Scheduled Reports**: Agendar envio de relatórios por email

---

## 📝 Notas Finais

- Todas as migrations são **idempotentes** (podem ser executadas múltiplas vezes)
- Views materializadas devem ser **atualizadas periodicamente** para refletir novos dados
- Scripts Python foram desenvolvidos com **pandas** para facilitar análise e exportação
- Logs detalhados são gerados em `logs/inhire_sync.log`

---

**Documentação criada em:** 19/11/2025
**Última atualização:** 19/11/2025
**Versão:** 1.0.0
