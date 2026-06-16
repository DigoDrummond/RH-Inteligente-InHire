# 🔍 DIAGNÓSTICO - Dashboard em Branco

## ✅ PASSO 1: VERIFICAR SE O CODE.GS FOI ATUALIZADO

1. Abra o projeto no Apps Script
2. Clique em **Code.gs**
3. **Procure** por esta função (Ctrl+F):
   ```javascript
   function getStatusDistribuicao
   ```
4. **Se NÃO encontrar:** O Code.gs não foi atualizado corretamente!
   - Copie novamente o conteúdo completo de `apps_script_webapp/Code.gs`
   - Cole no editor
   - Salve (Ctrl+S)

---

## ✅ PASSO 2: TESTAR A FUNÇÃO NO CONSOLE

1. No Apps Script, clique em **Code.gs**
2. Localize a função `getDashboardData()`
3. Clique no nome da função
4. Clique em **"Executar"** (botão ▶️ no topo)
5. Se pedir autorização, autorize novamente
6. Veja o resultado em **"Execuções"** (menu lateral)

**Resultado esperado:** "Execução concluída" sem erros

**Se der erro:**
- Copie a mensagem de erro
- Me envie para eu te ajudar

---

## ✅ PASSO 3: VERIFICAR CONSOLE DO NAVEGADOR

1. Abra o Web App no navegador
2. Pressione **F12** (abre DevTools)
3. Clique na aba **"Console"**
4. **Procure por erros em vermelho**

**Erros comuns:**

**A) "google.script.run... is not defined"**
- Solução: Recarregue a página (Ctrl+Shift+R)

**B) "Failed to load resource"**
- Solução: Verifique SPREADSHEET_ID no Code.gs

**C) "Uncaught TypeError"**
- Solução: Dados no formato errado, veja erro específico

---

## ✅ PASSO 4: LIMPAR CACHE COMPLETAMENTE

### Opção A: Hard Refresh
1. Abra o Web App
2. Pressione **Ctrl+Shift+R** (Windows) ou **Cmd+Shift+R** (Mac)
3. Aguarde carregar

### Opção B: Limpar Cache Manualmente
1. Pressione **F12**
2. Clique com **botão direito** no ícone de atualizar (🔄)
3. Selecionar **"Limpar cache e fazer recarga forçada"**

### Opção C: Modo Anônimo
1. Abra uma **janela anônima/privada**
2. Cole a URL do Web App
3. Teste se funciona

---

## ✅ PASSO 5: VERIFICAR PERMISSÕES

1. No Apps Script, vá em **Visão geral** (menu lateral)
2. Veja se há mensagens de erro
3. Se houver "Não autorizado":
   - Executar qualquer função (passo 2)
   - Autorizar novamente

---

## ✅ PASSO 6: VERIFICAR PLANILHA

1. Abra a planilha:
   ```
   https://docs.google.com/spreadsheets/d/1pWscZVbQ_jA7D5aJWycDuRi--8M_AIPSDN9j451-Pd0
   ```

2. Verifique:
   - [ ] A aba **"Posições_API"** existe?
   - [ ] Tem dados (mais de 1 linha)?
   - [ ] Você tem permissão de leitura?

**Se a aba não existir:**
- Rode o script Python:
  ```bash
  python upload_analise_posicoes_to_sheets.py
  ```

---

## ✅ PASSO 7: COPIAR CODE.GS ATUALIZADO

Se nada funcionou, **copie este Code.gs limpo:**

```javascript
const CONFIG = {
  SPREADSHEET_ID: '1pWscZVbQ_jA7D5aJWycDuRi--8M_AIPSDN9j451-Pd0',
  SHEET_NAME: 'Posições_API',
  APP_NAME: 'InHire Portal',
  VERSION: '2.0.0'
};

function doGet(e) {
  const page = e.parameter.page || 'dashboard';
  let template;

  switch(page) {
    case 'dashboard':
      template = HtmlService.createTemplateFromFile('Dashboard');
      break;
    case 'busca':
      template = HtmlService.createTemplateFromFile('Busca');
      break;
    case 'relatorios':
      template = HtmlService.createTemplateFromFile('Relatorios');
      break;
    default:
      template = HtmlService.createTemplateFromFile('Dashboard');
  }

  return template.evaluate()
    .setTitle(CONFIG.APP_NAME)
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

function getDashboardData() {
  try {
    const ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
    const sheet = ss.getSheetByName(CONFIG.SHEET_NAME);

    if (!sheet) {
      throw new Error('Aba "' + CONFIG.SHEET_NAME + '" não encontrada!');
    }

    const data = sheet.getDataRange().getValues();
    if (data.length < 2) {
      throw new Error('Planilha vazia ou sem dados!');
    }

    const rows = data.slice(1);

    return {
      totalPosicoes: rows.length,
      posicoesAbertas: rows.filter(r => r[4] === 'open').length,
      posicoesContratadas: rows.filter(r => r[13] !== null && r[13] !== '').length,
      posicoesCanceladas: rows.filter(r => r[4] === 'canceled').length,
      slaGeral: calcularMedia(rows, 16),
      topClientes: getTopN(rows, 11, 5),
      topRecrutadoras: getTopN(rows, 10, 5),
      porTorre: getDistribuicao(rows, 12),
      dentroDoPrazo: rows.filter(r => r[19] === 'Dentro do prazo').length,
      foraDoPrazo: rows.filter(r => r[19] === 'Fora do prazo').length,
      posicoesPorMes: getPosicoesPorMes(rows, 6),
      statusDistribuicao: getStatusDistribuicao(rows, 4),
      slaDistribuicao: getSLADistribuicao(rows, 16),
      tabelaPosicoes: getTabelaPosicoes(rows)
    };
  } catch (error) {
    Logger.log('ERRO: ' + error.toString());
    throw new Error('Erro ao carregar dados: ' + error.message);
  }
}

function buscarPosicoes(filtros) {
  const ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  const sheet = ss.getSheetByName(CONFIG.SHEET_NAME);
  const data = sheet.getDataRange().getValues();
  let rows = data.slice(1);

  if (filtros.cliente) {
    rows = rows.filter(r => r[11] && r[11].toString().toLowerCase().includes(filtros.cliente.toLowerCase()));
  }
  if (filtros.recrutadora) {
    rows = rows.filter(r => r[10] && r[10].toString().toLowerCase().includes(filtros.recrutadora.toLowerCase()));
  }
  if (filtros.status) {
    rows = rows.filter(r => r[4] === filtros.status);
  }
  if (filtros.torre) {
    rows = rows.filter(r => r[12] === filtros.torre);
  }

  return {
    headers: data[0],
    rows: rows.slice(0, 100),
    total: rows.length
  };
}

function calcularMedia(rows, colIndex) {
  const valores = rows.map(r => r[colIndex]).filter(v => v && !isNaN(v)).map(v => parseFloat(v));
  return valores.length ? Math.round(valores.reduce((a, b) => a + b, 0) / valores.length) : 0;
}

function getTopN(rows, colIndex, n) {
  const contagem = {};
  rows.forEach(r => {
    const v = r[colIndex];
    if (v) contagem[v] = (contagem[v] || 0) + 1;
  });
  return Object.entries(contagem)
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([nome, quantidade]) => ({ nome, quantidade }));
}

function getDistribuicao(rows, colIndex) {
  const contagem = {};
  rows.forEach(r => {
    const v = r[colIndex] || 'Não informado';
    contagem[v] = (contagem[v] || 0) + 1;
  });
  return Object.entries(contagem)
    .map(([nome, quantidade]) => ({ nome, quantidade }))
    .sort((a, b) => b.quantidade - a.quantidade);
}

function getStatusDistribuicao(rows, colIndex) {
  const contagem = {};
  rows.forEach(r => {
    const v = r[colIndex] || 'unknown';
    contagem[v] = (contagem[v] || 0) + 1;
  });
  return Object.entries(contagem)
    .map(([status, quantidade]) => ({ status, quantidade }))
    .sort((a, b) => b.quantidade - a.quantidade);
}

function getPosicoesPorMes(rows, colIndex) {
  const porMes = {};
  rows.forEach(r => {
    if (r[colIndex]) {
      const mes = Utilities.formatDate(new Date(r[colIndex]), 'GMT-3', 'yyyy-MM');
      porMes[mes] = (porMes[mes] || 0) + 1;
    }
  });
  return Object.entries(porMes)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([mes, quantidade]) => ({ mes, quantidade }));
}

function getSLADistribuicao(rows, colIndex) {
  const faixas = {'0-30 dias': 0, '31-60 dias': 0, '61-90 dias': 0, '91-120 dias': 0, '120+ dias': 0};
  rows.forEach(r => {
    const sla = parseFloat(r[colIndex]);
    if (!isNaN(sla)) {
      if (sla <= 30) faixas['0-30 dias']++;
      else if (sla <= 60) faixas['31-60 dias']++;
      else if (sla <= 90) faixas['61-90 dias']++;
      else if (sla <= 120) faixas['91-120 dias']++;
      else faixas['120+ dias']++;
    }
  });
  return Object.entries(faixas).map(([range, quantidade]) => ({ range, quantidade }));
}

function getTabelaPosicoes(rows) {
  return rows.slice(0, 100).map(row => ({
    id: row[0],
    cargo: row[3],
    status: row[4],
    cliente: row[11],
    recrutadora: row[10],
    torre: row[12],
    data_publicacao: row[6],
    sla_geral: row[16],
    indicador_prazo: row[19]
  }));
}
```

---

## 📞 ME ENVIE ESTAS INFORMAÇÕES:

1. **Console do navegador (F12):**
   - Print ou copie todos os erros em vermelho

2. **Resultado da execução:**
   - Apps Script → Executar getDashboardData() → Copie o erro

3. **Status da planilha:**
   - A aba "Posições_API" existe? ✅ ou ❌
   - Quantas linhas tem? _____ linhas

Com essas informações consigo te ajudar melhor! 🎯
