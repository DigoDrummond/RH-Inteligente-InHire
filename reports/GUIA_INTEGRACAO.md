# Guia de Integração dos Relatórios

Este guia mostra como usar os relatórios gerados em diferentes ferramentas de BI e análise.

## 📊 Power BI

### Método 1: Importar Excel Diretamente

1. Gere os relatórios:
   ```bash
   python gerar_relatorios.py
   ```

2. No Power BI Desktop:
   - **Página Inicial** → **Obter Dados** → **Excel**
   - Navegue até `reports/exports/`
   - Selecione o arquivo `.xlsx` desejado
   - Marque a planilha "Dados"
   - Clique em **Carregar**

### Método 2: Conexão Direta com PostgreSQL (Recomendado)

1. No Power BI Desktop:
   - **Página Inicial** → **Obter Dados** → **Banco de Dados** → **PostgreSQL**

2. Configure a conexão:
   ```
   Servidor: localhost:5432
   Banco de dados: inhire
   ```

3. Na janela de navegador:
   - Clique em **Avançado**
   - Cole a query SQL do relatório desejado
   - Clique em **OK**

4. Credenciais:
   - Usuário: `postgres`
   - Senha: [sua senha]

### Método 3: Query SQL Personalizada

```sql
-- Cole no Power BI → Obter Dados → PostgreSQL → Opções Avançadas
SELECT
    r.name AS requisicao,
    r.status,
    r.requested_at,
    v.name AS vaga,
    r.salary_max AS salario_maximo
FROM requisicoes r
LEFT JOIN vagas v ON r.vaga_id = v.id
WHERE r.requested_at >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY r.requested_at DESC
```

### Atualização Automática

Para atualizar os dados automaticamente no Power BI:

1. **Página Inicial** → **Atualizar**
2. Configure agendamento:
   - **Arquivo** → **Opções e Configurações** → **Opções**
   - **Carregamento de Dados** → **Atualização Agendada**

## 📈 Google Sheets

### Método 1: Importar CSV

1. Gere os relatórios:
   ```bash
   python gerar_relatorios.py
   ```

2. No Google Sheets:
   - **Arquivo** → **Importar**
   - **Upload** → Selecione o arquivo `.csv`
   - Escolha "Criar nova planilha"
   - Configure:
     - Separador: Detectar automaticamente
     - Converter texto em números: Sim

### Método 2: Google Apps Script (Conexão PostgreSQL)

**Importante:** Requer Cloud SQL Proxy ou IP público do banco.

```javascript
// Em Ferramentas → Editor de Scripts
function importarRequisicoes() {
  var conn = Jdbc.getConnection(
    'jdbc:postgresql://localhost:5432/inhire',
    'postgres',
    'senha'
  );

  var stmt = conn.createStatement();
  var results = stmt.executeQuery(`
    SELECT
      r.name,
      r.status,
      r.requested_at,
      v.name AS vaga
    FROM requisicoes r
    LEFT JOIN vagas v ON r.vaga_id = v.id
    ORDER BY r.requested_at DESC
    LIMIT 1000
  `);

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var row = 2; // Linha 1 = cabeçalho

  while (results.next()) {
    sheet.getRange(row, 1).setValue(results.getString(1));
    sheet.getRange(row, 2).setValue(results.getString(2));
    sheet.getRange(row, 3).setValue(results.getTimestamp(3));
    sheet.getRange(row, 4).setValue(results.getString(4));
    row++;
  }

  results.close();
  stmt.close();
  conn.close();
}
```

### Método 3: API + Google Sheets (Avançado)

Criar uma API Flask/FastAPI que serve os dados e consumir no Google Sheets via `IMPORTDATA()`.

## 📊 Excel Desktop

### Importar CSV

1. **Dados** → **Obter Dados** → **De Arquivo** → **De Texto/CSV**
2. Selecione o arquivo gerado
3. Configure:
   - Delimitador: Vírgula
   - Detectar tipo de dados: Automático
4. **Carregar**

### Conexão com PostgreSQL

Requer driver ODBC:

1. Instalar [PostgreSQL ODBC Driver](https://www.postgresql.org/ftp/odbc/versions/)

2. No Excel:
   - **Dados** → **Obter Dados** → **De Outras Fontes** → **Do ODBC**

3. Configurar DSN:
   ```
   Driver: PostgreSQL Unicode
   Server: localhost
   Port: 5432
   Database: inhire
   ```

4. Cole a query SQL do relatório

## 🐍 Python / Jupyter Notebook

```python
import pandas as pd
import psycopg2

# Conexão
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='inhire',
    user='postgres',
    password='senha'
)

# Query
query = """
    SELECT
        r.name,
        r.status,
        r.requested_at,
        v.name AS vaga,
        r.salary_max
    FROM requisicoes r
    LEFT JOIN vagas v ON r.vaga_id = v.id
    ORDER BY r.requested_at DESC
"""

# Carregar no DataFrame
df = pd.read_sql_query(query, conn)

# Análises
print(df.describe())
print(df.groupby('status')['salary_max'].mean())

# Visualizações
import matplotlib.pyplot as plt
df.groupby('status').size().plot(kind='bar')
plt.show()

conn.close()
```

## 📊 Tableau

### Conexão com PostgreSQL

1. **Conectar** → **Para um Servidor** → **PostgreSQL**

2. Configurar:
   ```
   Servidor: localhost
   Porta: 5432
   Banco de dados: inhire
   Usuário: postgres
   ```

3. Escolher:
   - **Tabela**: Selecione as tabelas necessárias
   - **Consulta Personalizada**: Cole a query SQL

### Query Personalizada

```sql
-- No Tableau, clique em "Nova Consulta Personalizada"
SELECT
    DATE_TRUNC('month', r.requested_at) AS mes,
    r.status,
    COUNT(*) AS total_requisicoes,
    AVG(r.salary_max) AS salario_medio
FROM requisicoes r
GROUP BY DATE_TRUNC('month', r.requested_at), r.status
ORDER BY mes DESC
```

## 🔄 Looker Studio (Google Data Studio)

### Conexão PostgreSQL

1. **Criar** → **Fonte de Dados**

2. Selecionar:
   - **PostgreSQL** (via Cloud SQL ou Connector)
   - Configure host, porta, banco, credenciais

3. Escolher:
   - **Tabela**: Navegue pelas tabelas
   - **Consulta Personalizada**: Cole a query SQL

### Importante

Para conectar ao PostgreSQL local no Looker Studio:
- Use Cloud SQL Proxy
- Ou exponha o banco via IP público (não recomendado para produção)

## 🔐 Segurança

### Boas Práticas

1. **Nunca exponha credenciais** em scripts compartilhados

2. **Use variáveis de ambiente**:
   ```python
   import os
   password = os.getenv('DB_PASSWORD')
   ```

3. **Crie usuário read-only** para BI:
   ```sql
   CREATE USER bi_readonly WITH PASSWORD 'senha_forte';
   GRANT CONNECT ON DATABASE inhire TO bi_readonly;
   GRANT USAGE ON SCHEMA public TO bi_readonly;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO bi_readonly;
   ```

4. **Use IP whitelist** no PostgreSQL:
   ```conf
   # pg_hba.conf
   host    inhire    bi_readonly    192.168.1.0/24    md5
   ```

## 🚀 Automação

### Agendar Geração de Relatórios

#### Windows Task Scheduler

1. Abrir **Agendador de Tarefas**

2. **Criar Tarefa Básica**:
   - Nome: "Gerar Relatórios Inhire"
   - Gatilho: Diário, 08:00
   - Ação: Iniciar programa
     ```
     Programa: python
     Argumentos: C:\path\to\reports\gerar_relatorios.py
     Iniciar em: C:\path\to\reports
     ```

#### Linux/Mac Cron

```bash
# Editar crontab
crontab -e

# Adicionar linha (executar todo dia às 08:00)
0 8 * * * cd /path/to/reports && python3 gerar_relatorios.py >> cron.log 2>&1
```

### Script de Envio por Email

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

def enviar_relatorio_email(arquivo_excel):
    """Envia relatório por email"""

    # Configurar servidor SMTP
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "seu_email@gmail.com"
    sender_password = "senha_app"
    receiver_email = "destinatario@empresa.com"

    # Criar mensagem
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"Relatório Inhire - {datetime.now().strftime('%d/%m/%Y')}"

    # Anexar arquivo
    with open(arquivo_excel, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename={Path(arquivo_excel).name}'
        )
        msg.attach(part)

    # Enviar
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)

    print(f"✅ Relatório enviado para {receiver_email}")
```

## 📱 Integração com APIs

### API REST para Servir Dados

```python
from flask import Flask, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

@app.route('/api/requisicoes')
def get_requisicoes():
    conn = psycopg2.connect(...)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM requisicoes LIMIT 100")
        data = cur.fetchall()
    conn.close()

    return jsonify(data)

if __name__ == '__main__':
    app.run(port=5000)
```

Consumir no Google Sheets:
```
=IMPORTDATA("http://localhost:5000/api/requisicoes")
```

## 📚 Recursos Adicionais

- [Documentação Power BI](https://docs.microsoft.com/pt-br/power-bi/)
- [Google Sheets JDBC](https://developers.google.com/apps-script/guides/jdbc)
- [Tableau PostgreSQL](https://help.tableau.com/current/pro/desktop/en-us/examples_postgresql.htm)
- [PostgreSQL ODBC](https://odbc.postgresql.org/)

---

**Última atualização:** 2026-07-21
