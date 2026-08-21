# Análise: Sincronização de Talentos - API vs Implementação

## 📋 Resumo Executivo

A sincronização de talentos está **FUNCIONAL** e captura todos os campos principais da API.
Os campos de **diversidade** (diversityBlack, diversityDisability, diversityLgbt, diversityTrans, diversityWoman)
estão sendo salvos dentro do campo JSON `attributes`, mas não há campos dedicados para consultas diretas.

---

## ✅ Campos Implementados Corretamente

### Campos Principais
| Campo API | Campo DB | Status | Notas |
|-----------|----------|---------|-------|
| id | inhire_id | ✅ OK | Primary key único |
| name | name | ✅ OK | Indexado |
| email | email | ✅ OK | Indexado |
| phone | phone | ✅ OK | String(50) |
| headline | headline | ✅ OK | String(500) |
| company | company | ✅ OK | String(255) |
| location | location | ✅ OK | String(255) |
| picture | picture | ✅ OK | String(1000) - URL |
| linkedinUsername | linkedin_username | ✅ OK | String(255) |
| contactMethod | contact_method | ✅ OK | String(50) |
| status | status | ✅ OK | String(50) |
| userId | user_id | ✅ OK | String(100) |
| userName | user_name | ✅ OK | String(255) |
| createdAt | created_at_inhire | ✅ OK | DateTime |
| updatedAt | updated_at_inhire | ✅ OK | DateTime, indexado |

### Campos Complexos (JSON)
| Campo API | Campo DB | Status | Estrutura |
|-----------|----------|---------|-----------|
| attributes | attributes | ✅ OK | JSON completo com todos subcampos |
| jobs | jobs | ✅ OK | JSON array |
| files | (tabela separada) | ✅ OK | Relação 1:N com `talento_arquivos` |
| tags | (tabela separada) | ✅ OK | Relação 1:N com `talento_tags` |

---

## 📊 Campos de Diversidade (Dentro de attributes)

Os campos de diversidade estão **dentro do campo `attributes`** como JSON:

### Campos de Diversidade da API
```json
{
  "attributes": {
    "diversityBlack": [{
      "createdAt": "string",
      "id": "string",
      "origin": "string",
      "updatedAt": "string",
      "value": boolean
    }],
    "diversityDisability": [{ ... }],
    "diversityLgbt": [{ ... }],
    "diversityTrans": [{ ... }],
    "diversityWoman": [{ ... }]
  }
}
```

### ✅ Status Atual
- **SALVOS**: Sim, dentro do campo JSON `attributes`
- **CONSULTÁVEIS**: Não diretamente via SQL padrão
- **ANALYTICS**: Requer queries JSON ou extração

---

## ⚠️ Campos Não Sincronizados

### Do Schema PATCH /talents/:id
Campos que aparecem no PATCH mas não no GET:
- city
- state
- originId
- diversityFormQuestionResponses

**Observação**: Esses campos podem não estar no GET response, apenas no PATCH request.

---

## 🔍 Estrutura de Attributes (Detalhado)

O campo `attributes` contém múltiplos subcampos, cada um como array de objetos:

```python
{
  "approach": [{"id": "...", "value": "...", "origin": "...", ...}],
  "diversityBlack": [{"id": "...", "value": true/false, ...}],
  "diversityDisability": [{"id": "...", "value": true/false, ...}],
  "diversityLgbt": [{"id": "...", "value": true/false, ...}],
  "diversityTrans": [{"id": "...", "value": true/false, ...}],
  "diversityWoman": [{"id": "...", "value": true/false, ...}],
  "email": [{"id": "...", "value": "email@...", ...}],
  "phone": [{"id": "...", "value": "+55...", ...}],
  "seniority": [{"id": "...", "value": "SENIOR", ...}],
  "tags": [{"id": "...", "value": ["Java", "Python"], ...}],
  "targetSalary": [{"id": "...", "value": {"min": 10000, "max": 15000, "type": "BRL"}, ...}]
}
```

**Cada subcampo é um array** porque pode ter múltiplos valores/origens ao longo do tempo.

---

## 📈 Recomendações

### 1. ✅ Manter Implementação Atual
A implementação atual está **correta e eficiente**:
- Campos principais em colunas dedicadas (rápidas para buscar)
- Campos complexos em JSON (flexível para evolução)
- Tabelas separadas para files e tags (normalização)

### 2. 🔧 Melhorias Opcionais

#### A) Adicionar Colunas de Diversidade (se necessário para analytics)
Se relatórios de diversidade forem críticos, considerar adicionar:

```sql
ALTER TABLE talentos ADD COLUMN diversity_black BOOLEAN;
ALTER TABLE talentos ADD COLUMN diversity_disability BOOLEAN;
ALTER TABLE talentos ADD COLUMN diversity_lgbt BOOLEAN;
ALTER TABLE talentos ADD COLUMN diversity_trans BOOLEAN;
ALTER TABLE talentos ADD COLUMN diversity_woman BOOLEAN;
```

E extrair do JSON durante o upsert:
```python
# Extrair valor mais recente de cada campo de diversidade
existing.diversity_black = self._extract_latest_diversity_value(
    talento_api.attributes, 'diversityBlack'
)
```

**Vantagem**: Queries SQL diretas para relatórios de diversidade
**Desvantagem**: Dados duplicados (em attributes JSON e colunas)

#### B) Criar Índices GIN para Queries JSON (PostgreSQL)
Para melhorar performance de queries no campo `attributes`:

```sql
CREATE INDEX idx_talento_attributes_gin ON talentos USING GIN (attributes);
```

Permite queries como:
```sql
SELECT * FROM talentos
WHERE attributes @> '{"diversityBlack": [{"value": true}]}';
```

#### C) Adicionar Campos do PATCH
Se precisar dos campos adicionais do PATCH:
```sql
ALTER TABLE talentos ADD COLUMN city VARCHAR(255);
ALTER TABLE talentos ADD COLUMN state VARCHAR(100);
ALTER TABLE talentos ADD COLUMN origin_id VARCHAR(100);
```

### 3. 📊 Queries de Exemplo para Diversidade

#### Extrair Talentos com Diversidade (usando JSON)
```sql
-- PostgreSQL: Talentos que se identificam como pessoa negra
SELECT
    id,
    name,
    email,
    attributes->'diversityBlack'->0->>'value' as is_black
FROM talentos
WHERE attributes->'diversityBlack'->0->>'value' = 'true';

-- Contar por categoria de diversidade
SELECT
    COUNT(CASE WHEN attributes->'diversityBlack'->0->>'value' = 'true' THEN 1 END) as black,
    COUNT(CASE WHEN attributes->'diversityWoman'->0->>'value' = 'true' THEN 1 END) as woman,
    COUNT(CASE WHEN attributes->'diversityLgbt'->0->>'value' = 'true' THEN 1 END) as lgbt,
    COUNT(CASE WHEN attributes->'diversityDisability'->0->>'value' = 'true' THEN 1 END) as disability,
    COUNT(CASE WHEN attributes->'diversityTrans'->0->>'value' = 'true' THEN 1 END) as trans
FROM talentos;
```

---

## ✅ Conclusão

### Status Atual: ✅ FUNCIONANDO CORRETAMENTE

1. **Todos os campos principais** estão sendo sincronizados ✅
2. **Campos de diversidade** estão salvos em `attributes` ✅
3. **Files e tags** em tabelas normalizadas ✅
4. **Timestamps** sendo comparados para sync incremental ✅

### Ações Recomendadas:

1. **SE** relatórios de diversidade forem frequentes:
   - Adicionar colunas dedicadas para campos de diversidade
   - Criar função para extrair valores do JSON

2. **SE** performance de queries JSON for problema:
   - Adicionar índice GIN no campo `attributes`

3. **Continuar** monitorando a API para novos campos

---

## 🧪 Teste de Sincronização

Para verificar se os dados de diversidade estão sendo salvos:

```sql
-- Ver um talento completo com attributes
SELECT
    id,
    name,
    email,
    attributes
FROM talentos
LIMIT 1;

-- Verificar se há talentos com dados de diversidade
SELECT COUNT(*)
FROM talentos
WHERE attributes IS NOT NULL
  AND attributes::text LIKE '%diversity%';
```

---

**Data da Análise**: 27/11/2025
**Versão da API**: InHire v1
**Status**: ✅ Implementação Completa e Funcional
