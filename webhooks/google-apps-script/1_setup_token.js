/**
 * ========================================
 * PASSO 1: GERAR TOKEN DE SEGURANÇA
 * ========================================
 *
 * Execute este código UMA VEZ para gerar seu token secreto
 *
 * COMO USAR:
 * 1. Abra sua planilha Google Sheets
 * 2. Menu: Extensões > Apps Script
 * 3. Cole SOMENTE este código
 * 4. Clique em Executar > gerarToken
 * 5. Copie o token que aparecer no log
 * 6. GUARDE este token (você vai usar nos próximos passos)
 */

function gerarToken() {
  // Gera token único e seguro
  const token = Utilities.getUuid();

  // Exibe no log de forma destacada
  console.log("=".repeat(70));
  console.log("🔑 SEU TOKEN SECRETO:");
  console.log("");
  console.log(token);
  console.log("");
  console.log("=".repeat(70));
  console.log("");
  console.log("📋 PRÓXIMOS PASSOS:");
  console.log("1. COPIE o token acima");
  console.log("2. GUARDE em local seguro");
  console.log("3. Use este token nos arquivos:");
  console.log("   - 2_setup_planilha.js (linha 19)");
  console.log("   - 3_webhook_receiver.js (linha 21)");
  console.log("   - Webhooks da Inhire (header Authorization)");
  console.log("");
  console.log("⚠️  IMPORTANTE: Não compartilhe este token publicamente!");
  console.log("=".repeat(70));

  return token;
}

/**
 * Exemplo de token gerado:
 * a1b2c3d4-e5f6-7890-abcd-ef1234567890
 *
 * Use este formato ao configurar:
 * Authorization: Bearer a1b2c3d4-e5f6-7890-abcd-ef1234567890
 */
