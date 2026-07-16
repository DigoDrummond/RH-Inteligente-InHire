# 🧪 Como Testar Webhooks Localmente

**Objetivo:** Receber webhooks REAIS da Inhire no seu computador, validar tudo, e depois migrar para Apps Script.

**Tempo:** 15 minutos

---

## PASSO 1: Instalar Flask (se não tiver)

```bash
pip install flask
```

---

## PASSO 2: Iniciar Servidor Local

```bash
cd webhooks
python servidor_webhook_local.py
```

**Você verá:**
```
======================================================================
🚀 SERVIDOR WEBHOOK LOCAL - INHIRE
======================================================================

Token de seguranca:
  a1b2c3d4-e5f6-7890-abcd-ef1234567890

Header para configurar na Inhire:
  Authorization: Bearer a1b2c3d4-e5f6-7890-abcd-ef1234567890

======================================================================

🌐 Servidor rodando em http://localhost:5000
```

**⚠️ IMPORTANTE:** Copie e guarde o TOKEN mostrado!

---

## PASSO 3: Expor Servidor com ngrok

Em **OUTRO TERMINAL**:

### 3.1. Baixar ngrok (se não tiver)

- Acesse: https://ngrok.com/download
- Faça download para Windows
- Extraia o arquivo `ngrok.exe`

### 3.2. Executar ngrok

```bash
ngrok http 5000
```

**Você verá:**
```
ngrok

Session Status      online
Forwarding          https://abc123.ngrok.io -> http://localhost:5000
```

**⚠️ COPIE** a URL `https://abc123.ngrok.io` (será diferente para você)

---

## PASSO 4: Configurar Webhooks na Inhire

### 4.1. Acessar Interface

1. Login: https://app.inhire.app
2. Navegue: **Configurações > Integrações > Webhooks**

### 4.2. Criar Webhook de Teste

**Exemplo: Candidaturas**

- **Nome:** `Teste Local - Candidaturas`
- **Evento:** `JOB_TALENT_ADDED`
- **URL:** `https://ABC123.ngrok.io/job-talent-added`
  - ⚠️ Substitua `ABC123` pela sua URL do ngrok
  - ⚠️ Note o `/job-talent-added` no final
- **Método:** `POST`
- **Headers:**
  - Nome: `Authorization`
  - Valor: `Bearer SEU_TOKEN_AQUI` (do Passo 2)
- **Status:** ✅ Ativo

**Clique:** "Salvar"

---

## PASSO 5: Testar com Evento Real

### 5.1. Fazer Ação na Inhire

1. Acesse uma vaga aberta
2. Adicione uma candidatura (pode ser de teste)
3. OU mude um candidato de etapa

### 5.2. Verificar Recebimento

**No terminal do servidor local**, você verá:

```
======================================================================
📥 WEBHOOK RECEBIDO: job_talent_added
======================================================================
Payload: {
  'tenantId': 'frameworkdigital',
  'jobId': '4b81b977-...',
  'jobName': 'Desenvolvedor Python Senior',
  'talentId': 'a7c3d984-...',
  'stageName': 'Triagem',
  'source': 'linkedin',
  ...
}

✅ Candidatura registrada: Desenvolvedor Python Senior
======================================================================
```

### 5.3. Verificar Arquivos CSV

1. Abra: `webhooks/webhooks_recebidos/`
2. Você verá:
   - `candidaturas.csv` ← Dados REAIS da candidatura
   - `log_webhooks.csv` ← Log de todos os webhooks

3. Abra no Excel/Google Sheets e valide!

---

## ✅ VALIDAÇÃO

Após receber webhook com sucesso:

- [ ] Servidor local recebeu webhook
- [ ] Token validou corretamente
- [ ] Payload foi processado
- [ ] CSV foi criado com dados REAIS
- [ ] Dados estão corretos e formatados

**Se TODOS os itens passaram:** ✅ **Logica validada!**

---

## PASSO 6: Migrar para Apps Script

Agora que validou localmente, você pode **confiantemente** migrar para Apps Script:

1. A lógica de processamento é IDÊNTICA
2. O formato de dados é IDÊNTICO
3. Você sabe que funciona com dados REAIS

**Siga:** `GUIA_IMPLANTACAO_RAPIDA.md` para subir para Apps Script

---

## 📊 URLs dos Webhooks

Configure estes 5 webhooks para testar todos os eventos:

| Evento | URL |
|--------|-----|
| Candidaturas | `https://SEU_NGROK.ngrok.io/job-talent-added` |
| Mudanças de Etapa | `https://SEU_NGROK.ngrok.io/job-talent-stage-added` |
| Novas Vagas | `https://SEU_NGROK.ngrok.io/job-added` |
| Formulários | `https://SEU_NGROK.ngrok.io/form-response-added` |
| Requisições | `https://SEU_NGROK.ngrok.io/requisition-status-updated` |

**Todos com:**
- Método: `POST`
- Header: `Authorization: Bearer SEU_TOKEN`

---

## 🔍 TROUBLESHOOTING

### Erro 401 Unauthorized

- **Causa:** Token incorreto
- **Solução:** Verifique se o token no header da Inhire é EXATAMENTE o mostrado no servidor

### Webhook não chega

- **Causa:** ngrok parou ou URL mudou
- **Solução:**
  1. Verifique se ngrok ainda está rodando
  2. ngrok muda URL a cada execução (versão gratuita)
  3. Atualize URL na Inhire se ngrok foi reiniciado

### Servidor parou

- **Causa:** Erro no processamento
- **Solução:** Veja o traceback no terminal e corrija

---

## 🎉 PRONTO!

Agora você está **recebendo webhooks REAIS** da Inhire no seu computador local!

**Próximo passo:** Migrar para Apps Script com confiança total.

---

**Criado em:** 2026-06-25
**Versão:** 1.0
