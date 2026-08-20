# 📋 Guia de Gerenciamento de Webhooks Inhire

## 🎯 Scripts Disponíveis

### 1️⃣ **Listar Webhooks**
```bash
python webhooks/listar_webhooks.py
```
**O que faz:** Mostra todos os webhooks configurados na Inhire

**Quando usar:** Para ver quais webhooks estão ativos

---

### 2️⃣ **Criar Webhook no Google Chat**
```bash
# Criar apenas webhook de candidaturas
python webhooks/criar_webhook_candidaturas.py

# Criar TODOS os 5 webhooks
python webhooks/registrar_todos_webhooks_google_chat.py
```
**O que faz:** Registra webhooks apontando para o Google Chat

**Quando usar:** Primeira configuração ou para adicionar novos webhooks

---

### 3️⃣ **Deletar Webhooks**
```bash
python webhooks/deletar_webhooks.py
```
**O que faz:** Menu interativo para deletar webhooks

**Opções:**
- Deletar todos do Google Chat
- Deletar webhook específico
- Deletar TODOS os webhooks

**Quando usar:** Para desabilitar/remover webhooks

---

## 🚀 Cenários Comuns

### 📊 "Quero ver o que está configurado"
```bash
python webhooks/listar_webhooks.py
```

### ⏸️ "Quero desabilitar temporariamente os webhooks"
```bash
python webhooks/deletar_webhooks.py
# Escolha opção 1: Deletar todos do Google Chat
```
💡 **Dica:** Depois pode recriar com `registrar_todos_webhooks_google_chat.py`

### 🗑️ "Quero remover um webhook específico"
```bash
python webhooks/deletar_webhooks.py
# Escolha opção 2: Deletar webhook específico
```

### 🔄 "Quero trocar a URL do Google Chat"
```bash
# 1. Edite a URL no arquivo
# webhooks/registrar_todos_webhooks_google_chat.py (linha 22)

# 2. Execute novamente
python webhooks/registrar_todos_webhooks_google_chat.py
```

### 🧹 "Quero limpar tudo e começar do zero"
```bash
# 1. Deletar todos
python webhooks/deletar_webhooks.py
# Escolha opção 3: Deletar TODOS

# 2. Recriar do zero
python webhooks/registrar_todos_webhooks_google_chat.py
```

---

## 📦 Webhooks Disponíveis (5 total)

| # | Nome | Evento | Descrição |
|---|------|--------|-----------|
| 1 | GChat - Novas Candidaturas | `JOB_TALENT_ADDED` | Nova candidatura recebida |
| 2 | GChat - Mudanças de Etapa | `JOB_TALENT_STAGE_ADDED` | Candidato muda de etapa |
| 3 | GChat - Novas Vagas | `JOB_ADDED` | Nova vaga criada |
| 4 | GChat - Status de Requisições | `REQUISITION_STATUS_UPDATED` | Requisição aprovada/rejeitada |
| 5 | GChat - Respostas de Formulários | `FORM_RESPONSE_ADDED` | Formulário preenchido |

---

## ⚠️ Importante

- **Webhooks funcionam na nuvem:** Não precisa de nada rodando no seu computador
- **Deletar é reversível:** Pode recriar a qualquer momento executando os scripts
- **Teste sempre:** Após mudanças, crie uma candidatura teste na Inhire
- **URL do Google Chat:** Se mudar, precisa recriar os webhooks

---

## 🔧 Troubleshooting

### "Não recebi notificação no Google Chat"

1. **Verifique se webhooks estão ativos:**
   ```bash
   python webhooks/listar_webhooks.py
   ```

2. **Teste a URL do Google Chat:**
   ```bash
   python webhooks/registrar_webhook_google_chat_auto.py
   # Envia mensagem de teste
   ```

3. **Recrie os webhooks:**
   ```bash
   python webhooks/deletar_webhooks.py  # Deletar todos
   python webhooks/registrar_todos_webhooks_google_chat.py  # Recriar
   ```

### "Quero pausar temporariamente"

**Solução 1: Deletar (recomendado)**
```bash
python webhooks/deletar_webhooks.py
```
*Depois recria quando quiser com `registrar_todos_webhooks_google_chat.py`*

**Solução 2: Mudar URL para inválida**
- Edite `GOOGLE_CHAT_URL` nos scripts
- Coloque URL inválida (ex: `https://exemplo.com`)
- Execute `registrar_todos_webhooks_google_chat.py`
- Webhooks dispararão mas não chegarão ao Google Chat

---

## 📞 URLs dos Scripts

- **Listar:** `webhooks/listar_webhooks.py`
- **Criar todos:** `webhooks/registrar_todos_webhooks_google_chat.py`
- **Deletar:** `webhooks/deletar_webhooks.py`
- **Criar candidaturas:** `webhooks/criar_webhook_candidaturas.py`

---

**Última atualização:** 2026-08-06
**Webhooks configurados:** 5/5 ✅
