/**
 * ========================================
 * PASSO 2: CRIAR ESTRUTURA DA PLANILHA
 * ========================================
 *
 * Execute este código UMA VEZ para criar todas as abas e cabeçalhos
 *
 * COMO USAR:
 * 1. Substitua SEU_TOKEN_AQUI pelo token gerado no Passo 1
 * 2. Execute: criarEstruturaPlanilha()
 * 3. Verifique se as 6 abas foram criadas
 * 4. Depois delete este código (não precisa mais)
 */

// ========================================
// CONFIGURAÇÃO
// ========================================

const CONFIG_SETUP = {
  // Cole aqui o token gerado no Passo 1
  SECRET_TOKEN: "SEU_TOKEN_AQUI",

  TIMEZONE: "America/Sao_Paulo"
};


// ========================================
// ESTRUTURA DAS ABAS
// ========================================

const ESTRUTURA_ABAS = {
  "Candidaturas": [
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
  ],

  "Mudanças de Etapa": [
    "Data/Hora",
    "Vaga",
    "Candidato ID",
    "Etapa Anterior",
    "Nova Etapa",
    "Tipo de Etapa",
    "Fase",
    "Usuário"
  ],

  "Novas Vagas": [
    "Data/Hora",
    "Nome da Vaga",
    "Vaga ID",
    "Descrição",
    "Criado por"
  ],

  "Formulários": [
    "Data/Hora",
    "Vaga ID",
    "Candidato ID",
    "Tipo",
    "Título",
    "Aprovado?",
    "Acertos",
    "Total",
    "% Acerto"
  ],

  "Requisições": [
    "Data/Hora",
    "Título",
    "Requisição ID",
    "Status Anterior",
    "Novo Status",
    "Usuário"
  ],

  "Log de Eventos": [
    "Data/Hora",
    "Tipo de Evento",
    "Status",
    "Payload (resumo)",
    "Erro"
  ]
};


// ========================================
// FUNÇÃO PRINCIPAL
// ========================================

/**
 * Cria todas as abas e estrutura da planilha
 */
function criarEstruturaPlanilha() {
  console.log("🚀 Criando estrutura da planilha...\n");

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let abasCriadas = 0;
  let abasExistentes = 0;

  // Criar cada aba
  for (const [nomeAba, colunas] of Object.entries(ESTRUTURA_ABAS)) {
    let sheet = ss.getSheetByName(nomeAba);

    if (!sheet) {
      // Criar nova aba
      sheet = ss.insertSheet(nomeAba);

      // Adicionar cabeçalho
      sheet.appendRow(colunas);

      // Formatar cabeçalho
      const headerRange = sheet.getRange(1, 1, 1, colunas.length);
      headerRange.setFontWeight("bold");
      headerRange.setBackground("#4A90E2");
      headerRange.setFontColor("#FFFFFF");
      headerRange.setHorizontalAlignment("center");
      headerRange.setVerticalAlignment("middle");

      // Ajustar largura das colunas
      for (let i = 1; i <= colunas.length; i++) {
        sheet.setColumnWidth(i, 150);
      }

      // Congelar primeira linha (cabeçalho)
      sheet.setFrozenRows(1);

      // Adicionar filtros
      sheet.getRange(1, 1, 1, colunas.length).createFilter();

      console.log(`✅ Aba criada: ${nomeAba} (${colunas.length} colunas)`);
      abasCriadas++;

    } else {
      console.log(`ℹ️  Aba já existe: ${nomeAba}`);
      abasExistentes++;
    }
  }

  // Criar aba de configuração
  criarAbaConfiguracao(ss);

  // Resumo final
  console.log("\n" + "=".repeat(70));
  console.log("✅ ESTRUTURA CRIADA COM SUCESSO!");
  console.log("=".repeat(70));
  console.log(`📊 Abas criadas: ${abasCriadas}`);
  console.log(`📊 Abas já existentes: ${abasExistentes}`);
  console.log(`📊 Total de abas: ${abasCriadas + abasExistentes}`);
  console.log("\n📋 PRÓXIMO PASSO:");
  console.log("1. Verifique se todas as abas foram criadas");
  console.log("2. Veja a aba '⚙️ Configuração' com informações importantes");
  console.log("3. Prossiga para o Passo 3: adicionar código do webhook receiver");
  console.log("=".repeat(70));
}


/**
 * Cria aba de configuração com instruções
 */
function criarAbaConfiguracao(ss) {
  const nomeAba = "⚙️ Configuração";
  let sheet = ss.getSheetByName(nomeAba);

  if (sheet) {
    ss.deleteSheet(sheet);
  }

  sheet = ss.insertSheet(nomeAba, 0); // Primeira posição

  // Dados da configuração
  const dados = [
    ["CONFIGURAÇÃO DO WEBHOOK RECEIVER"],
    [""],
    ["Item", "Valor"],
    ["Token Secreto", CONFIG_SETUP.SECRET_TOKEN],
    ["Fuso Horário", CONFIG_SETUP.TIMEZONE],
    ["Data de Setup", new Date()],
    [""],
    ["PRÓXIMOS PASSOS:"],
    [""],
    ["1", "Adicione o código do arquivo 3_webhook_receiver.js no Apps Script"],
    ["2", "Configure o mesmo token no código (linha 21)"],
    ["3", "Implante como Web App (Implantar > Nova implantação)"],
    ["4", "Copie a URL gerada"],
    ["5", "Configure webhooks na Inhire com esta URL"],
    ["6", "Use o token acima no header Authorization dos webhooks"],
    [""],
    ["FORMATO DO HEADER:"],
    ["Authorization", `Bearer ${CONFIG_SETUP.SECRET_TOKEN}`],
    [""],
    ["ABAS CRIADAS:"],
    ["Candidaturas", "Registra novas inscrições de candidatos"],
    ["Mudanças de Etapa", "Registra quando candidatos mudam de etapa"],
    ["Novas Vagas", "Registra quando novas vagas são criadas"],
    ["Formulários", "Registra respostas de formulários"],
    ["Requisições", "Registra mudanças de status de requisições"],
    ["Log de Eventos", "Histórico completo de todos os webhooks recebidos"]
  ];

  // Adicionar dados
  sheet.getRange(1, 1, dados.length, 2).setValues(dados);

  // Formatar título
  sheet.getRange(1, 1, 1, 2).merge()
    .setBackground("#2C3E50")
    .setFontColor("#FFFFFF")
    .setFontSize(14)
    .setFontWeight("bold")
    .setHorizontalAlignment("center");

  // Formatar cabeçalhos
  sheet.getRange(3, 1, 1, 2)
    .setBackground("#4A90E2")
    .setFontColor("#FFFFFF")
    .setFontWeight("bold");

  sheet.getRange(8, 1, 1, 2).merge()
    .setBackground("#E74C3C")
    .setFontColor("#FFFFFF")
    .setFontWeight("bold");

  sheet.getRange(17, 1, 1, 2).merge()
    .setBackground("#27AE60")
    .setFontColor("#FFFFFF")
    .setFontWeight("bold");

  sheet.getRange(20, 1, 1, 2).merge()
    .setBackground("#9B59B6")
    .setFontColor("#FFFFFF")
    .setFontWeight("bold");

  // Ajustar larguras
  sheet.setColumnWidth(1, 200);
  sheet.setColumnWidth(2, 500);

  console.log(`✅ Aba de configuração criada: ${nomeAba}`);
}


/**
 * Teste: adiciona linha de exemplo em cada aba
 */
function testarAbas() {
  console.log("🧪 Testando abas com dados de exemplo...\n");

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const agora = formatarDataHora(new Date());

  // Teste Candidaturas
  const abaCandidaturas = ss.getSheetByName("Candidaturas");
  if (abaCandidaturas) {
    abaCandidaturas.appendRow([
      agora,
      "Desenvolvedor Full Stack Senior",
      "job-123-abc",
      "talent-456-def",
      "Triagem",
      "career-page",
      "joaosilva",
      "São Paulo, SP",
      "R$ 8.000",
      "Híbrido",
      "Sistema (Teste)"
    ]);
    console.log("✅ Linha de teste adicionada: Candidaturas");
  }

  // Teste Mudanças de Etapa
  const abaMudancas = ss.getSheetByName("Mudanças de Etapa");
  if (abaMudancas) {
    abaMudancas.appendRow([
      agora,
      "Desenvolvedor Full Stack Senior",
      "talent-456-def",
      "Triagem",
      "Entrevista Técnica",
      "default",
      "screening",
      "Recrutador (Teste)"
    ]);
    console.log("✅ Linha de teste adicionada: Mudanças de Etapa");
  }

  console.log("\n✅ Teste concluído! Verifique as abas na planilha.");
}


/**
 * Formata data/hora
 */
function formatarDataHora(date) {
  return Utilities.formatDate(date, CONFIG_SETUP.TIMEZONE, "dd/MM/yyyy HH:mm:ss");
}


/**
 * Remove todas as abas criadas (útil para resetar)
 */
function removerTodasAbas() {
  const confirmacao = Browser.msgBox(
    "Confirmar Remoção",
    "Tem certeza que deseja remover TODAS as abas criadas?",
    Browser.Buttons.YES_NO
  );

  if (confirmacao === "yes") {
    const ss = SpreadsheetApp.getActiveSpreadsheet();

    for (const nomeAba of Object.keys(ESTRUTURA_ABAS)) {
      const sheet = ss.getSheetByName(nomeAba);
      if (sheet) {
        ss.deleteSheet(sheet);
        console.log(`🗑️  Aba removida: ${nomeAba}`);
      }
    }

    // Remover aba de configuração
    const configSheet = ss.getSheetByName("⚙️ Configuração");
    if (configSheet) {
      ss.deleteSheet(configSheet);
      console.log("🗑️  Aba removida: ⚙️ Configuração");
    }

    console.log("\n✅ Todas as abas foram removidas!");
  } else {
    console.log("❌ Operação cancelada.");
  }
}
