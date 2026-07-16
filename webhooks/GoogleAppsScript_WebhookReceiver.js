/**
 * INHIRE WEBHOOK RECEIVER - Google Apps Script
 *
 * Este script recebe webhooks da API Inhire e registra eventos
 * diretamente na planilha Google Sheets
 *
 * COMO USAR:
 * 1. Abra sua planilha Google Sheets
 * 2. Menu: Extensões > Apps Script
 * 3. Cole este código
 * 4. Implemente como Web App (Implantar > Nova implantação)
 * 5. Configure a URL gerada nos webhooks da Inhire
 */

// ========================================
// CONFIGURAÇÕES
// ========================================

const CONFIG = {
  // Token secreto para validar requisições (senha que protege a planilha)
  //
  // COMO GERAR (escolha 1 opção):
  // Opção 1: Invente uma senha longa (ex: "framework-inhire-2026-webhook-abc123")
  // Opção 2: Execute a função gerarToken() abaixo e copie o resultado do log
  // Opção 3: Aperte teclas aleatórias no teclado (ex: "asd8f9a7sd6f5a4sd3f2")
  //
  SECRET_TOKEN: "SEU_TOKEN_SECRETO_AQUI",

  // Nome das abas da planilha
  SHEETS: {
    CANDIDATURAS: "Candidaturas",
    MUDANCAS_ETAPA: "Mudanças de Etapa",
    NOVAS_VAGAS: "Novas Vagas",
    FORMULARIOS: "Formulários",
    REQUISICOES: "Requisições",
    LOG: "Log de Eventos"
  },

  // Fuso horário
  TIMEZONE: "America/Sao_Paulo"
};


// ========================================
// FUNÇÃO PRINCIPAL - RECEBE WEBHOOKS
// ========================================

/**
 * Recebe requisições POST da Inhire
 * Esta é a função que o Google chama automaticamente
 */
function doPost(e) {
  try {
    // 1. Validar autenticação
    const authHeader = e.parameter.authorization || e.postData?.headers?.Authorization;
    if (!validarAutenticacao(authHeader)) {
      return respostaJSON({ error: "Unauthorized" }, 401);
    }

    // 2. Parsear payload
    const payload = JSON.parse(e.postData.contents);
    const eventType = identificarTipoEvento(e.pathInfo || e.parameter.event);

    Logger.log(`📥 Webhook recebido: ${eventType}`);
    Logger.log(`Payload: ${JSON.stringify(payload)}`);

    // 3. Processar evento
    let resultado;
    switch(eventType) {
      case "job_talent_added":
        resultado = processarCandidatura(payload);
        break;

      case "job_talent_stage_added":
        resultado = processarMudancaEtapa(payload);
        break;

      case "job_added":
        resultado = processarNovaVaga(payload);
        break;

      case "form_response_added":
        resultado = processarFormulario(payload);
        break;

      case "requisition_status_updated":
        resultado = processarRequisicao(payload);
        break;

      default:
        Logger.log(`⚠️ Evento desconhecido: ${eventType}`);
        resultado = { success: false, error: "Evento desconhecido" };
    }

    // 4. Registrar no log
    registrarLog(eventType, resultado.success ? "success" : "failed", payload, resultado.error);

    // 5. Retornar resposta
    return respostaJSON({
      status: resultado.success ? "success" : "failed",
      message: resultado.message,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    Logger.log(`❌ Erro ao processar webhook: ${error}`);
    registrarLog("erro_geral", "failed", {}, error.toString());

    return respostaJSON({
      status: "error",
      message: error.toString()
    }, 500);
  }
}


/**
 * Recebe requisições GET (para testes)
 */
function doGet(e) {
  return respostaJSON({
    service: "Inhire Webhook Receiver",
    status: "running",
    version: "1.0.0",
    timestamp: new Date().toISOString(),
    message: "Use POST para enviar webhooks"
  });
}


// ========================================
// PROCESSADORES DE EVENTOS
// ========================================

/**
 * Processa candidatura (JOB_TALENT_ADDED)
 */
function processarCandidatura(payload) {
  try {
    const sheet = obterOuCriarAba(CONFIG.SHEETS.CANDIDATURAS, [
      "Data/Hora",
      "Vaga",
      "Vaga ID",
      "Candidato ID",
      "Etapa Inicial",
      "Origem",
      "LinkedIn",
      "Localização",
      "Pretensão Salarial",
      "Modelo de Trabalho",
      "Usuário"
    ]);

    const linha = [
      formatarDataHora(new Date()),
      payload.jobName || "",
      payload.jobId || "",
      payload.talentId || "",
      payload.stageName || "",
      payload.source || "",
      payload.linkedinUsername || "",
      payload.location || "",
      payload.targetSalary || "",
      payload.workModel || "",
      payload.userName || "Sistema"
    ];

    sheet.appendRow(linha);

    // Formatar última linha
    const lastRow = sheet.getLastRow();
    formatarLinha(sheet, lastRow);

    return {
      success: true,
      message: `Candidatura registrada: ${payload.jobName}`
    };

  } catch (error) {
    return {
      success: false,
      error: error.toString()
    };
  }
}


/**
 * Processa mudança de etapa (JOB_TALENT_STAGE_ADDED)
 */
function processarMudancaEtapa(payload) {
  try {
    const sheet = obterOuCriarAba(CONFIG.SHEETS.MUDANCAS_ETAPA, [
      "Data/Hora",
      "Vaga",
      "Candidato ID",
      "Etapa Anterior",
      "Nova Etapa",
      "Tipo de Etapa",
      "Fase",
      "Usuário"
    ]);

    const linha = [
      formatarDataHora(new Date()),
      payload.jobName || "",
      payload.talentId || "",
      payload.previousStageName || "",
      payload.stageName || "",
      payload.stageType || "",
      payload.phaseType || "",
      payload.userName || "Sistema"
    ];

    sheet.appendRow(linha);

    const lastRow = sheet.getLastRow();
    formatarLinha(sheet, lastRow);

    return {
      success: true,
      message: `Mudança registrada: ${payload.previousStageName} → ${payload.stageName}`
    };

  } catch (error) {
    return {
      success: false,
      error: error.toString()
    };
  }
}


/**
 * Processa nova vaga (JOB_ADDED)
 */
function processarNovaVaga(payload) {
  try {
    const sheet = obterOuCriarAba(CONFIG.SHEETS.NOVAS_VAGAS, [
      "Data/Hora",
      "Nome da Vaga",
      "Vaga ID",
      "Descrição",
      "Criado por"
    ]);

    const linha = [
      formatarDataHora(new Date()),
      payload.jobName || "",
      payload.jobId || "",
      payload.jobDescription || "",
      payload.userName || "Sistema"
    ];

    sheet.appendRow(linha);

    const lastRow = sheet.getLastRow();
    formatarLinha(sheet, lastRow);

    return {
      success: true,
      message: `Vaga registrada: ${payload.jobName}`
    };

  } catch (error) {
    return {
      success: false,
      error: error.toString()
    };
  }
}


/**
 * Processa formulário respondido (FORM_RESPONSE_ADDED)
 */
function processarFormulario(payload) {
  try {
    const sheet = obterOuCriarAba(CONFIG.SHEETS.FORMULARIOS, [
      "Data/Hora",
      "Vaga ID",
      "Candidato ID",
      "Tipo",
      "Título",
      "Aprovado?",
      "Acertos",
      "Total",
      "% Acerto"
    ]);

    const acertos = payload.correctQuestionsCount || 0;
    const total = payload.totalQuestions || 1;
    const percentual = Math.round((acertos / total) * 100);

    const linha = [
      formatarDataHora(new Date()),
      payload.jobId || "",
      payload.talentId || "",
      payload.formType || "",
      payload.title || "",
      payload.passed ? "Sim" : "Não",
      acertos,
      total,
      `${percentual}%`
    ];

    sheet.appendRow(linha);

    const lastRow = sheet.getLastRow();
    formatarLinha(sheet, lastRow);

    return {
      success: true,
      message: `Formulário registrado: ${payload.title}`
    };

  } catch (error) {
    return {
      success: false,
      error: error.toString()
    };
  }
}


/**
 * Processa mudança de requisição (REQUISITION_STATUS_UPDATED)
 */
function processarRequisicao(payload) {
  try {
    const sheet = obterOuCriarAba(CONFIG.SHEETS.REQUISICOES, [
      "Data/Hora",
      "Título",
      "Requisição ID",
      "Status Anterior",
      "Novo Status",
      "Usuário"
    ]);

    const linha = [
      formatarDataHora(new Date()),
      payload.title || "",
      payload.requisitionId || "",
      payload.oldStatus || "",
      payload.status || "",
      payload.userName || "Sistema"
    ];

    sheet.appendRow(linha);

    const lastRow = sheet.getLastRow();
    formatarLinha(sheet, lastRow);

    return {
      success: true,
      message: `Requisição atualizada: ${payload.title}`
    };

  } catch (error) {
    return {
      success: false,
      error: error.toString()
    };
  }
}


// ========================================
// FUNÇÕES AUXILIARES
// ========================================

/**
 * Obtém ou cria aba na planilha
 */
function obterOuCriarAba(nomeAba, colunas) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(nomeAba);

  if (!sheet) {
    // Criar nova aba
    sheet = ss.insertSheet(nomeAba);

    // Adicionar cabeçalho
    sheet.appendRow(colunas);

    // Formatar cabeçalho
    const headerRange = sheet.getRange(1, 1, 1, colunas.length);
    headerRange.setFontWeight("bold");
    headerRange.setBackground("#E0E0E0");
    headerRange.setHorizontalAlignment("center");

    // Congelar cabeçalho
    sheet.setFrozenRows(1);

    Logger.log(`✅ Aba criada: ${nomeAba}`);
  }

  return sheet;
}


/**
 * Formata linha adicionada
 */
function formatarLinha(sheet, row) {
  const range = sheet.getRange(row, 1, 1, sheet.getLastColumn());

  // Zebrar linhas (cinza claro para linhas pares)
  if (row % 2 === 0) {
    range.setBackground("#F9F9F9");
  }

  // Alinhar primeira coluna (data) à esquerda
  sheet.getRange(row, 1).setHorizontalAlignment("left");
}


/**
 * Registra evento no log
 */
function registrarLog(eventoTipo, status, payload, erro) {
  try {
    const sheet = obterOuCriarAba(CONFIG.SHEETS.LOG, [
      "Data/Hora",
      "Tipo de Evento",
      "Status",
      "Payload (resumo)",
      "Erro"
    ]);

    const payloadResumo = JSON.stringify(payload).substring(0, 500);

    const linha = [
      formatarDataHora(new Date()),
      eventoTipo,
      status,
      payloadResumo,
      erro || ""
    ];

    sheet.appendRow(linha);

    // Limitar log a 1000 linhas (evitar planilha muito grande)
    if (sheet.getLastRow() > 1001) {
      sheet.deleteRow(2); // Deletar linha mais antiga (linha 2, pois 1 é cabeçalho)
    }

  } catch (error) {
    Logger.log(`❌ Erro ao registrar log: ${error}`);
  }
}


/**
 * Valida autenticação do webhook
 */
function validarAutenticacao(authHeader) {
  if (!authHeader) {
    Logger.log("⚠️ Requisição sem Authorization header");
    return false;
  }

  const expectedToken = `Bearer ${CONFIG.SECRET_TOKEN}`;

  if (authHeader !== expectedToken) {
    Logger.log(`⚠️ Token inválido: ${authHeader}`);
    return false;
  }

  return true;
}


/**
 * Identifica tipo de evento pela URL
 */
function identificarTipoEvento(path) {
  if (!path) return "unknown";

  if (path.includes("job-talent-added")) return "job_talent_added";
  if (path.includes("job-talent-stage-added")) return "job_talent_stage_added";
  if (path.includes("job-added")) return "job_added";
  if (path.includes("form-response-added")) return "form_response_added";
  if (path.includes("requisition-status-updated")) return "requisition_status_updated";

  return "unknown";
}


/**
 * Formata data/hora no padrão brasileiro
 */
function formatarDataHora(date) {
  return Utilities.formatDate(date, CONFIG.TIMEZONE, "dd/MM/yyyy HH:mm:ss");
}


/**
 * Retorna resposta JSON
 */
function respostaJSON(data, statusCode = 200) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}


// ========================================
// FUNÇÕES AUXILIARES DE SETUP
// ========================================

/**
 * Gera token secreto automaticamente
 * Execute: Executar > gerarToken
 * Copie o resultado do log e cole em CONFIG.SECRET_TOKEN
 */
function gerarToken() {
  const token = Utilities.getUuid();
  Logger.log("=".repeat(60));
  Logger.log("SEU TOKEN SECRETO:");
  Logger.log(token);
  Logger.log("=".repeat(60));
  Logger.log("Copie o token acima e cole em CONFIG.SECRET_TOKEN");

  return token;
}


// ========================================
// FUNÇÕES DE TESTE
// ========================================

/**
 * Testa processamento de candidatura
 * Execute: Executar > testarCandidatura
 */
function testarCandidatura() {
  const payloadTeste = {
    tenantId: "frameworkdigital",
    jobId: "123-456-789",
    jobName: "Desenvolvedor Full Stack Senior",
    talentId: "talent-abc-123",
    stageName: "Triagem",
    source: "career-page",
    linkedinUsername: "joaosilva",
    location: "São Paulo, SP",
    targetSalary: 8000,
    workModel: "hybrid",
    userName: "Recrutador Teste"
  };

  const resultado = processarCandidatura(payloadTeste);
  Logger.log(`Resultado: ${JSON.stringify(resultado)}`);
}


/**
 * Testa processamento de mudança de etapa
 */
function testarMudancaEtapa() {
  const payloadTeste = {
    tenantId: "frameworkdigital",
    jobId: "123-456-789",
    jobName: "Desenvolvedor Full Stack Senior",
    talentId: "talent-abc-123",
    previousStageName: "Triagem",
    stageName: "Entrevista Técnica",
    stageType: "default",
    phaseType: "screening",
    userName: "Recrutador Teste"
  };

  const resultado = processarMudancaEtapa(payloadTeste);
  Logger.log(`Resultado: ${JSON.stringify(resultado)}`);
}
