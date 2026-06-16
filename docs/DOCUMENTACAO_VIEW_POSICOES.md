# Documentação Detalhada: VIEW vw_analise_posicoes

## Estrutura da View

### CTEs (Common Table Expressions)

#### 1. `ultima_etapa`
**Objetivo**: Busca a última etapa do funil de cada vaga baseada no maior `stage_order`.

```sql
WITH ultima_etapa AS (
    SELECT
        cd.vaga_id,
        cd.stage_name,
        cd.stage_order,
        ROW_NUMBER() OVER (PARTITION BY cd.vaga_id ORDER BY cd.stage_order DESC, cd.updated_at_inhire DESC) AS rn
    FROM candidaturas cd
    WHERE cd.stage_name IS NOT NULL AND cd.stage_order IS NOT NULL
)
```

**Campos**:
- `vaga_id` - ID da vaga (chave de agrupamento)
- `stage_name` - Nome da etapa do funil
- `stage_order` - Ordem da etapa (maior = mais avançada)
- `rn` - Row number (rn=1 = última etapa)

**Filtros**: Apenas candidaturas com stage_name e stage_order preenchidos

---

#### 2. `pessoa_contratada`
**Objetivo**: Identifica o talento contratado em cada vaga (etapa "Contratação" com stage_order > 9).

```sql
pessoa_contratada AS (
    SELECT
        cd.vaga_id,
        t.name AS talent_name,
        t.email AS talent_email,
        ROW_NUMBER() OVER (PARTITION BY cd.vaga_id ORDER BY cd.updated_at_inhire DESC) AS rn
    FROM candidaturas cd
    INNER JOIN talentos t ON t.inhire_id = cd.talent_inhire_id
    WHERE cd.stage_name = 'Contratação' AND cd.stage_order > 9
)
```

**Campos**:
- `vaga_id` - ID da vaga
- `talent_name` - Nome do talento contratado (de `talentos.name`)
- `talent_email` - Email do talento contratado (de `talentos.email`)
- `rn` - Row number (rn=1 = contratação mais recente)

**Join**: `candidaturas.talent_inhire_id = talentos.inhire_id`

**Filtros**:
- stage_name = 'Contratação'
- stage_order > 9

---

#### 3. `pendencias_posicao`
**Objetivo**: Calcula as datas de início e fim de pendências com cliente para cada posição.

```sql
pendencias_posicao AS (
    SELECT
        pt.posicao_id,
        MIN(pt.changed_at) FILTER (WHERE pt.previous_status = 'open' AND pt.new_status = 'paused') AS inicio_pendencia,
        MAX(pt.changed_at) FILTER (WHERE pt.previous_status = 'paused' AND pt.new_status IN ('open', 'canceled', 'closed')) AS fim_pendencia
    FROM position_timeline pt
    GROUP BY pt.posicao_id
)
```

**Campos**:
- `posicao_id` - ID da posição
- `inicio_pendencia` - Primeira mudança de status de 'open' para 'paused'
- `fim_pendencia` - Última mudança de status de 'paused' para ('open', 'canceled', 'closed')

**Fonte**: Tabela `position_timeline`

---

## Campos da View (SELECT Principal)

### IDENTIFICAÇÃO

#### 1. `id_position`
```sql
p.id AS id_position
```
- **Fonte**: `posicoes.id`
- **Tipo**: BigInteger (PRIMARY KEY)
- **Descrição**: ID único da posição
- **Observação**: Cada posição é uma instância única, mesmo dentro da mesma vaga

---

#### 2. `cargo`
```sql
v.name AS cargo
```
- **Fonte**: `vagas.name`
- **Tipo**: String(255)
- **Join**: `posicoes.vaga_id = vagas.id`
- **Descrição**: Nome do cargo/vaga
- **Observação**: Múltiplas posições podem compartilhar o mesmo cargo

---

### DATAS

#### 3. `data_abertura`
```sql
DATE(r.requested_at) AS data_abertura
```
- **Fonte**: `requisicoes.requested_at`
- **Tipo**: Date
- **Join**: `requisicoes.job_inhire_id = vagas.inhire_id` (LEFT JOIN)
- **Descrição**: Data de abertura da requisição
- **Pode ser NULL**: Sim (37.5% das posições não têm requisição)

---

#### 4. `data_publicacao`
```sql
DATE(p.created_at_inhire) AS data_publicacao
```
- **Fonte**: `posicoes.created_at_inhire`
- **Tipo**: Date
- **Descrição**: Data de publicação/criação da posição no InHire
- **Observação**: Campo específico de cada posição

---

### CONFIGURAÇÃO

#### 5. `prazo_processo_seletivo`
```sql
v.sla_days_goal AS prazo_processo_seletivo
```
- **Fonte**: `vagas.sla_days_goal`
- **Tipo**: Integer
- **Descrição**: Prazo em dias para conclusão do processo (meta/SLA da vaga)

---

### RELACIONAMENTOS

#### 6. `cliente`
```sql
c.name AS cliente
```
- **Fonte**: `clientes.name`
- **Tipo**: String(255)
- **Join**: `clientes.inhire_id = vagas.tenant_client_id` (LEFT JOIN)
- **Descrição**: Nome do cliente/empresa

---

#### 7. `torre`
```sql
r.custom_fields->>'Torre' AS torre
```
- **Fonte**: `requisicoes.custom_fields->>'Torre'`
- **Tipo**: JSON field (String)
- **Join**: `requisicoes.job_inhire_id = vagas.inhire_id` (LEFT JOIN)
- **Descrição**: Torre de negócio (ex: "Varejo e Finanças", "Saúde e Indústria")
- **Pode ser NULL**: Sim (se não houver requisição ou se campo não estiver preenchido)
- **Observação**: Campo corrigido recentemente (antes buscava de vagas.custom_fields)

---

### STATUS E ENCERRAMENTO

#### 8. `status_atual`
```sql
p.status AS status_atual
```
- **Fonte**: `posicoes.status` (DIRETAMENTE, não usa position_timeline)
- **Tipo**: String(50)
- **Valores**: 'open', 'closed', 'canceled', 'paused'
- **Descrição**: Status atual da posição
- **Observação**: Usa a tabela posicoes diretamente pois position_timeline estava desatualizado

---

#### 9. `data_encerramento`
```sql
CASE
    WHEN p.status IN ('closed', 'canceled')
    THEN DATE(p.updated_at_inhire)
    ELSE NULL
END AS data_encerramento
```
- **Fonte**: `posicoes.updated_at_inhire` (condicional)
- **Tipo**: Date
- **Descrição**: Data de encerramento da posição
- **Regra**: Só preenche se status = 'closed' OU 'canceled'
- **Observação**: Usa updated_at_inhire como proxy para data de encerramento

---

### INFORMAÇÕES ADICIONAIS

#### 10. `motivo_cancelamento_paralisacao`
```sql
v.custom_fields->>'Motivo de Cancelamento' AS motivo_cancelamento_paralisacao
```
- **Fonte**: `vagas.custom_fields->>'Motivo de Cancelamento'`
- **Tipo**: JSON field (String)
- **Descrição**: Motivo do cancelamento da vaga
- **Pode ser NULL**: Sim

---

#### 11. `etapa_funil`
```sql
ue.stage_name AS etapa_funil
```
- **Fonte**: CTE `ultima_etapa.stage_name`
- **Origem**: `candidaturas.stage_name` (WHERE rn=1)
- **Tipo**: String(255)
- **Descrição**: Última etapa do funil alcançada por candidatos desta vaga
- **Observação**: Busca o maior stage_order entre todas as candidaturas da vaga

---

#### 12. `senioridade`
```sql
COALESCE(v.custom_fields->>'Senioridade', v.seniority::text) AS senioridade
```
- **Fonte**:
  1. `vagas.custom_fields->>'Senioridade'` (prioridade)
  2. `vagas.seniority` (fallback)
- **Tipo**: String
- **Descrição**: Nível de senioridade da vaga (Junior, Pleno, Sênior, etc)

---

#### 13. `motivo_contratacao`
```sql
p.reason AS motivo_contratacao
```
- **Fonte**: `posicoes.reason`
- **Tipo**: Text
- **Descrição**: Motivo/razão da abertura desta posição específica

---

#### 14. `pessoa_substituida`
```sql
v.custom_fields->>'Se substituição, informar o nome do colaborador: ' AS pessoa_substituida
```
- **Fonte**: `vagas.custom_fields->>'Se substituição, informar o nome do colaborador: '`
- **Tipo**: JSON field (String)
- **Descrição**: Nome do colaborador que será substituído (se aplicável)

---

### RESPONSÁVEIS

#### 15. `responsavel`
```sql
r.user_name AS responsavel
```
- **Fonte**: `requisicoes.user_name`
- **Tipo**: String(255)
- **Join**: LEFT JOIN
- **Descrição**: Responsável pela requisição
- **Pode ser NULL**: Sim (41.8% das posições não têm requisição)

---

#### 16. `recrutador_vaga`
```sql
v.user_name AS recrutador_vaga
```
- **Fonte**: `vagas.user_name`
- **Tipo**: String(255)
- **Descrição**: Recrutador responsável pela vaga

---

### PENDÊNCIAS

#### 17. `inicio_pendencia_cliente`
```sql
DATE(pp.inicio_pendencia) AS inicio_pendencia_cliente
```
- **Fonte**: CTE `pendencias_posicao.inicio_pendencia`
- **Origem**: `position_timeline` (MIN changed_at WHERE open→paused)
- **Tipo**: Date
- **Descrição**: Data da primeira mudança de status de 'open' para 'paused'

---

#### 18. `fim_pendencia_cliente`
```sql
DATE(pp.fim_pendencia) AS fim_pendencia_cliente
```
- **Fonte**: CTE `pendencias_posicao.fim_pendencia`
- **Origem**: `position_timeline` (MAX changed_at WHERE paused→open/canceled/closed)
- **Tipo**: Date
- **Descrição**: Data da última mudança de status de 'paused' para 'open', 'canceled' ou 'closed'

---

#### 19. `sla_pendencia_cliente`
```sql
CASE
    WHEN pp.inicio_pendencia IS NOT NULL AND pp.fim_pendencia IS NOT NULL
    THEN (DATE(pp.fim_pendencia) - DATE(pp.inicio_pendencia))::INTEGER
    ELSE NULL
END AS sla_pendencia_cliente
```
- **Fonte**: Cálculo baseado em `pendencias_posicao`
- **Tipo**: Integer
- **Descrição**: Dias em pendência com cliente (fim - inicio)
- **Observação**: Só calcula se ambas as datas existirem

---

### SLAs

#### 20. `sla_recrutamento`
```sql
CASE
    WHEN r.requested_at IS NOT NULL AND p.created_at_inhire IS NOT NULL
    THEN (DATE(p.created_at_inhire) - DATE(r.requested_at))::INTEGER
    ELSE NULL
END AS sla_recrutamento
```
- **Fonte**: Cálculo entre `requisicoes.requested_at` e `posicoes.created_at_inhire`
- **Tipo**: Integer
- **Descrição**: Dias desde abertura da requisição até publicação da posição
- **Fórmula**: data_publicacao - data_abertura

---

### CONTRATAÇÃO

#### 21. `nome_pessoa_contratada`
```sql
pct.talent_name AS nome_pessoa_contratada
```
- **Fonte**: CTE `pessoa_contratada.talent_name`
- **Origem**: `talentos.name`
- **Tipo**: String(255)
- **Descrição**: Nome do talento contratado para esta vaga

---

#### 22. `email_pessoal`
```sql
pct.talent_email AS email_pessoal
```
- **Fonte**: CTE `pessoa_contratada.talent_email`
- **Origem**: `talentos.email`
- **Tipo**: String(255)
- **Descrição**: Email do talento contratado

---

#### 23. `modalidade_contratacao`
```sql
v.custom_fields->>'Modalidade de Contratação' AS modalidade_contratacao
```
- **Fonte**: `vagas.custom_fields->>'Modalidade de Contratação'`
- **Tipo**: JSON field (String)
- **Descrição**: Tipo de contratação (CLT, PJ, etc)

---

### SLA GERAL

#### 24. `sla_geral`
```sql
CASE
    WHEN p.updated_at_inhire IS NOT NULL
    THEN (DATE(p.updated_at_inhire) - DATE(COALESCE(r.requested_at, p.created_at_inhire)))::INTEGER
    ELSE (CURRENT_DATE - DATE(COALESCE(r.requested_at, p.created_at_inhire)))::INTEGER
END AS sla_geral
```
- **Fonte**: Cálculo
- **Tipo**: Integer
- **Descrição**: SLA geral em dias
- **Lógica**:
  - Se posição encerrada: usa `updated_at_inhire`
  - Se posição aberta: usa `CURRENT_DATE`
  - Data inicial: `requested_at` (se existir requisição) ou `created_at_inhire`

---

### CLASSIFICAÇÃO

#### 25. `classificacao_vaga`
```sql
v.custom_fields->>'Classificação' AS classificacao_vaga
```
- **Fonte**: `vagas.custom_fields->>'Classificação'`
- **Tipo**: JSON field (String)
- **Descrição**: Classificação da vaga

---

#### 26. `area_vaga`
```sql
v.area AS area_vaga
```
- **Fonte**: `vagas.area`
- **Tipo**: String(255)
- **Descrição**: Área da vaga (ex: Tecnologia, RH, etc)

---

### INDICADORES

#### 27. `indicador_prazo`
```sql
CASE
    WHEN v.sla_days_goal IS NOT NULL AND p.updated_at_inhire IS NOT NULL
    THEN CASE
        WHEN (DATE(p.updated_at_inhire) - DATE(COALESCE(r.requested_at, p.created_at_inhire))) <= v.sla_days_goal
        THEN 'Dentro do Prazo'
        ELSE 'Fora do Prazo'
    END
    WHEN v.sla_days_goal IS NOT NULL
    THEN CASE
        WHEN (CURRENT_DATE - DATE(COALESCE(r.requested_at, p.created_at_inhire))) <= v.sla_days_goal
        THEN 'Dentro do Prazo'
        ELSE 'Fora do Prazo'
    END
    ELSE NULL
END AS indicador_prazo
```
- **Fonte**: Cálculo comparativo
- **Tipo**: String ('Dentro do Prazo', 'Fora do Prazo', NULL)
- **Descrição**: Indica se a posição está dentro ou fora do prazo estabelecido
- **Lógica**:
  - Se posição encerrada: compara `sla_geral` com `sla_days_goal`
  - Se posição aberta: compara tempo decorrido com `sla_days_goal`
  - Se não há `sla_days_goal`: retorna NULL

---

## JOINS da View

```
posicoes p (INNER JOIN)
  └── vagas v ON p.vaga_id = v.id
       ├── (LEFT JOIN) requisicoes r ON r.job_inhire_id = v.inhire_id
       ├── (LEFT JOIN) clientes c ON c.inhire_id = v.tenant_client_id
       ├── (LEFT JOIN) ultima_etapa ue ON ue.vaga_id = p.vaga_id AND ue.rn = 1
       ├── (LEFT JOIN) pessoa_contratada pct ON pct.vaga_id = p.vaga_id AND pct.rn = 1
       └── (LEFT JOIN) pendencias_posicao pp ON pp.posicao_id = p.id
```

---

## FILTROS

### WHERE
```sql
WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
```

**Vagas excluídas**:
- 88: Teste
- 99: Banco de Talentos
- 114: Template vaga frame
- 479: Banco de Talentos - frame
- 680: Programa de Estágio Framework Padawans

**Total excluído**: 41 posições, 964 candidaturas

---

## ORDENAÇÃO

```sql
ORDER BY p.created_at_inhire DESC NULLS LAST
```

Ordena por data de publicação da posição (mais recentes primeiro), colocando NULLs no final.

---

## Observações Importantes

### 1. Campos que podem ser NULL
- `data_abertura` (37.5% sem requisição)
- `torre` (se não houver requisição ou campo não preenchido)
- `responsavel` (41.8% sem requisição)
- `data_encerramento` (só preenche para closed/canceled)
- Campos de pendências (se não houver mudanças de status)
- Campos de contratação (se não houver contratação)

### 2. Diferença entre Vaga e Posição
- **Vaga**: Template/modelo (ex: "Desenvolvedor Python Sênior")
- **Posição**: Instância específica dentro da vaga (cada vaga pode ter N posições)
- Exemplo: "Redator SEO Sênior" tem 2 posições:
  - Posição 1405: status=closed
  - Posição 1406: status=open

### 3. Por que não usa position_timeline para status?
O `position_timeline` estava desatualizado (mostrando 'open' quando a tabela posicoes tinha 'canceled').
A fonte de verdade é `posicoes.status`.

### 4. Cálculo de SLA Geral
- **Posição encerrada**: data_encerramento - data_inicio
- **Posição aberta**: hoje - data_inicio
- **Data início**: data_abertura (se existir requisição) OU data_publicacao

---

## Total de Registros

**831 posições** (872 total - 41 excluídas pelo filtro)
