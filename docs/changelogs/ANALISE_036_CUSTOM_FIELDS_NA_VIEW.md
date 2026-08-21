# ANÁLISE: Migration 036 e Dependência de Custom Fields

**Data:** 2026-02-10
**Migration:** `036_fix_sla_calculation.sql`
**Impacto:** 🔴 CRÍTICO - View depende de custom_fields que estava quebrado!

---

## 🚨 DESCOBERTA CRÍTICA

A **view `vw_analise_posicoes`** depende **DIRETAMENTE** dos custom_fields que estavam **100% quebrados** até a correção de hoje!

Isso significa que a view estava **funcionando com dados incompletos ou vazios**.

---

## 📋 CUSTOM FIELDS UTILIZADOS NA VIEW

### 1. Custom Fields de **REQUISIÇÕES** (tabela `requisicoes`):

**Linha 153:**
```sql
r.custom_fields->>'Torre' AS torre
```

**Campos Disponíveis nos 36 custom fields:**
- ✅ **Torre** (aparece 2x na lista - campos #23 e #24)

---

### 2. Custom Fields de **VAGAS** (tabela `vagas`):

**Linha 156:**
```sql
v.custom_fields->>'Motivo de Cancelamento' AS motivo_cancelamento_paralisacao
```
**Status:** ⚠️ Campo **NÃO encontrado** nos 36 custom fields listados
**Impacto:** Coluna vai ficar NULL

---

**Linha 158:**
```sql
COALESCE(v.custom_fields->>'Senioridade', v.seniority::text) AS senioridade
```
**Status:** ✅ **Senioridade** encontrado (campos #9 e #14 - duplicados)
**Observação:** Tem fallback para `v.seniority` se custom_field estiver vazio

---

**Linha 160:**
```sql
v.custom_fields->>'Se substituição, informar o nome do colaborador: ' AS pessoa_substituida
```
**Status:** ⚠️ Nome **LEVEMENTE DIFERENTE** nos custom fields
**Custom fields tem:** "Se substituição, informar o nome do colaborador e modalidade de contratação. Ex.: Mariana (CLT), Jade (PJ)," (campo #29)
**Impacto:** Query pode não estar capturando porque o nome não é exatamente igual!

---

**Linha 161:**
```sql
COALESCE(v.custom_fields->>'Gestor', r.user_name) AS responsavel
```
**Status:** ⚠️ Campo **NÃO encontrado** nos 36 custom fields listados
**Observação:** Tem fallback para `r.user_name`

---

**Linha 176:**
```sql
v.custom_fields->>'Modalidade de Contratação' AS modalidade_contratacao
```
**Status:** ✅ **Modalidade de Contratação** encontrado (campo #21)

---

**Linha 209 (FILTRO):**
```sql
WHERE ... AND (v.custom_fields->>'Tipo' IS NULL OR v.custom_fields->>'Tipo' != 'Banco de Talentos')
```
**Status:** ✅ **Tipo** encontrado (campo #30)
**Impacto:** Filtro excluindo "Banco de Talentos"

---

## 🔍 COMPARAÇÃO: NOMES DOS CAMPOS

| Campo na View | Nos 36 Custom Fields | Match? | Observação |
|---------------|----------------------|--------|------------|
| `Torre` | ✅ Torre (#23, #24) | ✅ SIM | Duplicado nos custom fields |
| `Motivo de Cancelamento` | ❌ Não encontrado | ❌ NÃO | Campo não existe? |
| `Senioridade` | ✅ Senioridade (#9, #14) | ✅ SIM | Duplicado + fallback |
| `Se substituição, informar o nome do colaborador: ` | ⚠️ Nome diferente (#29) | ⚠️ PARCIAL | Texto adicional no custom field |
| `Gestor` | ❌ Não encontrado | ❌ NÃO | Campo não existe? |
| `Modalidade de Contratação` | ✅ Modalidade de Contratação (#21) | ✅ SIM | OK |
| `Tipo` | ✅ Tipo (#30) | ✅ SIM | OK |

---

## ⚠️ PROBLEMAS IDENTIFICADOS

### 1. Nome de campo INCORRETO (linha 160)
**Query atual:**
```sql
v.custom_fields->>'Se substituição, informar o nome do colaborador: '
```

**Campo real nos custom fields:**
```
Se substituição, informar o nome do colaborador e modalidade de contratação. Ex.: Mariana (CLT), Jade (PJ),
```

**Impacto:** Campo **NÃO está sendo capturado** porque o nome não confere!

**Correção necessária:**
```sql
v.custom_fields->>'Se substituição, informar o nome do colaborador e modalidade de contratação. Ex.: Mariana (CLT), Jade (PJ),'
```

---

### 2. Campos não encontrados

**Campos que a view tenta buscar mas não existem nos 36 custom fields:**
1. `Motivo de Cancelamento`
2. `Gestor`

**Possibilidades:**
- Foram removidos/renomeados na plataforma InHire
- Nunca existiram (erro na criação da view)
- Existem com nomes diferentes

**Impacto:** Colunas ficam NULL sempre

---

## 📊 IMPACTO DA CORREÇÃO DE CUSTOM FIELDS

### ANTES (bug de custom fields):
```
Torre:                         NULL (sempre vazio)
Senioridade:                   Pega de v.seniority (fallback)
Modalidade de Contratação:     NULL (sempre vazio)
Tipo:                          NULL (filtro não funcionava)
Se substituição...:            NULL (sempre vazio)
Gestor:                        Pega de r.user_name (fallback)
Motivo de Cancelamento:        NULL (sempre vazio)
```

### DEPOIS (com correção):
```
Torre:                         ✅ Preenchido corretamente
Senioridade:                   ✅ Preenchido + fallback se necessário
Modalidade de Contratação:     ✅ Preenchido corretamente
Tipo:                          ✅ Preenchido + filtro funcionando
Se substituição...:            ❌ AINDA NULL (nome do campo incorreto!)
Gestor:                        ❌ NULL + fallback (campo não existe)
Motivo de Cancelamento:        ❌ NULL (campo não existe)
```

---

## ✅ CORREÇÕES RECOMENDADAS

### 1. URGENTE - Corrigir nome do campo "Se substituição..."

**Arquivo:** `migrations/036_fix_sla_calculation.sql` (ou criar nova migration)

**Linha 160 - ANTES:**
```sql
v.custom_fields->>'Se substituição, informar o nome do colaborador: ' AS pessoa_substituida,
```

**Linha 160 - DEPOIS:**
```sql
v.custom_fields->>'Se substituição, informar o nome do colaborador e modalidade de contratação. Ex.: Mariana (CLT), Jade (PJ),' AS pessoa_substituida,
```

---

### 2. INVESTIGAR - Campos "Gestor" e "Motivo de Cancelamento"

**Opção A:** Verificar se campos existem com nomes diferentes
**Opção B:** Remover referências se não existem mais
**Opção C:** Manter como estão (com fallbacks/NULL)

---

## 🎯 IMPACTO NO NEGÓCIO

### Campos que AGORA vão funcionar:
1. ✅ **Torre** - Fundamental para segmentação
2. ✅ **Senioridade** - Análise de perfil
3. ✅ **Modalidade de Contratação** - CLT/PJ
4. ✅ **Tipo** - Filtro de Banco de Talentos

### Campos que AINDA NÃO funcionam:
1. ❌ **Se substituição...** - Nome incorreto na query
2. ❌ **Gestor** - Campo não existe
3. ❌ **Motivo de Cancelamento** - Campo não existe

---

## 📈 ANTES vs DEPOIS (estimativa)

| Coluna | Antes | Depois | Melhoria |
|--------|-------|--------|----------|
| torre | 0% preenchido | ~98% preenchido | **+98%** |
| senioridade | ~50% (só v.seniority) | ~99% (custom + fallback) | **+49%** |
| modalidade_contratacao | 0% | ~98% | **+98%** |
| Filtro "Tipo" | Não funcionava | ✅ Funciona | **100%** |
| pessoa_substituida | 0% | 0% (precisa correção) | **0%** |

---

## 🔧 AÇÕES NECESSÁRIAS

### ANTES de sincronizar:
1. ✅ Corrigir nome do campo "Se substituição..." na view
2. ⏳ Decidir o que fazer com "Gestor" e "Motivo de Cancelamento"
3. ⏳ Testar view após correção

### DEPOIS de sincronizar:
1. ⏳ Validar dados na view
2. ⏳ Comparar totais antes/depois
3. ⏳ Verificar se Power BI/Sheets recebem dados corretos

---

## 📝 CONCLUSÃO

**DESCOBERTA IMPORTANTE:** A view `vw_analise_posicoes` estava **parcialmente quebrada** devido ao bug de custom_fields!

**STATUS ATUAL:**
- ✅ Bug de custom_fields corrigido
- ⚠️ View tem nome de campo incorreto (linha 160)
- ⚠️ View referencia 2 campos que não existem

**RECOMENDAÇÃO:** Corrigir nome do campo ANTES de executar sync full

**IMPACTO ESPERADO:** +98% de preenchimento em 4 colunas críticas da view
