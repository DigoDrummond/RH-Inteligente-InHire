# 🚀 GUIA PASSO A PASSO - DEPLOY DO WEB APP

## 📋 PASSO 1: ACESSAR O GOOGLE APPS SCRIPT

1. Abra seu navegador (Chrome recomendado)
2. Acesse: **https://script.google.com**
3. Faça login com sua conta Google (@frwk.com.br)
4. Clique no botão **"+ Novo projeto"** (canto superior esquerdo)

---

## 📂 PASSO 2: RENOMEAR O PROJETO

1. No editor que abrir, clique em **"Projeto sem título"** (canto superior esquerdo)
2. Digite: **InHire - Portal Web**
3. Pressione Enter para salvar

---

## 📝 PASSO 3: CRIAR OS ARQUIVOS

### 3.1. Code.gs (já existe)

1. O arquivo **Code.gs** já está criado
2. **DELETAR** todo o conteúdo que está nele
3. Abrir o arquivo: `apps_script_webapp/Code.gs` no seu computador
4. **COPIAR TODO** o conteúdo (Ctrl+A → Ctrl+C)
5. **COLAR** no editor do Apps Script (Ctrl+V)
6. Clicar em **Salvar** (ícone de disquete ou Ctrl+S)

---

### 3.2. Dashboard.html (criar novo)

1. Clicar no **ícone "+"** ao lado de "Arquivos" (menu lateral esquerdo)
2. Selecionar **"HTML"**
3. Na janela que abrir, digitar: **Dashboard**
4. Clicar em **"OK"**
5. Abrir o arquivo: `apps_script_webapp/Dashboard.html` no seu computador
6. **COPIAR TODO** o conteúdo (Ctrl+A → Ctrl+C)
7. **COLAR** no novo arquivo HTML no Apps Script (Ctrl+V)
8. Clicar em **Salvar** (Ctrl+S)

---

### 3.3. Styles.html (criar novo)

1. Clicar no **ícone "+"** ao lado de "Arquivos"
2. Selecionar **"HTML"**
3. Digitar: **Styles**
4. Clicar em **"OK"**
5. Abrir o arquivo: `apps_script_webapp/Styles.html` no seu computador
6. **COPIAR TODO** o conteúdo (Ctrl+A → Ctrl+C)
7. **COLAR** no novo arquivo HTML (Ctrl+V)
8. Clicar em **Salvar** (Ctrl+S)

---

### 3.4. Busca.html (criar novo)

1. Clicar no **ícone "+"** ao lado de "Arquivos"
2. Selecionar **"HTML"**
3. Digitar: **Busca**
4. Clicar em **"OK"**
5. Abrir o arquivo: `apps_script_webapp/Busca.html` no seu computador
6. **COPIAR TODO** o conteúdo (Ctrl+A → Ctrl+C)
7. **COLAR** no novo arquivo HTML (Ctrl+V)
8. Clicar em **Salvar** (Ctrl+S)

---

### 3.5. Relatorios.html (criar novo)

1. Clicar no **ícone "+"** ao lado de "Arquivos"
2. Selecionar **"HTML"**
3. Digitar: **Relatorios**
4. Clicar em **"OK"**
5. Abrir o arquivo: `apps_script_webapp/Relatorios.html` no seu computador
6. **COPIAR TODO** o conteúdo (Ctrl+A → Ctrl+C)
7. **COLAR** no novo arquivo HTML (Ctrl+V)
8. Clicar em **Salvar** (Ctrl+S)

---

## ✅ PASSO 4: VERIFICAR ESTRUTURA

No menu lateral esquerdo (Arquivos), você deve ver:

```
📂 InHire - Portal Web
  📄 Code.gs
  📄 Dashboard.html
  📄 Styles.html
  📄 Busca.html
  📄 Relatorios.html
```

**Total: 5 arquivos**

---

## 🚀 PASSO 5: FAZER O DEPLOY

### 5.1. Iniciar Deploy

1. Clicar no botão **"Implantar"** (canto superior direito)
2. Selecionar **"Nova implantação"**

---

### 5.2. Configurar Tipo

1. Na janela que abrir, clicar no **ícone de engrenagem ⚙️** ao lado de "Selecionar tipo"
2. Selecionar **"Aplicativo da Web"**

---

### 5.3. Configurar Descrição

No campo **"Descrição"**, digitar:
```
v1.0 - Portal InHire Framework
```

---

### 5.4. Configurar Permissões

**Executar como:**
- Selecionar: **Eu (seu-email@frwk.com.br)**

**Quem tem acesso:**
- Selecionar: **Qualquer pessoa na organização Framework**

OU (se quiser público):
- Selecionar: **Qualquer pessoa**

---

### 5.5. Implantar

1. Clicar no botão **"Implantar"**
2. Uma janela de autorização vai abrir
3. Clicar em **"Autorizar acesso"**

---

## 🔐 PASSO 6: AUTORIZAR O APLICATIVO

### 6.1. Primeira Autorização

1. Uma janela do Google vai abrir
2. Selecionar sua conta **@frwk.com.br**
3. Você verá: "Google não verificou este app"
4. Clicar em **"Avançado"** (texto pequeno embaixo)
5. Clicar em **"Ir para InHire - Portal Web (não seguro)"**

---

### 6.2. Conceder Permissões

1. Você verá a lista de permissões necessárias:
   - Ver e gerenciar planilhas
   - Exibir e executar conteúdo da Web
2. Clicar em **"Permitir"**

---

## 🎉 PASSO 7: COPIAR A URL

1. Após autorizar, você verá uma tela com:
   - **ID de implantação:** (copiar se precisar)
   - **URL do aplicativo da web:** (ESTA É A URL QUE VOCÊ PRECISA!)

2. **COPIAR** a URL completa
   - Exemplo: `https://script.google.com/macros/s/ABC123.../exec`

3. Colar em um bloco de notas para guardar

---

## 🌐 PASSO 8: ACESSAR O WEB APP

1. Abrir uma nova aba no navegador
2. **COLAR** a URL copiada
3. Pressionar Enter
4. Aguardar 3-5 segundos (primeira vez é mais lento)
5. **SEU PORTAL ESTÁ NO AR!** 🎉

---

## 📧 PASSO 9: COMPARTILHAR COM A EQUIPE

### Modelo de E-mail:

```
Assunto: 🎉 Novo Portal InHire Analytics no Ar!

Olá equipe,

Nosso novo portal de análise de posições está disponível!

🔗 LINK DE ACESSO:
https://script.google.com/macros/s/ABC123.../exec

📊 FUNCIONALIDADES:
✅ Dashboard com estatísticas em tempo real
✅ Filtros por Cliente, Torre e Status
✅ Distribuição de SLA
✅ Tabela completa de posições
✅ Busca avançada
✅ Relatórios executivos

📱 Acesse de qualquer dispositivo (desktop, tablet, mobile)

Qualquer dúvida, me avise!

Abs,
[Seu Nome]
```

---

## 🔄 PASSO 10: ATUALIZAR O WEB APP (FUTURO)

Quando fizer alterações nos arquivos:

1. Editar os arquivos no Apps Script
2. Clicar em **Salvar** (Ctrl+S)
3. Ir em **Implantar** → **Gerenciar implantações**
4. Clicar no **ícone de lápis** ✏️ da implantação ativa
5. Em **"Versão"**, clicar em **"Nova versão"**
6. Adicionar descrição: `v1.1 - Correções e melhorias`
7. Clicar em **"Implantar"**
8. **A URL permanece a mesma!** ✅

---

## 🐛 RESOLUÇÃO DE PROBLEMAS

### Problema 1: "Erro ao carregar dados"
**Solução:**
- Verificar se o SPREADSHEET_ID está correto no Code.gs (linha 24)
- Verificar se a planilha existe e você tem acesso

---

### Problema 2: Página em branco
**Solução:**
- Pressionar F12 (abrir console)
- Ver se há erros JavaScript
- Verificar se todos os 5 arquivos foram criados

---

### Problema 3: "Script não autorizado"
**Solução:**
- Ir em **Implantar** → **Gerenciar implantações**
- Deletar a implantação
- Criar nova implantação
- Autorizar novamente

---

### Problema 4: Dados não aparecem
**Solução:**
1. Verificar SPREADSHEET_ID no Code.gs:
```javascript
SPREADSHEET_ID: '1pWscZVbQ_jA7D5aJWycDuRi--8M_AIPSDN9j451-Pd0'
```

2. Verificar SHEET_NAME:
```javascript
SHEET_NAME: 'Posições_API'
```

3. Rodar o script de upload:
```bash
python upload_analise_posicoes_to_sheets.py
```

---

## 📞 SUPORTE

**Dúvidas sobre:**
- Deploy: Revisar este guia
- Erros: Ver console (F12)
- Dados: Verificar planilha
- Permissões: Refazer autorização

---

## ✅ CHECKLIST FINAL

Antes de compartilhar com a equipe:

- [ ] 5 arquivos criados no Apps Script
- [ ] Deploy realizado com sucesso
- [ ] Autorização concedida
- [ ] URL copiada
- [ ] Portal acessível (testado)
- [ ] Dados carregando corretamente
- [ ] Filtros funcionando
- [ ] Busca funcional
- [ ] Relatórios visíveis
- [ ] Responsivo (testar no celular)

---

## 🎯 RESUMO RÁPIDO

```
1. script.google.com → Novo projeto
2. Renomear: "InHire - Portal Web"
3. Criar 5 arquivos (Code.gs + 4 HTML)
4. Copiar conteúdo de cada arquivo
5. Salvar tudo
6. Implantar → Nova implantação → Aplicativo da Web
7. Autorizar
8. Copiar URL
9. Acessar e testar
10. Compartilhar com equipe
```

---

**🎉 PRONTO! SEU PORTAL ENTERPRISE ESTÁ NO AR!**

Link oficial: `https://script.google.com/macros/s/ABC123.../exec`

---

**Data:** 06/02/2026
**Versão:** 1.0
**Status:** ✅ Deploy Ready
