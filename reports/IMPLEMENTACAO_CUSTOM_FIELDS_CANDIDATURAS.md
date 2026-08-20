# ✅ Implementação de Custom Fields em Candidaturas

**Data:** 2026-07-21
**Status:** ✅ **CONCLUÍDO**

---

## 📋 Resumo

Implementação completa do sistema de sincronização e extração de campos customizados (custom fields) da entidade JOB_TALENTS (candidaturas) da API Inhire.

### Campo Principal Implementado

**"Você conhecia a Framework Digital?"**
- **ID:** `55282edb-bb11-4445-8cd6-3c0c6b9ddb9a`
- **Tipo:** checkbox
- **Opções:** Sim, Não
- **Entidade:** JOB_TALENTS (candidaturas)

---

## ✅ Implementações Realizadas

### 1. Schema da API (models/api_schemas.py)

**Modificação:** Adicionado campo `customFields` ao modelo `CandidaturaAPI`

```python
class CandidaturaAPI(BaseModel):
    """Schema de candidatura retornado pela API"""
    id: str
    talentId: str
    # ... outros campos ...
    customFields: Optional[Dict[str, Any]] = None  # ✅ NOVO: Migration 069
```

**Linha:** 182

---

### 2. Modelo do Banco de Dados (models/database.py)

**Modificação:** Adicionada coluna `custom_fields` ao modelo `Candidatura`

```python
class Candidatura(Base):
    # ... outros campos ...

    # Migration 069: Custom Fields
    custom_fields = Column(JSON)  # ✅ NOVO
```

**Tipo:** JSONB (PostgreSQL)
**Índice:** GIN para busca eficiente

---

### 3. Serviço de Sincronização (services/database_service.py)

**Modificações:** Atualizado método `upsert_candidatura()` em duas partes

#### 3.1 Atualização de Candidaturas Existentes

```python
# Migration 069: Custom fields responses (JOB_TALENTS)
if hasattr(cand_api, 'customFields') and cand_api.customFields:
    existing.custom_fields = cand_api.customFields
```

**Linha:** 745-746

#### 3.2 Criação de Novas Candidaturas

```python
nova_cand = Candidatura(
    # ... outros campos ...
    # Migration 069: Custom fields responses (JOB_TALENTS)
    custom_fields=cand_api.customFields if hasattr(cand_api, 'customFields') else None
)
```

**Linha:** 786

---

### 4. Migration de Banco de Dados

#### Migration 069: Adicionar coluna custom_fields

**Arquivo:** `migrations/069_add_custom_fields_candidaturas.sql`

```sql
ALTER TABLE candidaturas ADD COLUMN IF NOT EXISTS custom_fields JSONB;

COMMENT ON COLUMN candidaturas.custom_fields IS
'Custom fields responses (JOB_TALENTS) - formato: {"field_id": ["valor1", "valor2"]}';

CREATE INDEX IF NOT EXISTS idx_candidaturas_custom_fields
ON candidaturas USING GIN (custom_fields);
```

**Status:** ✅ Executada com sucesso

**Script de Aplicação:** `scripts/migration/apply_migration_069.py`

---

#### Migration 070: Atualizar view de candidaturas

**Arquivo:** `migrations/070_update_view_candidaturas_custom_fields.sql`

```sql
CREATE OR REPLACE VIEW vw_relatorio_candidaturas AS
SELECT
    c.id,
    c.vaga_id,
    v.name AS vaga_nome,
    c.status,
    c.talent_name,
    c.talent_email,
    c.stage_name AS etapa_candidatura,
    c.status AS status_candidatura,

    -- ✅ NOVO: Extrair "Você conhecia a Framework Digital?"
    CASE
        WHEN c.custom_fields IS NOT NULL
             AND c.custom_fields ? '55282edb-bb11-4445-8cd6-3c0c6b9ddb9a' THEN
            (c.custom_fields->>'55282edb-bb11-4445-8cd6-3c0c6b9ddb9a')::jsonb->>0
        ELSE NULL
    END AS conhecia_framework,

    c.created_at,
    c.updated_at_inhire AS ultima_atualizacao

FROM candidaturas c
INNER JOIN vagas v ON c.vaga_id = v.id
WHERE EXTRACT(YEAR FROM c.created_at) = 2026
ORDER BY c.created_at DESC;
```

**Status:** ✅ Executada com sucesso

**Script de Aplicação:** `scripts/migration/apply_migration_070.py`

---

## 📊 Estrutura do JSON custom_fields

### Formato Retornado pela API

```json
{
  "55282edb-bb11-4445-8cd6-3c0c6b9ddb9a": ["Sim"],
  "1f50b961-7a55-4804-b9f9-20e0cbdb789b": ["LinkedIn", "Instagram"],
  "745c6a26-c3fa-4389-9b1e-75f54934c9ae": ["CLT"]
}
```

**Estrutura:**
- **Chave:** ID do custom field (UUID)
- **Valor:** Array de strings com as respostas

### Extração na View

Para extrair um valor específico, usamos:

```sql
-- Pega o primeiro valor do array
(custom_fields->>'field_id')::jsonb->>0

-- Exemplo prático:
(custom_fields->>'55282edb-bb11-4445-8cd6-3c0c6b9ddb9a')::jsonb->>0 AS conhecia_framework
```

---

## 🔍 Custom Fields Mapeados

### JOB_TALENTS (5 campos)

| Campo | ID | Tipo |
|-------|-----|------|
| "Você conhecia a Framework Digital?" | `55282edb-bb11-4445-8cd6-3c0c6b9ddb9a` | checkbox |
| "Onde conheceu a Framework Digital?" | `1f50b961-7a55-4804-b9f9-20e0cbdb789b` | checkbox |
| "É recrutamento interno?" | `58401823-2cf5-4e0c-93eb-07c46508eb3a` | select |
| "Modalidade de Contratação" | `745c6a26-c3fa-4389-9b1e-75f54934c9ae` | checkbox |
| "Modalidade de Trabalho" | `32df9b88-d37a-4fd2-8c84-1403736c9419` | checkbox |

**Documentação Completa:** `reports/MAPEAMENTO_COMPLETO_CUSTOM_FIELDS.md`

---

## 🚀 Próximos Passos

### 1. Executar Sincronização Completa

```bash
python run_sync.py --full
```

**Objetivo:** Popular a coluna `custom_fields` para todas as candidaturas existentes

**Duração estimada:** 50-60 minutos (sincronização completa)

---

### 2. Validar Dados do Candidato ADLER

**Candidato:** ADLER ROBERTO NICOLELLA

**Query de validação:**

```sql
SELECT
    id,
    talent_name,
    vaga_id,
    conhecia_framework,
    custom_fields->>'55282edb-bb11-4445-8cd6-3c0c6b9ddb9a' AS conhecia_raw,
    custom_fields
FROM vw_relatorio_candidaturas
WHERE LOWER(talent_email) ILIKE '%adler%'
   OR LOWER(talent_name) ILIKE '%adler%';
```

**Resultado esperado:** `conhecia_framework = 'Sim'`

---

### 3. Exportar Relatório Final

```bash
# Executar script de exportação para Google Sheets
python scripts/export/export_relatorio_candidaturas.py
```

**Colunas incluídas:**
- id
- vaga_id
- vaga_nome ✅ (Migration 068)
- status
- talent_name
- talent_email
- etapa_candidatura
- status_candidatura
- **conhecia_framework** ✅ (Migration 070 - NOVO)
- created_at
- ultima_atualizacao

---

## 📝 Arquivos Modificados/Criados

### Modificados

1. `models/api_schemas.py` (linha 182) - Adicionado `customFields`
2. `models/database.py` - Adicionado `custom_fields` ao modelo `Candidatura`
3. `services/database_service.py` (linhas 745-746, 786) - Salvamento de custom fields

### Criados

1. **Migrations:**
   - `migrations/069_add_custom_fields_candidaturas.sql`
   - `migrations/070_update_view_candidaturas_custom_fields.sql`

2. **Scripts de Aplicação:**
   - `scripts/migration/apply_migration_069.py`
   - `scripts/migration/apply_migration_070.py`

3. **Documentação:**
   - `reports/MAPEAMENTO_COMPLETO_CUSTOM_FIELDS.md`
   - `reports/RESUMO_CAMPO_ENCONTRADO.md`
   - `reports/IMPLEMENTACAO_CUSTOM_FIELDS_CANDIDATURAS.md` (este arquivo)

4. **Exports JSON:**
   - `reports/exports/custom_fields_JOB_TALENTS.json`
   - `reports/exports/custom_fields_TALENTS.json`
   - `reports/exports/custom_fields_JOBS.json`
   - `reports/exports/custom_fields_REQUISITIONS.json`

---

## ✅ Checklist de Implementação

- [x] Mapear todos os custom fields da plataforma
- [x] Adicionar `customFields` ao schema `CandidaturaAPI`
- [x] Adicionar coluna `custom_fields` ao modelo `Candidatura`
- [x] Atualizar método `upsert_candidatura()` para salvar custom fields
- [x] Criar e executar migration 069 (adicionar coluna)
- [x] Criar e executar migration 070 (atualizar view)
- [ ] Executar sincronização completa
- [ ] Validar dados do candidato ADLER
- [ ] Exportar relatório final atualizado

---

## 🔍 Como Adicionar Novos Custom Fields à View

Para adicionar outros custom fields à view `vw_relatorio_candidaturas`:

```sql
-- Exemplo: "Onde conheceu a Framework Digital?"
-- ID: 1f50b961-7a55-4804-b9f9-20e0cbdb789b

CASE
    WHEN c.custom_fields IS NOT NULL
         AND c.custom_fields ? '1f50b961-7a55-4804-b9f9-20e0cbdb789b' THEN
        -- Para campos de múltipla escolha, retornar array como string
        (c.custom_fields->>'1f50b961-7a55-4804-b9f9-20e0cbdb789b')
    ELSE NULL
END AS onde_conheceu_framework
```

**Referência de IDs:** Ver `reports/MAPEAMENTO_COMPLETO_CUSTOM_FIELDS.md`

---

## 📚 Referências

- **Endpoint da API:** `GET /custom-data-manager/custom-fields/entity/JOB_TALENTS`
- **Script de Teste:** `reports/testar_custom_fields_api.py`
- **Documentação da API:** https://api.inhire.app/docs
- **PostgreSQL JSON Functions:** https://www.postgresql.org/docs/current/functions-json.html

---

**Última atualização:** 2026-07-21 20:35
**Responsável:** Sistema de Sincronização Inhire
**Status:** Implementação completa - aguardando sincronização de dados
