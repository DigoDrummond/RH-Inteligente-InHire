# 🚀 GUIA DE IMPLANTAÇÃO RÁPIDA - Webhooks Inhire

**Tempo estimado:** 20-30 minutos
**Objetivo:** Configurar webhook e começar a receber dados REAIS da Inhire

---

## PASSO 1: Criar Planilha Google Sheets

1. **Acesse:** https://sheets.google.com
2. **Crie planilha nova:** "Webhooks Inhire - Framework"
3. **Anote a URL** da planilha

---

## PASSO 2: Configurar Google Apps Script

### 2.1. Abrir Editor Apps Script

1. Na planilha, clique: **Extensões > Apps Script**
2. Você verá um editor de código
3. Delete o código padrão (`function myFunction() {}`)

### 2.2. Gerar Token de Segurança

1. **Cole este código:**

```javascript
function gerarToken() {
  const token = Utilities.getUuid();
  console.log("=".repeat(70));
  console.log("🔑 SEU TOKEN SECRETO:");
  console.log("");
  console.log(token);
  console.log("");
  console.log("=".repeat(70));
  console.log("");
  console.log("📋 COPIE E GUARDE ESTE TOKEN!");
  console.log("=".repeat(70));
  return token;
}
```

2. **Execute:** Clique em "Executar" (▶️)
3. **Autorize:** Se pedir permissões, clique "Revisar permissões" > Escolha sua conta > "Permitir"
4. **Veja o token:** Clique em "Execuções" (ícone de lista à esquerda) e copie o token gerado
5. **GUARDE o token** em local seguro (você vai usar várias vezes)

**Exemplo de token gerado:**
```
a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### 2.3. Criar Estrutura da Planilha

1. **Substitua TODO o código** do Apps Script por este:

```javascript
const CONFIG_SETUP = {
  SECRET_TOKEN: "COLE_SEU_TOKEN_AQUI",  // ← Substitua pelo token gerado
  TIMEZONE: "America/Sao_Paulo"
};

const ESTRUTURA_ABAS = {
  "Candidaturas": [
    "Data/Hora", "Vaga", "Vaga ID", "Candidato ID", "Etapa Inicial",
    "Origem", "LinkedIn", "Localização", "Pretensão Salarial",
    "Modelo de Trabalho", "Usuário"
  ],
  "Mudanças de Etapa": [
    "Data/Hora", "Vaga", "Candidato ID", "Etapa Anterior",
    "Nova Etapa", "Tipo de Etapa", "Fase", "Usuário"
  ],
  "Novas Vagas": [
    "Data/Hora", "Nome da Vaga", "Vaga ID", "Descrição", "Criado por"
  ],
  "Formulários": [
    "Data/Hora", "Vaga ID", "Candidato ID", "Tipo", "Título",
    "Aprovado?", "Acertos", "Total", "% Acerto"
  ],
  "Requisições": [
    "Data/Hora", "Título", "Requisição ID", "Status Anterior",
    "Novo Status", "Usuário"
  ],
  "Log de Eventos": [
    "Data/Hora", "Tipo de Evento", "Status", "Payload (resumo)", "Erro"
  ]
};

function criarEstruturaPlanilha() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  for (const [nomeAba, colunas] of Object.entries(ESTRUTURA_ABAS)) {
    let sheet = ss.getSheetByName(nomeAba);

    if (!sheet) {
      sheet = ss.insertSheet(nomeAba);
      sheet.appendRow(colunas);

      // Formatar cabeçalho
      const headerRange = sheet.getRange(1, 1, 1, colunas.length);
      headerRange.setFontWeight("bold");
      headerRange.setBackground("#4A90E2");
      headerRange.setFontColor("#FFFFFF");
      headerRange.setHorizontalAlignment("center");

      sheet.setFrozenRows(1);
      sheet.getRange(1, 1, 1, colunas.length).createFilter();

      console.log(`✅ Aba criada: ${nomeAba}`);
    }
  }

  console.log("✅ ESTRUTURA CRIADA COM SUCESSO!");
}
```

2. **Substitua** `COLE_SEU_TOKEN_AQUI` pelo token que você gerou
3. **Salve:** Ctrl+S ou clique no ícone de disquete
4. **Execute:** Selecione `criarEstruturaPlanilha` no dropdown e clique "Executar"
5. **Verifique:** Volte na planilha e veja se as 6 abas foram criadas

### 2.4. Adicionar Webhook Receiver (Código Principal)

1. **Substitua TODO o código** novamente por este arquivo completo:

👉 **Copie TODO o conteúdo do arquivo:** `webhooks/google-apps-script/3_webhook_receiver.js`

2. **IMPORTANTE:** Na linha 22, substitua `SEU_TOKEN_AQUI` pelo **mesmo token** que você gerou
3. **Salve:** Ctrl+S

### 2.5. Fazer Deploy do Web App

1. **Clique:** "Implantar" (canto superior direito) > "Nova implantação"
2. **Tipo:** Clique no ícone de engrenagem ⚙️ > Selecione "Aplicativo da Web"
3. **Configurações:**
   - **Descrição:** "Webhook Receiver Inhire v1"
   - **Executar como:** Eu (seu email)
   - **Quem tem acesso:** Qualquer pessoa
4. **Clique:** "Implantar"
5. **Autorize:** Se pedir, clique "Autorizar acesso" > Escolha sua conta > "Permitir"
6. **COPIE A URL:** Você verá uma URL como:
   ```
   https://script.google.com/macros/s/AKfycbx.../exec
   ```
   **COPIE esta URL completa e guarde!**

---

## PASSO 3: Configurar Webhooks na Inhire

### 3.1. Acessar Interface de Webhooks

1. **Login Inhire:** https://app.inhire.app
2. **Acesse:** Configurações > Integrações > Webhooks
3. **Ou direto:** https://app.inhire.app/tenants/frameworkdigital/settings/integrations/webhooks

### 3.2. Criar 5 Webhooks

Você precisa criar **5 webhooks diferentes**, um para cada tipo de evento.

#### WEBHOOK 1: Candidaturas

- **Nome:** `Candidaturas → Google Sheets`
- **Evento:** `JOB_TALENT_ADDED`
- **URL:** `https://script.google.com/macros/s/SEU_ID_AQUI/exec/job-talent-added`
  - ⚠️ Substitua `SEU_ID_AQUI` pelo ID da sua URL do passo 2.5
  - ⚠️ Note o `/job-talent-added` no final
- **Método:** `POST`
- **Headers:**
  - Nome: `Authorization`
  - Valor: `Bearer SEU_TOKEN_AQUI` (substitua pelo token)
- **Status:** ✅ Ativo

**Clique:** "Salvar"

#### WEBHOOK 2: Mudanças de Etapa

- **Nome:** `Mudanças de Etapa → Google Sheets`
- **Evento:** `JOB_TALENT_STAGE_ADDED`
- **URL:** `https://script.google.com/macros/s/SEU_ID_AQUI/exec/job-talent-stage-added`
- **Método:** `POST`
- **Headers:**
  - Nome: `Authorization`
  - Valor: `Bearer SEU_TOKEN_AQUI`
- **Status:** ✅ Ativo

**Clique:** "Salvar"

#### WEBHOOK 3: Novas Vagas

- **Nome:** `Novas Vagas → Google Sheets`
- **Evento:** `JOB_ADDED`
- **URL:** `https://script.google.com/macros/s/SEU_ID_AQUI/exec/job-added`
- **Método:** `POST`
- **Headers:**
  - Nome: `Authorization`
  - Valor: `Bearer SEU_TOKEN_AQUI`
- **Status:** ✅ Ativo

**Clique:** "Salvar"

#### WEBHOOK 4: Formulários

- **Nome:** `Formulários → Google Sheets`
- **Evento:** `FORM_RESPONSE_ADDED`
- **URL:** `https://script.google.com/macros/s/SEU_ID_AQUI/exec/form-response-added`
- **Método:** `POST`
- **Headers:**
  - Nome: `Authorization`
  - Valor: `Bearer SEU_TOKEN_AQUI`
- **Status:** ✅ Ativo

**Clique:** "Salvar"

#### WEBHOOK 5: Requisições

- **Nome:** `Requisições → Google Sheets`
- **Evento:** `REQUISITION_STATUS_UPDATED`
- **URL:** `https://script.google.com/macros/s/SEU_ID_AQUI/exec/requisition-status-updated`
- **Método:** `POST`
- **Headers:**
  - Nome: `Authorization`
  - Valor: `Bearer SEU_TOKEN_AQUI`
- **Status:** ✅ Ativo

**Clique:** "Salvar"

---

## PASSO 4: Testar Webhook

### Opção 1: Teste Manual no Apps Script

1. **No Apps Script**, encontre a função `testarCandidatura()`
2. **Execute** esta função
3. **Verifique** se uma linha foi adicionada na aba "Candidaturas"

### Opção 2: Evento Real na Inhire

1. **Faça alguma ação na Inhire:**
   - Adicione uma candidatura a uma vaga
   - Mude um candidato de etapa
   - Crie uma nova vaga
2. **Aguarde 5-10 segundos**
3. **Verifique a planilha:**
   - Vá até a aba correspondente
   - Deve aparecer uma nova linha com os dados REAIS

---

## PASSO 5: Monitorar Logs

### Logs no Apps Script

1. **Acesse:** Apps Script > "Execuções" (ícone à esquerda)
2. **Veja:** Últimas execuções do webhook
3. **Debug:** Se houver erro, clique na execução para ver detalhes

### Logs na Planilha

1. **Acesse:** Aba "Log de Eventos"
2. **Veja:** Histórico completo de todos webhooks recebidos
3. **Filtros:** Use filtros para buscar eventos específicos

---

## ✅ CHECKLIST DE VALIDAÇÃO

Após configurar, verifique:

- [ ] Token gerado e guardado
- [ ] 6 abas criadas na planilha
- [ ] Código do webhook receiver implantado
- [ ] URL do Web App copiada
- [ ] 5 webhooks configurados na Inhire
- [ ] Headers `Authorization` configurados corretamente
- [ ] Teste manual executado com sucesso
- [ ] Primeira linha de dados reais recebida

---

## 🔍 TROUBLESHOOTING

### Webhook não recebe dados

**Causa 1:** Token incorreto
- **Solução:** Verifique se o token no Apps Script (linha 22) é EXATAMENTE o mesmo que nos headers da Inhire

**Causa 2:** URL incorreta
- **Solução:** Verifique se a URL tem `/exec/TIPO-EVENTO` no final

**Causa 3:** Headers mal configurados
- **Solução:** Header deve ser `Authorization` (com A maiúsculo) e valor `Bearer TOKEN` (com espaço)

### Erro 401 Unauthorized

- **Causa:** Token não bate
- **Solução:** Gere novo token e atualize em TODOS os lugares:
  1. Apps Script linha 22
  2. 5 webhooks na Inhire

### Erro 404 Not Found

- **Causa:** URL incorreta
- **Solução:** Verifique se você implantou como "Aplicativo da Web" e copiou a URL correta

### Dados não aparecem na planilha

- **Causa:** Aba não foi criada
- **Solução:** Execute `criarEstruturaPlanilha()` novamente

---

## 📊 PRÓXIMOS PASSOS

Com o webhook funcionando:

1. **Analise os dados:** Use filtros e gráficos do Google Sheets
2. **Exporte dados:** Arquivo > Download > CSV ou Excel
3. **Automatize relatórios:** Crie dashboards com Google Data Studio
4. **Integre com BI:** Conecte com Power BI, Tableau, etc.

---

## 🎉 PRONTO!

Seu webhook está **FUNCIONANDO** e coletando dados reais da Inhire em tempo real!

**Latência:** ~5 segundos (evento na Inhire → linha na planilha)
**Custo:** R$ 0 (quota gratuita do Google)
**Manutenção:** Zero (roda automaticamente)

---

**Criado em:** 2026-06-25
**Versão:** 1.0
**Status:** ✅ Pronto para produção
