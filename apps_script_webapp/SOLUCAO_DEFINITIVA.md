# ✅ SOLUÇÃO DEFINITIVA - Dashboard em Branco

## 🎯 DIAGNÓSTICO

Analisando o código, **TODOS os arquivos estão corretos**:
- ✅ Code.gs tem a função `getStatusDistribuicao()`
- ✅ Dashboard.html chama corretamente `getDashboardData()`
- ✅ Busca.html tem funcionalidade completa
- ✅ Relatórios.html tem funcionalidade completa

**O problema é um dos seguintes:**
1. Os arquivos não foram atualizados no Apps Script
2. A implantação não foi atualizada (ainda está na versão antiga)
3. Cache do navegador carregando versão antiga

---

## 🚀 SOLUÇÃO EM 4 PASSOS

### PASSO 1: VERIFICAR SE OS ARQUIVOS FORAM ATUALIZADOS

1. Abra o Apps Script: https://script.google.com
2. Abra seu projeto "InHire - Portal Web"
3. Clique em **Code.gs**
4. Pressione **Ctrl+F** (buscar)
5. Digite: `getStatusDistribuicao`
6. **Se NÃO encontrar:** Os arquivos não foram atualizados! Vá para PASSO 2
7. **Se encontrar:** Vá para PASSO 3

---

### PASSO 2: ATUALIZAR TODOS OS ARQUIVOS

Execute isto **NA ORDEM**:

#### 2.1. Atualizar Code.gs

1. Abra **Code.gs** no Apps Script
2. **SELECIONE TUDO** (Ctrl+A)
3. **DELETE** (Backspace)
4. Copie o código abaixo e cole no Code.gs:

```javascript
const CONFIG = {
  SPREADSHEET_ID: '1pWscZVbQ_jA7D5aJWycDuRi--8M_AIPSDN9j451-Pd0',
  SHEET_NAME: 'Posições_API',
  APP_NAME: 'Sistema de Consulta de Posições - InHire',
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
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
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

    const headers = data[0];
    const rows = data.slice(1);

    return {
      totalPosicoes: rows.length,
      posicoesAbertas: rows.filter(r => r[4] === 'open').length,
      posicoesFechadas: rows.filter(r => r[4] === 'closed').length,
      posicoesContratadas: rows.filter(r => r[13] !== null && r[13] !== '').length,
      posicoesCanceladas: rows.filter(r => r[4] === 'canceled').length,
      slaGeral: calcularMedia(rows, 16),
      slaRecrutamento: calcularMedia(rows, 17),
      topClientes: getTopN(rows, 11, 5),
      topRecrutadoras: getTopN(rows, 10, 5),
      porTorre: getDistribuicao(rows, 12),
      dentroDoPrazo: rows.filter(r => r[19] === 'Dentro do prazo').length,
      foraDoPrazo: rows.filter(r => r[19] === 'Fora do prazo').length,
      comPausa: rows.filter(r => r[21] > 0).length,
      posicoesPorMes: getPosicoesPorMes(rows, 6),
      statusDistribuicao: getStatusDistribuicao(rows, 4),
      slaDistribuicao: getSLADistribuicao(rows, 16),
      tabelaPosicoes: getTabelaPosicoes(rows, headers)
    };
  } catch (error) {
    Logger.log('Erro em getDashboardData: ' + error.toString());
    throw new Error('Erro ao carregar dados: ' + error.message);
  }
}

function buscarPosicoes(filtros) {
  try {
    const ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
    const sheet = ss.getSheetByName(CONFIG.SHEET_NAME);
    const data = sheet.getDataRange().getValues();
    const headers = data[0];
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
      rows = rows.filter(r => r[12] && r[12].toString().toLowerCase().includes(filtros.torre.toLowerCase()));
    }
    if (filtros.dataInicio && filtros.dataFim) {
      rows = rows.filter(r => {
        const dataPublicacao = new Date(r[6]);
        const inicio = new Date(filtros.dataInicio);
        const fim = new Date(filtros.dataFim);
        return dataPublicacao >= inicio && dataPublicacao <= fim;
      });
    }

    return {
      headers: headers,
      rows: rows.slice(0, 100),
      total: rows.length
    };
  } catch (error) {
    Logger.log('Erro em buscarPosicoes: ' + error.toString());
    throw error;
  }
}

function calcularMedia(rows, colIndex) {
  const valores = rows
    .map(r => r[colIndex])
    .filter(v => v !== null && v !== '' && !isNaN(v))
    .map(v => parseFloat(v));

  if (valores.length === 0) return 0;
  const soma = valores.reduce((a, b) => a + b, 0);
  return Math.round(soma / valores.length);
}

function getTopN(rows, colIndex, n) {
  const contagem = {};
  rows.forEach(r => {
    const valor = r[colIndex];
    if (valor) {
      contagem[valor] = (contagem[valor] || 0) + 1;
    }
  });

  return Object.entries(contagem)
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([nome, qtd]) => ({ nome, quantidade: qtd }));
}

function getDistribuicao(rows, colIndex) {
  const contagem = {};
  rows.forEach(r => {
    const valor = r[colIndex] || 'Não informado';
    contagem[valor] = (contagem[valor] || 0) + 1;
  });

  return Object.entries(contagem)
    .map(([nome, qtd]) => ({ nome, quantidade: qtd }))
    .sort((a, b) => b.quantidade - a.quantidade);
}

function getStatusDistribuicao(rows, colIndex) {
  const contagem = {};
  rows.forEach(r => {
    const valor = r[colIndex] || 'unknown';
    contagem[valor] = (contagem[valor] || 0) + 1;
  });

  return Object.entries(contagem)
    .map(([status, qtd]) => ({ status, quantidade: qtd }))
    .sort((a, b) => b.quantidade - a.quantidade);
}

function getPosicoesPorMes(rows, colIndex) {
  const porMes = {};
  rows.forEach(r => {
    const data = r[colIndex];
    if (data) {
      const mes = Utilities.formatDate(new Date(data), 'GMT-3', 'yyyy-MM');
      porMes[mes] = (porMes[mes] || 0) + 1;
    }
  });

  return Object.entries(porMes)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([mes, qtd]) => ({ mes, quantidade: qtd }));
}

function getSLADistribuicao(rows, colIndex) {
  const faixas = {
    '0-30 dias': 0,
    '31-60 dias': 0,
    '61-90 dias': 0,
    '91-120 dias': 0,
    '120+ dias': 0
  };

  rows.forEach(r => {
    const sla = parseFloat(r[colIndex]);
    if (isNaN(sla) || sla === null) return;

    if (sla <= 30) faixas['0-30 dias']++;
    else if (sla <= 60) faixas['31-60 dias']++;
    else if (sla <= 90) faixas['61-90 dias']++;
    else if (sla <= 120) faixas['91-120 dias']++;
    else faixas['120+ dias']++;
  });

  return Object.entries(faixas).map(([range, quantidade]) => ({ range, quantidade }));
}

function getTabelaPosicoes(rows, headers) {
  const idIdx = 0;
  const cargoIdx = 3;
  const statusIdx = 4;
  const dataPubIdx = 6;
  const recrutadoraIdx = 10;
  const clienteIdx = 11;
  const torreIdx = 12;
  const slaGeralIdx = 16;
  const indicadorPrazoIdx = 19;

  return rows.slice(0, 100).map(row => ({
    id: row[idIdx],
    cargo: row[cargoIdx],
    status: row[statusIdx],
    cliente: row[clienteIdx],
    recrutadora: row[recrutadoraIdx],
    torre: row[torreIdx],
    data_publicacao: row[dataPubIdx],
    sla_geral: row[slaGeralIdx],
    indicador_prazo: row[indicadorPrazoIdx]
  }));
}
```

5. **SALVE** (Ctrl+S)

#### 2.2. Verificar os outros arquivos

**Não precisa atualizar Dashboard.html, Busca.html, Relatorios.html e Styles.html** se você já os copiou anteriormente. Eles estão corretos.

Se tiver dúvida, os arquivos estão em:
- `apps_script_webapp/Dashboard.html`
- `apps_script_webapp/Busca.html`
- `apps_script_webapp/Relatorios.html`
- `apps_script_webapp/Styles.html`

---

### PASSO 3: ATUALIZAR A IMPLANTAÇÃO

**ISSO É CRÍTICO!** Atualizar os arquivos não basta. Você precisa criar uma **NOVA VERSÃO** da implantação.

1. No Apps Script, clique em **Implantar** (canto superior direito)
2. Clique em **Gerenciar implantações**
3. Na linha da implantação ativa, clique no **ícone de lápis** ✏️
4. Em **"Versão"**, clique em **"Nova versão"**
5. Em **"Descrição"**, digite: `v2.0 - Correção dashboard + status + busca funcional`
6. Clique em **"Implantar"**
7. **A URL permanece a mesma!** ✅

---

### PASSO 4: LIMPAR CACHE E TESTAR

1. **Feche** todas as abas do Web App
2. Abra uma **nova janela anônima** (Ctrl+Shift+N no Chrome)
3. Cole a URL do Web App
4. Aguarde 5-10 segundos
5. O dashboard deve carregar! 🎉

**Se ainda estiver em branco na janela anônima:**
- Pressione **F12**
- Vá na aba **Console**
- Tire um print dos erros
- Me envie

---

## 🧪 TESTE RÁPIDO

Depois de fazer os passos acima:

1. Abra o Web App na janela anônima
2. Dashboard deve mostrar:
   - ✅ Total de Posições
   - ✅ Posições Abertas
   - ✅ Gráfico "Status Atual das Posições" (barras horizontais)
   - ✅ Cards de SLA (0-30, 31-60, 61-90, 91-120, 120+)
   - ✅ Tabela com 50 posições

3. Clique em **Buscar Posições**
   - ✅ Deve carregar a página de busca
   - ✅ Digite um nome de cliente e clique em Buscar
   - ✅ Deve mostrar resultados

4. Clique em **Relatórios**
   - ✅ Deve carregar estatísticas
   - ✅ Deve mostrar resumo executivo

---

## ❌ SE AINDA NÃO FUNCIONAR

Execute este teste no Apps Script:

1. No Apps Script, clique em **Code.gs**
2. Localize a função `getDashboardData` (linha 35)
3. Clique no nome da função
4. Clique em **Executar** (▶️)
5. Veja o resultado em **Execuções** (menu lateral)

**Resultado esperado:**
- ✅ "Execução concluída" sem erros

**Se der erro:**
- Copie a mensagem de erro completa
- Me envie para diagnóstico

---

## 📋 CHECKLIST FINAL

Antes de testar:

- [ ] Code.gs atualizado e salvo
- [ ] Busquei por "getStatusDistribuicao" no Code.gs (encontrei!)
- [ ] Fui em Implantar → Gerenciar implantações
- [ ] Criei "Nova versão" da implantação
- [ ] Abri janela anônima
- [ ] Testei na janela anônima

---

## 🎯 RESUMO RÁPIDO

```bash
1. Copiar Code.gs completo (acima)
2. Colar no Apps Script
3. Salvar (Ctrl+S)
4. Implantar → Gerenciar → Editar → Nova versão
5. Janela anônima + testar
```

**Tempo estimado:** 3 minutos

---

## 📞 INFORMAÇÕES PARA DEBUG

Se ainda não funcionar, me envie:

1. **Print do console** (F12 → Console → Print dos erros em vermelho)
2. **Resultado de executar getDashboardData()** no Apps Script
3. **Confirme:** A aba "Posições_API" existe na planilha? Tem quantas linhas?

---

**Data:** 07/02/2026
**Status:** ✅ Solução Definitiva Ready
**Versão:** 2.0
