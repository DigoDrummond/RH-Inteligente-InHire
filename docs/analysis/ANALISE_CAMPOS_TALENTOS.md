# Análise: Campos Disponíveis na Tabela de Talentos

**Data**: 2026-06-23
**Total de Talentos no BD**: 71.799
**Fonte**: Banco de Dados PostgreSQL - tabela `talentos`

---

## 📋 Estrutura Completa da Tabela

### 🔑 Identificadores

| Campo | Tipo | Descrição | Uso |
|-------|------|-----------|-----|
| `id` | BigInteger | ID interno sequencial do BD | Chave primária |
| `inhire_id` | String(100) | ID único do Inhire (UUID) | Chave externa, único, indexado |

### 👤 Dados Principais

| Campo | Tipo | Descrição | Análises Possíveis |
|-------|------|-----------|-------------------|
| `name` | String(255) | Nome completo do talento | Análise demográfica, busca |
| `email` | String(255) | Email de contato | Comunicação, unicidade |
| `phone` | String(50) | Telefone de contato | Canal de contato |
| `headline` | String(500) | Título profissional / resumo | Segmentação por senioridade/área |
| `company` | String(255) | Empresa atual/mais recente | Análise de sourcing, concorrência |
| `location` | String(255) | Localização (cidade/estado/país) | Análise geográfica, remoto vs presencial |
| `picture` | String(1000) | URL da foto de perfil | Completude do perfil |

**Análises Possíveis**:
- Taxa de preenchimento de perfil
- Distribuição geográfica
- Principais empresas de origem
- Senioridades mais comuns (via headline)

### 🌐 Redes Sociais

| Campo | Tipo | Descrição | Análises Possíveis |
|-------|------|-----------|-------------------|
| `linkedin_username` | String(255) | Username do LinkedIn | Enriquecimento de dados, sourcing |

**Análises Possíveis**:
- % de talentos com LinkedIn
- Integração com LinkedIn para enrichment

### ⚙️ Configurações

| Campo | Tipo | Descrição | Valores | Análises Possíveis |
|-------|------|-----------|---------|-------------------|
| `contact_method` | String(50) | Meio de contato preferido | email, linkedin, whatsapp | Preferência de comunicação |
| `status` | String(50) | Status atual do talento | active, inactive, etc | Talent pool ativo vs inativo |

**Análises Possíveis**:
- % de talentos ativos vs inativos
- Canal de comunicação preferido

### 👥 Responsável

| Campo | Tipo | Descrição | Análises Possíveis |
|-------|------|-----------|-------------------|
| `user_id` | String(100) | ID do usuário responsável | Distribuição de talentos por recrutador |
| `user_name` | String(255) | Nome do usuário responsável | Performance por recrutador |

**Análises Possíveis**:
- Talentos por recrutador
- Performance de sourcing por usuário
- Distribuição de carga de trabalho

### 📄 Currículo

| Campo | Tipo | Descrição | Análises Possíveis |
|-------|------|-----------|-------------------|
| `resume` | Text | Conteúdo do currículo em texto | Análise de skills, word cloud, matching |

**Análises Possíveis**:
- Skills mais frequentes (NLP)
- Análise de experiências
- Matching automático com vagas

### 🌈 Diversidade & Inclusão

| Campo | Tipo | Descrição | Análises Possíveis |
|-------|------|-----------|-------------------|
| `diversity_black` | Boolean | Se identifica como pessoa negra | Métricas de D&I |
| `diversity_woman` | Boolean | Se identifica como mulher | Métricas de gênero |
| `diversity_lgbt` | Boolean | Se identifica como LGBTQIA+ | Métricas de D&I |
| `diversity_disability` | Boolean | Se identifica como PCD | Métricas de acessibilidade |
| `diversity_trans` | Boolean | Se identifica como transgênero | Métricas de D&I |

**Análises Possíveis**:
- Diversidade do talent pool
- % de representatividade por grupo
- Comparação com mercado
- Tracking de metas de D&I
- Diversidade por área/senioridade

**Índices Otimizados**:
- Índices parciais criados apenas para valores `true` (economia de espaço)
- Queries rápidas para filtrar por grupos de diversidade

### 📊 Campos JSON

| Campo | Tipo | Descrição | Conteúdo |
|-------|------|-----------|----------|
| `attributes` | JSON | Atributos customizados completos | Metadados adicionais do tenant |
| `jobs` | JSON | Preferências de vagas/trabalhos | Array de preferências |

**Análises Possíveis**:
- Custom fields específicos do tenant
- Preferências de tipo de trabalho
- Expectativas salariais (se armazenado)
- Disponibilidade

### 📅 Auditoria

| Campo | Tipo | Descrição | Análises Possíveis |
|-------|------|-----------|-------------------|
| `created_at_inhire` | DateTime | Data de criação no Inhire | Análise de crescimento do pool |
| `updated_at_inhire` | DateTime | Última atualização no Inhire | Atividade recente, talentos dormentes |
| `created_at` | DateTime | Data de criação no BD local | Auditoria interna |
| `updated_at` | DateTime | Última atualização no BD local | Auditoria interna |

**Análises Possíveis**:
- Crescimento do talent pool ao longo do tempo
- Talentos ativos vs dormentes (sem atualização há X meses)
- Picos de sourcing (sazonalidade)
- Idade média dos perfis

---

## 📊 Análises Estratégicas Possíveis

### 1. **Análise de Completude de Perfil**

```sql
SELECT
    CASE
        WHEN email IS NOT NULL
         AND phone IS NOT NULL
         AND headline IS NOT NULL
         AND company IS NOT NULL
         AND location IS NOT NULL
         AND linkedin_username IS NOT NULL
        THEN 'Completo (100%)'
        WHEN (email IS NOT NULL OR phone IS NOT NULL)
         AND headline IS NOT NULL
        THEN 'Parcial (50-99%)'
        ELSE 'Incompleto (<50%)'
    END as nivel_completude,
    COUNT(*) as quantidade,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentual
FROM talentos
GROUP BY 1
ORDER BY 2 DESC;
```

**Insights**:
- % de perfis completos vs incompletos
- Campos com menor taxa de preenchimento
- Oportunidades de enrichment

### 2. **Análise Geográfica**

```sql
SELECT
    location,
    COUNT(*) as total_talentos,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentual
FROM talentos
WHERE location IS NOT NULL
GROUP BY location
ORDER BY total_talentos DESC
LIMIT 20;
```

**Insights**:
- Principais cidades/regiões
- Comparação com localizações de vagas
- Identificar gaps geográficos

### 3. **Análise de Diversidade**

```sql
SELECT
    'Pessoas Negras' as grupo,
    COUNT(CASE WHEN diversity_black = true THEN 1 END) as quantidade,
    ROUND(COUNT(CASE WHEN diversity_black = true THEN 1 END) * 100.0 / COUNT(*), 2) as percentual
FROM talentos
UNION ALL
SELECT 'Mulheres', COUNT(CASE WHEN diversity_woman = true THEN 1 END),
       ROUND(COUNT(CASE WHEN diversity_woman = true THEN 1 END) * 100.0 / COUNT(*), 2)
FROM talentos
UNION ALL
SELECT 'LGBTQIA+', COUNT(CASE WHEN diversity_lgbt = true THEN 1 END),
       ROUND(COUNT(CASE WHEN diversity_lgbt = true THEN 1 END) * 100.0 / COUNT(*), 2)
FROM talentos
UNION ALL
SELECT 'PCD', COUNT(CASE WHEN diversity_disability = true THEN 1 END),
       ROUND(COUNT(CASE WHEN diversity_disability = true THEN 1 END) * 100.0 / COUNT(*), 2)
FROM talentos
UNION ALL
SELECT 'Transgênero', COUNT(CASE WHEN diversity_trans = true THEN 1 END),
       ROUND(COUNT(CASE WHEN diversity_trans = true THEN 1 END) * 100.0 / COUNT(*), 2)
FROM talentos;
```

**Insights**:
- Representatividade de cada grupo
- Comparação com metas de D&I
- Evolução ao longo do tempo

### 4. **Análise de Atividade (Talentos Dormentes)**

```sql
SELECT
    CASE
        WHEN updated_at_inhire >= NOW() - INTERVAL '30 days' THEN 'Ativo (últimos 30 dias)'
        WHEN updated_at_inhire >= NOW() - INTERVAL '90 days' THEN 'Recente (30-90 dias)'
        WHEN updated_at_inhire >= NOW() - INTERVAL '180 days' THEN 'Inativo (90-180 dias)'
        WHEN updated_at_inhire >= NOW() - INTERVAL '365 days' THEN 'Dormente (6-12 meses)'
        ELSE 'Muito dormente (>1 ano)'
    END as atividade,
    COUNT(*) as quantidade,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentual
FROM talentos
GROUP BY 1
ORDER BY
    CASE
        WHEN atividade = 'Ativo (últimos 30 dias)' THEN 1
        WHEN atividade = 'Recente (30-90 dias)' THEN 2
        WHEN atividade = 'Inativo (90-180 dias)' THEN 3
        WHEN atividade = 'Dormente (6-12 meses)' THEN 4
        ELSE 5
    END;
```

**Insights**:
- % de talentos ativos
- Identificar talentos para reengajamento
- Saúde do talent pool

### 5. **Análise de Sourcing por Empresa**

```sql
SELECT
    company as empresa_origem,
    COUNT(*) as total_talentos,
    COUNT(DISTINCT CASE WHEN EXISTS (
        SELECT 1 FROM candidaturas c WHERE c.talent_inhire_id = talentos.inhire_id
    ) THEN talentos.id END) as com_candidaturas,
    ROUND(COUNT(DISTINCT CASE WHEN EXISTS (
        SELECT 1 FROM candidaturas c WHERE c.talent_inhire_id = talentos.inhire_id
    ) THEN talentos.id END) * 100.0 / COUNT(*), 2) as taxa_conversao
FROM talentos
WHERE company IS NOT NULL AND company != ''
GROUP BY company
HAVING COUNT(*) >= 10
ORDER BY total_talentos DESC
LIMIT 20;
```

**Insights**:
- Principais empresas de origem
- Taxa de conversão por empresa
- Identificar melhores fontes de talentos

### 6. **Crescimento do Talent Pool**

```sql
SELECT
    DATE_TRUNC('month', created_at_inhire) as mes,
    COUNT(*) as novos_talentos,
    SUM(COUNT(*)) OVER (ORDER BY DATE_TRUNC('month', created_at_inhire)) as total_acumulado
FROM talentos
WHERE created_at_inhire IS NOT NULL
GROUP BY DATE_TRUNC('month', created_at_inhire)
ORDER BY mes DESC
LIMIT 24;
```

**Insights**:
- Crescimento mensal do pool
- Sazonalidade de sourcing
- Tendências de aquisição

### 7. **Análise de Canal de Comunicação**

```sql
SELECT
    COALESCE(contact_method, 'Não informado') as canal_preferido,
    COUNT(*) as quantidade,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentual
FROM talentos
GROUP BY contact_method
ORDER BY quantidade DESC;
```

**Insights**:
- Canal preferido dos talentos
- Otimização de estratégia de comunicação

### 8. **Análise de Performance por Recrutador**

```sql
SELECT
    COALESCE(user_name, 'Sem responsável') as recrutador,
    COUNT(*) as total_talentos,
    COUNT(DISTINCT CASE WHEN EXISTS (
        SELECT 1 FROM candidaturas c WHERE c.talent_inhire_id = talentos.inhire_id
    ) THEN talentos.id END) as com_candidaturas,
    ROUND(COUNT(DISTINCT CASE WHEN EXISTS (
        SELECT 1 FROM candidaturas c WHERE c.talent_inhire_id = talentos.inhire_id
    ) THEN talentos.id END) * 100.0 / COUNT(*), 2) as taxa_conversao
FROM talentos
GROUP BY user_name
ORDER BY total_talentos DESC
LIMIT 20;
```

**Insights**:
- Performance de sourcing por recrutador
- Distribuição de carga
- Identificar melhores práticas

---

## 🔗 Relacionamentos

### Tabelas Relacionadas

1. **`candidaturas`** (via `talent_inhire_id`)
   - Todas as candidaturas do talento
   - Histórico de processos seletivos
   - Taxa de conversão

2. **`talento_arquivos`** (via `talento_id`)
   - Currículos anexados
   - Documentos adicionais
   - Múltiplas versões de CV

3. **`talento_tags`** (via `talento_id`)
   - Tags customizadas
   - Categorização adicional
   - Segmentação avançada

---

## 📈 Dashboards Recomendados

### Dashboard 1: **Visão Geral do Talent Pool**

**KPIs**:
- Total de talentos
- Crescimento mensal
- % de perfis completos
- Taxa de atividade (últimos 30 dias)

**Gráficos**:
- Evolução do pool ao longo do tempo
- Distribuição geográfica (mapa)
- Top 10 empresas de origem
- Completude de perfis (gauge/medidor)

### Dashboard 2: **Diversidade & Inclusão**

**KPIs**:
- % Pessoas negras
- % Mulheres
- % LGBTQIA+
- % PCD
- % Transgênero

**Gráficos**:
- Comparação com metas de D&I
- Evolução da diversidade ao longo do tempo
- Diversidade por senioridade/área
- Interseccionalidade

### Dashboard 3: **Performance de Sourcing**

**KPIs**:
- Talentos adicionados (mês)
- Taxa de conversão (candidaturas/total)
- Top recrutadores
- Principais fontes de talentos

**Gráficos**:
- Sourcing por recrutador
- Taxa de conversão por fonte
- Sazonalidade de sourcing
- Funil de talento → candidatura → contratação

### Dashboard 4: **Saúde do Pool**

**KPIs**:
- % Talentos ativos
- % Talentos dormentes
- Tempo médio desde última atualização
- % Com informações de contato

**Gráficos**:
- Distribuição de atividade
- Talentos para reengajamento
- Completude de campos críticos
- Qualidade do pool

---

## 🎯 Casos de Uso Avançados

### 1. **Matching Automático de Talentos**

Combinar dados de `headline`, `company`, `location`, `resume` com requisitos de vagas.

### 2. **Análise de Skills**

NLP sobre o campo `resume` para extrair skills técnicas e soft skills.

### 3. **Enriquecimento via LinkedIn**

Usar `linkedin_username` para buscar dados atualizados via API do LinkedIn.

### 4. **Segmentação para Campanhas**

Criar listas segmentadas por:
- Localização
- Empresa atual
- Senioridade (headline)
- Diversidade
- Atividade recente

### 5. **Análise Preditiva**

Prever probabilidade de conversão (candidatura → contratação) baseado em:
- Completude do perfil
- Empresa de origem
- Senioridade
- Localização

---

## 📝 Observações Importantes

### Limitações Conhecidas

1. **Campos JSON (`attributes`, `jobs`)**
   - Estrutura pode variar por talento
   - Necessário análise exploratória antes de uso em larga escala

2. **Taxa de Preenchimento**
   - Alguns campos podem ter baixa taxa de preenchimento
   - Verificar estatísticas antes de basear análises críticas

3. **Dados de Diversidade**
   - Auto-declaração (pode ter viés)
   - Nem todos os talentos preenchem
   - Respeitar privacidade/LGPD

4. **Dados Desatualizados**
   - `company`, `location` podem estar desatualizados
   - Verificar `updated_at_inhire` para idade da informação

### Boas Práticas

1. **Sempre filtrar por `updated_at_inhire`** para garantir dados recentes
2. **Usar `COALESCE` ou `IS NOT NULL`** ao trabalhar com campos opcionais
3. **Respeitar LGPD** ao trabalhar com dados sensíveis (diversidade, contato)
4. **Validar email/phone** antes de usar em campanhas
5. **Monitorar completude** de campos críticos

---

**Documento gerado em**: 2026-06-23
**Total de Campos Analisados**: 24 campos principais + 2 JSON + relacionamentos
**Versão**: 1.0
