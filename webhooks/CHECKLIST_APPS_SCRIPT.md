# ✅ CHECKLIST - Configuração Apps Script

**Status:** Pronto para implantar
**Credenciais necessárias:** Apenas TOKEN de segurança

---

## 📋 O QUE ESTÁ PRONTO

### Arquivos JavaScript (100% completos)

✅ `1_setup_token.js` - Gerador de token
✅ `2_setup_planilha.js` - Criador de abas
✅ `3_webhook_receiver.js` - Receptor principal

### Lógica Validada

✅ Processamento de webhooks testado localmente
✅ Formato de dados validado (CSV gerado com sucesso)
✅ Autenticação funcionando (Bearer token)
✅ 5 tipos de eventos suportados

---

## 🔐 CREDENCIAIS NECESSÁRIAS

### ❌ NÃO PRECISA (IMPORTANTE!)

- ❌ **NÃO** precisa de credenciais da API Inhire
- ❌ **NÃO** precisa de Service Account
- ❌ **NÃO** precisa de Client ID/Secret
- ❌ **NÃO** precisa de senha da Framework

**Por quê?** Webhooks são **RECEBIDOS** (Inhire → Você), não enviados (Você → Inhire)

### ✅ PRECISA APENAS

1. **Token de segurança** (você gera no Apps Script)
   - Gerado com `Utilities.getUuid()`
   - Exemplo: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
   - Usado para validar requests vindos da Inhire

---

## 📝 ONDE CONFIGURAR O TOKEN

### Arquivo 1: `1_setup_token.js`

**Linha:** Qualquer (só executar a função)
**Ação:** Executar `gerarToken()` e copiar o resultado

**Status:** ✅ Pronto (não precisa editar)

---

### Arquivo 2: `2_setup_planilha.js`

**Linha:** 21
```javascript
const CONFIG_SETUP = {
  SECRET_TOKEN: "SEU_TOKEN_AQUI",  // ← SUBSTITUIR
  TIMEZONE: "America/Sao_Paulo"
};
```

**Ação:** Substituir `SEU_TOKEN_AQUI` pelo token gerado no arquivo 1

**Status:** ⚠️ **PRECISA CONFIGURAR**

---

### Arquivo 3: `3_webhook_receiver.js`

**Linha:** 22
```javascript
const CONFIG = {
  SECRET_TOKEN: "SEU_TOKEN_AQUI",  // ← SUBSTITUIR
  // ...
};
```

**Ação:** Substituir `SEU_TOKEN_AQUI` pelo **MESMO** token usado no arquivo 2

**Status:** ⚠️ **PRECISA CONFIGURAR**

---

## 🚀 PASSO A PASSO DE IMPLANTAÇÃO

### PASSO 1: Gerar Token

1. Acesse: https://script.google.com
2. Crie novo projeto: "Webhook Inhire Framework"
3. Cole o código do arquivo `1_setup_token.js`
4. Execute a função `gerarToken()`
5. Copie o token que aparecer no log

**Exemplo de token:**
```
a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**⚠️ GUARDE ESTE TOKEN!** Você vai usar várias vezes.

---

### PASSO 2: Criar Abas da Planilha

1. **No mesmo projeto Apps Script**, substitua o código pelo do arquivo `2_setup_planilha.js`
2. **IMPORTANTE:** Na linha 21, cole o token que você gerou
3. Execute a função `criarEstruturaPlanilha()`
4. Autorize permissões se pedir
5. Volte na planilha e verifique se as 6 abas foram criadas

**Abas criadas:**
- Candidaturas
- Mudanças de Etapa
- Novas Vagas
- Formulários
- Requisições
- Log de Eventos

---

### PASSO 3: Implantar Webhook Receiver

1. **No mesmo projeto Apps Script**, substitua o código pelo do arquivo `3_webhook_receiver.js`
2. **IMPORTANTE:** Na linha 22, cole o **MESMO** token
3. Salve (Ctrl+S)
4. Clique em "Implantar" > "Nova implantação"
5. Tipo: **Aplicativo da Web**
6. Configurações:
   - **Executar como:** Eu (seu email)
   - **Quem tem acesso:** Qualquer pessoa
7. Clique "Implantar"
8. **COPIE A URL** gerada (algo como `https://script.google.com/macros/s/AKfycbx.../exec`)

**⚠️ GUARDE ESTA URL!** Você vai usar na Inhire.

---

### PASSO 4: Configurar Webhooks na Inhire

Acesse: https://app.inhire.app/tenants/frameworkdigital/settings/integrations/webhooks

**Criar 5 webhooks:**

#### Webhook 1: Candidaturas
- **Nome:** Candidaturas → Google Sheets
- **Evento:** JOB_TALENT_ADDED
- **URL:** `https://script.google.com/macros/s/SEU_ID/exec/job-talent-added`
- **Método:** POST
- **Header:**
  - Nome: `Authorization`
  - Valor: `Bearer SEU_TOKEN_AQUI`
- **Status:** ✅ Ativo

#### Webhook 2: Mudanças de Etapa
- **Nome:** Mudanças de Etapa → Google Sheets
- **Evento:** JOB_TALENT_STAGE_ADDED
- **URL:** `https://script.google.com/macros/s/SEU_ID/exec/job-talent-stage-added`
- **Método:** POST
- **Header:** `Authorization: Bearer SEU_TOKEN_AQUI`
- **Status:** ✅ Ativo

#### Webhook 3: Novas Vagas
- **Nome:** Novas Vagas → Google Sheets
- **Evento:** JOB_ADDED
- **URL:** `https://script.google.com/macros/s/SEU_ID/exec/job-added`
- **Método:** POST
- **Header:** `Authorization: Bearer SEU_TOKEN_AQUI`
- **Status:** ✅ Ativo

#### Webhook 4: Formulários
- **Nome:** Formulários → Google Sheets
- **Evento:** FORM_RESPONSE_ADDED
- **URL:** `https://script.google.com/macros/s/SEU_ID/exec/form-response-added`
- **Método:** POST
- **Header:** `Authorization: Bearer SEU_TOKEN_AQUI`
- **Status:** ✅ Ativo

#### Webhook 5: Requisições
- **Nome:** Requisições → Google Sheets
- **Evento:** REQUISITION_STATUS_UPDATED
- **URL:** `https://script.google.com/macros/s/SEU_ID/exec/requisition-status-updated`
- **Método:** POST
- **Header:** `Authorization: Bearer SEU_TOKEN_AQUI`
- **Status:** ✅ Ativo

**⚠️ IMPORTANTE:**
- Todos os webhooks usam o **MESMO** token
- Cada webhook tem URL diferente (final da URL muda)
- Header SEMPRE: `Authorization: Bearer SEU_TOKEN`

---

## 🧪 TESTAR

### Teste 1: Health Check

Acesse no navegador:
```
https://script.google.com/macros/s/SEU_ID/exec
```

Deve retornar:
```json
{
  "service": "Inhire Webhook Receiver",
  "status": "running",
  "message": "Use POST para enviar webhooks"
}
```

### Teste 2: Evento Real

1. Adicione uma candidatura a uma vaga na Inhire
2. Aguarde 5-10 segundos
3. Verifique a aba "Candidaturas" na planilha
4. Deve aparecer uma nova linha com os dados

---

## 📊 RESUMO DE CONFIGURAÇÃO

| Item | Status | Onde Configurar |
|------|--------|-----------------|
| Token gerado | ⚠️ **FAZER** | Apps Script > `gerarToken()` |
| Token no arquivo 2 | ⚠️ **FAZER** | `2_setup_planilha.js` linha 21 |
| Token no arquivo 3 | ⚠️ **FAZER** | `3_webhook_receiver.js` linha 22 |
| Abas criadas | ⚠️ **FAZER** | Executar `criarEstruturaPlanilha()` |
| Web App implantado | ⚠️ **FAZER** | Implantar > Nova implantação |
| URL copiada | ⚠️ **FAZER** | Guardar URL do Web App |
| 5 webhooks na Inhire | ⚠️ **FAZER** | Configurar cada um |
| Header Authorization | ⚠️ **FAZER** | `Bearer TOKEN` em cada webhook |

---

## ✅ CHECKLIST FINAL

Antes de testar em produção:

- [ ] Token gerado e guardado
- [ ] Token configurado no arquivo 2 (linha 21)
- [ ] Token configurado no arquivo 3 (linha 22)
- [ ] 6 abas criadas na planilha
- [ ] Web App implantado
- [ ] URL do Web App copiada
- [ ] 5 webhooks configurados na Inhire
- [ ] Todos os webhooks com header `Authorization: Bearer TOKEN`
- [ ] Todos os webhooks ativos
- [ ] Health check testado (GET na URL)

**Se TODOS marcados:** ✅ **PRONTO PARA RECEBER DADOS REAIS!**

---

## 🎯 EXPECTATIVA

**Após configurar:**
- ✅ Cada ação na Inhire dispara webhook
- ✅ Webhook chega no Apps Script em ~5 segundos
- ✅ Dados são processados
- ✅ Nova linha aparece na planilha
- ✅ Log é registrado
- ✅ Tudo automático, sem intervenção

**Custo:** R$ 0 (quota gratuita do Google)
**Manutenção:** Zero
**Latência:** ~5 segundos

---

**Criado em:** 2026-06-26
**Versão:** 1.0
**Status:** ✅ Pronto para implantação
