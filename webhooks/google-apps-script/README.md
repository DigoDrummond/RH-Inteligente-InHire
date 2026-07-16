# Webhooks Inhire → Google Sheets

Sistema completo para monitorar ações da Inhire em tempo real usando Google Sheets.

---

## 📁 Arquivos (Use Nesta Ordem)

### 1️⃣ **1_setup_token.js**
Gera token de segurança (senha de proteção)

**Execute:** UMA VEZ
**Tempo:** 2 minutos
**Resultado:** Token secreto gerado

---

### 2️⃣ **2_setup_planilha.js**
Cria estrutura de abas na planilha

**Execute:** UMA VEZ
**Tempo:** 3 minutos
**Resultado:** 6 abas criadas automaticamente

---

### 3️⃣ **3_webhook_receiver.js**
Código principal que recebe webhooks

**Execute:** FICA PERMANENTE
**Tempo:** 5 minutos de setup
**Resultado:** Planilha atualiza automaticamente quando eventos acontecem

---

### 📖 **GUIA_PASSO_A_PASSO.md**
Instruções detalhadas de setup

**Leia:** ANTES de começar
**Tempo:** 15-20 minutos total

---

## 🚀 Quick Start

```
1. Gerar token        → Execute 1_setup_token.js
2. Criar abas         → Execute 2_setup_planilha.js
3. Adicionar webhook  → Cole 3_webhook_receiver.js
4. Implantar Web App  → Implantar > Nova implantação
5. Configurar Inhire  → Criar 5 webhooks
6. Testar             → Criar candidatura na Inhire
```

---

## ❓ FAQ Rápido

**Q: Preciso executar todos os arquivos sempre?**
A: Não! Apenas no setup inicial. Depois só o arquivo 3 fica rodando.

**Q: Posso apagar os arquivos 1 e 2 depois?**
A: Sim! Após usar, pode apagar. Só mantenha o arquivo 3.

**Q: Preciso de credenciais da Framework?**
A: **NÃO!** Você configura webhooks logado na Inhire. A Inhire já sabe quem você é.

**Q: Quanto custa?**
A: R$ 0 (grátis). Google Apps Script é gratuito.

**Q: Funciona em tempo real?**
A: Sim! Latência de ~5 segundos.

---

## 🔑 Sobre Autenticação

### **Você NÃO precisa passar credenciais da Framework!**

**Por quê?**

```
SISTEMA ATUAL (Polling):           WEBHOOKS (Novo):
━━━━━━━━━━━━━━━━━━━━━            ━━━━━━━━━━━━━━━━━━
Você → Inhire                      Inhire → Você
Você busca dados                   Inhire envia dados
Precisa autenticar ✅              Não precisa ❌

Login:                             Já está logado:
- email: service@...               - Você configura logado
- password: xxx                    - Inhire sabe tenant
- Inhire valida você               - Você valida Inhire
```

**Autenticação de Webhooks:**
- Você gera UM token (arquivo 1)
- Configura no código (arquivo 3)
- Passa para Inhire nos webhooks
- Inhire envia token de volta
- Apps Script valida e aceita

**Fluxo:**
```
1. Você: Gera token "abc123"
2. Você: Configura no código
3. Você: Passa para Inhire (header Authorization: Bearer abc123)
4. Inhire: Envia webhook com esse token
5. Apps Script: Valida token e aceita
```

---

## 📊 Estrutura Final

Após setup, sua planilha terá:

```
📊 Monitoramento Inhire
├── ⚙️ Configuração       (instruções e token)
├── 📋 Candidaturas        (novas inscrições)
├── 🔄 Mudanças de Etapa   (transições)
├── 💼 Novas Vagas         (vagas criadas)
├── 📝 Formulários         (respostas)
├── 📋 Requisições         (aprovações)
└── 📜 Log de Eventos      (histórico completo)
```

---

## 🎯 Resultado

**Antes (Polling):**
- Latência: 6-12 horas
- Custo: Variável
- Requer servidor

**Depois (Webhooks):**
- Latência: 5 segundos ⚡
- Custo: R$ 0 💰
- Sem servidor ✅

---

## 📞 Suporte

**Documentação completa:**
- `GUIA_PASSO_A_PASSO.md` - Instruções detalhadas
- `../GUIA_WEBHOOKS_GOOGLE_SHEETS.md` - Guia original
- `../../RESUMO_WEBHOOKS_GOOGLE_SHEETS.md` - Resumo executivo

**Problemas comuns:**
Consulte seção "Troubleshooting" no guia passo a passo.

---

**Versão:** 1.0.0
**Data:** 2026-06-25
**Status:** ✅ Pronto para uso
