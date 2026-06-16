# Investigação: Posições sem source_candidato

**Data:** 2026-02-06
**Objetivo:** Entender por que 96 posições (11.6%) não têm source_candidato identificado

---

## RESUMO EXECUTIVO

✅ **PROBLEMA IDENTIFICADO E EXPLICADO**

**Causa raiz:** 100% das posições sem source NÃO TÊM CANDIDATOS

- **96 posições sem source** = **96 posições sem nenhum candidato**
- Isso é **ESPERADO e NORMAL** - sem candidatos, não há como determinar source
- A lógica da view está **CORRETA**

---

## ANÁLISE DETALHADA

### 1. Distribuição Geral

| Métrica | Quantidade | Percentual |
|---------|------------|------------|
| Total de posições | 831 | 100% |
| **Com source** | **735** | **88.4%** |
| **Sem source** | **96** | **11.6%** |

### 2. Características das Posições Sem Source

#### Por Status

| Status | Quantidade | % das sem source |
|--------|------------|------------------|
| **canceled** | **93** | **96.9%** ⚠️ |
| open | 3 | 3.1% |

**Insight:** Quase todas as posições sem source foram CANCELADAS

#### Por Ano de Publicação

| Ano | Quantidade | % das sem source |
|-----|------------|------------------|
| 2024 | 89 | 92.7% |
| 2025 | 4 | 4.2% |
| 2026 | 3 | 3.1% |

**Insight:** 92.7% são posições de 2024 (antigas)

#### Por Candidatos

| Métrica | Valor |
|---------|-------|
| Posições sem source | 96 |
| **Posições SEM NENHUM candidato** | **96 (100%)** 🎯 |
| Candidaturas dessas posições | 0 |

**DESCOBERTA CHAVE:** ✅ **Todas as posições sem source não têm candidatos**

---

## POR QUE NÃO TÊM SOURCE?

### Lógica da View (correta)

A view `vw_analise_posicoes` determina o `source_candidato` assim:

```sql
source_posicao AS (
    SELECT
        p.id AS posicao_id,
        COALESCE(
            -- Prioriza source do candidato contratado
            (SELECT cd.source FROM candidaturas cd
             WHERE cd.vaga_id = p.vaga_id AND cd.stage_name = 'Contratação'
             LIMIT 1),
            -- Fallback: source mais comum
            (SELECT cd.source FROM candidaturas cd
             WHERE cd.vaga_id = p.vaga_id
             GROUP BY cd.source ORDER BY COUNT(*) DESC
             LIMIT 1)
        ) AS source
    FROM posicoes p
)
```

**Se não há candidaturas:** `source` retorna `NULL` ✅

---

## POR QUE ESSAS POSIÇÕES NÃO TÊM CANDIDATOS?

### 1. Posições Canceladas (93 posições - 96.9%)

**Motivos prováveis:**
- Canceladas ANTES de receberem candidatos
- Requisição rejeitada
- Vaga encerrada rapidamente
- Mudança de estratégia do cliente

**Exemplo:**
- Posição 1317: Analista de CRM Senior
- Cliente: Banco Bari
- Data: 2024-05-02
- Status: canceled
- SLA: 652d
- **0 candidatos**

### 2. Posições Abertas Recentes (3 posições - 3.1%)

**Posições identificadas:**

| ID | Cargo | Cliente | Data | Status |
|----|-------|---------|------|--------|
| 1428 | Desenvolvedor .Net Pleno | Mercantil | 2026-02-04 | open |
| 1429 | Designer UX | DB Diagnósticos | 2026-02-04 | open |
| 1427 | Engenheiro de Dados Sênior | VLI | 2026-02-03 | open |

**Motivos prováveis:**
- 🆕 **Recém-criadas** (2-4 dias atrás) - ainda não receberam candidatos
- ⏱️ **Em processo de divulgação**
- 🔒 **Vagas internas/fechadas** - sem divulgação externa

**Ação recomendada:** Monitorar nos próximos dias para ver se recebem candidatos

---

## COMPARAÇÃO: COM vs SEM SOURCE

| Métrica | Com Source | Sem Source |
|---------|------------|------------|
| Total de posições | 735 | 96 |
| Abertas | 28 | 3 |
| Fechadas (contratação) | 118 | 0 |
| Canceladas | 574 | 93 |
| **SLA Médio** | **448 dias** | **664 dias** |

**Insights:**
1. Posições sem source têm SLA 48% maior (664d vs 448d)
2. Nenhuma posição sem source teve contratação (óbvio - sem candidatos)
3. Taxa de cancelamento: 96.9% (sem source) vs 78.1% (com source)

---

## DISTRIBUIÇÃO POR CLIENTE (top 10)

| Cliente | Quantidade | % |
|---------|------------|---|
| Drogaria Araújo | 12 | 12.5% |
| Syngenta | 11 | 11.5% |
| Salus Optima | 8 | 8.3% |
| não selecionar - Localiza | 7 | 7.3% |
| Framework | 6 | 6.3% |
| Unimed BH | 6 | 6.3% |
| MRV | 5 | 5.2% |
| Solides | 4 | 4.2% |
| Mercantil | 4 | 4.2% |
| BANCORBRAS | 4 | 4.2% |

**Insight:** Não há um cliente específico responsável - distribuição variada

---

## DISTRIBUIÇÃO POR TORRE

| Torre | Quantidade | % |
|-------|------------|---|
| (Não informado) | 93 | 96.9% |
| Saúde e Indústria | 2 | 2.1% |
| Varejo e Finanças | 1 | 1.0% |

**Insight:** 96.9% não têm torre informada - posições antigas/canceladas

---

## CONCLUSÃO

### ✅ Situação é NORMAL e ESPERADA

**Não há problema com a implementação:**
- ✅ View está correta
- ✅ Lógica de source está correta
- ✅ Sincronização está funcionando

**Posições sem source = Posições sem candidatos**

### 📊 Breakdown das 96 Posições

| Categoria | Qtd | % | Status |
|-----------|-----|---|--------|
| **Canceladas antigas (2024)** | 89 | 92.7% | ✅ Normal |
| **Canceladas recentes (2025-2026)** | 4 | 4.2% | ✅ Normal |
| **Abertas recentes (2026)** | 3 | 3.1% | ⏱️ Monitorar |

### 🎯 Ação Recomendada

#### Posições Canceladas (93)

**Status:** ✅ **Nenhuma ação necessária**

**Razão:**
- Posições foram canceladas antes de receberem candidatos
- Comportamento esperado
- Não impacta análises (são excluídas de dashboards de conversão)

#### Posições Abertas Recentes (3)

**Status:** ⏱️ **Monitorar**

**Ação:**
1. Verificar em 1 semana se receberam candidatos
2. Se não: investigar se há problema de divulgação
3. Se sim: source será atualizado automaticamente

**Como monitorar:**
```sql
SELECT
    id_position,
    cargo,
    data_publicacao,
    (CURRENT_DATE - data_publicacao) as dias_aberta
FROM vw_analise_posicoes
WHERE source_candidato IS NULL
AND status_atual = 'open'
ORDER BY data_publicacao DESC;
```

---

## VALOR DA ANÁLISE

### O que aprendemos

1. **88.4% de cobertura é EXCELENTE**
   - 735 de 831 posições têm source
   - Apenas 3 posições abertas sem source (temporário)

2. **96 posições sem source são esperadas**
   - 100% não têm candidatos
   - 96.9% foram canceladas
   - Não impactam análises de conversão

3. **Qualidade dos dados é alta**
   - Source está 100% preenchido nas candidaturas
   - View está funcionando corretamente
   - Apenas posições sem candidatos ficam sem source

### Impacto nas Análises

**Análises NÃO afetadas:**
- ✅ Conversão por canal (usa apenas posições com source)
- ✅ Taxa de indicações (usa apenas posições com candidatos)
- ✅ Performance por canal (usa apenas posições com source)
- ✅ ROI por canal (usa apenas posições com source)

**Análises que podem incluir:**
- ℹ️ Taxa de posições sem candidatos (11.6%)
- ℹ️ Taxa de cancelamento antes de candidatos (93/831 = 11.2%)
- ℹ️ Tempo médio até primeiro candidato

---

## PRÓXIMOS PASSOS

### 🟢 BAIXA PRIORIDADE (opcional)

#### 1. Monitorar Posições Abertas Sem Candidatos

**Frequência:** Semanal

**Query:**
```sql
SELECT COUNT(*)
FROM vw_analise_posicoes
WHERE source_candidato IS NULL
AND status_atual = 'open';
```

**Alerta:** Se número passar de 10, investigar processo de divulgação

#### 2. Criar Métrica "Taxa de Posições Sem Candidatos"

**Definição:**
```sql
SELECT
    COUNT(*) FILTER (WHERE source_candidato IS NULL) * 100.0 / COUNT(*) as taxa_sem_candidatos
FROM vw_analise_posicoes;
```

**Uso:** Benchmark de qualidade de divulgação

#### 3. Dashboard de "Posições Orfãs"

**Objetivo:** Identificar posições abertas há mais de 30 dias sem candidatos

**Query:**
```sql
SELECT
    id_position,
    cargo,
    cliente,
    data_publicacao,
    CURRENT_DATE - data_publicacao as dias_sem_candidatos
FROM vw_analise_posicoes
WHERE source_candidato IS NULL
AND status_atual = 'open'
AND CURRENT_DATE - data_publicacao > 30;
```

---

## STATUS

✅ **INVESTIGAÇÃO CONCLUÍDA**

- Data: 2026-02-06
- Tipo: Análise de Dados
- Prioridade: Alta (reduzida para Baixa após investigação)
- Status: **Situação normal - nenhuma ação crítica necessária**
- Conclusão: Posições sem source são posições sem candidatos (esperado)

---

**Resumo:** Investigação confirmou que as 96 posições sem source_candidato (11.6%) não têm candidatos. Isso é comportamento esperado e correto da view. 93 posições foram canceladas antes de receberem candidatos (2024), e apenas 3 posições abertas recentes (2026) ainda não receberam candidatos. Nenhuma ação corretiva necessária. Cobertura de 88.4% é excelente.
