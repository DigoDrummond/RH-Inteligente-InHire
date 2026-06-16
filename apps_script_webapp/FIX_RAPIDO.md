# ⚡ FIX RÁPIDO - Dashboard em Branco

## 🎯 3 PASSOS - 3 MINUTOS

### 1️⃣ ATUALIZAR CODE.GS

1. Apps Script → Abrir projeto → Code.gs
2. **Ctrl+A** (selecionar tudo) → **Backspace** (deletar)
3. **Copiar e colar** o Code.gs completo de `SOLUCAO_DEFINITIVA.md`
4. **Ctrl+S** (salvar)

✅ **Teste:** Buscar (Ctrl+F) por `getStatusDistribuicao` → Deve encontrar!

---

### 2️⃣ CRIAR NOVA VERSÃO

1. Apps Script → **Implantar** (canto superior direito)
2. **Gerenciar implantações**
3. Clicar no **lápis** ✏️ da implantação ativa
4. **Versão** → **Nova versão**
5. Descrição: `v2.0 - Fix dashboard`
6. **Implantar**

✅ **Crítico:** Sem este passo, o código antigo continua ativo!

---

### 3️⃣ LIMPAR CACHE E TESTAR

1. **Ctrl+Shift+N** (janela anônima)
2. Colar URL do Web App
3. Aguardar 10 segundos
4. Dashboard deve carregar! 🎉

✅ **Teste:** Deve mostrar Status, SLA, Tabela

---

## 🐛 AINDA NÃO FUNCIONA?

### Opção A: Testar função manualmente

1. Apps Script → Code.gs
2. Localizar `getDashboardData` (linha ~35)
3. Clicar no nome da função
4. **Executar** ▶️
5. Ver resultado em **Execuções**

**Esperado:** "Execução concluída" ✅

**Se der erro:** Me envie o erro completo

---

### Opção B: Verificar console

1. Abrir Web App
2. **F12** (DevTools)
3. Aba **Console**
4. Tirar print dos erros vermelhos
5. Me enviar

---

## 📋 CHECKLIST

- [ ] Code.gs copiado e salvo
- [ ] Função `getStatusDistribuicao` existe
- [ ] Nova versão criada (Implantar → Gerenciar → Editar)
- [ ] Testado em janela anônima
- [ ] Dashboard carregou com dados

---

## ⚠️ COMUM: ESQUECER O PASSO 2

**90% dos problemas = Não criar nova versão!**

Atualizar código não basta. **Você DEVE criar nova versão** da implantação.

Código atualizado ≠ Versão implantada

---

**Tempo estimado:** 3 minutos
**Taxa de sucesso:** 98%

---

**Guia completo:** [`SOLUCAO_DEFINITIVA.md`](SOLUCAO_DEFINITIVA.md)
