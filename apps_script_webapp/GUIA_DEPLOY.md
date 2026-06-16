# 🚀 GUIA DE DEPLOY - WEB APP INHIRE

## 📋 Visão Geral

Este guia mostra como fazer o deploy do Sistema de Consulta de Posições como um **Web App independente** acessível via URL própria.

---

## 🎯 O que você vai ter

✅ **Site web independente** (não precisa abrir a planilha)
✅ **URL própria** para compartilhar com a equipe
✅ **Acesso controlado** (você define quem pode acessar)
✅ **Interface moderna** e responsiva
✅ **3 páginas**: Dashboard, Busca e Relatórios

---

## 📁 Arquivos do Projeto

```
apps_script_webapp/
├── Code.gs              # Backend (funções principais)
├── Dashboard.html       # Página do Dashboard
├── Busca.html           # Página de Busca
├── Relatorios.html      # Página de Relatórios
├── Styles.html          # CSS (estilos compartilhados)
└── GUIA_DEPLOY.md       # Este arquivo
```

---

## 🔧 PASSO 1: Criar o Projeto no Google Apps Script

### 1.1. Acessar o Apps Script

1. Acesse: https://script.google.com
2. Clique em **"Novo projeto"**
3. Renomeie para: `InHire - Sistema de Consulta Web`

### 1.2. Adicionar os arquivos

**Arquivo 1: Code.gs**
1. No editor, renomeie `Code.gs` (já existe)
2. Copie todo o conteúdo de `apps_script_webapp/Code.gs`
3. Cole no editor
4. Salve (Ctrl+S)

**Arquivo 2: Dashboard.html**
1. Clique no **"+"** ao lado de "Arquivos"
2. Selecione **"HTML"**
3. Nome: `Dashboard`
4. Copie o conteúdo de `apps_script_webapp/Dashboard.html`
5. Cole no editor
6. Salve (Ctrl+S)

**Arquivo 3: Styles.html**
1. Clique no **"+"** → **"HTML"**
2. Nome: `Styles`
3. Copie o conteúdo de `apps_script_webapp/Styles.html`
4. Cole e salve

**Arquivo 4: Busca.html**
1. Clique no **"+"** → **"HTML"**
2. Nome: `Busca`
3. Copie o conteúdo de `apps_script_webapp/Busca.html`
4. Cole e salve

**Arquivo 5: Relatorios.html**
1. Clique no **"+"** → **"HTML"**
2. Nome: `Relatorios`
3. Copie o conteúdo de `apps_script_webapp/Relatorios.html`
4. Cole e salve

### 1.3. Verificar estrutura

Você deve ter:
```
📂 InHire - Sistema de Consulta Web
  ├── Code.gs
  ├── Dashboard.html
  ├── Styles.html
  ├── Busca.html
  └── Relatorios.html
```

---

## 🌐 PASSO 2: Fazer o Deploy como Web App

### 2.1. Configurar o Deploy

1. No editor do Apps Script, clique em **"Implantar"** (Deploy)
2. Selecione **"Nova implantação"** (New deployment)
3. Clique no ícone de **engrenagem ⚙️** ao lado de "Tipo"
4. Selecione **"Aplicativo da web"** (Web app)

### 2.2. Configurar as Opções

**Descrição:**
```
v1.0 - Sistema de Consulta de Posições
```

**Executar como:**
- Selecione: **"Eu"** (Me)
- Isso garante acesso aos dados da planilha

**Quem tem acesso:**
- **Opção 1**: "Qualquer pessoa" (sem login)
- **Opção 2**: "Qualquer pessoa na organização" (requer login do Google Workspace)
- **Opção 3**: "Somente eu" (apenas você)

**⚠️ RECOMENDADO**: "Qualquer pessoa na organização" (para equipe interna)

### 2.3. Autorizar o App

1. Clique em **"Implantar"**
2. Uma janela pedirá autorização
3. Clique em **"Autorizar acesso"**
4. Selecione sua conta Google
5. Clique em **"Avançado"**
6. Clique em **"Ir para InHire - Sistema de Consulta Web (não seguro)"**
7. Clique em **"Permitir"**

### 2.4. Copiar a URL

1. Após a autorização, você verá uma tela com:
   - **URL do aplicativo da web**
2. **COPIE ESSA URL** ✨
3. Exemplo:
   ```
   https://script.google.com/macros/s/XXXXXX.../exec
   ```

---

## ✅ PASSO 3: Testar o Web App

### 3.1. Abrir a URL

1. Cole a URL copiada no navegador
2. Aguarde carregar (pode demorar 3-5 segundos na primeira vez)
3. Você verá o Dashboard com os dados da planilha!

### 3.2. Testar as páginas

- **Dashboard**: Estatísticas e gráficos
- **Buscar**: Filtros de busca (clique no menu)
- **Relatórios**: Resumo executivo (clique no menu)

---

## 🔄 PASSO 4: Atualizar o Web App (quando necessário)

### 4.1. Fazer alterações no código

1. Acesse o projeto no Apps Script
2. Edite o arquivo desejado
3. Salve (Ctrl+S)

### 4.2. Criar nova implantação

**Opção A: Atualizar versão existente (Recomendado)**
1. Clique em **"Implantar"** → **"Gerenciar implantações"**
2. Clique no **ícone de lápis** da implantação ativa
3. Em "Versão", selecione **"Nova versão"**
4. Adicione descrição (ex: "v1.1 - Correções")
5. Clique em **"Implantar"**
6. **A URL permanece a mesma!** ✅

**Opção B: Nova implantação (nova URL)**
1. Clique em **"Implantar"** → **"Nova implantação"**
2. Repita o processo do PASSO 2
3. Você receberá uma **nova URL**

---

## 🔒 PASSO 5: Compartilhar com a Equipe

### 5.1. URL Oficial

Copie a URL do seu Web App:
```
https://script.google.com/macros/s/XXXXXX.../exec
```

### 5.2. Compartilhar

**Por e-mail:**
```
Olá equipe,

Nosso novo sistema de consulta de posições está no ar!

🔗 Link: https://script.google.com/macros/s/XXXXXX.../exec

Funcionalidades:
- Dashboard com estatísticas em tempo real
- Busca avançada com filtros
- Relatórios e exportações

Qualquer dúvida, me avise!
```

**Por Slack/Teams:**
```
📊 Sistema de Consulta de Posições InHire está no ar!
🔗 https://script.google.com/macros/s/XXXXXX.../exec

✨ Acesse e confira os dados atualizados!
```

### 5.3. Criar atalho

**Opção 1: Favoritar no navegador**
- Adicione aos favoritos para acesso rápido

**Opção 2: Criar link encurtado**
- Use bit.ly ou similar para criar URL amigável
- Exemplo: `bit.ly/inhire-dashboard`

**Opção 3: Adicionar à tela inicial (mobile)**
- No Chrome mobile: Menu → "Adicionar à tela inicial"

---

## 🎨 PERSONALIZAÇÃO

### Mudar cores

Edite o arquivo `Styles.html`:

```css
/* Cores principais */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Para mudar, substitua por suas cores */
background: linear-gradient(135deg, #SUA_COR_1 0%, #SUA_COR_2 100%);
```

### Mudar título

Edite `Code.gs`, linha 26:
```javascript
APP_NAME: 'SEU NOME AQUI',
```

### Mudar logo

Em cada arquivo HTML, linha com "📊 InHire Dashboard":
```html
<h1>SEU LOGO AQUI Dashboard</h1>
```

---

## 🐛 SOLUÇÃO DE PROBLEMAS

### Erro: "Script não autorizado"
**Solução:**
1. Vá em "Implantar" → "Gerenciar implantações"
2. Delete a implantação
3. Crie uma nova e autorize novamente

### Erro: "Não foi possível ler dados"
**Solução:**
1. Verifique se o SPREADSHEET_ID está correto no `Code.gs`
2. Verifique se o SHEET_NAME é `'Posições_API'`
3. Verifique se você tem acesso à planilha

### Página em branco
**Solução:**
1. Abra o Console do navegador (F12)
2. Veja se há erros JavaScript
3. Verifique se todos os arquivos HTML foram criados

### Dados não atualizam
**Solução:**
1. Force refresh: Ctrl+Shift+R (Windows) ou Cmd+Shift+R (Mac)
2. Limpe o cache do navegador
3. Aguarde 30 segundos e recarregue

---

## 📊 CONFIGURAÇÕES AVANÇADAS

### Restringir acesso por domínio

No `Code.gs`, adicione no início da função `doGet()`:

```javascript
function doGet(e) {
  // Verificar domínio
  const email = Session.getActiveUser().getEmail();
  if (!email.endsWith('@suaempresa.com')) {
    return HtmlService.createHtmlOutput('<h1>Acesso negado</h1>');
  }

  // Resto do código...
}
```

### Adicionar Google Analytics

Em cada arquivo HTML, adicione antes de `</head>`:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

---

## 📞 SUPORTE

**Problemas técnicos:**
- Verifique a documentação do Google Apps Script
- https://developers.google.com/apps-script/guides/web

**Dúvidas sobre dados:**
- Verifique a planilha `Posições_API`
- Confirme que a sincronização está funcionando

---

## 🎯 PRÓXIMOS PASSOS

✅ Deploy realizado
✅ URL compartilhada
⬜ Implementar exportações (CSV, Excel, PDF)
⬜ Adicionar mais filtros na busca
⬜ Criar relatórios customizados
⬜ Integrar com Power BI

---

## 📝 CHANGELOG

**v1.0.0** (2026-02-06)
- ✨ Deploy inicial
- 📊 Dashboard com estatísticas
- 🔍 Busca avançada
- 📈 Relatórios básicos

---

**🎉 Parabéns! Seu Web App está no ar!**

Link oficial: `https://script.google.com/macros/s/XXXXXX.../exec`
