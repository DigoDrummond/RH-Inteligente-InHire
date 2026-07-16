# Guia Completo: Webhooks Inhire → Google Sheets

**Data:** 2026-06-25
**Objetivo:** Monitorar ações da Inhire em tempo real usando Google Sheets
**Duração setup:** 15-20 minutos
**Custo:** Grátis ✅

---

## 📋 O Que Você Vai Conseguir

Após configurar, sua planilha Google Sheets será atualizada **automaticamente** quando:

| Evento na Inhire | O que acontece | Tempo |
|------------------|----------------|-------|
| 👤 Candidato se inscreve | Nova linha na aba "Candidaturas" | ~5 segundos |
| 🔄 Candidato muda de etapa | Nova linha em "Mudanças de Etapa" | ~5 segundos |
| 💼 Nova vaga criada | Nova linha em "Novas Vagas" | ~5 segundos |
| 📝 Formulário respondido | Nova linha em "Formulários" | ~5 segundos |
| 📋 Requisição aprovada | Nova linha em "Requisições" | ~5 segundos |

**Exemplo real:**
```
08:30:00 - Candidato João se inscreve em "Desenvolvedor Senior"
08:30:05 - Planilha já está atualizada!
```

---

## 🎯 Passo a Passo Completo

### PASSO 1: Criar Planilha Google Sheets

1. Acesse: https://sheets.google.com
2. Clique em **"Planilha em branco"**
3. Renomeie para: `Monitoramento Inhire`

✅ Pronto! Planilha criada.

---

### PASSO 2: Adicionar Código do Apps Script

1. Na planilha, clique em **Extensões** → **Apps Script**
2. Apague o código padrão que aparece
3. Copie **TODO** o código do arquivo `GoogleAppsScript_WebhookReceiver.js`
4. Cole no editor do Apps Script
5. **IMPORTANTE:** Gere um token secreto (senha de proteção)

**Escolha UMA das opções abaixo:**

**Opção A - Automática (Recomendada):**
```
1. No Apps Script, execute: Executar > gerarToken
2. Veja o log: Exibir > Logs (ou Ctrl+Enter)
3. Copie o token que apareceu
4. Cole no lugar de "SEU_TOKEN_SECRETO_AQUI"
```

**Opção B - Manual (Mais Simples):**
Invente uma senha longa (mínimo 20 caracteres):
```javascript
SECRET_TOKEN: "framework-inhire-webhook-2026-seguro-abc123",
```

**Opção C - Aleatória:**
Aperte teclas aleatórias no teclado:
```javascript
SECRET_TOKEN: "asd8f9a7sd6f5a4sd3f2a1sdf09asdf87",
```

**Exemplo final:**
```javascript
SECRET_TOKEN: "framework-digital-inhire-2026-v1-abc",
```

6. Clique em **Salvar** (ícone de disquete) 💾
7. Nomeie o projeto: `Webhook Receiver`

✅ Código adicionado!

---

### PASSO 3: Implantar como Web App

1. No Apps Script, clique em **Implantar** → **Nova implantação**
2. Clique no ícone de **engrenagem** ⚙️ ao lado de "Selecione o tipo"
3. Selecione **"Aplicativo da Web"**
4. Configure:
   - **Descrição:** `Webhook Receiver v1.0`
   - **Executar como:** `Eu (seu-email@gmail.com)`
   - **Quem tem acesso:** `Qualquer pessoa` ⚠️
5. Clique em **Implantar**
6. **IMPORTANTE:** Copie a **URL da implantação**

**A URL será algo como:**
```
https://script.google.com/macros/s/AKfycby...xyz123/exec
```

📋 **SALVE ESTA URL!** Você vai precisar dela no próximo passo.

7. Clique em **Concluído**

✅ Web App implantado!

---

### PASSO 4: Configurar Webhooks na Inhire

Agora você precisa dizer à Inhire para enviar notificações para sua planilha.

#### Opção A: Configuração Manual (via Interface Inhire)

1. Acesse: https://app.inhire.com.br
2. Login → Tenant: `frameworkdigital`
3. Menu → **Integrações** → **Webhooks**
4. Clique em **+ Novo Webhook**

**Para cada evento, crie um webhook:**

##### Webhook 1: Candidaturas

- **Nome:** Candidaturas para Planilha
- **Descrição:** Registra novas candidaturas no Google Sheets
- **Evento:** `JOB_TALENT_ADDED`
- **URL:** `SUA_URL_DO_APPS_SCRIPT/job-talent-added`
  _(exemplo: https://script.google.com/.../exec/job-talent-added)_
- **Método:** `POST`
- **Headers:**
  ```
  Authorization: Bearer SEU_TOKEN_SECRETO_AQUI
  ```
  _(use o mesmo token que colocou no código)_
- **Ativo:** ✅ Sim

##### Webhook 2: Mudanças de Etapa

- **Nome:** Mudanças de Etapa para Planilha
- **Evento:** `JOB_TALENT_STAGE_ADDED`
- **URL:** `SUA_URL_DO_APPS_SCRIPT/job-talent-stage-added`
- **Headers:**
  ```
  Authorization: Bearer SEU_TOKEN_SECRETO_AQUI
  ```

##### Webhook 3: Novas Vagas

- **Nome:** Novas Vagas para Planilha
- **Evento:** `JOB_ADDED`
- **URL:** `SUA_URL_DO_APPS_SCRIPT/job-added`
- **Headers:**
  ```
  Authorization: Bearer SEU_TOKEN_SECRETO_AQUI
  ```

##### Webhook 4: Formulários

- **Nome:** Formulários para Planilha
- **Evento:** `FORM_RESPONSE_ADDED`
- **URL:** `SUA_URL_DO_APPS_SCRIPT/form-response-added`
- **Headers:**
  ```
  Authorization: Bearer SEU_TOKEN_SECRETO_AQUI
  ```

##### Webhook 5: Requisições

- **Nome:** Requisições para Planilha
- **Evento:** `REQUISITION_STATUS_UPDATED`
- **URL:** `SUA_URL_DO_APPS_SCRIPT/requisition-status-updated`
- **Headers:**
  ```
  Authorization: Bearer SEU_TOKEN_SECRETO_AQUI
  ```

---

#### Opção B: Configuração Automatizada (via Python Script)

**Mais rápido e menos propenso a erros!**

1. Abra o arquivo `webhooks/registrar_webhooks_google_sheets.py`
2. Edite estas linhas:

```python
# Linha 10
APPS_SCRIPT_URL = "SUA_URL_DO_APPS_SCRIPT"

# Linha 11
SECRET_TOKEN = "SEU_TOKEN_SECRETO_AQUI"
```

3. Execute:
```bash
python webhooks/registrar_webhooks_google_sheets.py
```

4. O script vai:
   - ✅ Autenticar na API Inhire
   - ✅ Criar os 5 webhooks automaticamente
   - ✅ Mostrar resumo dos webhooks criados

✅ Webhooks configurados!

---

### PASSO 5: Testar

#### Teste 1: Testar Código Localmente

1. No Apps Script, execute a função de teste:
   - Menu: **Executar** → `testarCandidatura`
2. Autorize o script (primeira vez)
3. Verifique a planilha:
   - Deve aparecer aba **"Candidaturas"**
   - Com 1 linha de teste

✅ Se apareceu, código está funcionando!

#### Teste 2: Testar Webhook Real

Crie um evento real na Inhire:

1. Acesse https://app.inhire.com.br
2. Abra uma vaga qualquer
3. Inscreva um candidato de teste
4. Aguarde 5-10 segundos
5. Verifique a planilha:
   - Aba "Candidaturas" deve ter nova linha
   - Aba "Log de Eventos" deve mostrar evento recebido

✅ Se apareceu, **TUDO FUNCIONANDO!** 🎉

---

## 📊 Estrutura da Planilha

Após receber eventos, a planilha terá estas abas:

### Aba: Candidaturas

| Data/Hora | Vaga | Vaga ID | Candidato ID | Etapa Inicial | Origem | LinkedIn | Localização | Pretensão | Modelo | Usuário |
|-----------|------|---------|--------------|---------------|--------|----------|-------------|-----------|--------|---------|
| 25/06/2026 08:30 | Dev Senior | abc-123 | talent-456 | Triagem | career-page | joaosilva | São Paulo | 8000 | hybrid | Sistema |

### Aba: Mudanças de Etapa

| Data/Hora | Vaga | Candidato ID | Etapa Anterior | Nova Etapa | Tipo | Fase | Usuário |
|-----------|------|--------------|----------------|------------|------|------|---------|
| 25/06/2026 09:15 | Dev Senior | talent-456 | Triagem | Entrevista | default | screening | Recrutador |

### Aba: Log de Eventos

| Data/Hora | Tipo de Evento | Status | Payload | Erro |
|-----------|----------------|--------|---------|------|
| 25/06/2026 08:30 | job_talent_added | success | {...} | |

---

## 🔧 Personalizações

### Mudar Colunas da Planilha

Edite no código do Apps Script (linha ~60):

```javascript
const sheet = obterOuCriarAba(CONFIG.SHEETS.CANDIDATURAS, [
  "Data/Hora",
  "Vaga",
  "NOVA_COLUNA_AQUI",  // ← Adicionar
  "Candidato ID",
  // ...
]);
```

E ajuste a linha de dados (linha ~85):

```javascript
const linha = [
  formatarDataHora(new Date()),
  payload.jobName || "",
  payload.NOVO_CAMPO_AQUI || "",  // ← Adicionar
  payload.talentId || "",
  // ...
];
```

### Adicionar Notificações

Adicione ao final da função `processarCandidatura`:

```javascript
// Enviar email
MailApp.sendEmail({
  to: "recrutador@empresa.com",
  subject: `Nova candidatura: ${payload.jobName}`,
  body: `Candidato ${payload.talentId} se inscreveu em ${payload.jobName}`
});
```

### Adicionar Gráficos Automáticos

1. Na planilha, crie nova aba: **Dashboard**
2. Adicione gráfico:
   - Tipo: Gráfico de linha
   - Fonte: Aba "Candidaturas"
   - Eixo X: Data/Hora
   - Eixo Y: COUNT(Candidato ID)

O gráfico atualiza automaticamente conforme novos dados chegam!

---

## ⚠️ Troubleshooting

### Problema: Planilha não atualiza

**Causa possível:** Webhook não está sendo enviado

**Solução:**
1. Verifique na Inhire se webhook está **Ativo**
2. Veja logs em: Integrações → Webhooks → (selecionar webhook) → Histórico
3. Se aparecer erro 401: Token está incorreto
4. Se aparecer erro 404: URL está incorreta

---

### Problema: Erro "Script não autorizado"

**Causa:** Você não autorizou o script

**Solução:**
1. Apps Script → Executar → `testarCandidatura`
2. Clique em **Analisar permissões**
3. Selecione sua conta Google
4. Clique em **Avançado** → **Ir para... (não seguro)**
5. Clique em **Permitir**

---

### Problema: Aba não é criada

**Causa:** Código com erro

**Solução:**
1. Apps Script → Ver → **Execuções**
2. Veja mensagens de erro
3. Verifique se copiou código completo

---

## 📈 Monitoramento

### Ver Logs de Execução

1. Apps Script → **Execuções** (ícone de relógio)
2. Veja todas as execuções
3. Clique em qualquer execução para ver logs

### Ver Estatísticas

Aba "Log de Eventos" mostra:
- Total de eventos recebidos
- Taxa de sucesso/falha
- Últimos eventos

### Alertas Automáticos

Adicione ao código:

```javascript
// No final de processarCandidatura
if (payload.stageName === "Proposta") {
  MailApp.sendEmail({
    to: "gerente@empresa.com",
    subject: "🎉 Candidato em Proposta!",
    body: `${payload.jobName} - ${payload.talentId}`
  });
}
```

---

## 🎯 Próximos Passos

Após configurar, você pode:

### 1. Criar Dashboard

Use Google Data Studio para visualizar dados:
- https://datastudio.google.com
- Conecte à planilha
- Crie gráficos de:
  - Candidaturas por dia
  - Tempo médio por etapa
  - Taxa de conversão por origem

### 2. Integrar com Outros Serviços

O Apps Script pode enviar dados para:
- **Slack:** Notificações em canal
- **WhatsApp:** Via API Twilio
- **Email:** Resumos diários
- **Google Calendar:** Agendar entrevistas

### 3. Criar Automações

Exemplos:
```javascript
// Aprovar automaticamente se formulário >80%
if (payload.passed && percentual > 80) {
  // Chamar API Inhire para mover para próxima etapa
}

// Enviar teste técnico automaticamente
if (payload.stageName === "Teste Técnico") {
  MailApp.sendEmail(...);
}
```

---

## 💰 Custos e Limites

### Google Apps Script (Grátis)

| Recurso | Limite Grátis | Suficiente para |
|---------|---------------|-----------------|
| **Execuções/dia** | 20.000 | ~1 evento a cada 4 segundos |
| **Tempo execução** | 6 min/exec | ✅ Webhooks levam <1s |
| **Tamanho planilha** | 5 milhões células | ~200.000 eventos |
| **Requisições HTTP** | 20.000/dia | ✅ Só recebe, não faz |

**Conclusão:** Grátis é mais que suficiente! ✅

---

## 🔐 Segurança

### Boas Práticas

✅ **Use token secreto forte** (UUID aleatório)
✅ **Não compartilhe o token** publicamente
✅ **Valide sempre** o header Authorization
✅ **Limite acesso à planilha** (compartilhe só com equipe)
✅ **Monitore a aba "Log"** para detectar abusos

### Se Token Vazar

1. Gere novo token
2. Atualize no código do Apps Script
3. Atualize nos webhooks da Inhire
4. Clique em **Implantar** → **Gerenciar implantações** → **Editar** → **Nova versão**

---

## 📞 Suporte

### Documentação Oficial

- **Apps Script:** https://developers.google.com/apps-script
- **API Inhire:** https://docs.inhire.com.br (se disponível)
- **Webhooks Inhire:** Contate suporte Inhire

### Problemas Comuns

Consulte arquivo: `docs/TROUBLESHOOTING_WEBHOOKS.md`

---

## ✅ Checklist de Configuração

Marque conforme avança:

- [ ] Planilha Google Sheets criada
- [ ] Código do Apps Script adicionado
- [ ] Token secreto gerado e configurado
- [ ] Web App implantado
- [ ] URL do Web App copiada
- [ ] 5 webhooks criados na Inhire
- [ ] Token adicionado nos headers
- [ ] Teste local executado (função `testarCandidatura`)
- [ ] Teste real executado (candidatura na Inhire)
- [ ] Planilha atualizando automaticamente ✅

---

**🎉 Parabéns!** Você configurou webhooks Inhire → Google Sheets com sucesso!

**Tempo real:** Latência de ~5 segundos
**Custo:** R$ 0,00
**Manutenção:** Mínima

---

**Última atualização:** 2026-06-25
**Versão:** 1.0.0
