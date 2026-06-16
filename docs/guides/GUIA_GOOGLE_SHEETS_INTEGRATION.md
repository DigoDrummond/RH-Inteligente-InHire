# Guia de Integração com Google Sheets

## Formato Correto das Credenciais

O arquivo `credentials.json` deve ser uma **Service Account** do Google Cloud com este formato:

```json
{
  "type": "service_account",
  "project_id": "seu-projeto-123456",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "nome-service-account@seu-projeto.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

**Campos obrigatórios:**
- ✅ `type` - Deve ser "service_account"
- ✅ `client_email` - E-mail da Service Account
- ✅ `private_key` - Chave privada
- ✅ `token_uri` - URL do token

---

## Como Obter as Credenciais Corretas

### Passo 1: Acesse o Google Cloud Console

1. Vá para https://console.cloud.google.com/
2. Faça login com sua conta Google

### Passo 2: Crie ou Selecione um Projeto

1. No topo da página, clique no seletor de projetos
2. Clique em "NOVO PROJETO" ou selecione um existente
3. Dê um nome (ex: "InHire-Integration")
4. Clique em "Criar"

### Passo 3: Ative a Google Sheets API

1. No menu à esquerda, vá em "APIs e serviços" > "Biblioteca"
2. Pesquise por "Google Sheets API"
3. Clique em "Google Sheets API"
4. Clique em "ATIVAR"

### Passo 4: Crie uma Service Account

1. No menu à esquerda, vá em "APIs e serviços" > "Credenciais"
2. Clique em "+ CRIAR CREDENCIAIS"
3. Selecione "Conta de serviço"
4. Preencha:
   - **Nome da conta de serviço:** inhire-sheets-integration
   - **ID da conta de serviço:** (será preenchido automaticamente)
   - **Descrição:** Service Account para integração InHire com Google Sheets
5. Clique em "CRIAR E CONTINUAR"
6. Em "Conceder acesso ao projeto" (opcional), clique em "CONTINUAR"
7. Em "Conceder acesso aos usuários" (opcional), clique em "CONCLUIR"

### Passo 5: Crie e Baixe a Chave

1. Na lista de contas de serviço, clique na que você acabou de criar
2. Vá para a aba "CHAVES"
3. Clique em "ADICIONAR CHAVE" > "Criar nova chave"
4. Selecione "JSON"
5. Clique em "CRIAR"
6. O arquivo JSON será baixado automaticamente
7. **RENOMEIE** o arquivo para `credentials.json`
8. **MOVA** o arquivo para a raiz do projeto InHire

### Passo 6: Compartilhe a Planilha com a Service Account

**IMPORTANTE:** Este passo é ESSENCIAL!

1. Abra o arquivo `credentials.json` que você baixou
2. Copie o valor do campo `client_email` (será algo como: `inhire-sheets-integration@seu-projeto.iam.gserviceaccount.com`)
3. Abra sua planilha do Google Sheets
4. Clique em "Compartilhar" (canto superior direito)
5. Cole o e-mail da Service Account
6. Defina a permissão como "Editor"
7. DESMARQUE "Notificar pessoas"
8. Clique em "Compartilhar"

---

## Opção Alternativa: Exportação Manual via CSV

Se você tiver dificuldade com as credenciais, use a exportação via CSV:

### Método 1: Exportar View de Posições

```bash
python export_to_csv.py
```

**Arquivo gerado:** `vw_analise_posicoes_export.csv`
**Planilha destino:** Teste_API

### Método 2: Exportar Dados do Funil

```bash
python export_funil_to_csv.py
```

**Arquivo gerado:** `funil_performance_export.csv`
**Planilha destino:** Funil_API

### Como Importar o CSV

1. Abra a planilha no Google Sheets
2. Vá para a aba desejada (Teste_API ou Funil_API)
3. Clique em **Arquivo** > **Importar** > **Upload**
4. Selecione o arquivo CSV
5. Em "Local de importação", escolha **"Substituir dados na aba selecionada"**
6. Em "Tipo de separador", escolha **"Vírgula"**
7. Clique em **"Importar dados"**

---

## Verificar se as Credenciais Estão Corretas

Execute este comando para verificar:

```bash
python -c "import json; c=json.load(open('credentials.json')); print('✓ OK' if 'client_email' in c and 'token_uri' in c else '✗ ERRO: Faltam campos')"
```

**Resultado esperado:**
- ✅ `✓ OK` - Credenciais estão corretas
- ❌ `✗ ERRO: Faltam campos` - Arquivo está incorreto

---

## Scripts Disponíveis

### 1. Exportar View de Posições (Teste_API)

```bash
# Via API (requer credenciais)
python export_to_sheets_direct.py

# Via CSV (sempre funciona)
python export_to_csv.py
```

### 2. Exportar Dados do Funil (Funil_API)

```bash
# Via CSV
python export_funil_to_csv.py
```

---

## Planilhas de Destino

### Planilha 1: Análise de Posições
- **URL:** https://docs.google.com/spreadsheets/d/1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw/
- **Aba:** Teste_API
- **Dados:** View `vw_analise_posicoes` (831 registros)
- **Script:** `export_to_csv.py`

### Planilha 2: Dados do Funil
- **URL:** https://docs.google.com/spreadsheets/d/1pWscZVbQ_jA7D5aJWycDuRi--8M_AIPSDN9j451-Pd0/
- **Aba:** Funil_API
- **Dados:** View `vw_funil_performance` (82,584 registros)
- **Script:** `export_funil_to_csv.py`

---

## Problemas Comuns

### Erro: "Service account info was not in the expected format"

**Causa:** Arquivo `credentials.json` não é uma Service Account válida

**Solução:**
1. Verifique se baixou o arquivo correto do Google Cloud Console
2. O arquivo deve ter os campos `client_email` e `token_uri`
3. Siga o guia acima para criar uma nova Service Account

### Erro: "Permission denied"

**Causa:** Service Account não tem permissão na planilha

**Solução:**
1. Abra o `credentials.json` e copie o `client_email`
2. Compartilhe a planilha com este e-mail
3. Defina permissão como "Editor"

### Erro: "The caller does not have permission"

**Causa:** Google Sheets API não está ativada

**Solução:**
1. Vá para https://console.cloud.google.com/
2. Selecione seu projeto
3. Vá em "APIs e serviços" > "Biblioteca"
4. Pesquise "Google Sheets API"
5. Clique em "ATIVAR"

---

## Automatização

Depois de configurar as credenciais corretamente, você pode automatizar:

```bash
# Atualizar ambas as planilhas automaticamente
python export_to_sheets_direct.py
# (quando suportar múltiplas planilhas)
```

Ou criar um agendamento (Windows Task Scheduler / Cron):

```batch
@echo off
cd "C:\Users\...\Framework_Data\Inhire"
python export_to_csv.py
python export_funil_to_csv.py
echo Exportação concluída em %date% %time%
```

---

## Resumo Rápido

**Para usar AGORA (sem configuração):**
```bash
python export_funil_to_csv.py
# Depois importar manualmente o CSV no Google Sheets
```

**Para automação completa (requer configuração):**
1. Criar Service Account no Google Cloud
2. Baixar credentials.json
3. Ativar Google Sheets API
4. Compartilhar planilha com Service Account
5. Executar: `python export_to_sheets_direct.py`

---

_Para dúvidas, consulte a documentação oficial do Google Cloud:_
https://cloud.google.com/iam/docs/service-accounts
