# Guia Passo a Passo - Configuração na Inhire

**Tempo estimado:** 10-15 minutos
**Pré-requisitos:**
- ✅ Token gerado (Passo 1 concluído)
- ✅ Abas criadas (Passo 2 concluído)
- ✅ Web App implantado (URL copiada)

---

## 📋 O Que Você Vai Criar

Ao final, você terá **5 webhooks** configurados:

| # | Nome | Evento | Quando Dispara |
|---|------|--------|----------------|
| 1 | Candidaturas | `JOB_TALENT_ADDED` | Candidato se inscreve |
| 2 | Mudanças de Etapa | `JOB_TALENT_STAGE_ADDED` | Candidato muda de etapa |
| 3 | Novas Vagas | `JOB_ADDED` | Vaga criada |
| 4 | Formulários | `FORM_RESPONSE_ADDED` | Formulário respondido |
| 5 | Requisições | `REQUISITION_STATUS_UPDATED` | Requisição aprovada/rejeitada |

---

## 🔐 PASSO 1: Acessar a Inhire

### 1.1 Fazer Login

1. Acesse: **https://app.inhire.com.br**

2. Faça login com **QUALQUER conta da Framework**:
   ```
   Email: sua-conta@framework.com (ou qualquer email autorizado)
   Senha: sua senha
   ```

3. Selecione o tenant:
   ```
   Tenant: frameworkdigital
   ```

**✅ Pronto!** Você está logado.

⚠️ **IMPORTANTE:** Não precisa usar credenciais especiais. Qualquer conta com acesso ao tenant Framework serve.

---

## 🔧 PASSO 2: Acessar Área de Webhooks

### 2.1 Navegação

1. **Menu lateral esquerdo** → Procure por **"Integrações"** ou **"Configurações"**

   ```
   ┌─────────────────────────┐
   │ 📊 Dashboard            │
   │ 💼 Vagas                │
   │ 👥 Candidatos           │
   │ 📋 Requisições          │
   │ ...                     │
   │ ⚙️  Configurações       │  ← Clique aqui
   │   ├─ Geral              │
   │   ├─ Usuários           │
   │   └─ Integrações        │  ← Ou aqui
   └─────────────────────────┘
   ```

2. Clique em **"Integrações"**

3. Procure pela aba ou seção **"Webhooks"**

   ```
   ┌──────────────────────────────────────┐
   │ Integrações                          │
   ├──────────────────────────────────────┤
   │ [API Keys] [Webhooks] [SSO] [...]   │
   │            ^^^^^^^^                  │
   │            Clique aqui               │
   └──────────────────────────────────────┘
   ```

**✅ Você está na tela de Webhooks!**

---

## ➕ PASSO 3: Criar Primeiro Webhook (Candidaturas)

### 3.1 Iniciar Criação

1. Clique no botão **"+ Novo Webhook"** ou **"Adicionar Webhook"**

   ```
   ┌────────────────────────────────────────────────┐
   │ Webhooks                    [+ Novo Webhook]  │
   │                                                │
   │ Nenhum webhook configurado.                    │
   └────────────────────────────────────────────────┘
   ```

2. Um formulário vai abrir (modal ou nova página)

---

### 3.2 Preencher Formulário - Webhook 1 (Candidaturas)

Preencha **EXATAMENTE** estes campos:

#### **Campo 1: Nome do Webhook**
```
┌─────────────────────────────────────────────┐
│ Nome: Candidaturas → Google Sheets         │
└─────────────────────────────────────────────┘
```

**Valor:** `Candidaturas → Google Sheets`

**Observação:** Nome é só para você identificar. Pode ser qualquer coisa.

---

#### **Campo 2: Descrição** (opcional)
```
┌─────────────────────────────────────────────┐
│ Descrição: Registra novas candidaturas     │
│            automaticamente na planilha      │
└─────────────────────────────────────────────┘
```

**Valor:** `Registra novas candidaturas automaticamente na planilha`

---

#### **Campo 3: Evento** ⚠️ IMPORTANTE!
```
┌─────────────────────────────────────────────┐
│ Evento: [Selecione um evento ▼]            │
│                                             │
│ 🔽 Dropdown com opções:                    │
│    - JOB_ADDED                              │
│    - JOB_UPDATED                            │
│    - JOB_TALENT_ADDED          ← SELECIONE │
│    - JOB_TALENT_STAGE_ADDED                │
│    - FORM_RESPONSE_ADDED                    │
│    - REQUISITION_STATUS_UPDATED             │
│    - ...                                    │
└─────────────────────────────────────────────┘
```

**Valor:** Selecione **`JOB_TALENT_ADDED`**

⚠️ **ATENÇÃO:** Este é o evento que dispara quando candidato se inscreve!

---

#### **Campo 4: URL de Destino** ⚠️ MUITO IMPORTANTE!
```
┌─────────────────────────────────────────────────────────────────┐
│ URL: https://script.google.com/macros/s/AKfycbxXXXXX/exec/     │
│      job-talent-added                                          │
│      └───────────── URL do Apps Script ──────────┘└─ Path ──┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Valor:**
```
https://script.google.com/macros/s/AKfycbxXXXXXXXXXXXXXXX/exec/job-talent-added
```

**Como montar:**
1. Pegue a URL do Apps Script (que você copiou no Passo 4)
2. Adicione `/job-talent-added` no final

**Exemplo:**
```
URL do Apps Script:
https://script.google.com/macros/s/AKfycbxABC123/exec

URL final do webhook:
https://script.google.com/macros/s/AKfycbxABC123/exec/job-talent-added
                                                       └─ Adicionar isto ─┘
```

⚠️ **ATENÇÃO:**
- NÃO esqueça o `/job-talent-added` no final!
- NÃO adicione espaços
- Use HTTPS (não HTTP)

---

#### **Campo 5: Método HTTP**
```
┌─────────────────────────────────────────────┐
│ Método: [GET ▼] [POST ▼] [PUT ▼]           │
│                 ^^^^^^                       │
│                 Selecione POST              │
└─────────────────────────────────────────────┘
```

**Valor:** Selecione **`POST`**

---

#### **Campo 6: Headers** ⚠️ CRÍTICO!

Esta é a parte da **autenticação**!

```
┌─────────────────────────────────────────────────────────┐
│ Headers:                         [+ Adicionar Header]   │
│                                                          │
│ ┌────────────────┬──────────────────────────────────┐  │
│ │ Nome           │ Valor                            │  │
│ ├────────────────┼──────────────────────────────────┤  │
│ │ Authorization  │ Bearer abc123-def456-ghi789     │  │
│ │                │ └────┘ └──── SEU TOKEN ─────┘   │  │
│ └────────────────┴──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Como adicionar:**

1. Clique em **"+ Adicionar Header"** ou **"+ Novo Header"**

2. Um formulário com 2 campos vai aparecer:

   **Campo A - Nome do Header:**
   ```
   Nome: Authorization
   ```

   **Campo B - Valor do Header:**
   ```
   Valor: Bearer a1b2c3d4-e5f6-7890-abcd-ef1234567890
          └────┘ └──────────── SEU TOKEN ────────────┘
          Fixo   (gerado no Passo 1)
   ```

**⚠️ SUPER IMPORTANTE:**
- Palavra `Bearer` com **B maiúsculo**
- **1 espaço** depois de "Bearer"
- Token **EXATAMENTE igual** ao configurado no código
- Não adicione aspas, parênteses ou outros caracteres

**Exemplo correto:**
```
✅ Bearer a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Exemplos ERRADOS:**
```
❌ bearer a1b2c3d4...           (bearer minúsculo)
❌ Bearer  a1b2c3d4...          (2 espaços)
❌ Bearera1b2c3d4...            (sem espaço)
❌ "Bearer a1b2c3d4..."         (com aspas)
❌ Bearer abc123                (token diferente do código)
```

---

#### **Campo 7: Ativo**
```
┌─────────────────────────────────────────────┐
│ Status: [ ] Inativo  [✓] Ativo             │
│                      ^^^^^                  │
│                      Marque ATIVO           │
└─────────────────────────────────────────────┘
```

**Valor:** Marque como **Ativo** ✅

---

#### **Campo 8: Filtros** (se houver - opcional)

Alguns sistemas permitem filtrar. **Deixe em branco** para receber todos os eventos.

---

### 3.3 Salvar Webhook

1. Revise todos os campos
2. Clique em **"Salvar"** ou **"Criar Webhook"**

**✅ Primeiro webhook criado!**

---

## 📝 Resumo do Webhook 1 (Candidaturas)

```yaml
Nome: Candidaturas → Google Sheets
Descrição: Registra novas candidaturas automaticamente
Evento: JOB_TALENT_ADDED
URL: https://script.google.com/.../exec/job-talent-added
Método: POST
Headers:
  - Nome: Authorization
    Valor: Bearer a1b2c3d4-e5f6-7890-abcd-ef1234567890
Status: ✅ Ativo
```

---

## 🔁 PASSO 4: Criar Webhooks Restantes (2 a 5)

Repita o **PASSO 3** para cada um dos 4 webhooks restantes.

**⚠️ O QUE MUDA:** Apenas 3 campos
- Nome (para identificar)
- Evento (diferente para cada um)
- URL (path diferente no final)

**O QUE NÃO MUDA:**
- Método: sempre `POST`
- Header: sempre o **MESMO token**
- Status: sempre `Ativo`

---

### Webhook 2: Mudanças de Etapa

```yaml
Nome: Mudanças de Etapa → Google Sheets
Descrição: Registra quando candidatos mudam de etapa
Evento: JOB_TALENT_STAGE_ADDED              ← Diferente
URL: https://script.google.com/.../exec/job-talent-stage-added  ← Path diferente
Método: POST
Headers:
  - Authorization: Bearer SEU_TOKEN_AQUI   ← Mesmo token
Status: Ativo
```

---

### Webhook 3: Novas Vagas

```yaml
Nome: Novas Vagas → Google Sheets
Descrição: Registra quando novas vagas são criadas
Evento: JOB_ADDED                          ← Diferente
URL: https://script.google.com/.../exec/job-added  ← Path diferente
Método: POST
Headers:
  - Authorization: Bearer SEU_TOKEN_AQUI   ← Mesmo token
Status: Ativo
```

---

### Webhook 4: Formulários

```yaml
Nome: Formulários → Google Sheets
Descrição: Registra respostas de formulários
Evento: FORM_RESPONSE_ADDED                ← Diferente
URL: https://script.google.com/.../exec/form-response-added  ← Path diferente
Método: POST
Headers:
  - Authorization: Bearer SEU_TOKEN_AQUI   ← Mesmo token
Status: Ativo
```

---

### Webhook 5: Requisições

```yaml
Nome: Requisições → Google Sheets
Descrição: Registra mudanças de status de requisições
Evento: REQUISITION_STATUS_UPDATED          ← Diferente
URL: https://script.google.com/.../exec/requisition-status-updated  ← Path diferente
Método: POST
Headers:
  - Authorization: Bearer SEU_TOKEN_AQUI   ← Mesmo token
Status: Ativo
```

---

## ✅ PASSO 5: Verificar Webhooks Criados

Após criar os 5 webhooks, você deve ver uma lista assim:

```
┌────────────────────────────────────────────────────────────────┐
│ Webhooks Configurados                        [+ Novo Webhook] │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ ✅ Candidaturas → Google Sheets                               │
│    Evento: JOB_TALENT_ADDED                                   │
│    Status: Ativo                                              │
│    [Editar] [Testar] [Ver Histórico] [Excluir]               │
│                                                                │
│ ✅ Mudanças de Etapa → Google Sheets                          │
│    Evento: JOB_TALENT_STAGE_ADDED                            │
│    Status: Ativo                                              │
│    [Editar] [Testar] [Ver Histórico] [Excluir]               │
│                                                                │
│ ✅ Novas Vagas → Google Sheets                                │
│    Evento: JOB_ADDED                                          │
│    Status: Ativo                                              │
│    [Editar] [Testar] [Ver Histórico] [Excluir]               │
│                                                                │
│ ✅ Formulários → Google Sheets                                │
│    Evento: FORM_RESPONSE_ADDED                                │
│    Status: Ativo                                              │
│    [Editar] [Testar] [Ver Histórico] [Excluir]               │
│                                                                │
│ ✅ Requisições → Google Sheets                                │
│    Evento: REQUISITION_STATUS_UPDATED                         │
│    Status: Ativo                                              │
│    [Editar] [Testar] [Ver Histórico] [Excluir]               │
└────────────────────────────────────────────────────────────────┘
```

**Checklist:**
- [ ] 5 webhooks criados
- [ ] Todos com status "Ativo"
- [ ] Todos com o mesmo token no header
- [ ] URLs corretas com paths diferentes

---

## 🧪 PASSO 6: Testar Webhook (Opcional)

Algumas plataformas têm botão **"Testar"** na lista de webhooks.

### Como testar:

1. Clique em **"Testar"** no webhook "Candidaturas"

2. A Inhire vai enviar um POST de teste para sua URL

3. Verifique:
   - ✅ Resposta: 200 OK
   - ✅ Aba "Log de Eventos" na planilha tem nova linha
   - ✅ Status: "success"

**Se deu erro:**
- ❌ 401 Unauthorized → Token incorreto
- ❌ 404 Not Found → URL errada
- ❌ 500 Error → Problema no código do Apps Script

---

## 📊 PASSO 7: Teste Real (Criar Candidatura)

Agora teste com ação real:

1. **Na Inhire, abra qualquer vaga**

2. **Inscreva um candidato** (ou use candidato de teste)

3. **Aguarde 5-10 segundos**

4. **Verifique a planilha Google Sheets:**
   - Aba "Candidaturas" deve ter **nova linha**
   - Aba "Log de Eventos" deve registrar o evento

**Exemplo de linha na planilha:**
```
| Data/Hora         | Vaga              | Candidato ID | Etapa   | Origem      |
|-------------------|-------------------|--------------|---------|-------------|
| 25/06/2026 10:30 | Dev Full Stack    | talent-123   | Triagem | career-page |
```

**✅ Se apareceu:** TUDO FUNCIONANDO! 🎉

**❌ Se não apareceu:** Vá para Troubleshooting abaixo

---

## 🔍 Ver Histórico de Webhooks (Debug)

A maioria das plataformas mostra histórico de webhooks enviados.

### Como ver:

1. Na lista de webhooks, clique em **"Ver Histórico"** ou **"Logs"**

2. Você verá algo assim:

```
┌────────────────────────────────────────────────────────────┐
│ Histórico: Candidaturas → Google Sheets                   │
├────────────────────────────────────────────────────────────┤
│ Data/Hora        │ Status │ Resposta │ Tempo              │
├──────────────────┼────────┼──────────┼────────────────────┤
│ 25/06 10:30:15  │ ✅ 200 │ success  │ 234ms              │
│ 25/06 09:15:42  │ ✅ 200 │ success  │ 187ms              │
│ 24/06 16:22:11  │ ❌ 401 │ Unauth   │ 123ms              │
└────────────────────────────────────────────────────────────┘
```

**Como interpretar:**
- ✅ **200 OK** = Funcionou
- ❌ **401 Unauthorized** = Token errado
- ❌ **404 Not Found** = URL errada
- ❌ **500 Internal Error** = Problema no código

---

## ⚠️ Troubleshooting

### Erro: "Webhook não encontrado" ao criar

**Problema:** Pode estar na tela errada.

**Solução:** Procure por "Integrações" → "Webhooks" no menu.

---

### Erro: Evento não aparece na lista

**Problema:** Tenant pode não ter acesso a esse evento.

**Solução:** Contate suporte Inhire perguntando quais eventos estão disponíveis para o tenant `frameworkdigital`.

---

### Webhook criado mas não dispara

**Checklist:**
- [ ] Webhook está **Ativo**?
- [ ] URL está correta com path (`/job-talent-added`)?
- [ ] Token no header está correto?
- [ ] Evento real aconteceu? (ex: candidato se inscreveu)

**Ver logs:**
1. Inhire → Histórico do webhook (veja se enviou)
2. Apps Script → Execuções (veja se recebeu)
3. Planilha → Aba "Log de Eventos" (veja se processou)

---

### Erro 401 Unauthorized

**Problema:** Token está diferente entre código e webhook.

**Solução:**

1. **Verifique token no código** (Apps Script, linha 21):
   ```javascript
   SECRET_TOKEN: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
   ```

2. **Verifique token no webhook** (Inhire):
   ```
   Authorization: Bearer a1b2c3d4-e5f6-7890-abcd-ef1234567890
   ```

3. **Devem ser EXATAMENTE iguais!**

4. **Detalhes importantes:**
   - ✅ `Bearer ` tem espaço depois
   - ✅ Token sem aspas
   - ✅ Não tem caracteres extras

---

### Erro 404 Not Found

**Problema:** URL está errada.

**Solução:**

1. **Verifique URL base** (deve ter `/exec` no final):
   ```
   ✅ https://script.google.com/macros/s/AKfycbx.../exec
   ❌ https://script.google.com/macros/s/AKfycbx.../dev
   ```

2. **Verifique path** (deve ter `/job-talent-added` etc):
   ```
   ✅ .../exec/job-talent-added
   ❌ .../exec
   ```

3. **Formato final correto:**
   ```
   https://script.google.com/macros/s/AKfycbxXXXXX/exec/job-talent-added
   ```

---

## 📋 Tabela de Referência Rápida

| Webhook | Evento | Path da URL |
|---------|--------|-------------|
| 1. Candidaturas | `JOB_TALENT_ADDED` | `/job-talent-added` |
| 2. Mudanças | `JOB_TALENT_STAGE_ADDED` | `/job-talent-stage-added` |
| 3. Vagas | `JOB_ADDED` | `/job-added` |
| 4. Formulários | `FORM_RESPONSE_ADDED` | `/form-response-added` |
| 5. Requisições | `REQUISITION_STATUS_UPDATED` | `/requisition-status-updated` |

**Headers (TODOS os 5 webhooks):**
```
Nome: Authorization
Valor: Bearer SEU_TOKEN_AQUI
```

---

## ✅ Checklist Final

**Para cada webhook, verifique:**

- [ ] Nome preenchido (qualquer nome para identificar)
- [ ] Evento correto selecionado
- [ ] URL = `URL_do_Apps_Script/exec/path_do_evento`
- [ ] Método = `POST`
- [ ] Header `Authorization` adicionado
- [ ] Valor = `Bearer SEU_TOKEN` (com espaço, sem aspas)
- [ ] Token igual ao do código
- [ ] Status = Ativo ✅
- [ ] Webhook salvo com sucesso

**Após criar os 5:**

- [ ] Teste real com candidatura
- [ ] Planilha atualiza em ~5 segundos
- [ ] Aba "Log de Eventos" registra evento
- [ ] Histórico de webhooks mostra 200 OK

---

## 🎉 Pronto!

Após seguir todos os passos, você terá:

✅ 5 webhooks ativos na Inhire
✅ Planilha atualizando em tempo real (~5s)
✅ Histórico completo de eventos
✅ Zero custo
✅ Zero manutenção

**Próximo passo:** Compartilhe a planilha com a equipe RH! 🚀

---

**Versão:** 1.0.0
**Data:** 2026-06-25
**Última atualização:** 2026-06-25
