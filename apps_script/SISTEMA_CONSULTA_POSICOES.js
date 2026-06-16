/**
 * ================================================================================
 * SISTEMA DE CONSULTA DE POSIÇÕES - GOOGLE APPS SCRIPT
 * ================================================================================
 *
 * Sistema visual e fluído para consulta de informações de posições
 * Conecta com a planilha Posições_API
 *
 * Funcionalidades:
 * 1. Dashboard principal com estatísticas
 * 2. Busca por filtros (cliente, recrutadora, status, período)
 * 3. Detalhes da posição
 * 4. Exportar resultados
 * 5. Gráficos e indicadores visuais
 *
 * ================================================================================
 */

// ============================================================================
// CONFIGURAÇÕES
// ============================================================================

const CONFIG = {
  SPREADSHEET_ID: '1pWscZVbQ_jA7D5aJWycDuRi--8M_AIPSDN9j451-Pd0',
  SHEET_NAME: 'Posições_API',
  APP_NAME: 'Sistema de Consulta de Posições',
  VERSION: '1.0.0'
};

// ============================================================================
// MENU PRINCIPAL
// ============================================================================

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🎯 Sistema Posições')
    .addItem('📊 Dashboard', 'abrirDashboard')
    .addItem('🔍 Buscar Posição', 'abrirBusca')
    .addItem('📈 Relatórios', 'abrirRelatorios')
    .addSeparator()
    .addItem('⚙️ Configurações', 'abrirConfiguracoes')
    .addToUi();
}

// ============================================================================
// DASHBOARD PRINCIPAL
// ============================================================================

function abrirDashboard() {
  const html = HtmlService.createHtmlOutputFromFile('Dashboard')
    .setWidth(1200)
    .setHeight(800)
    .setTitle('📊 Dashboard - Posições');

  SpreadsheetApp.getUi().showModalDialog(html, CONFIG.APP_NAME);
}

function getDashboardData() {
  const ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  const sheet = ss.getSheetByName(CONFIG.SHEET_NAME);
  const data = sheet.getDataRange().getValues();

  // Headers
  const headers = data[0];
  const rows = data.slice(1);

  // Estatísticas gerais
  const stats = {
    totalPosicoes: rows.length,
    posicoesAbertas: rows.filter(r => r[4] === 'open').length,
    posicoesFechadas: rows.filter(r => r[4] === 'closed').length,
    posicoesContratadas: rows.filter(r => r[13] !== null && r[13] !== '').length,
    posicoesCanceladas: rows.filter(r => r[4] === 'canceled').length,

    // SLA médio
    slaGeral: calcularMedia(rows, 16),
    slaRecrutamento: calcularMedia(rows, 17),

    // Top clientes
    topClientes: getTopN(rows, 11, 5),

    // Top recrutadoras
    topRecrutadoras: getTopN(rows, 10, 5),

    // Distribuição por torre
    porTorre: getDistribuicao(rows, 12),

    // Indicador de prazo
    dentroDoPrazo: rows.filter(r => r[19] === 'Dentro do prazo').length,
    foraDoPrazo: rows.filter(r => r[19] === 'Fora do prazo').length,

    // Posições com pausa
    comPausa: rows.filter(r => r[21] > 0).length,

    // Timeline (últimos 12 meses)
    posicoesPorMes: getPosicoesPorMes(rows, 6)
  };

  return stats;
}

// ============================================================================
// BUSCA AVANÇADA
// ============================================================================

function abrirBusca() {
  const html = HtmlService.createHtmlOutputFromFile('Busca')
    .setWidth(1000)
    .setHeight(700)
    .setTitle('🔍 Buscar Posições');

  SpreadsheetApp.getUi().showModalDialog(html, 'Busca de Posições');
}

function buscarPosicoes(filtros) {
  const ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  const sheet = ss.getSheetByName(CONFIG.SHEET_NAME);
  const data = sheet.getDataRange().getValues();

  const headers = data[0];
  let rows = data.slice(1);

  // Aplicar filtros
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

  if (filtros.dataInicio && filtros.dataFim) {
    rows = rows.filter(r => {
      const dataPublicacao = new Date(r[6]);
      const inicio = new Date(filtros.dataInicio);
      const fim = new Date(filtros.dataFim);
      return dataPublicacao >= inicio && dataPublicacao <= fim;
    });
  }

  // Retornar dados formatados
  return {
    headers: headers,
    rows: rows.slice(0, 100), // Limitar a 100 resultados
    total: rows.length
  };
}

// ============================================================================
// DETALHES DA POSIÇÃO
// ============================================================================

function getDetalhesPosicao(posicaoId) {
  const ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  const sheet = ss.getSheetByName(CONFIG.SHEET_NAME);
  const data = sheet.getDataRange().getValues();

  const headers = data[0];
  const row = data.find(r => r[0] == posicaoId);

  if (!row) {
    return null;
  }

  // Montar objeto com todos os dados
  const detalhes = {};
  headers.forEach((header, index) => {
    detalhes[header] = row[index];
  });

  return detalhes;
}

// ============================================================================
// RELATÓRIOS
// ============================================================================

function abrirRelatorios() {
  const html = HtmlService.createHtmlOutputFromFile('Relatorios')
    .setWidth(1000)
    .setHeight(700)
    .setTitle('📈 Relatórios');

  SpreadsheetApp.getUi().showModalDialog(html, 'Relatórios');
}

function getOpcoesFiltros() {
  const ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  const sheet = ss.getSheetByName(CONFIG.SHEET_NAME);
  const data = sheet.getDataRange().getValues();
  const rows = data.slice(1);

  return {
    clientes: [...new Set(rows.map(r => r[11]).filter(v => v))].sort(),
    recrutadoras: [...new Set(rows.map(r => r[10]).filter(v => v))].sort(),
    torres: [...new Set(rows.map(r => r[12]).filter(v => v))].sort(),
    status: [...new Set(rows.map(r => r[4]).filter(v => v))].sort()
  };
}

// ============================================================================
// FUNÇÕES AUXILIARES
// ============================================================================

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

// ============================================================================
// EXPORTAR DADOS
// ============================================================================

function exportarParaCSV(dados) {
  const csv = dados.map(row => row.join(',')).join('\n');
  const blob = Utilities.newBlob(csv, 'text/csv', 'posicoes_export.csv');

  return blob.getDataAsString();
}
