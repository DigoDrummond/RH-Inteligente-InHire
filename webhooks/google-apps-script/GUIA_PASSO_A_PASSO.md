# Guia Passo a Passo - Webhooks Inhire → Google Sheets

**Tempo total:** 15-20 minutos
**Custo:** R$ 0 (grátis)
**Arquivos:** 3 scripts separados por etapa

---

## 📋 Visão Geral dos Passos

```
PASSO 1: Gerar Token          (2 min)
    ↓
PASSO 2: Criar Abas           (3 min)
    ↓
PASSO 3: Adicionar Webhook    (5 min)
    ↓
PASSO 4: Implantar Web App    (2 min)
    ↓
PASSO 5: Configurar na Inhire (5 min)
    ↓
PASSO 6: Testar               (3 min)
```

---

## 🚀 PASSO 1: Gerar Token de Segurança

### O que é?
Token é uma "senha" que protege sua planilha de receber dados de fontes não autorizadas.

### Como fazer:

1. **Abra sua planilha Google Sheets**
   - https://sheets.google.com
   - Nova planilha em branco
   - Nomeie: "Monitoramento Inhire"

2. **Abra Apps Script**
   - Menu: **Extensões** → **Apps Script**

3. **Cole o código do Passo 1**
   - Apague o código padrão
   - Copie **TODO** o conteúdo de `1_setup_token.js`
   - Cole no editor

4. **Execute**
   - Clique em **Executar** → Selecione `gerarToken`
   - Autorize o script (primeira vez)

5. **Copie o token**
   - Veja o log que aparece embaixo
   - Copie o token gerado (ex: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`)
   - **GUARDE este token!** Você vai usar várias vezes

**Exemplo do log:**
```
======================================================================
🔑 SEU TOKEN SECRETO:

a1b2c3d4-e5f6-7890-abcd-ef1234567890

======================================================================
```

✅ **Pronto!** Token gerado. Próximo passo →

---

## 📊 PASSO 2: Criar Estrutura da Planilha

### O que faz?
Cria automaticamente 6 abas com cabeçalhos formatados.

### Como fazer:

1. **No mesmo Apps Script, apague o código anterior**

2. **Cole o código do Passo 2**
   - Copie **TODO** o conteúdo de `2_setup_planilha.js`
   - Cole no editor

3. **Configure o token**
   - Linha 19: `SECRET_TOKEN: "SEU_TOKEN_AQUI"`
   - Substitua pelo token gerado no Passo 1

4. **Execute**
   - Clique em **Executar** → Selecione `criarEstruturaPlanilha`

5. **Verifique**
   - Volte para a planilha
   - Deve ter 7 abas criadas:
     - ⚙️ Configuração
     - Candidaturas
     - Mudanças de Etapa
     - Novas Vagas
     - Formulários
     - Requisições
     - Log de Eventos

**Exemplo do log:**
```
✅ Aba criada: Candidaturas (11 colunas)
✅ Aba criada: Mudanças de Etapa (8 colunas)
✅ Aba criada: Novas Vagas (5 colunas)
...
✅ ESTRUTURA CRIADA COM SUCESSO!
```

✅ **Pronto!** Estrutura criada. Próximo passo →

---

## 🔔 PASSO 3: Adicionar Código do Webhook

### O que faz?
Este é o código que fica rodando permanentemente e recebe os webhooks da Inhire.

### Como fazer:

1. **No Apps Script, apague o código anterior**

2. **Cole o código do Passo 3**
   - Copie **TODO** o conteúdo de `3_webhook_receiver.js`
   - Cole no editor

3. **Configure o token**
   - Linha 21: `SECRET_TOKEN: "SEU_TOKEN_AQUI"`
   - Substitua pelo **MESMO token** do Passo 1

4. **Salve**
   - Ctrl+S ou ícone de disquete 💾
   - Nomeie o projeto: "Webhook Receiver"

5. **Teste localmente (opcional)**
   - Execute: `testarCandidatura`
   - Verifique se linha de teste aparece na aba "Candidaturas"

✅ **Pronto!** Código adicionado. Próximo passo →

---

## 🌐 PASSO 4: Implantar Web App

### O que é?
Cria uma URL pública que a Inhire vai usar para enviar webhooks.

### Como fazer:

1. **No Apps Script, clique em Implantar**
   - Menu: **Implantar** → **Nova implantação**

2. **Configure o tipo**
   - Clique no ícone ⚙️ ao lado de "Selecione o tipo"
   - Escolha: **Aplicativo da Web**

3. **Preencha os dados**
   ```
   Descrição: Webhook Receiver v1.0
   Executar como: Eu (seu-email@gmail.com)
   Quem tem acesso: Qualquer pessoa  ← IMPORTANTE!
   ```

4. **Implante**
   - Clique em **Implantar**
   - Aguarde alguns segundos

5. **Copie a URL**
   - Uma URL será gerada, algo como:
   ```
   https://script.google.com/macros/s/AKfycbxXXXXXXXXXXXXXXXXX/exec
   ```
   - **COPIE E GUARDE** esta URL!

6. **Clique em Concluído**

✅ **Pronto!** Web App implantado. Próximo passo →

---

## 🔗 PASSO 5: Configurar Webhooks na Inhire

### ⚠️ IMPORTANTE: Sobre Credenciais

**VOCÊ NÃO PRECISA PASSAR CREDENCIAIS DA FRAMEWORK!**

**Por quê?**
- Você vai configurar os webhooks **LOGADO** na conta da Framework na Inhire
- A Inhire já sabe que é você (tenant frameworkdigital)
- Webhooks são a **Inhire enviando dados PARA VOCÊ** (não o contrário)
- A autenticação é **reversa**: você valida a Inhire com seu token

**Fluxo:**
```
❌ ERRADO (Polling - sistema atual):
Você → [Login com credenciais] → Inhire → Busca dados
      ├─ email: service-account@...
      └─ password: xxx

✅ CORRETO (Webhooks - novo):
Inhire → [Token do webhook] → Você → Valida e aceita
         └─ Authorization: Bearer SEU_TOKEN
```

### Como fazer:

1. **Acesse a Inhire**
   - https://app.inhire.com.br
   - Login: Conta da Framework
   - Tenant: `frameworkdigital`

2. **Vá para Integrações**
   - Menu lateral → **Integrações** → **Webhooks**

3. **Crie 5 webhooks** (um para cada evento)

---

### Webhook 1: Candidaturas

```yaml
Nome: Candidaturas → Google Sheets
Descrição: Registra novas candidaturas automaticamente
Evento: JOB_TALENT_ADDED
URL: https://script.google.com/macros/s/AKfycbxXXXXX/exec/job-talent-added
     └─────────────── SUA URL ────────────────┘  └─ /job-talent-added ─┘
Método: POST
Ativo: ✅ Sim

Headers:
┌──────────────┬────────────────────────────────────────────────┐
│ Nome         │ Valor                                          │
├──────────────┼────────────────────────────────────────────────┤
│Authorization │ Bearer a1b2c3d4-e5f6-7890-abcd-ef1234567890   │
│              │ └────┘ └──────── SEU TOKEN ─────────────┘     │
│              │  Fixo   (mesmo do Passo 1)                     │
└──────────────┴────────────────────────────────────────────────┘
```

**⚠️ ATENÇÃO:**
- Formato: `Bearer <token>` (com espaço após "Bearer")
- Use o **MESMO token** configurado no código
- Adicione `/job-talent-added` no final da URL

---

### Webhook 2: Mudanças de Etapa

```yaml
Nome: Mudanças de Etapa → Google Sheets
Evento: JOB_TALENT_STAGE_ADDED
URL: SUA_URL/exec/job-talent-stage-added
Headers:
  Authorization: Bearer SEU_TOKEN_AQUI
```

---

### Webhook 3: Novas Vagas

```yaml
Nome: Novas Vagas → Google Sheets
Evento: JOB_ADDED
URL: SUA_URL/exec/job-added
Headers:
  Authorization: Bearer SEU_TOKEN_AQUI
```

---

### Webhook 4: Formulários

```yaml
Nome: Formulários → Google Sheets
Evento: FORM_RESPONSE_ADDED
URL: SUA_URL/exec/form-response-added
Headers:
  Authorization: Bearer SEU_TOKEN_AQUI
```

---

### Webhook 5: Requisições

```yaml
Nome: Requisições → Google Sheets
Evento: REQUISITION_STATUS_UPDATED
URL: SUA_URL/exec/requisition-status-updated
Headers:
  Authorization: Bearer SEU_TOKEN_AQUI
```

---

### ⚡ Atalho: Script Automatizado (Python)

Se preferir automatizar, edite e execute:

```bash
# Arquivo: webhooks/registrar_webhooks_google_sheets.py

# Edite estas linhas:
APPS_SCRIPT_URL = "https://script.google.com/.../exec"
SECRET_TOKEN = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# Execute:
python webhooks/registrar_webhooks_google_sheets.py
```

O script cria os 5 webhooks automaticamente!

✅ **Pronto!** Webhooks configurados. Próximo passo →

---

## 🧪 PASSO 6: Testar

### Teste 1: Criar Candidatura Real

1. **Na Inhire, abra uma vaga**
2. **Inscreva um candidato** (ou use candidato de teste)
3. **Aguarde 5-10 segundos**
4. **Verifique a planilha:**
   - Aba "Candidaturas" deve ter nova linha
   - Aba "Log de Eventos" deve registrar o evento

**Se funcionou:** 🎉 **TUDO CERTO!**

---

### Teste 2: Mudar Etapa

1. **Mova um candidato de etapa**
2. **Aguarde 5-10 segundos**
3. **Verifique aba "Mudanças de Etapa"**

---

### Troubleshooting

**Planilha não atualizou?**

1. **Verifique aba "Log de Eventos"**
   - Se não tem nada: Webhook não chegou (problema na Inhire)
   - Se tem linha com status "failed": Problema no processamento

2. **Verifique token**
   - Código (linha 21): `SECRET_TOKEN: "abc..."`
   - Webhook Inhire: `Authorization: Bearer abc...`
   - Devem ser **EXATAMENTE iguais**!

3. **Verifique URL**
   - Webhook deve ter `/job-talent-added` no final
   - Ex: `.../exec/job-talent-added` ✅
   - Ex: `.../exec` ❌ (faltou path)

4. **Veja logs do Apps Script**
   - Apps Script → Execuções (ícone relógio)
   - Veja erros nas últimas execuções

---

## ✅ Checklist Final

- [ ] Token gerado (Passo 1)
- [ ] Abas criadas (Passo 2)
- [ ] Código do webhook adicionado (Passo 3)
- [ ] Token configurado no código
- [ ] Web App implantado (Passo 4)
- [ ] URL copiada
- [ ] 5 webhooks criados na Inhire (Passo 5)
- [ ] Token igual em todos os webhooks
- [ ] Teste com candidatura real funcionou (Passo 6)

---

## 🎯 Resumo de URLs e Tokens

**URL do Apps Script:**
```
https://script.google.com/macros/s/AKfycbxXXXXXXXXXX/exec
```

**Token Secreto:**
```
a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**URLs dos Webhooks:**
```
1. .../exec/job-talent-added
2. .../exec/job-talent-stage-added
3. .../exec/job-added
4. .../exec/form-response-added
5. .../exec/requisition-status-updated
```

**Header de todos os webhooks:**
```
Authorization: Bearer a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

---

## 📞 Próximos Passos

Após configurar:

1. **Compartilhe a planilha** com equipe RH
2. **Crie dashboards** (gráficos automáticos)
3. **Configure notificações** (email/Slack quando evento acontecer)
4. **Monitore aba "Log"** regularmente

---

**🎉 Parabéns!** Sistema configurado e funcionando em tempo real!

**Latência:** ~5 segundos
**Custo:** R$ 0
**Manutenção:** Mínima
