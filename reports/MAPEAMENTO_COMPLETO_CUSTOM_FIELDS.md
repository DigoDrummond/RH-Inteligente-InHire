# Mapeamento Completo de Custom Fields - Inhire API

**Data:** 2026-07-21
**Fonte:** `GET /custom-data-manager/custom-fields/entity/{entity}`

---

## 📊 Resumo Geral

| Entidade | Total de Campos | Sincronizado Atualmente |
|----------|-----------------|-------------------------|
| **JOB_TALENTS** (Candidaturas) | 5 | ❌ Não |
| **TALENTS** (Talentos) | 3 | ❌ Não |
| **JOBS** (Vagas) | 13 | ✅ Parcial |
| **REQUISITIONS** (Requisições) | 0 | N/A |

**Total:** 21 campos customizados configurados

---

## 1️⃣ JOB_TALENTS - Candidaturas (5 campos)

### Campo 1: "Onde conheceu a Framework Digital?"
```json
{
  "id": "1f50b961-7a55-4804-b9f9-20e0cbdb789b",
  "name": "Onde conheceu a Framework Digital?",
  "entity": "JOB_TALENTS",
  "type": "checkbox",
  "required": false,
  "order": 4,
  "showIn": ["JOB_TALENT_MODAL"],
  "options": [
    {"value": "LinkedIN", "label": "LinkedIN"},
    {"value": "Instagram", "label": "Instagram"},
    {"value": "Google", "label": "Google"},
    {"value": "Instituições de Ensino", "label": "Instituições de Ensino"},
    {"value": "Eventos", "label": "Eventos"},
    {"value": "Conhecido e/ou amigo que trabalha na empresa", "label": "Conhecido e/ou amigo que trabalha na empresa"},
    {"value": "Não conhecia a Framework Digital", "label": "Não conhecia a Framework Digital"}
  ]
}
```

### Campo 2: "É recrutamento interno?" ⭐
```json
{
  "id": "58401823-2cf5-4e0c-93eb-07c46508eb3a",
  "name": "É recrutamento interno?",
  "entity": "JOB_TALENTS",
  "type": "select",
  "required": true,
  "order": 1,
  "showIn": ["ADMISSION_MODAL", "JOB_TALENT_MODAL"],
  "requiredIn": ["ADMISSION_MODAL"],
  "options": [
    {"value": "Não", "label": "Não"},
    {"value": "Sim", "label": "Sim"}
  ]
}
```

### Campo 3: "Modalidade de Contratação" ⭐
```json
{
  "id": "745c6a26-c3fa-4389-9b1e-75f54934c9ae",
  "name": "Modalidade de Contratação",
  "entity": "JOB_TALENTS",
  "type": "select",
  "required": true,
  "order": 2,
  "showIn": ["ADMISSION_MODAL", "JOB_TALENT_MODAL"],
  "requiredIn": ["ADMISSION_MODAL"],
  "options": [
    {"value": "CLT Flex", "label": "CLT Flex"},
    {"value": "CLT Full", "label": "CLT Full"},
    {"value": "Estágio", "label": "Estágio"},
    {"value": "PJ", "label": "PJ"}
  ]
}
```

### Campo 4: "Você conhecia a Framework Digital?" ⭐🎯
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
    {"value": "Sim", "label": "Sim"},
    {"value": "Não", "label": "Não"}
  ]
}
```
**🎯 Este é o campo solicitado pelo usuário!**

### Campo 5: "Modalidade de Trabalho"
```json
{
  "id": "32df9b88-d37a-4fd2-8c84-1403736c9419",
  "name": "Modalidade de Trabalho",
  "entity": "JOB_TALENTS",
  "type": "checkbox",
  "required": false,
  "order": 5,
  "showIn": ["JOB_TALENT_MODAL"],
  "options": [
    {"value": "Remoto", "label": "Remoto"},
    {"value": "Híbrido", "label": "Híbrido"},
    {"value": "Presencial", "label": "Presencial"}
  ]
}
```

---

## 2️⃣ TALENTS - Talentos (3 campos)

### Campo 1: "Onde conheceu a Framework?"
```json
{
  "id": "4a2af968-b11c-48a5-bdc9-7cbb369224cc",
  "name": "Onde conheceu a Framework?",
  "entity": "TALENTS",
  "type": "select",
  "required": false,
  "order": 3,
  "showIn": ["JOB_TALENT_MODAL"],
  "options": [
    {"value": "Linkedin", "label": "Linkedin"},
    {"value": "Instagram", "label": "Instagram"},
    {"value": "Google", "label": "Google"},
    {"value": "Instituições de Ensino", "label": "Instituições de Ensino"},
    {"value": "Eventos", "label": "Eventos"},
    {"value": "Conhecido e/ou amigo que trabalha/ou na Framework Digital"},
    {"value": "Não conhecia a Framework Digital"}
  ]
}
```

### Campo 2: "O Candidato já conhecia a Framework?"
```json
{
  "id": "36564519-7214-46af-b02c-36b551dd170d",
  "name": "O Candidato já conhecia a Framework?",
  "entity": "TALENTS",
  "type": "select",
  "required": false,
  "order": 2,
  "showIn": ["JOB_TALENT_MODAL"],
  "options": [
    {"value": "Sim", "label": "Sim"},
    {"value": "Não", "label": "Não"}
  ]
}
```

### Campo 3: "Tem fluência em algum idioma"
```json
{
  "id": "197ea7ce-979d-4aa9-9811-cb9a6257cef6",
  "name": "Tem fluência em algum idioma",
  "entity": "TALENTS",
  "type": "checkbox",
  "required": false,
  "order": 1,
  "showIn": ["JOB_TALENT_MODAL"],
  "options": [
    {"value": "Sim", "label": "Sim"},
    {"value": "Não", "label": "Não"}
  ]
}
```

---

## 3️⃣ JOBS - Vagas (13 campos)

### Campo 1: "Tipo" ⭐
```json
{
  "id": "bd63c64c-08ee-4018-b2a5-ee1db452c7ff",
  "name": "Tipo",
  "entity": "JOBS",
  "type": "select",
  "required": true,
  "order": 1,
  "options": [
    {"value": "Substituição", "label": "Substituição"},
    {"value": "Vaga", "label": "Vaga"}
  ]
}
```
**✅ JÁ SINCRONIZADO** em `vagas.custom_fields`

### Campo 2: "Senioridade" ⭐
```json
{
  "id": "58a5aaec-96b7-450f-a000-9b711dbf2d63",
  "name": "Senioridade",
  "entity": "JOBS",
  "type": "select",
  "required": true,
  "order": 2,
  "options": [
    {"value": "Estágio", "label": "Estágio"},
    {"value": "Júnior", "label": "Júnior"},
    {"value": "Pleno", "label": "Pleno"},
    {"value": "Sênior", "label": "Sênior"},
    {"value": "Especialista", "label": "Especialista"}
  ]
}
```
**✅ JÁ SINCRONIZADO**

### Campo 3: "Custo Hora (ideal)"
```json
{
  "id": "68ad8ef2-210f-4542-bcfc-951c57c1b91d",
  "name": "Custo Hora (ideal) - Ex. R$ xx,xx",
  "entity": "JOBS",
  "type": "text",
  "required": true,
  "order": 3
}
```
**✅ JÁ SINCRONIZADO**

### Campo 4: "Custo Hora (máximo)"
```json
{
  "id": "31a28f22-7a8a-4f8b-b6ca-ae9fb36e0b47",
  "name": "Custo Hora (máximo) - Ex. R$ xx,xx",
  "entity": "JOBS",
  "type": "text",
  "required": true,
  "order": 4
}
```
**✅ JÁ SINCRONIZADO**

### Campo 5: "Área" ⭐
```json
{
  "id": "b3bfa235-ed27-4c86-b43e-766884c5bb57",
  "name": "Área",
  "entity": "JOBS",
  "type": "select",
  "required": true,
  "order": 5,
  "options": [
    {"value": "Rethink", "label": "Rethink"},
    {"value": "Operação", "label": "Operação"}
  ]
}
```
**✅ JÁ SINCRONIZADO**

### Campo 6: "Tipo de Posição"
```json
{
  "id": "0961fd3a-0af2-4a91-9efb-1915d5c382e4",
  "name": "Tipo de Posição",
  "entity": "JOBS",
  "type": "select",
  "required": true,
  "order": 6,
  "conditions": [{"sourceFieldId": "c54a1d18-fed0-4a11-92a8-25961f8efebc", "targetValue": "Rethink"}],
  "options": [
    {"value": "Projeto", "label": "Projeto"},
    {"value": "Alocação", "label": "Alocação"}
  ]
}
```

### Campo 7: "Torre" ⭐
```json
{
  "id": "86fb4dc5-5d7d-47f7-8772-37ccb45382df",
  "name": "Torre",
  "entity": "JOBS",
  "type": "select",
  "required": false,
  "order": 7,
  "options": [
    {"value": "Finanças e Varejo", "label": "Finanças e Varejo"},
    {"value": "Saúde e Indústria", "label": "Saúde e Indústria"}
  ]
}
```
**✅ JÁ SINCRONIZADO**

### Campo 8: "Empresa"
```json
{
  "id": "c54a1d18-fed0-4a11-92a8-25961f8efebc",
  "name": "Empresa",
  "entity": "JOBS",
  "type": "select",
  "required": true,
  "order": 8,
  "options": [
    {"value": "Framework", "label": "Framework"},
    {"value": "Rethink", "label": "Rethink"}
  ]
}
```
**✅ JÁ SINCRONIZADO**

### Campo 9: "Cliente Framework" ⭐
```json
{
  "id": "ebf9f14b-ad2e-4485-afd9-f6e69becf779",
  "name": "Cliente Framework",
  "entity": "JOBS",
  "type": "select",
  "required": true,
  "order": 9,
  "conditions": [{"sourceFieldId": "b3bfa235-ed27-4c86-b43e-766884c5bb57", "targetValue": "Operação"}],
  "options": [
    "PUC PR", "Hidrovias", "Mastercard", "Programa Feedback", "Afya",
    "Allos", "Arcelor Mittal", "Bancorbrás", "Black Ticket", "Cantu Pneus",
    "Care Plus", "Clamper", "D'Granel", "DB Diagnósticos", "Demarco",
    "Drogaria Araujo", "FIEMG", "Framework", "Group Software", "Grupo SFA",
    "Grupo Supernosso", "Grupo Zelo", "GTI Solution", "Hermes Pardini",
    "Hypofarma", "Inter", "JSL", "Localiza", "Mapa", "Mediquo",
    "Mercantil do Brasil", "MRV", "Pague Menos", "Pottencial", "Reserva",
    "Rumo Logística", "Salus Optima", "Sami Saúde", "Santander", "Sólides",
    "Supermix", "Syngenta", "Transpes", "Unifique", "Vamos", "Via Varejo",
    "Vila Nova", "Volvo", "Whirlpool"
    // ... (48 opções no total)
  ]
}
```
**✅ JÁ SINCRONIZADO**

### Campo 10: "Time Rethink"
```json
{
  "id": "a7025436-b763-4ad9-b5d0-86a5ee59408e",
  "name": "Time Rethink",
  "entity": "JOBS",
  "type": "select",
  "required": false,
  "order": 10,
  "conditions": [{"sourceFieldId": "c54a1d18-fed0-4a11-92a8-25961f8efebc", "targetValue": "Rethink"}],
  "options": [
    {"value": "Operação", "label": "Operação"},
    {"value": "Product", "label": "Product"}
  ]
}
```

### Campo 11: "Vertical"
```json
{
  "id": "4a9f550f-b2b4-4442-a398-708c1b594cdd",
  "name": "Vertical",
  "entity": "JOBS",
  "type": "select",
  "required": false,
  "order": 11,
  "conditions": [{"sourceFieldId": "a7025436-b763-4ad9-b5d0-86a5ee59408e", "targetValue": "Product"}],
  "options": [
    {"value": "Design", "label": "Design"},
    {"value": "Engineering", "label": "Engineering"},
    {"value": "Product", "label": "Product"}
  ]
}
```

### Campo 12: "Cliente Rethink" ⭐
```json
{
  "id": "25a7ff1b-e13c-467f-a282-8333082c266a",
  "name": "Cliente Rethink",
  "entity": "JOBS",
  "type": "select",
  "required": true,
  "order": 12,
  "conditions": [{"sourceFieldId": "c54a1d18-fed0-4a11-92a8-25961f8efebc", "targetValue": "Rethink"}],
  "options": [
    "SULGÁS", "JUNTO SEGUROS", "RETHINK", "COMGÁS", "ESFERA FIDELIDADE",
    "GOL LINHAS AÉREAS", "PAGOL", "SMILES", "NECTA GÁS NATURAL S.A.",
    "EDGE COMERCIALIZAÇÃO S.A", "SWIFT", "ECAD", "BANKLY"
    // ... (13 opções no total)
  ]
}
```
**✅ JÁ SINCRONIZADO**

### Campo 13: "Se substituição, informar colaborador"
```json
{
  "id": "bc659325-3335-4ce0-a1a8-be35c9f1ed13",
  "name": "Se substituição, informar o nome do colaborador e modalidade de contratação. Ex.: Mariana (CLT), Jade (PJ),",
  "entity": "JOBS",
  "type": "text",
  "required": true,
  "order": 13
}
```
**✅ JÁ SINCRONIZADO**

---

## 4️⃣ REQUISITIONS - Requisições (0 campos)

Nenhum campo customizado configurado para requisições.

---

## 📋 Campos Prioritários para Sincronização

### 🔴 Alta Prioridade (JOB_TALENTS)

1. **"Você conhecia a Framework Digital?"** 🎯
   - ID: `55282edb-bb11-4445-8cd6-3c0c6b9ddb9a`
   - **SOLICITADO PELO USUÁRIO**

2. **"É recrutamento interno?"**
   - ID: `58401823-2cf5-4e0c-93eb-07c46508eb3a`
   - Required: true

3. **"Modalidade de Contratação"**
   - ID: `745c6a26-c3fa-4389-9b1e-75f54934c9ae`
   - Required: true

4. **"Onde conheceu a Framework Digital?"**
   - ID: `1f50b961-7a55-4804-b9f9-20e0cbdb789b`

5. **"Modalidade de Trabalho"**
   - ID: `32df9b88-d37a-4fd2-8c84-1403736c9419`

### 🟡 Média Prioridade (TALENTS)

6. **"O Candidato já conhecia a Framework?"**
   - ID: `36564519-7214-46af-b02c-36b551dd170d`

7. **"Onde conheceu a Framework?"**
   - ID: `4a2af968-b11c-48a5-bdc9-7cbb369224cc`

8. **"Tem fluência em algum idioma"**
   - ID: `197ea7ce-979d-4aa9-9811-cb9a6257cef6`

### 🟢 Baixa Prioridade (JOBS)

Campos adicionais de vagas (complementar os 13 já sincronizados).

---

## 🔄 Estratégia de Implementação

### Fase 1: Adicionar Coluna custom_fields ✅
- Tabela: `candidaturas`
- Tipo: `JSON`
- Armazena: `{"field_id": ["valor1", "valor2"], ...}`

### Fase 2: Atualizar Sincronização
- Modificar `services/sync_service.py`
- Método: `_sync_candidaturas_full()`
- Salvar campo `customFields` da API

### Fase 3: Atualizar Modelo
- Arquivo: `models/database.py`
- Classe: `Candidatura`
- Adicionar: `custom_fields = Column(JSON)`

### Fase 4: Criar View Atualizada
- Extrair campos do JSON
- Criar colunas calculadas para principais campos

### Fase 5: Executar Sync
- Rodar sync completa para popular dados
- Validar dados do candidato ADLER

---

## 📊 Impacto Esperado

**Candidaturas com custom fields:** ~28.472 registros (2026)
**Novos dados disponíveis:** 5 campos por candidatura
**Tamanho estimado do JSON:** ~500 bytes por candidatura
**Armazenamento adicional:** ~14 MB

---

**Última atualização:** 2026-07-21 20:00
**Próximo passo:** Implementar sincronização de custom_fields em candidaturas
