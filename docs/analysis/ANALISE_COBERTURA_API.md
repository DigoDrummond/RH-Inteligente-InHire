# Análise de Cobertura da API InHire

## 📊 Resumo Executivo

**Data da Análise:** 19/11/2025

Este documento analisa a cobertura atual da sincronização em relação a todos os dados disponíveis na API InHire.

---

## ✅ Dados ATUALMENTE Sincronizados

### 1. Vagas (Jobs) ✓
**Endpoint:** `POST /jobs/paginated/lean`
- ✅ **Status:** Sincronizado completamente
- **Dados capturados:**
  - ID, nome, descrição, status
  - Datas de criação e atualização
  - Configurações da vaga
  - Metadados

### 2. Posições (Positions) ✓
**Endpoint:** `GET /jobs/positions/paginated/{job_id}`
- ✅ **Status:** Sincronizado completamente
- **Dados capturados:**
  - ID da posição
  - Vaga relacionada (jobId)
  - Status da posição
  - Datas de criação e atualização

### 3. Candidaturas (Applications/JobTalents) ✓
**Endpoint:** `POST /job-talents/{job_id}/talents/paginated/lean`
- ✅ **Status:** Sincronizado completamente
- **Dados capturados:**
  - ID composto (jobId*talentId)
  - Status da candidatura
  - Stage e phase atuais
  - Datas de criação e atualização
  - Informações de matching

### 4. Talentos (Talents) ✓
**Endpoint:** `POST /talents/paginated`
**Endpoint:** `GET /talents/{talent_id}`
- ✅ **Status:** Sincronizado completamente
- **Dados capturados:**
  - Dados pessoais (nome, email, telefone)
  - Informações profissionais
  - Skills e competências
  - Datas de criação e atualização

### 5. Timeline de Candidaturas ✓ (Parcial)
**Endpoint:** `GET /job-talents/{candidatura_id}/timeline`
- ⚠️ **Status:** Implementado mas não sincronizado automaticamente
- **Dados capturados:**
  - Histórico de transições de stage/phase
  - Usuário responsável por cada mudança
  - Timestamps de cada evento
- **Nota:** Código existe em `api_client.py` mas não é chamado pela sincronização padrão

---

## ❌ Dados DISPONÍVEIS mas NÃO Sincronizados

### 📋 Categoria: Histórico e Auditoria

#### 1. Activities (Atividades) ❌
**Endpoints explorados:**
- `GET /activities` - Status 403 (Forbidden)
- `GET /activities?jobId={job_id}` - Status 403
- `GET /activities?talentId={talent_id}` - Status 403
- `GET /job-talents/{id}/activities` - Status 403
- `GET /talents/{id}/activities` - Status 403
- `GET /applications/{id}/activities` - Status 403

**O que são:** Registro de atividades/ações realizadas no sistema

**Utilidade potencial:**
- Auditoria completa de ações
- Análise de engajamento
- Rastreamento de interações

**Status:** ❌ Não acessível (403 Forbidden)

#### 2. Events (Eventos) ❌
**Endpoints explorados:**
- `GET /events` - Status 403
- `GET /events?jobId={job_id}` - Status 403

**O que são:** Eventos do sistema

**Utilidade potencial:**
- Registro de eventos importantes
- Notificações e alertas

**Status:** ❌ Não acessível (403 Forbidden)

#### 3. History (Histórico) ❌
**Endpoints explorados:**
- `GET /applications/{id}/history` - Status 403
- `GET /job-talents/{id}/history` - Status 403
- `GET /talents/{id}/history` - Status 403

**O que são:** Histórico completo de mudanças

**Utilidade potencial:**
- Rastreamento de todas as mudanças
- Auditoria detalhada

**Status:** ❌ Não acessível (403 Forbidden)

---

### 📝 Categoria: Processo Seletivo

#### 4. Stages (Etapas) ❌
**Endpoints explorados:**
- `GET /stages` - Status 403
- `GET /stages?jobId={job_id}` - Status 403
- `GET /jobs/{job_id}/stages` - Status 403

**O que são:** Definições de etapas do processo seletivo

**Utilidade potencial:**
- Mapear pipeline completo de cada vaga
- Análise de conversão por etapa
- Tempo médio em cada etapa

**Status:** ❌ Não acessível (403 Forbidden)

**Nota:** Stages/Phases atuais da candidatura JÁ estão nas candidaturas, mas as **definições** do pipeline não.

#### 5. Phases (Fases) ❌
**Endpoints explorados:**
- `GET /phases` - Status 403
- `GET /phases?jobId={job_id}` - Status 403
- `GET /jobs/{job_id}/phases` - Status 403

**O que são:** Definições de fases do processo

**Status:** ❌ Não acessível (403 Forbidden)

#### 6. Pipeline/Workflow ❌
**Endpoints explorados:**
- `GET /jobs/{job_id}/pipeline` - Status 403
- `GET /jobs/{job_id}/workflow` - Status 403

**O que são:** Configuração completa do fluxo de trabalho da vaga

**Utilidade potencial:**
- Mapear processo completo
- Análise de eficiência do pipeline

**Status:** ❌ Não acessível (403 Forbidden)

---

### 🎯 Categoria: Avaliações e Feedback

#### 7. Interviews (Entrevistas) ❌
**Endpoints explorados:**
- `GET /interviews` - Status 403
- `GET /interviews?applicationId={id}` - Status 403
- `GET /applications/{id}/interviews` - Status 403

**O que são:** Registros de entrevistas realizadas

**Utilidade potencial:**
- **ALTO VALOR** para análise
- Agendar/rastrear entrevistas
- Análise de tempo até contratação
- Métricas de processo seletivo

**Status:** ❌ Não acessível (403 Forbidden)

#### 8. Evaluations (Avaliações) ❌
**Endpoints explorados:**
- `GET /evaluations` - Status 403
- `GET /evaluations?applicationId={id}` - Status 403
- `GET /applications/{id}/evaluations` - Status 403

**O que são:** Avaliações formais dos candidatos

**Utilidade potencial:**
- **ALTO VALOR** para análise
- Scores de avaliação
- Feedback estruturado
- Análise de qualidade dos candidatos

**Status:** ❌ Não acessível (403 Forbidden)

#### 9. Feedback ❌
**Endpoints explorados:**
- `GET /applications/{id}/feedback` - Status 403

**O que são:** Feedback sobre candidatos

**Utilidade potencial:**
- **MÉDIO VALOR**
- Insights qualitativos

**Status:** ❌ Não acessível (403 Forbidden)

#### 10. Notes (Notas) ❌
**Endpoints explorados:**
- `GET /applications/{id}/notes` - Status 403

**O que são:** Anotações sobre candidaturas

**Utilidade potencial:**
- **MÉDIO VALOR**
- Contexto adicional sobre decisões

**Status:** ❌ Não acessível (403 Forbidden)

#### 11. Comments (Comentários) ❌
**Endpoints explorados:**
- `GET /applications/{id}/comments` - Status 403

**O que são:** Comentários sobre candidaturas

**Utilidade potencial:**
- **MÉDIO VALOR**
- Discussões sobre candidatos

**Status:** ❌ Não acessível (403 Forbidden)

---

### 📊 Categoria: Métricas e Analytics

#### 12. Analytics ❌
**Endpoints explorados:**
- `GET /analytics` - Status 403
- `GET /analytics/jobs/{job_id}` - Status 403

**O que são:** Analytics agregados do InHire

**Utilidade potencial:**
- **MÉDIO VALOR** (podemos calcular nossas próprias métricas)
- Métricas pré-calculadas

**Status:** ❌ Não acessível (403 Forbidden)

#### 13. Metrics ❌
**Endpoints explorados:**
- `GET /metrics` - Status 403
- `GET /metrics/jobs/{job_id}` - Status 403

**O que são:** Métricas do sistema

**Status:** ❌ Não acessível (403 Forbidden)

#### 14. Reports ❌
**Endpoints explorados:**
- `GET /reports` - Status 403

**O que são:** Relatórios pré-configurados

**Status:** ❌ Não acessível (403 Forbidden)

---

### 🔔 Categoria: Gestão e Colaboração

#### 15. Tasks (Tarefas) ❌
**Endpoints explorados:**
- `GET /tasks` - Status 403

**O que são:** Tarefas relacionadas ao recrutamento

**Utilidade potencial:**
- **BAIXO VALOR** para analytics
- Gestão de processos

**Status:** ❌ Não acessível (403 Forbidden)

#### 16. Notifications (Notificações) ❌
**Endpoints explorados:**
- `GET /notifications` - Status 403

**O que são:** Notificações do sistema

**Utilidade potencial:**
- **BAIXO VALOR** para analytics

**Status:** ❌ Não acessível (403 Forbidden)

#### 17. Reminders (Lembretes) ❌
**Endpoints explorados:**
- `GET /reminders` - Status 403

**O que são:** Lembretes configurados

**Utilidade potencial:**
- **BAIXO VALOR** para analytics

**Status:** ❌ Não acessível (403 Forbidden)

---

### 👥 Categoria: Configurações e Metadados

#### 18. Users (Usuários) ❌
**Endpoints explorados:**
- `GET /users` - Status 403

**O que são:** Usuários do sistema InHire

**Utilidade potencial:**
- **MÉDIO VALOR**
- Análise de produtividade por recrutador
- Atribuição de responsabilidades

**Status:** ❌ Não acessível (403 Forbidden)

**Nota:** Nomes de usuários JÁ aparecem no timeline

#### 19. Teams (Times) ❌
**Endpoints explorados:**
- `GET /teams` - Status 403

**O que são:** Times/grupos de usuários

**Utilidade potencial:**
- **BAIXO VALOR**
- Organização interna

**Status:** ❌ Não acessível (403 Forbidden)

#### 20. Tags ❌
**Endpoints explorados:**
- `GET /tags` - Status 403

**O que são:** Tags para categorização

**Utilidade potencial:**
- **MÉDIO VALOR**
- Segmentação e filtros

**Status:** ❌ Não acessível (403 Forbidden)

#### 21. Sources (Fontes) ❌
**Endpoints explorados:**
- `GET /sources` - Status 403

**O que são:** Fontes de candidaturas (LinkedIn, site, etc)

**Utilidade potencial:**
- **ALTO VALOR** para análise de origem
- ROI de canais de recrutamento

**Status:** ❌ Não acessível (403 Forbidden)

#### 22. Templates ❌
**Endpoints explorados:**
- `GET /templates` - Status 403

**O que são:** Templates de comunicação

**Utilidade potencial:**
- **BAIXO VALOR** para analytics

**Status:** ❌ Não acessível (403 Forbidden)

---

## 📊 Matriz de Priorização

### Dados com ALTO VALOR (Não Acessíveis)

| Endpoint | Valor para Analytics | Status | Impacto |
|----------|---------------------|--------|---------|
| **Interviews** | ⭐⭐⭐⭐⭐ | 403 | **MUITO ALTO** - Métricas de tempo, taxa de conversão |
| **Evaluations** | ⭐⭐⭐⭐⭐ | 403 | **MUITO ALTO** - Scores, qualidade dos candidatos |
| **Sources** | ⭐⭐⭐⭐ | 403 | **ALTO** - ROI de canais de sourcing |
| **Pipeline/Stages** | ⭐⭐⭐⭐ | 403 | **ALTO** - Análise de conversão por etapa |

### Dados com MÉDIO VALOR (Não Acessíveis)

| Endpoint | Valor para Analytics | Status |
|----------|---------------------|--------|
| **Users** | ⭐⭐⭐ | 403 |
| **Tags** | ⭐⭐⭐ | 403 |
| **Feedback/Notes** | ⭐⭐⭐ | 403 |
| **Analytics** | ⭐⭐ | 403 (podemos calcular) |

### Dados com BAIXO VALOR

| Endpoint | Valor para Analytics | Status |
|----------|---------------------|--------|
| Tasks, Notifications, Reminders | ⭐ | 403 |
| Templates | ⭐ | 403 |

---

## ✅ Dados que TEMOS e são Suficientes

Com os dados que **JÁ SINCRONIZAMOS**, podemos calcular:

### Métricas Disponíveis AGORA

#### 📈 Funil de Recrutamento
- ✅ Vagas abertas vs fechadas
- ✅ Número de candidaturas por vaga
- ✅ Distribuição de candidatos por stage/phase (dados no campo `stage` e `phase` das candidaturas)
- ✅ Taxa de conversão entre stages (via análise do campo `updatedAt`)
- ⚠️ **Limitação:** Não temos histórico completo de transições (timeline não é sincronizado automaticamente)

#### ⏱️ Tempo e Velocidade
- ✅ Tempo médio no processo (data candidatura → data atualização)
- ✅ Tempo de resposta (updatedAt - createdAt)
- ✅ Vagas mais rápidas vs mais lentas
- ⚠️ **Limitação:** Não temos tempo por etapa individual (precisaria do timeline)

#### 📊 Volume e Performance
- ✅ Candidaturas por vaga
- ✅ Candidatos ativos vs rejeitados vs declined
- ✅ Taxa de rejeição geral
- ✅ Vagas com mais candidatos
- ✅ Posições preenchidas vs abertas

#### 👥 Talentos
- ✅ Base de talentos total
- ✅ Talentos com múltiplas candidaturas
- ✅ Skills mais comuns
- ✅ Distribuição geográfica (se disponível nos dados)

---

## 🎯 Recomendações

### Curto Prazo (Implementar Agora)

#### 1. ✅ Ativar Sincronização de Timeline
**Prioridade:** ALTA
**Esforço:** BAIXO (código já existe!)

```python
# Arquivo: services/sync_service.py
# Adicionar sync de timeline após sync de candidaturas
```

**Benefícios:**
- Histórico completo de transições de stage/phase
- Cálculo preciso de tempo por etapa
- Identificação de gargalos no processo
- Análise de quem moveu cada candidatura

**Dados adicionais:**
- Histórico de mudanças de stage/phase
- Usuário responsável por cada mudança
- Timestamp de cada transição

### Médio Prazo (Investigar Permissões)

#### 2. Solicitar Acesso a Endpoints Bloqueados
**Prioridade:** MÉDIA
**Esforço:** MÉDIO (depende da InHire)

**Endpoints a solicitar (em ordem de prioridade):**

1. **Interviews** - Entrevistas agendadas/realizadas
2. **Evaluations** - Avaliações dos candidatos
3. **Sources** - Fonte das candidaturas
4. **Stages/Pipeline** - Definições do processo seletivo
5. **Users** - Lista de recrutadores

**Ação:** Contatar suporte da InHire para solicitar acesso

### Longo Prazo (Melhorias)

#### 3. Campos Calculados no Banco
**Prioridade:** MÉDIA
**Esforço:** MÉDIO

Adicionar campos calculados às tabelas:
- `dias_no_processo` (já existe!)
- `dias_no_stage_atual`
- `numero_de_transicoes`
- `taxa_de_progresso`

---

## 📋 Checklist de Cobertura Atual

### Dados Principais ✅
- ✅ Vagas (100%)
- ✅ Posições (100%)
- ✅ Candidaturas (100%)
- ✅ Talentos (100%)
- ⚠️ Timeline (código existe, não sincronizado automaticamente)

### Dados Complementares ❌
- ❌ Entrevistas (403 Forbidden)
- ❌ Avaliações (403 Forbidden)
- ❌ Pipeline/Stages (403 Forbidden)
- ❌ Fontes (403 Forbidden)
- ❌ Usuários (403 Forbidden)
- ❌ Feedback/Notas (403 Forbidden)

### Analytics que PODEMOS fazer ✅
- ✅ Funil de recrutamento básico
- ✅ Tempo médio de processo
- ✅ Volume de candidaturas
- ✅ Taxa de conversão geral
- ⚠️ Tempo por etapa (limitado sem timeline)
- ❌ Análise de entrevistas (não temos dados)
- ❌ Scores de avaliação (não temos dados)
- ❌ ROI por canal (não temos dados de source)

---

## 📊 Resumo Final

### Cobertura Atual: ~70-80%

**Temos acesso a:**
- ✅ 100% dos dados principais (Vagas, Posições, Candidaturas, Talentos)
- ✅ Campos de stage/phase atuais nas candidaturas
- ⚠️ Timeline (existe código, precisa ativar sincronização)

**NÃO temos acesso a:**
- ❌ ~20-30% dos dados complementares (entrevistas, avaliações, pipeline detalhado)
- ❌ Maioria bloqueada por permissões (403 Forbidden)

### Impacto na Análise

**Podemos analisar:**
- ✅ Volume e distribuição de candidaturas
- ✅ Tempo médio de processos
- ✅ Taxas de conversão gerais
- ✅ Performance de vagas

**Análises limitadas:**
- ⚠️ Tempo por etapa individual (melhoraria com timeline)
- ❌ Qualidade de candidatos (sem evaluations)
- ❌ Eficiência de entrevistas (sem interviews)
- ❌ ROI de canais (sem sources)

---

## 🎯 Ação Imediata Recomendada

**PRIORIDADE 1:** Ativar sincronização de Timeline

Isso aumentaria nossa cobertura de ~70% para ~85% sem precisar de novas permissões, pois o endpoint já funciona (status 200).

**Próximo passo:**
```bash
# Modificar services/sync_service.py para incluir sync de timeline
# Criar tabela 'candidatura_timeline' no banco
# Adicionar ao fluxo de sincronização automática
```

---

**Última atualização:** 19/11/2025
**Responsável:** Claude (Assistente AI)
**Baseado em:** Exploração de API (api_endpoints_exploration.json)
