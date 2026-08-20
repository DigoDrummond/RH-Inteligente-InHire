# Nota: Campo "Você conhecia a Framework Digital?"

**Data:** 2026-07-21
**Status:** ❌ Campo não encontrado nos dados sincronizados

---

## 📋 Contexto

Foi solicitado incluir no relatório de candidaturas a resposta à pergunta customizada:

> **"Você conhecia a Framework Digital?"**

Essa pergunta faz parte do **"Formulário de Inscrição Frame"** e candidatos respondem com opções como "Sim" ou "Não".

### Exemplo Real

- **Candidato:** ADLER ROBERTO NICOLELLA
- **Email:** adlerbcc95@hotmail.com
- **Vaga:** Desenvolvedor .NET Sênior (Pottencial)
- **Resposta esperada:** "Sim"

---

## 🔍 Investigação Realizada

Foram investigados todos os locais possíveis onde esse campo poderia estar armazenado:

### 1. ❌ talentos.attributes
- **Resultado:** Campo vazio para o candidato ADLER
- **Verificado em:** `talentos.attributes` (JSON)

### 2. ❌ talentos.jobs[].customFields
- **Resultado:** Contém apenas campos da **vaga** (Área, Senioridade, Torre, Tipo)
- **Exemplo encontrado:**
  ```json
  {
    "name": "Senioridade",
    "value": "Sênior"
  }
  ```
- **Verificado em:** `talentos.jobs[].customFields` (JSON Array)

### 3. ❌ candidaturas.stage_metadata
- **Resultado:** Contém apenas metadados do stage (id, name, type, order, userId, userName, timestamps)
- **Não há campos customizados**
- **Verificado em:** `candidaturas.stage_metadata` (JSON)

### 4. ❌ candidaturas.phase_metadata
- **Resultado:** Campo vazio (NULL)
- **Verificado em:** `candidaturas.phase_metadata` (JSON)

### 5. ❌ vagas.custom_fields
- **Resultado:** Contém apenas campos da **vaga** (Tipo, Torre, Área, Senioridade)
- **Verificado em:** `vagas.custom_fields` (JSON)

### 6. ❌ requisicoes.custom_fields
- **Resultado:** Contém apenas campos da **requisição** (Custo Hora, Vertical, Cliente, etc.)
- **Verificado em:** `requisicoes.custom_fields` (JSON)

---

## 🎯 Conclusão

### O que foi encontrado:
✅ Campos customizados de **vagas** (Senioridade, Área, Torre, etc.)
✅ Campos customizados de **requisições** (Custo Hora, Cliente, etc.)
✅ Campos customizados de **preferências de trabalho do talento** (via talentos.jobs)

### O que NÃO foi encontrado:
❌ Campos customizados de **formulário de inscrição da candidatura**
❌ Respostas a perguntas do formulário de inscrição
❌ Campo "Você conhecia a Framework Digital?"

---

## 💡 Possíveis Causas

### 1. API Inhire não retorna esse campo
A API pode não estar incluindo respostas de formulários de inscrição nos endpoints que estamos usando:
- `GET /jobs/{id}/job-talents` (candidaturas por vaga)
- `GET /talents/{id}` (dados do talento)
- `POST /talents/paginated` (lista de talentos)

### 2. Endpoint específico necessário
Pode haver um endpoint específico para buscar respostas de formulários de inscrição que ainda não está sendo utilizado:
- `GET /job-talents/{id}/form-responses` (?)
- `GET /job-talents/{id}/application-fields` (?)

### 3. Campo só disponível via interface web
O campo pode estar disponível apenas via interface web do Inhire, sem estar exposto pela API.

---

## 🔄 Próximos Passos Recomendados

### 1. Consultar Documentação Inhire API
- Verificar documentação oficial da API Inhire
- Procurar por endpoints relacionados a:
  - Application forms
  - Custom form responses
  - Application custom fields

### 2. Contatar Suporte Inhire
Perguntas para o suporte:

```
Olá equipe Inhire,

Estamos sincronizando dados via API e precisamos acessar respostas de
campos customizados do "Formulário de Inscrição" das candidaturas.

Especificamente, queremos a resposta à pergunta:
"Você conhecia a Framework Digital?"

Já verificamos os seguintes endpoints e campos:
- GET /talents/{id} → talents.attributes (vazio)
- GET /talents/{id} → talents.jobs[].customFields (só tem campos de vaga)
- GET /jobs/{id}/job-talents → stage/phase metadata (sem custom fields)

Pergunta: Qual endpoint ou campo retorna as respostas do formulário de
inscrição da candidatura?

Obrigado!
```

### 3. Verificar logs da API
- Examinar response completo da API para buscar campos não mapeados
- Verificar se há campos adicionais sendo retornados mas não salvos no BD

---

## 📝 Solução Temporária Aplicada

Enquanto o campo não é localizado, a view `vw_relatorio_candidaturas` foi criada com:

```sql
-- Placeholder para campo customizado
NULL::text AS conhecia_framework
```

**Quando o campo for localizado:**
1. Atualizar migration para extrair o campo corretamente
2. Remover o placeholder NULL
3. Testar com casos reais (ex: ADLER ROBERTO NICOLELLA)

---

## 📊 Estrutura Atual da View

A view `vw_relatorio_candidaturas` foi criada com os seguintes campos:

```sql
SELECT
    c.id,
    c.vaga_id,
    v.name AS vaga_nome,              -- ✅ IMPLEMENTADO
    c.status,
    c.talent_name,
    c.talent_email,
    c.stage_name AS etapa_candidatura,-- ✅ IMPLEMENTADO
    c.status AS status_candidatura,   -- ✅ IMPLEMENTADO
    NULL::text AS conhecia_framework, -- ❌ PENDENTE
    c.created_at,
    c.updated_at_inhire
FROM candidaturas c
INNER JOIN vagas v ON c.vaga_id = v.id
WHERE EXTRACT(YEAR FROM c.created_at) = 2026;
```

---

## 📂 Arquivos Relacionados

### Scripts de Investigação:
- `reports/buscar_resposta_adler.py` - Busca específica do candidato ADLER
- `reports/investigar_campo_framework.py` - Investigação geral
- `reports/investigar_custom_fields_candidatura.py` - Investigação de custom fields

### Migrations:
- `migrations/068_add_vaga_name_candidaturas_view.sql` - View com placeholder

### Documentação:
- `reports/NOTA_CAMPO_CONHECIA_FRAMEWORK.md` - Este arquivo

---

## ✅ Próxima Revisão

**Quando:** Após resposta do suporte Inhire ou descoberta de novo endpoint

**Atualizar:**
1. Este documento com a solução encontrada
2. Migration 068 com extração correta do campo
3. View `vw_relatorio_candidaturas` com dados reais
4. Testar com candidato ADLER ROBERTO NICOLELLA

---

**Última atualização:** 2026-07-21
**Responsável:** Sistema de Sincronização Inhire
**Status:** Aguardando investigação adicional ou resposta do suporte Inhire
