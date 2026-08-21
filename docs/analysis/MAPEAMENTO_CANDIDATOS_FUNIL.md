# 🎯 Mapeamento Completo: Candidatos, Vagas, Status e Progressão no Funil

**Data:** 2026-07-07
**Objetivo:** Documentar todos os campos úteis das tabelas de Requisições, Talentos, Candidaturas e Timeline para mapear a jornada completa dos candidatos.

---

## 📊 Visão Geral das Tabelas

### 🔗 Relacionamentos entre Tabelas

```
┌─────────────┐
│  TALENTOS   │ ← Dados pessoais do candidato
│  (61.916)   │
└──────┬──────┘
       │ 1:N
       │
┌──────▼───────────┐
│  CANDIDATURAS    │ ← Aplicação do candidato na vaga
│   (116.300)      │
└──────┬───────────┘
       │ 1:N
       │
┌──────▼──────────────┐
│ CANDIDATURA_TIMELINE│ ← Histórico de movimentações no Kanban
│     (500k+)         │
└─────────────────────┘

        │
        │ N:1
        │
┌───────▼──────┐      ┌────────────┐
│    VAGAS     │ 1:1  │ REQUISIÇÕES│ ← Aprovação da vaga
│   (1.376)    │◄─────┤   (1.437)  │
└──────────────┘      └────────────┘
```

---

## 1️⃣ TALENTOS (Dados dos Candidatos)

### 📋 Campos Principais

| Campo | Tipo | Descrição | Uso |
|-------|------|-----------|-----|
| `id` | BigInt | ID interno | Chave primária |
| `inhire_id` | String | ID da API Inhire | Identificador único |
| `name` | String | Nome completo | Identificação |
| `email` | String | Email | Contato ✉️ |
| `phone` | String | Telefone | Contato 📞 |
| `headline` | String | Cargo/Título | "Desenvolvedor Full Stack Senior" |
| `company` | String | Empresa atual | "Google", "Microsoft" |
| `location` | String | Localização | "São Paulo, SP" |
| `linkedin_username` | String | Perfil LinkedIn | URL do perfil |
| `picture` | String | Foto | URL da imagem |
| `metadata` | JSON | Campos customizados | Dados adicionais |

### 🔗 Tabelas Relacionadas

**talento_tags** (Skills/Habilidades)
```sql
SELECT t.name, ARRAY_AGG(tt.name) as skills
FROM talentos t
LEFT JOIN talento_tags tt ON t.id = tt.talento_id
GROUP BY t.name;
```

**talento_arquivos** (Currículos/Documentos)
```sql
SELECT t.name, ta.name as arquivo, ta.url
FROM talentos t
LEFT JOIN talento_arquivos ta ON t.id = ta.talento_id;
```

---

## 2️⃣ CANDIDATURAS (Aplicações nas Vagas)

### 📋 Campos Principais

| Campo | Tipo | Descrição | Uso |
|-------|------|-----------|-----|
| `id` | BigInt | ID interno | Chave primária |
| `inhire_id` | String | ID da API | Identificador único |
| `vaga_id` | BigInt | FK → vagas | Qual vaga |
| `talento_id` | BigInt | FK → talentos | Quem se candidatou |
| **`status`** | Enum | **Status da candidatura** | ⭐ Campo-chave! |
| `source` | String | Origem | LinkedIn, Site, Indeed |
| **`stage_name`** | String | **Etapa atual no Kanban** | ⭐ "Entrevista Técnica" |
| **`stage_order`** | Int | **Ordem da etapa** | ⭐ 1, 2, 3, 4... |
| **`phase_name`** | String | **Subfase** | "Aguardando feedback" |
| **`phase_order`** | Int | **Ordem da subfase** | 1, 2, 3... |
| `applied_at` | DateTime | Data de aplicação | Quando aplicou |
| `created_at_inhire` | DateTime | Criado na API | Auditoria |
| `updated_at_inhire` | DateTime | Atualizado na API | Auditoria |

### 🎯 Status da Candidatura

| Status | Significado | % Típico |
|--------|-------------|----------|
| `active` | 🟢 Em processo | ~60-70% |
| `hired` | ✅ Contratado | ~5-10% |
| `rejected` | ❌ Rejeitado | ~20-30% |
| `declined` | ⛔ Desistiu | ~5-10% |
| `inactive` | ⚪ Inativo | ~5% |

### 📊 Stages (Etapas do Kanban)

As etapas variam por empresa, mas tipicamente:

| Order | Stage Name | Descrição |
|-------|------------|-----------|
| 1 | "Triagem" | Análise inicial do currículo |
| 2 | "Entrevista RH" | Primeira conversa |
| 3 | "Entrevista Técnica" | Avaliação de skills |
| 4 | "Entrevista com Gestor" | Fit cultural |
| 5 | "Proposta" | Negociação |
| 6 | "Contratado" | Finalizado ✅ |

---

## 3️⃣ CANDIDATURA_TIMELINE (Histórico de Movimentações)

### 📋 Campos Principais

| Campo | Tipo | Descrição | Uso |
|-------|------|-----------|-----|
| `id` | BigInt | ID interno | Chave primária |
| `candidatura_id` | BigInt | FK → candidaturas | De qual candidatura |
| `event_type` | String | Tipo de evento | "stage_changed", "hired", "rejected" |
| **`changed_at`** | DateTime | **Data da mudança** | ⭐ Quando aconteceu |
| **`from_stage_name`** | String | **De qual stage** | ⭐ "Triagem" |
| **`from_stage_order`** | Int | **Ordem anterior** | ⭐ 1 |
| **`to_stage_name`** | String | **Para qual stage** | ⭐ "Entrevista RH" |
| **`to_stage_order`** | Int | **Ordem nova** | ⭐ 2 |
| `from_phase_name` | String | Subfase anterior | Detalhe |
| `to_phase_name` | String | Subfase nova | Detalhe |
| `changed_by_name` | String | Quem moveu | Nome do recrutador |
| `notes` | Text | Observações | Feedback |
| **`duration_days`** | Int | **Dias no stage anterior** | ⭐ Tempo |

### 🎬 Tipos de Eventos

| Event Type | Significado |
|------------|-------------|
| `stage_changed` | Moveu de etapa |
| `phase_changed` | Mudou subfase |
| `status_changed` | Mudou status |
| `hired` | Foi contratado ✅ |
| `rejected` | Foi rejeitado ❌ |
| `declined` | Desistiu ⛔ |

---

## 4️⃣ REQUISIÇÕES (Aprovações de Vagas)

### 📋 Campos Principais

| Campo | Tipo | Descrição | Uso |
|-------|------|-----------|-----|
| `id` | BigInt | ID interno | Chave primária |
| `inhire_id` | String | ID da API | Identificador único |
| `vaga_id` | BigInt | FK → vagas | Vaga relacionada |
| `client_id` | BigInt | FK → clientes | Cliente solicitante |
| **`status`** | String | **Status da requisição** | ⭐ "approved", "pending" |
| `reason` | String | Motivo | "Substituição", "Expansão" |
| `name` | String | Nome da requisição | Título |
| `description` | Text | Descrição | Detalhes |
| `positions` | JSON | Posições solicitadas | Array de posições |
| `approval_workflow` | JSON | Fluxo de aprovação | Etapas |
| `approvers` | JSON | Aprovadores | Lista de gestores |
| `salary_min` | Float | Salário mínimo | R$ 5.000 |
| `salary_max` | Float | Salário máximo | R$ 10.000 |
| `user_name` | String | Criador | Recrutador |
| `status_updated_at` | DateTime | Data atualização status | Quando mudou |

### 🎯 Status da Requisição

| Status | Significado | Ação |
|--------|-------------|------|
| `pending` | ⏳ Aguardando aprovação | Ainda não pode contratar |
| `approved` | ✅ Aprovada | Pode iniciar processo |
| `rejected` | ❌ Rejeitada | Não vai abrir vaga |
| `canceled` | ⛔ Cancelada | Desistiu |

---

## 5️⃣ VAGAS (Jobs)

### 📋 Campos Principais (Relevantes)

| Campo | Tipo | Descrição | Uso |
|-------|------|-----------|-----|
| `id` | BigInt | ID interno | Chave primária |
| `name` | String | Nome da vaga | "Desenvolvedor Python Senior" |
| `area` | String | Área | "Tecnologia", "Marketing" |
| `seniority` | String | Senioridade | "Senior", "Pleno" |
| `status` | String | Status da vaga | "OPEN", "CLOSED" |
| `location` | String | Localização | "São Paulo", "Remoto" |
| `salary_max` | Float | Salário máximo | R$ 15.000 |
| `open_positions` | Int | Vagas abertas | 3 |
| `user_name` | String | Recrutador | Nome |
| `manager_id` | String | Gestor | ID do gestor |
| `tenant_client_id` | String | Cliente | ID do cliente |

---

## 🎯 Casos de Uso Práticos

### 1. **Listar todos os candidatos de uma vaga específica**

```sql
SELECT
    t.name AS candidato,
    t.email,
    c.status AS status_candidatura,
    c.stage_name AS etapa_atual,
    c.applied_at AS data_aplicacao,
    EXTRACT(DAY FROM NOW() - c.applied_at) AS dias_no_processo
FROM candidaturas c
INNER JOIN talentos t ON c.talento_id = t.id
INNER JOIN vagas v ON c.vaga_id = v.id
WHERE v.name ILIKE '%Desenvolvedor Python%'
ORDER BY c.stage_order DESC, c.applied_at DESC;
```

### 2. **Ver histórico completo de um candidato**

```sql
SELECT
    ct.changed_at AS data,
    ct.from_stage_name || ' → ' || ct.to_stage_name AS movimentacao,
    ct.changed_by_name AS quem_moveu,
    ct.duration_days AS dias_no_stage_anterior,
    ct.notes AS observacoes
FROM candidatura_timeline ct
INNER JOIN candidaturas c ON ct.candidatura_id = c.id
INNER JOIN talentos t ON c.talento_id = t.id
WHERE t.email = 'joao.silva@email.com'
ORDER BY ct.changed_at;
```

### 3. **Funil de conversão por vaga**

```sql
SELECT
    v.name AS vaga,
    COUNT(*) AS total_candidatos,
    COUNT(*) FILTER (WHERE c.stage_order = 1) AS triagem,
    COUNT(*) FILTER (WHERE c.stage_order = 2) AS entrevista_rh,
    COUNT(*) FILTER (WHERE c.stage_order = 3) AS entrevista_tecnica,
    COUNT(*) FILTER (WHERE c.stage_order >= 4) AS final_proposta,
    COUNT(*) FILTER (WHERE c.status = 'hired') AS contratados,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE c.status = 'hired') / COUNT(*),
        2
    ) AS taxa_conversao_pct
FROM candidaturas c
INNER JOIN vagas v ON c.vaga_id = v.id
WHERE v.status = 'OPEN'
GROUP BY v.id, v.name
ORDER BY total_candidatos DESC;
```

### 4. **Tempo médio em cada etapa do funil**

```sql
SELECT
    to_stage_name AS etapa,
    COUNT(*) AS total_passagens,
    ROUND(AVG(duration_days), 1) AS media_dias,
    MIN(duration_days) AS minimo_dias,
    MAX(duration_days) AS maximo_dias,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_days) AS mediana_dias
FROM candidatura_timeline
WHERE duration_days IS NOT NULL
  AND duration_days > 0
GROUP BY to_stage_name
ORDER BY media_dias DESC;
```

### 5. **Candidatos ativos em etapas avançadas**

```sql
SELECT
    t.name AS candidato,
    t.email,
    t.phone,
    v.name AS vaga,
    c.stage_name AS etapa_atual,
    c.updated_at_inhire AS ultima_atualizacao,
    EXTRACT(DAY FROM NOW() - c.updated_at_inhire) AS dias_sem_movimentacao
FROM candidaturas c
INNER JOIN talentos t ON c.talento_id = t.id
INNER JOIN vagas v ON c.vaga_id = v.id
WHERE c.status = 'active'
  AND c.stage_order >= 3  -- Entrevista técnica ou superior
ORDER BY c.stage_order DESC, dias_sem_movimentacao DESC;
```

### 6. **Candidatos que retrocederam no funil**

```sql
SELECT
    t.name AS candidato,
    v.name AS vaga,
    ct.changed_at AS data,
    ct.from_stage_name AS de,
    ct.to_stage_name AS para,
    ct.from_stage_order AS ordem_anterior,
    ct.to_stage_order AS ordem_nova,
    ct.notes AS motivo
FROM candidatura_timeline ct
INNER JOIN candidaturas c ON ct.candidatura_id = c.id
INNER JOIN talentos t ON c.talento_id = t.id
INNER JOIN vagas v ON c.vaga_id = v.id
WHERE ct.to_stage_order < ct.from_stage_order  -- Retrocedeu
ORDER BY ct.changed_at DESC;
```

### 7. **Requisições aprovadas vs vagas abertas**

```sql
SELECT
    r.name AS requisicao,
    r.status AS status_requisicao,
    v.name AS vaga,
    v.status AS status_vaga,
    v.open_positions AS vagas_abertas,
    COUNT(c.id) AS total_candidatos,
    COUNT(c.id) FILTER (WHERE c.status = 'active') AS candidatos_ativos,
    COUNT(c.id) FILTER (WHERE c.status = 'hired') AS contratados
FROM requisicoes r
LEFT JOIN vagas v ON r.vaga_id = v.id
LEFT JOIN candidaturas c ON v.id = c.vaga_id
WHERE r.status = 'approved'
GROUP BY r.id, r.name, r.status, v.name, v.status, v.open_positions
ORDER BY candidatos_ativos DESC;
```

---

## 📊 Views SQL Criadas

O arquivo `analise_candidatos_funil.sql` cria **4 views prontas**:

### 1. `vw_candidatos_status_atual`
Visão geral de todos os candidatos com status atual

### 2. `vw_candidatos_progressao_funil`
Histórico completo de todas as movimentações no Kanban

### 3. `vw_funil_conversao_vagas`
Análise quantitativa do funil por vaga

### 4. `vw_candidatos_completo`
Dados completos combinando TODAS as tabelas

---

## 🎨 Exportação para Power BI / Google Sheets

### Opção 1: Conectar diretamente nas views

```
1. Abra Power BI / Google Sheets
2. Conecte ao PostgreSQL:
   - Host: localhost
   - Port: 5432
   - Database: inhire
   - User: postgres
3. Selecione as views criadas:
   - vw_candidatos_status_atual
   - vw_candidatos_progressao_funil
   - vw_funil_conversao_vagas
   - vw_candidatos_completo
```

### Opção 2: Usar queries específicas

Copie as queries de exemplo acima e use como fonte de dados personalizada.

---

## 🔑 Campos-Chave para Análise

### Para rastrear PROGRESSÃO no funil:

✅ **candidaturas.stage_name** - Etapa atual
✅ **candidaturas.stage_order** - Ordem numérica (1, 2, 3...)
✅ **candidatura_timeline.from_stage_name** - De onde veio
✅ **candidatura_timeline.to_stage_name** - Para onde foi
✅ **candidatura_timeline.changed_at** - Quando aconteceu
✅ **candidatura_timeline.duration_days** - Tempo no stage

### Para rastrear STATUS:

✅ **candidaturas.status** - Status da candidatura (active, hired, rejected)
✅ **vagas.status** - Status da vaga (OPEN, CLOSED)
✅ **requisicoes.status** - Status da requisição (approved, pending)

### Para identificar PESSOAS:

✅ **talentos.name** - Nome completo
✅ **talentos.email** - Email (único)
✅ **talentos.phone** - Telefone
✅ **talentos.linkedin_username** - LinkedIn

### Para identificar VAGAS:

✅ **vagas.name** - Nome da vaga
✅ **vagas.area** - Área (Tecnologia, Marketing...)
✅ **vagas.seniority** - Senioridade (Junior, Pleno, Senior)

---

## 📈 Métricas Recomendadas

### KPIs de Conversão

1. **Taxa de Conversão Geral**: `contratados / total_candidatos`
2. **Taxa de Avanço por Etapa**: `passaram_para_etapa_N / total_candidatos`
3. **Taxa de Rejeição**: `rejeitados / total_candidatos`
4. **Taxa de Desistência**: `desistiram / total_candidatos`

### KPIs de Tempo

1. **Tempo Médio no Processo**: `AVG(dias_desde_aplicacao)`
2. **Tempo Médio por Etapa**: `AVG(duration_days) GROUP BY stage_name`
3. **Time to Hire**: `data_contratacao - data_aplicacao`
4. **Velocidade do Funil**: `1 / tempo_medio_total_processo`

### KPIs de Eficiência

1. **Candidatos Ativos por Vaga**: `COUNT(candidatos_ativos) / COUNT(vagas_abertas)`
2. **Candidatos por Recrutador**: `COUNT(candidatos) / COUNT(DISTINCT recrutador)`
3. **Taxa de Aprovação de Requisições**: `approved / total_requisicoes`

---

## ✅ Checklist de Implementação

- [x] Criar views SQL
- [x] Documentar campos disponíveis
- [x] Exemplos de queries prontos
- [ ] Conectar no Power BI / Google Sheets
- [ ] Criar dashboards visuais
- [ ] Agendar atualização automática

---

## 📞 Próximos Passos

1. **Execute o script SQL** (`analise_candidatos_funil.sql`) no PostgreSQL
2. **Teste as queries** de exemplo para validar os dados
3. **Conecte no Power BI** ou Google Sheets
4. **Crie visualizações** com os dados das views
5. **Agende sincronizações** para manter dados atualizados

---

## 📝 Notas Importantes

- ✅ Todos os dados são sincronizados automaticamente da API Inhire
- ✅ Views são atualizadas em tempo real (refletem o BD atual)
- ✅ Histórico completo preservado na `candidatura_timeline`
- ⚠️ Certifique-se de executar sync incremental regularmente (1-2x/dia)
- ⚠️ Requisições são opcionais (nem toda vaga tem requisição)

---

**Arquivo criado:** 2026-07-07
**Script SQL:** `analise_candidatos_funil.sql`
**Status:** ✅ Pronto para uso
