# Relatório: Cobertura da API InHire

**Data:** 2026-02-06
**Objetivo:** Analisar se estamos extraindo as principais informações da API InHire e verificar dados de indicação

---

## 1. RESUMO EXECUTIVO

✅ **COBERTURA GERAL: BOA**

- **10 de 17 entidades** do glossário InHire sincronizadas (58.8%)
- **Todas as entidades CRÍTICAS e de ALTA IMPORTÂNCIA** estão sincronizadas
- **Campo `source` 100% preenchido** (82.584 candidaturas)
- **Indicações identificadas:** 2.040 candidaturas (2.5% do total)

---

## 2. ENTIDADES SINCRONIZADAS

### ✅ CRÍTICAS (100% cobertura)

| Entidade | Tabela | Status | Registros |
|----------|--------|--------|-----------|
| JOB / VAGA | `vagas` | ✅ Sincronizado | 1.167 |
| POSITION / POSIÇÃO | `posicoes` | ✅ Sincronizado | 831+ |
| TALENT / TALENTO | `talentos` | ✅ Sincronizado | ~50k |
| JOB_TALENT / CANDIDATO | `candidaturas` | ✅ Sincronizado | 82.584 |

### ✅ ALTA IMPORTÂNCIA (100% cobertura)

| Entidade | Tabela | Status |
|----------|--------|--------|
| REQUISITION | `requisicoes` | ✅ Sincronizado |
| CLIENTS | `clientes` | ✅ Sincronizado |
| CUSTOM_FIELDS | JSONB em várias tabelas | ✅ Sincronizado |
| POSITION_TIMELINE | `position_timeline` | ✅ Sincronizado |
| CANDIDATURA_TIMELINE | `candidatura_timeline` | ✅ Sincronizado |

### ⚠️ MÉDIA IMPORTÂNCIA (parcialmente coberto)

| Entidade | Status | Prioridade |
|----------|--------|------------|
| **REFERRAL / INDICAÇÃO** | ⚠️ **Dados indiretos via `source`** | **ALTA** |
| TEST / TESTE | ❌ Não sincronizado | MÉDIA |
| STAGE / ETAPA | ✅ Dados em `candidaturas` | BAIXA |

### ❌ BAIXA IMPORTÂNCIA (não essencial agora)

- JOB_PAGE
- FORM / FORMULÁRIO
- DIVERSITY_FORM
- SCORECARD
- INTERVIEW_KIT
- OFFER_LETTER
- WORKFLOW

---

## 3. INFORMAÇÕES DE INDICAÇÃO ⭐

### ✅ SITUAÇÃO ATUAL: DADOS DISPONÍVEIS

**Campo `source` em candidaturas:**
- ✅ **100% preenchido** (82.584 de 82.584 candidaturas)
- ✅ **18 valores únicos** identificando canais de origem

### 📊 Distribuição de Indicações

| Source | Quantidade | % do Total | Tipo |
|--------|------------|------------|------|
| **referral** | **1.440** | **1.7%** | 🎯 **Indicação** |
| **direct-referral** | **577** | **0.7%** | 🎯 **Indicação Direta** |
| **employee** | **23** | **0.0%** | 🎯 **Colaborador** |
| **TOTAL INDICAÇÕES** | **2.040** | **2.5%** | ✅ |

### 📊 Outros Canais de Origem

| Canal | Quantidade | % |
|-------|------------|---|
| LinkedIn | 34.313 | 41.6% |
| Manual | 27.295 | 33.0% |
| Job Page | 13.856 | 16.8% |
| NetVagas | 2.224 | 2.7% |
| Gupy | 1.767 | 2.1% |
| Indeed | 993 | 1.2% |
| Outros | 96 | 0.1% |

### ⚠️ LIMITAÇÕES ATUAIS

**O que TEMOS:**
- ✅ Identificação se é indicação (`source = 'referral'` ou `'direct-referral'`)
- ✅ 100% de cobertura do campo

**O que NÃO TEMOS (mas seria valioso):**
- ❌ **Quem indicou** (referrer_id, referrer_name)
- ❌ **Bônus de indicação** (referral_bonus)
- ❌ **Status da indicação** (aprovada, paga, etc.)
- ❌ **Link de indicação usado** (referral_link_id)

---

## 4. CAMPOS IMPORTANTES POR ENTIDADE

### ✅ CANDIDATURAS (muito completa)

| Campo | Status | Observação |
|-------|--------|-----------|
| source | ✅ 100% | **Identifica indicações!** |
| stage_name | ✅ | Etapa do funil |
| stage_order | ✅ | Ordem numérica |
| status | ✅ | active/inactive/disqualified |
| time_in_current_stage | ✅ | Tempo na etapa |
| talent_name | ✅ | Nome do candidato |
| talent_email | ✅ | Email do candidato |
| user_name | ✅ | Recrutador responsável |
| **referrer_id** | ❌ | **Falta: quem indicou** |
| **referrer_name** | ❌ | **Falta: nome de quem indicou** |
| **test_score** | ❌ | Falta: nota do teste |
| **interview_score** | ❌ | Falta: nota da entrevista |

### ✅ TALENTOS (boa cobertura)

| Campo | Status | Observação |
|-------|--------|-----------|
| name | ✅ | Nome |
| email | ✅ | Email |
| phone | ✅ | Telefone |
| linkedin_username | ✅ | LinkedIn |
| diversity_* | ✅ | 5 campos de diversidade |
| resume | ✅ | Currículo em texto |
| **source** | ❌ | **Falta: origem do talento** |
| **referred_by** | ❌ | **Falta: quem indicou** |
| **resume_url** | ❌ | Falta: URL do arquivo |
| **portfolio_url** | ❌ | Falta: portfólio |

### ✅ VAGAS (muito completa)

| Campo | Status | Observação |
|-------|--------|-----------|
| name | ✅ | Nome da vaga |
| seniority | ✅ | Nível |
| area | ✅ | Área |
| custom_fields | ✅ | 32 campos customizados |
| sla_days_goal | ✅ | Meta de prazo |
| user_name | ✅ | Recrutador |
| **job_page_url** | ❌ | Falta: URL divulgação |
| **visibility** | ❌ | Falta: pública/privada |
| **workflow_id** | ❌ | Falta: automação |

### ✅ POSIÇÕES (completa)

| Campo | Status | Observação |
|-------|--------|-----------|
| status | ✅ | open/closed/canceled/paused |
| opened_at | ✅ | Data abertura |
| hired_at | ✅ | Data contratação |
| reason | ✅ | Motivo contratação |
| position_timeline | ✅ | Histórico completo |

### ✅ REQUISIÇÕES (completa)

| Campo | Status | Observação |
|-------|--------|-----------|
| requested_at | ✅ | Data solicitação |
| user_name | ✅ | Solicitante |
| custom_fields | ✅ | Campos customizados |

---

## 5. DADOS DE VALOR QUE ESTAMOS CAPTURANDO

### ✅ MÉTRICAS DE FUNIL

- ✅ Etapas do processo (stage_name, stage_order)
- ✅ Tempo em cada etapa (time_in_current_stage)
- ✅ Histórico de mudanças (candidatura_timeline)
- ✅ Status final (contratado, descartado, ativo)

### ✅ MÉTRICAS DE SLA E PERFORMANCE

- ✅ Data abertura, publicação, contratação
- ✅ Meta de prazo (sla_days_goal)
- ✅ Histórico de pausas (position_timeline)
- ✅ Múltiplos ciclos de pausa/retorno
- ✅ Cálculo de SLA geral, recrutamento, pendências

### ✅ ORIGEM E CONVERSÃO

- ✅ **Canal de origem** (source): LinkedIn, indicação, job boards
- ✅ Cliente/empresa solicitante
- ✅ Torre/área de negócio
- ✅ Recrutador responsável
- ✅ Gestor da vaga

### ✅ DIVERSIDADE

- ✅ 5 campos: negro, mulher, LGBT, PcD, trans
- ✅ Permite análise de DEI

### ⚠️ LIMITAÇÕES (dados valiosos não capturados)

- ❌ **Detalhes de indicação** (quem indicou, bônus)
- ❌ **Notas de testes** (aprovação, pontuação)
- ❌ **Scorecards** (avaliação estruturada)
- ❌ **Salário oferecido** (faixa salarial, pretensão)
- ❌ **Entrevistas** (feedback, notas)

---

## 6. RECOMENDAÇÕES

### 🔴 PRIORIDADE ALTA (implementar agora)

#### 1. Adicionar Campo `source` na View de Análise

**Ação:**
```sql
ALTER VIEW vw_analise_posicoes ADD COLUMN
    source_candidato VARCHAR  -- origem: linkedin, referral, etc
```

**Valor:**
- Análise de conversão por canal
- ROI de cada canal de divulgação
- Identificação de indicações
- Benchmarking de fontes

**Impacto:**
- 28 → 29 colunas
- 2.5% dos candidatos identificados como indicação
- Permite filtrar e analisar programa de indicações

#### 2. Adicionar Campo Calculado `is_referral`

**Ação:**
```sql
ALTER VIEW vw_analise_posicoes ADD COLUMN
    is_referral BOOLEAN  -- TRUE se source contém 'referral' ou 'employee'
```

**Valor:**
- Facilita filtros e análises
- Dashboard de indicações
- Comparação indicação vs outros canais

### 🟡 PRIORIDADE MÉDIA (próximas iterações)

#### 3. Investigar Endpoint `/referrals` na API

**Objetivo:** Verificar se existe endpoint específico para programa de indicações

**Campos esperados:**
- `referrer_id` - quem indicou
- `referrer_name` - nome
- `referee_id` - quem foi indicado
- `referral_status` - aprovado, contratado, bonus pago
- `referral_bonus` - valor do bônus
- `referral_link_id` - link usado

**Se existir:** Criar tabela `referrals` e sincronizar

#### 4. Adicionar Campos de Testes (se disponível na API)

**Campos:**
- `test_id` - ID do teste aplicado
- `test_score` - nota obtida
- `test_status` - aprovado/reprovado
- `test_completed_at` - data conclusão

**Valor:** Análise de correlação entre nota do teste e contratação

#### 5. Adicionar Salário/Pretensão (se disponível)

**Campos:**
- `salary_expectation` - pretensão salarial
- `salary_offered` - salário oferecido
- `salary_range_min` - faixa mínima
- `salary_range_max` - faixa máxima

**Valor:** Análise de compatibilidade, negociação, budget

### 🟢 PRIORIDADE BAIXA (futuro)

- Scorecards (avaliação estruturada)
- Interview Kits (roteiros de entrevista)
- Job Pages (configuração de divulgação)
- Workflows (automações)
- Offer Letters (cartas proposta)

---

## 7. ANÁLISE DE VALOR vs ESFORÇO

### ✅ ALTO VALOR, BAIXO ESFORÇO

| Item | Esforço | Valor | Status |
|------|---------|-------|--------|
| Adicionar `source` na view | 🟢 Baixo | ⭐⭐⭐ Alto | **Recomendado agora** |
| Adicionar `is_referral` calculado | 🟢 Baixo | ⭐⭐ Médio | **Recomendado agora** |

### ✅ ALTO VALOR, MÉDIO ESFORÇO

| Item | Esforço | Valor | Status |
|------|---------|-------|--------|
| Investigar endpoint `/referrals` | 🟡 Médio | ⭐⭐⭐ Alto | Próxima iteração |
| Adicionar testes (se API tiver) | 🟡 Médio | ⭐⭐ Médio | Próxima iteração |

### ⚠️ MÉDIO VALOR, ALTO ESFORÇO

| Item | Esforço | Valor | Status |
|------|---------|-------|--------|
| Scorecards | 🔴 Alto | ⭐⭐ Médio | Avaliar necessidade |
| Salário/pretensão | 🔴 Alto | ⭐⭐ Médio | Avaliar disponibilidade |

### ❌ BAIXO VALOR (não priorizar)

- Job Pages, Forms, Workflows, Offer Letters

---

## 8. CONCLUSÃO

### ✅ PONTOS FORTES

1. **Cobertura excelente** das entidades críticas (100%)
2. **Campo `source` 100% preenchido** - raro em integrações!
3. **Indicações identificáveis** - 2.040 candidaturas (2.5%)
4. **Timeline completo** de posições e candidaturas
5. **Métricas de SLA** calculadas e precisas
6. **Custom fields** capturando dados específicos
7. **Dados de diversidade** para análise DEI

### ⚠️ OPORTUNIDADES DE MELHORIA

1. **Adicionar `source` na view** de análise (alto valor, baixo esforço)
2. **Investigar detalhes de indicação** (quem indicou, bônus)
3. **Considerar testes** se API disponibilizar
4. **Avaliar salário/pretensão** se for relevante

### 🎯 RECOMENDAÇÃO FINAL

**Estamos capturando as PRINCIPAIS informações de valor da API InHire.**

As lacunas identificadas são secundárias ou dependem de investigação adicional da API. A prioridade imediata deve ser:

1. ✅ **Adicionar campo `source` na view** (implementar já!)
2. ✅ **Adicionar campo `is_referral` calculado**
3. 🔍 Investigar endpoint `/referrals` na documentação da API
4. 🔍 Verificar disponibilidade de dados de testes

**Status geral:** ⭐⭐⭐⭐ (4/5 estrelas)

---

## ANEXO: Campos de Custom_Fields das Vagas

**Total de chaves únicas:** 32

Lista completa disponível via query:
```sql
SELECT DISTINCT jsonb_object_keys(custom_fields) FROM vagas;
```

Alguns exemplos capturados:
- Tipo
- Torre
- Área
- Gestor
- Senioridade
- Motivo de Cancelamento
- Modalidade de Contratação
- Se substituição, informar nome...
- Classificação
- E outros 23 campos personalizados
