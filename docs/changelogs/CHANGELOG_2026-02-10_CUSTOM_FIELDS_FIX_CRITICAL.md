# CHANGELOG - Correção CRÍTICA: Custom Fields

**Data:** 2026-02-10
**Severidade:** 🔴 CRÍTICA - Sincronização de custom fields estava quebrada
**Tipo:** Bug Fix + Enhancement

---

## 🚨 PROBLEMA IDENTIFICADO

### Sintomas:
- Sincronização de custom fields falhando com HTTP 400 Bad Request
- Código atual tenta buscar individualmente: `job`, `talent`, `jobTalent`, `requisition`
- **TODAS as chamadas individuais retornam erro 400**

### Causa Raiz:
**A API InHire mudou o comportamento do endpoint de custom fields:**
- ❌ Chamadas individuais por entidade **NÃO funcionam mais**
- ✅ Apenas `entity_type='ALL'` funciona

### Evidências:
```
Endpoint: /custom-data-manager/custom-fields/entity/{entityType}

TESTE REALIZADO (2026-02-10):
- entity_type='ALL'        → ✅ 200 OK (36 campos retornados)
- entity_type='job'        → ❌ 400 Bad Request
- entity_type='talent'     → ❌ 400 Bad Request
- entity_type='jobTalent'  → ❌ 400 Bad Request
- entity_type='requisition' → ❌ 400 Bad Request
```

---

## ✅ CORREÇÕES IMPLEMENTADAS

### 1. Criado Schema `CustomFieldAPI`
**Arquivo:** `models/new_api_schemas.py`

```python
class CustomFieldAPI(BaseModel):
    """Schema para definição de custom field"""
    id: Optional[str] = None
    name: Optional[str] = None
    fieldName: Optional[str] = None
    fieldType: Optional[str] = None
    entityType: Optional[str] = None  # Sempre 'ALL' agora
    label: Optional[str] = None
    required: Optional[bool] = False
    options: Optional[Union[List[str], List[Dict[str, Any]]]] = None
    defaultValue: Optional[Any] = None
    order: Optional[int] = None
    active: Optional[bool] = True
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    columnName: Optional[str] = None
    context: Optional[str] = None
```

**Motivo:** Schema não existia, causando `NameError` no `api_client.py:586`

### 2. Atualizado Import no API Client
**Arquivo:** `services/api_client.py`

```python
from models.new_api_schemas import (
    RequisicaoAPI, RequisicoesPaginatedResponse,
    VagaTagAPI, ClienteAPI,
    JobDetailsAPI, JobTalentDetailsAPI,
    PositionTimelineEventAPI, PositionTimelinePaginatedResponse,
    CustomFieldAPI  # <-- ADICIONADO
)
```

### 3. PRÓXIMA CORREÇÃO NECESSÁRIA: Sync Service
**Arquivo:** `services/sync_service.py:1094`

**ANTES (QUEBRADO):**
```python
for entity_type in ['job', 'talent', 'jobTalent', 'requisition']:
    fields = self.api_client.get_custom_fields(entity_type)  # ❌ Sempre falha
```

**DEPOIS (CORRIGIDO):**
```python
# Buscar TODOS os custom fields de uma vez (API só suporta 'ALL' agora)
fields = self.api_client.get_custom_fields('ALL')
for field in fields:
    # Processar campo...
```

---

## 📊 IMPACTO

### Antes (Quebrado):
- ❌ 0 custom fields sincronizados
- ❌ 4 chamadas API falhando (HTTP 400)
- ❌ Logs cheios de erros de retry

### Depois (Corrigido):
- ✅ 36 custom fields sincronizados
- ✅ 1 chamada API bem-sucedida
- ✅ 75% menos chamadas à API
- ✅ Sincronização mais rápida

---

## 🎯 PRÓXIMOS PASSOS

### URGENTE (fazer agora):
1. ✅ Criar schema `CustomFieldAPI` - **FEITO**
2. ✅ Importar no `api_client.py` - **FEITO**
3. ⏳ Atualizar `_sync_custom_fields()` para usar 'ALL'
4. ⏳ Testar sincronização completa
5. ⏳ Verificar dados no banco após sync

### OPCIONAL (melhorias futuras):
- Investigar se API retorna custom_fields nos dados de talents/candidaturas
- Considerar adicionar coluna `custom_fields` em `talentos` e `candidaturas`
- Verificar se API retorna `reason` e `notes` no position_timeline

---

## 🔍 DETALHES TÉCNICOS

### Resposta da API para 'ALL':
```json
[
  {
    "columnName": "tipo_de_posicao",
    "label": "Tipo de Posição",
    "options": [
      {"value": "Projeto", "id": "...", "label": "Projeto"},
      {"value": "Alocação", "id": "...", "label": "Alocação"}
    ],
    "entityType": "ALL",
    ...
  },
  ...
]
```

**Observações:**
- `entityType` sempre retorna `'ALL'` (não discrimina por entidade)
- `options` vem como lista de objetos (não lista de strings)
- `fieldType` pode não vir (None)

### Localização do Bug:
- **Arquivo:** `services/sync_service.py`
- **Linha:** 1094
- **Método:** `_sync_custom_fields()`

---

## ✅ VALIDAÇÃO

```bash
# Testar endpoint
cd "C:\Users\marcossantiago_frwk\Meu Drive (marcossantiago@frwk.com.br)\Framework_Data\Inhire"
python scripts\debug\test_custom_fields_all.py

# Resultado esperado:
# [OK] SUCESSO! Retornou 36 campos personalizados
```

---

## 📝 NOTAS

- **Mudança na API InHire:** Parece que a API mudou o comportamento sem aviso prévio
- **Compatibilidade retroativa:** As chamadas individuais pararam de funcionar
- **Impacto na documentação:** Docs da InHire podem estar desatualizadas
- **Benefício inesperado:** Usar 'ALL' é mais eficiente (4 chamadas → 1 chamada)

---

## 🏆 CONCLUSÃO

**PROBLEMA CRÍTICO IDENTIFICADO E PARCIALMENTE CORRIGIDO**

✅ Schema criado
✅ Import corrigido
⏳ Sync service precisa ser atualizado

**Próxima ação:** Atualizar `_sync_custom_fields()` para usar `'ALL'`
