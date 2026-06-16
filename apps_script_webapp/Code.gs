/**
 * ================================================================================
 * WEB APP - SISTEMA DE CONSULTA DE POSIÇÕES
 * ================================================================================
 *
 * Aplicação web standalone para consulta de posições
 * Acesso via URL do Google Apps Script
 *
 * ================================================================================
 */

// ============================================================================
// CONFIGURAÇÕES
// ============================================================================

const CONFIG = {
  SPREADSHEET_ID: '1pWscZVbQ_jA7D5aJWycDuRi--8M_AIPSDN9j451-Pd0',
  SHEET_NAME: 'Posições_API',
  APP_NAME: 'Sistema de Consulta de Posições - InHire',
  VERSION: '1.0.0'
};

// ============================================================================
// WEB APP - PONTO DE ENTRADA
// ============================================================================

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

// ============================================================================
// INCLUDE - Para importar CSS e JS
// ============================================================================

function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

// ============================================================================
// API - DASHBOARD DATA
// ============================================================================

function getDashboardData() {
  try {
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
      posicoesPorMes: getPosicoesPorMes(rows, 6),

      // Status distribuição (substituiu Top Recrutadoras)
      statusDistribuicao: getStatusDistribuicao(rows, 4),

      // SLA Distribuição por faixas
      slaDistribuicao: getSLADistribuicao(rows, 16),

      // Tabela de posições (primeiras 50)
      tabelaPosicoes: getTabelaPosicoes(rows, headers)
    };

    return stats;
  } catch (error) {
    Logger.log('Erro em getDashboardData: ' + error.toString());
    throw error;
  }
}

// ============================================================================
// API - BUSCA AVANÇADA
// ============================================================================

function buscarPosicoes(filtros) {
  try {
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
  } catch (error) {
    Logger.log('Erro em buscarPosicoes: ' + error.toString());
    throw error;
  }
}

// ============================================================================
// API - DETALHES DA POSIÇÃO
// ============================================================================

function getDetalhesPosicao(posicaoId) {
  try {
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
  } catch (error) {
    Logger.log('Erro em getDetalhesPosicao: ' + error.toString());
    throw error;
  }
}

// ============================================================================
// API - OPÇÕES DE FILTROS
// ============================================================================

function getOpcoesFiltros() {
  try {
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
  } catch (error) {
    Logger.log('Erro em getOpcoesFiltros: ' + error.toString());
    throw error;
  }
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
  // Mapear índices das colunas
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

// ============================================================================
// EXPORTAR DADOS
// ============================================================================

function exportarParaCSV(dados) {
  const csv = dados.map(row => row.join(',')).join('\n');
  const blob = Utilities.newBlob(csv, 'text/csv', 'posicoes_export.csv');

  return blob.getDataAsString();
}
