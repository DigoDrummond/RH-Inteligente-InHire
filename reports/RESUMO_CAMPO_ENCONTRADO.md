# ✅ Campo "Você conhecia a Framework Digital?" - ENCONTRADO!

**Data:** 2026-07-21
**Status:** ✅ **LOCALIZADO**

---

## 🎯 Descoberta

O campo **"Você conhecia a Framework Digital?"** foi encontrado através do endpoint:

```
GET /custom-data-manager/custom-fields/entity/JOB_TALENTS
```

### Informações do Campo

```json
{
  "id": "55282edb-bb11-4445-8cd6-3c0c6b9ddb9a",
  "name": "Você conhecia a Framework Digital?",
  "entity": "JOB_TALENTS",
  "type": "checkbox",
  "required": false,
  "order": 3,
  "showIn": ["JOB_TALENT_MODAL"],
  "options": [
    {
      "id": "7bea56c4-4272-44e1-b45c-2cd567a49d3d",
      "value": "Sim",
      "label": "Sim"
    },
    {
      "id": "3c3ddaee-0a5a-49ab-91c3-f8882c5edd23",
      "value": "Não",
      "label": "Não"
    }
  ],
  "createdAt": "2025-05-17T02:35:24Z",
  "updatedAt": "2025-05-17T02:35:24Z"
}
```

---

## 📊 Outros Campos Relacionados Encontrados

### 1. "Onde conheceu a Framework Digital?" (JOB_TALENTS)
- **ID:** `1f50b961-7a55-4804-b9f9-20e0cbdb789b`
- **Tipo:** checkbox (múltipla escolha)
- **Opções:** LinkedIn, Instagram, Google, Instituições de Ensino, Eventos, Conhecido/amigo, Não conhecia

### 2. "O Candidato já conhecia a Framework?" (TALENTS)
- **ID:** `36564519-7214-46af-b02c-36b551dd170d`
- **Tipo:** select
- **Opções:** Sim, Não

### 3. "Onde conheceu a Framework?" (TALENTS)
- **ID:** `4a2af968-b11c-48a5-bdc9-7cbb369224cc`
- **Tipo:** select
- **Opções:** Linkedin, Instagram, Google, Instituições de Ensino, Eventos, Conhecido/amigo, Não conhecia

---

## 🔍 Onde as Respostas Estão Armazenadas?

As respostas dos candidatos a esses campos customizados **NÃO** estão nas tabelas que já sincronizamos:

- ❌ Não estão em `candidaturas.stage_metadata`
- ❌ Não estão em `candidaturas.phase_metadata`
- ❌ Não estão em `talentos.attributes`
- ❌ Não estão em `talentos.jobs`

### ⚠️ Campos Customizados Não Sincronizados

As respostas dos campos customizados de `JOB_TALENTS` (candidaturas) **NÃO estão sendo sincronizadas** pelo sistema atual.

**Possível localização:**
- Endpoint: `GET /jobs/{jobId}/job-talents/{jobTalentId}` pode retornar um campo `customFields` com as respostas
- Endpoint: `POST /job-talents/paginated` pode retornar as respostas no objeto de candidatura

---

## 🔄 Próximos Passos

### 1. Verificar se endpoint retorna custom fields
Testar se o endpoint de candidaturas retorna as respostas dos campos customizados.

### 2. Adicionar sincronização de custom fields
Se o endpoint retornar os dados:
- Adicionar coluna `custom_fields` (JSON) na tabela `candidaturas`
- Atualizar método `_sync_candidaturas_full()` para salvar custom fields
- Atualizar modelo `Candidatura` em `models/database.py`

### 3. Atualizar view de candidaturas
Extrair o campo do JSON:
```sql
SELECT
    c.id,
    c.vaga_id,
    v.name AS vaga_nome,
    c.status,
    c.talent_name,
    c.talent_email,
    c.stage_name AS etapa_candidatura,

    -- ✅ NOVO: Extrair resposta do JSON
    c.custom_fields->>'55282edb-bb11-4445-8cd6-3c0c6b9ddb9a' AS conhecia_framework,

    c.created_at
FROM candidaturas c
INNER JOIN vagas v ON c.vaga_id = v.id;
```

---

## 📝 Arquivos de Referência

**JSON completo dos custom fields salvo em:**
- `reports/exports/custom_fields_JOB_TALENTS.json`
- `reports/exports/custom_fields_TALENTS.json`
- `reports/exports/custom_fields_JOBS.json`
- `reports/exports/custom_fields_REQUISITIONS.json`

---

## ✅ Ação Imediata

**TESTAR** se as respostas dos custom fields são retornadas ao buscar uma candidatura específica via API.

**Exemplo:** Buscar candidatura do ADLER ROBERTO NICOLELLA e verificar se há campo `customFields` na resposta.

---

**Última atualização:** 2026-07-21 19:45
**Responsável:** Sistema de Sincronização Inhire
**Status:** Campo localizado - aguardando implementação de sincronização
