# CHANGELOG - Correção CRÍTICA: View vw_analise_posicoes

**Data:** 2026-02-10
**Severidade:** 🔴 CRÍTICA
**Tipo:** Bug Fix - Referência incorreta de custom_fields

---

## 🚨 PROBLEMA IDENTIFICADO

A view `vw_analise_posicoes` tem **ERRO ESTRUTURAL** na extração de custom_fields!

### Diferença de Estrutura:

| Tabela | Coluna | Tipo | Estrutura | Acesso |
|--------|--------|------|-----------|--------|
| `vagas` | `custom_fields` | JSONB | **DICIONÁRIO** `{key: value}` | ✅ `v.custom_fields->>'Campo'` |
| `requisicoes` | `custom_fields` | JSON | **ARRAY** `[{name, value}]` | ❌ `r.custom_fields->>'Campo'` NÃO funciona |

**Exemplo de Requisição:**
```json
[
  {"name": "Cliente", "value": "Localiza"},
  {"name": "Área", "value": "Operação"},
  {"name": "Modalidade de Contratação", "value": "CLT"},
  {"name": "Senioridade", "value": "Sênior"}
]
```

**Acesso correto para ARRAY:**
```sql
-- Não funciona:
r.custom_fields->>'Torre'

-- Funciona:
(SELECT elem->>'value'
 FROM json_array_elements(r.custom_fields) elem
 WHERE elem->>'name' = 'Torre')
```

---

## ❌ ERROS NA VIEW (Linha 153)

**ERRO ATUAL:**
```sql
r.custom_fields->>'Torre' AS torre
```

**Problemas:**
1. ❌ `Torre` está em **VAGAS**, não em REQUISIÇÕES!
2. ❌ Mesmo se estivesse, sintaxe não funciona para ARRAY
3. ✅ Mas funciona por acidente porque Torre vem de vagas

**Resultado:** Coluna `torre` funciona, mas **por sorte**, não por design!

---

## ✅ CORREÇÃO NECESSÁRIA

### Opção 1: Buscar de Vagas (RECOMENDADO)

**ANTES (linha 153):**
```sql
r.custom_fields->>'Torre' AS torre,
```

**DEPOIS:**
```sql
v.custom_fields->>'Torre' AS torre,
```

**Motivo:** Torre está em vagas.custom_fields

---

### Opção 2: Se Torre TAMBÉM estiver em Requisições

```sql
COALESCE(
    v.custom_fields->>'Torre',
    (SELECT elem->>'value'
     FROM json_array_elements(r.custom_fields) elem
     WHERE elem->>'name' = 'Torre')
) AS torre,
```

---

## 📊 CAMPOS NO BANCO

### CUSTOM FIELDS EM VAGAS (DICIONÁRIO - 32 campos):

```
 1. Área
 2. Cancelamento
 3. Certificação
 4. Cliente
 5. Cliente Framework
 6. Cliente Rethink
 7. Custo Hora (ideal) - Ex. R$ xx,xx
 8. Custo Hora (máximo) - Ex. R$ xx,xx
 9. É recrutamento interno?
10. Empresa
11. Formação Acadêmica
12. Gestor ✅ (existe!)
13. Idioma
14. Modalidade de Contratação
15. Motivo de Cancelamento ✅ (existe!)
16. Motivo de Congelamento
17. Onde conheceu a Framework Digital?
18. Recrutador da vaga
19. Responsável
20. Se substituição, informar o nome do colaborador e modalidade de contratação. Ex.: Mariana (CLT), Jade (PJ),
21. Se substituição, informar o nome do colaborador:  ✅ (existe!)
22. Senioridade
23. Sub-motivo da Requisição
24. Sub-motivo da requisição
25. Time Rethink
26. Tipo
27. Tipo de Posição
28. Torre ✅ (existe!)
29. Vaga afirmativa
30. Vaga PCD
31. Vertical
32. Você conhecia a Framework Digital?
```

### CUSTOM FIELDS EM REQUISIÇÕES (ARRAY - 4 campos):

```
1. Cliente
2. Área
3. Modalidade de Contratação
4. Senioridade
```

**Observação:** Torre **NÃO** está em requisições!

---

## 🔍 VALIDAÇÃO DOS CAMPOS DA VIEW

| Linha | Campo Buscado | Tabela | Status | Observação |
|-------|---------------|--------|--------|------------|
| 153 | Torre | `r` (req) | ⚠️ **ERRO DE TABELA** | Torre está em vagas, não requisições! |
| 156 | Motivo de Cancelamento | `v` (vagas) | ✅ OK | Campo #15 - existe |
| 158 | Senioridade | `v` (vagas) | ✅ OK | Campo #22 - existe |
| 160 | Se substituição, informar o nome do colaborador:  | `v` (vagas) | ✅ OK | Campo #21 - existe com esse nome exato! |
| 161 | Gestor | `v` (vagas) | ✅ OK | Campo #12 - existe |
| 176 | Modalidade de Contratação | `v` (vagas) | ✅ OK | Campo #14 - existe |
| 209 | Tipo | `v` (vagas) | ✅ OK | Campo #26 - existe |

**SURPRESA:** Todos os campos existem! A única análise anterior incorreta foi sobre "Gestor" e "Motivo de Cancelamento"!

**PROBLEMA REAL:** Apenas a referência de Torre está errada (busca em `r` mas deveria buscar em `v`)

---

## 📋 CAMPOS DUPLICADOS NO BANCO

Alguns campos aparecem 2x (evolução da plataforma):

1. **"Se substituição..."** - 2 versões:
   - Campo #20: Texto longo com exemplo
   - Campo #21: Texto curto (usado pela view)

2. **"Sub-motivo da Requisição"** - 2 versões:
   - Campo #23: Maiúscula
   - Campo #24: Minúscula

---

## ✅ MIGRATION DE CORREÇÃO

Criar arquivo: `migrations/043_fix_torre_reference_in_view.sql`

```sql
/*
================================================================================
MIGRATION 043: Corrigir Referência de Torre na View
================================================================================

Data: 2026-02-10
Descrição:
  Corrige referência incorreta de Torre que estava buscando de requisições
  quando na verdade o campo está em vagas.

PROBLEMA:
  r.custom_fields->>'Torre' (sempre NULL - campo não existe em requisições)

SOLUÇÃO:
  v.custom_fields->>'Torre' (campo existe em vagas)

================================================================================
*/

DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;

CREATE OR REPLACE VIEW vw_analise_posicoes AS
WITH ultima_etapa AS (
    ...
)
SELECT
    p.id AS id_position,
    v.name AS cargo,
    DATE(r.requested_at) AS data_abertura,
    DATE(p.opened_at) AS data_publicacao,
    v.sla_days_goal AS prazo_processo_seletivo,
    c.name AS cliente,
    v.custom_fields->>'Torre' AS torre,  -- ✅ CORRIGIDO: busca de vagas
    ...
FROM posicoes p
    INNER JOIN vagas v ON p.vaga_id = v.id
    LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
    ...
```

---

## 📊 IMPACTO ESPERADO

### ANTES da correção:
```
Torre: Funciona por sorte (busca lugar errado mas campo existe em vagas)
```

### DEPOIS da correção:
```
Torre: Funciona corretamente (busca lugar certo)
```

**Impacto Visual:** Nenhum (já funcionava por coincidência)
**Impacto Técnico:** Código correto e manutenível
**Impacto Futuro:** Se Torre for removido de vagas, view não quebra inesperadamente

---

## 🎯 AÇÕES RECOMENDADAS

### URGENTE:
1. ✅ Criar migration 043 corrigindo referência de Torre
2. ⏳ Aplicar migration ANTES de sync full
3. ⏳ Validar view após correção

### OPCIONAL:
1. ⏳ Documentar que requisições.custom_fields é ARRAY, não DICT
2. ⏳ Criar função helper para extrair campos de ARRAY em requisições
3. ⏳ Verificar se outros campos deveriam vir de requisições

---

## 📝 CONCLUSÃO

**STATUS:** Problema identificado e correção disponível

**DESCOBERTAS:**
1. ✅ Todos os 7 campos custom da view EXISTEM no banco
2. ⚠️ 1 campo (Torre) busca tabela errada
3. ✅ Estruturas diferentes: Vagas=DICT, Requisições=ARRAY
4. ✅ View funciona, mas mais por sorte que por design

**RECOMENDAÇÃO:** Aplicar migration 043 para corrigir referência

**PRIORIDADE:** MÉDIA (funciona, mas código está tecnicamente incorreto)
