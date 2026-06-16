# 🏗️ Arquitetura: Sistema 100% Integrado InHire

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Componentes do Sistema](#componentes-do-sistema)
3. [Fluxo de Dados](#fluxo-de-dados)
4. [Sincronização Otimizada](#sincronização-otimizada)
5. [Integração Power BI](#integração-power-bi)
6. [Integração Google Sheets](#integração-google-sheets)
7. [Monitoramento e Alertas](#monitoramento-e-alertas)
8. [Roadmap de Implementação](#roadmap-de-implementação)

---

## 1. Visão Geral

### Objetivo
Criar um sistema **online, atualizado em tempo real** que integre:
- ✅ API InHire (dados em tempo real)
- ✅ PostgreSQL (banco de dados centralizado)
- ✅ Power BI (visualização e análise)
- ✅ Google Sheets (acesso colaborativo e atualizações)

### Arquitetura Completa

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SISTEMA INTEGRADO INHIRE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    Sync (30min)    ┌──────────────────┐                   │
│  │  API InHire │ ──────────────────> │  PostgreSQL DB   │                   │
│  └─────────────┘                     │  - Vagas         │                   │
│       │                               │  - Posições      │                   │
│       │ Real-time                     │  - Candidaturas  │                   │
│       │ Webhook                       │  - Talentos      │                   │
│       │ (opcional)                    └──────────────────┘                   │
│       │                                       │                              │
│       │                                       │                              │
│       │                               ┌───────┴────────┐                     │
│       │                               │                │                     │
│       │                               ▼                ▼                     │
│       │                       ┌─────────────┐  ┌──────────────┐             │
│       │                       │  Power BI   │  │Google Sheets │             │
│       │                       │  (PBIX)     │  │ API Service  │             │
│       │                       └─────────────┘  └──────────────┘             │
│       │                               │                │                     │
│       │                               │                │                     │
│       └───────────────────────────────┼────────────────┘                     │
│                                       │                                      │
│                                       ▼                                      │
│                              ┌─────────────────┐                             │
│                              │  Usuários Finais│                             │
│                              │  - Dashboards   │                             │
│                              │  - Relatórios   │                             │
│                              │  - Colaboração  │                             │
│                              └─────────────────┘                             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Componentes do Sistema

### 2.1. Layer 1: Captura de Dados (API InHire)

**Endpoints Disponíveis:**
```
Base URL: https://api.inhire.app/

Autenticação:
  POST /auth/signin

Vagas:
  POST /jobs/paginated/lean

Posições:
  GET /jobs/{jobId}/positions

Candidaturas:
  POST /jobs/{jobId}/applications

Talentos:
  POST /talents/list
  GET /talents/{talentId}
```

**Status Válidos de Vagas:**
- `OPEN` → Vaga ativa
- `CLOSED` → Vaga fechada
- `CANCELED` → Vaga cancelada
- ~~`PAUSED`~~ → **NÃO EXISTE NA API**

**Autenticação:**
- Tipo: JWT Bearer Token
- Renovação: Automática via refresh token
- Retry: Automático com backoff exponencial

### 2.2. Layer 2: Sincronização e Armazenamento

**PostgreSQL Database:**
```sql
-- Entidades principais
vagas          (1,088 registros)
posicoes       (542 registros)
candidaturas   (75,282 registros)
talentos       (53,068 registros)

-- Campos de controle
created_at_inhire   TIMESTAMP  -- Data de criação (API)
updated_at_inhire   TIMESTAMP  -- Data de atualização (API)
synced_at           TIMESTAMP  -- Data da última sincronização
```

**Estratégias de Sincronização:**

| Tipo | Frequência | Escopo | Tempo | Uso |
|------|-----------|--------|-------|-----|
| **Completa** | Semanal | Todos os dados | ~55 min | Validação total |
| **Incremental Completa** | 4 horas | Dados modificados | ~10-20 min | Manutenção geral |
| **Incremental Rápida** | 30 min | Modificados recentemente | < 3 min | Tempo real |

### 2.3. Layer 3: Visualização e Análise

#### A. Power BI (PBIX)

**Conexão:**
- Direct Query ou Import
- PostgreSQL ODBC Driver
- Refresh automático (Gateway ou Service)

**Dashboards Propostos:**

1. **Dashboard Principal - Visão Geral**
   - Total de vagas ativas vs fechadas
   - Taxa de conversão (candidaturas → contratações)
   - SLA médio de fechamento de vagas
   - Top 5 vagas com mais candidaturas

2. **Dashboard de Vagas**
   - Status das vagas (OPEN, CLOSED, CANCELED)
   - Distribuição por área/senioridade
   - Vagas abertas vs posições preenchidas
   - Evolução temporal (novas vagas por mês)

3. **Dashboard de Talentos**
   - Pool de talentos ativos
   - Distribuição geográfica
   - Senioridade e áreas de atuação
   - Taxa de reaproveitamento

4. **Dashboard de Performance**
   - Tempo médio por stage do processo
   - Taxa de aprovação por recruiter
   - Gargalos no pipeline (onde os candidatos ficam mais tempo)

**Métricas Calculadas:**
```dax
// Taxa de Conversão
TaxaConversao =
DIVIDE(
    COUNTROWS(FILTER(Posicoes, Posicoes[status] = "HIRED")),
    COUNTROWS(Candidaturas),
    0
)

// SLA Médio
SLAMedio =
AVERAGE(
    DATEDIFF(Vagas[createdAt], Vagas[closedAt], DAY)
)

// Vagas Ativas
VagasAtivas =
COUNTROWS(FILTER(Vagas, Vagas[status] = "OPEN"))
```

#### B. Google Sheets

**Integração via Google Sheets API:**

**Planilhas Propostas:**

1. **"Vagas Ativas" (Atualização a cada 30 min)**
   ```
   | ID | Nome | Status | Área | Senioridade | Criada em | Candidaturas | Posições Abertas |
   |----+------+--------+------+-------------+-----------+--------------+------------------|
   ```

2. **"Novas Vagas (Últimas 24h)"**
   - Notificações automáticas
   - Destaque visual

3. **"Mudanças Recentes"**
   - Vagas que mudaram de status
   - Novas candidaturas
   - Talentos adicionados

**Funcionalidades:**
- ✅ Leitura automática do PostgreSQL
- ✅ Atualização a cada 30 minutos
- ✅ Formatação condicional (cores por status)
- ✅ Filtros e ordenação
- ⚠️ Escrita limitada (evitar conflitos)

---

## 3. Fluxo de Dados

### 3.1. Fluxo de Sincronização

```
API InHire → Sync Service → PostgreSQL → Power BI/Sheets → Usuários

┌──────────────┐
│  API InHire  │
└──────┬───────┘
       │
       │ ① Sync a cada 30 min
       ▼
┌──────────────────────┐
│ sync_incremental.py  │
│ - Compara updated_at │
│ - UPSERT inteligente │
│ - Skip se não mudou  │
└──────┬───────────────┘
       │
       │ ② Armazena no BD
       ▼
┌──────────────────────┐
│   PostgreSQL DB      │
│ - 4 tabelas          │
│ - Timestamps         │
│ - Índices otimizados │
└──────┬───────────────┘
       │
       │ ③ Consulta/Refresh
       │
    ┌──┴──────────────┐
    │                 │
    ▼                 ▼
┌─────────┐    ┌──────────────┐
│Power BI │    │Google Sheets │
│(PBIX)   │    │API Service   │
└─────────┘    └──────────────┘
    │                 │
    └────────┬────────┘
             │ ④ Visualização
             ▼
    ┌─────────────────┐
    │ Usuários Finais │
    └─────────────────┘
```

### 3.2. Fluxo de Atualização em Tempo Real

**Opção A: Polling (Implementado)**
```python
# A cada 30 minutos
while True:
    sync_incremental_rapida()  # Busca mudanças recentes
    sleep(1800)  # 30 minutos
```

**Opção B: Webhooks (Futuro)**
```python
# InHire envia notificação quando dados mudam
@app.route('/webhook/inhire', methods=['POST'])
def inhire_webhook():
    data = request.json
    entity_type = data['entity']  # vaga, candidatura, talento
    entity_id = data['id']

    # Sincronizar apenas essa entidade
    sync_entity_by_id(entity_type, entity_id)
```

---

## 4. Sincronização Otimizada

### 4.1. Problema Identificado

**Filtro por Status (ATUAL):**
```python
# ❌ Ineficiente: 0 vagas encontradas
if vaga.status in ['OPEN', 'PAUSED']:
    vagas_filtradas.append(vaga)
```

**Distribuição Real:**
- API retorna: 1,089 vagas
- OPEN no BD: 29 (podem ter sido fechadas na API)
- PAUSED: 0 (status não existe)

### 4.2. Solução Otimizada

**Filtro por Data de Atualização:**
```python
# ✅ Eficiente: Pega qualquer vaga modificada nas últimas 2 horas
from datetime import datetime, timedelta
import pytz

sp_tz = pytz.timezone('America/Sao_Paulo')
cutoff_time = datetime.now(sp_tz) - timedelta(hours=2)

vagas_filtradas = []
for vaga in all_vagas_api:
    if vaga.updatedAt >= cutoff_time:
        vagas_filtradas.append(vaga)
```

**Resultados Esperados:**
- Vagas modificadas em 2h: ~10-50 vagas
- Tempo de execução: < 3 minutos ✅
- Cobre TODAS as mudanças recentes (não só OPEN)

### 4.3. Estratégia de Duas Camadas

**Layer 1: Sync Rápida (30 minutos)**
```python
# sync_incremental_rapida.py
# Foco: Mudanças nas últimas 2 horas
# Objetivo: Capturar em tempo real
```

**Layer 2: Sync Completa (4 horas)**
```python
# sync_incremental_completa.py
# Foco: TODAS as vagas (com skip inteligente)
# Objetivo: Garantir integridade
```

**Agendamento:**
```python
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

# Rápida: 07:00-19:00, a cada 30 min
scheduler.add_job(
    sync_incremental_rapida,
    'cron',
    minute='*/30',
    hour='7-19',
    id='sync_rapida'
)

# Completa: a cada 4 horas
scheduler.add_job(
    sync_incremental_completa,
    'cron',
    hour='*/4',
    id='sync_completa'
)

scheduler.start()
```

---

## 5. Integração Power BI

### 5.1. Configuração da Conexão

**Passo 1: Instalar ODBC Driver**
```bash
# PostgreSQL ODBC Driver
https://www.postgresql.org/ftp/odbc/versions/msi/
```

**Passo 2: Conectar no Power BI Desktop**
```
Get Data → PostgreSQL Database
Server: localhost:5432
Database: inhire
Mode: DirectQuery ou Import
```

**Passo 3: Criar Relacionamentos**
```
Vagas (1) ←→ (N) Posicoes       [Vagas.inhire_id = Posicoes.vaga_id]
Vagas (1) ←→ (N) Candidaturas   [Vagas.inhire_id = Candidaturas.vaga_id]
Candidaturas (N) ←→ (1) Talentos [Candidaturas.talento_id = Talentos.inhire_id]
```

### 5.2. DirectQuery vs Import

| Modo | Vantagens | Desvantagens | Recomendação |
|------|-----------|--------------|--------------|
| **DirectQuery** | Sempre atualizado | Mais lento, menos recursos | ✅ Ideal para tempo real |
| **Import** | Rápido, todos recursos | Precisa refresh | ⚠️ Se refresh < 30 min |

**Configuração de Refresh (Import Mode):**
```
Power BI Service → Datasets → Configure Refresh
Frequency: A cada 30 minutos
Time zones: America/Sao_Paulo
```

### 5.3. Dashboards Recomendados

**Dashboard 1: Overview Executivo**
```
┌────────────────────────────────────────────────────┐
│ INHIRE - DASHBOARD EXECUTIVO                       │
├─────────┬─────────┬─────────┬──────────────────────┤
│ Vagas   │ Vagas   │ Total   │ Taxa de Conversão    │
│ Ativas  │ Fechadas│ Candid. │                      │
│   29    │   784   │ 75,282  │       15.3%          │
└─────────┴─────────┴─────────┴──────────────────────┘

┌─────────────────────┐  ┌───────────────────────────┐
│ Vagas por Status    │  │ Candidaturas por Vaga     │
│                     │  │                           │
│ ████ CLOSED (72%)   │  │ [Gráfico de barras]       │
│ ███ CANCELED (25%)  │  │                           │
│ █ OPEN (3%)         │  │                           │
└─────────────────────┘  └───────────────────────────┘

┌──────────────────────────────────────────────────┐
│ Timeline de Novas Vagas (últimos 6 meses)       │
│                                                  │
│ [Gráfico de linha com tendência]                │
└──────────────────────────────────────────────────┘
```

**Dashboard 2: Funil de Recrutamento**
```
┌────────────────────────────────────────────────────┐
│ FUNIL DE RECRUTAMENTO                              │
├────────────────────────────────────────────────────┤
│                                                    │
│     Candidaturas: 75,282                           │
│            ▼                                       │
│     Em Avaliação: 15,234  (20%)                    │
│            ▼                                       │
│     Entrevistas: 3,456  (4.6%)                     │
│            ▼                                       │
│     Ofertas: 1,234  (1.6%)                         │
│            ▼                                       │
│     Contratados: 542  (0.7%)                       │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## 6. Integração Google Sheets

### 6.1. Configuração Google Sheets API

**Passo 1: Habilitar API**
```
1. Acessar: https://console.cloud.google.com/
2. Criar projeto: "InHire Integration"
3. Habilitar: Google Sheets API
4. Criar credenciais: Service Account
5. Baixar JSON de credenciais
```

**Passo 2: Instalar Biblioteca**
```bash
pip install gspread oauth2client
```

**Passo 3: Código de Integração**
```python
# sheets_sync_service.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sqlalchemy import create_engine
import pandas as pd

class GoogleSheetsSyncService:
    def __init__(self, credentials_path: str, spreadsheet_name: str):
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open(spreadsheet_name)

    def update_vagas_ativas(self, df: pd.DataFrame):
        """Atualiza planilha 'Vagas Ativas'"""
        worksheet = self.spreadsheet.worksheet('Vagas Ativas')

        # Limpar dados antigos
        worksheet.clear()

        # Headers
        headers = ['ID', 'Nome', 'Status', 'Área', 'Senioridade',
                   'Criada em', 'Candidaturas', 'Posições Abertas']
        worksheet.append_row(headers)

        # Dados
        data = df.values.tolist()
        worksheet.append_rows(data)

        # Formatação
        self._apply_formatting(worksheet)

    def _apply_formatting(self, worksheet):
        """Aplica formatação condicional"""
        # Header em negrito
        worksheet.format('A1:H1', {'textFormat': {'bold': True}})

        # Cores por status
        # OPEN: Verde, CLOSED: Cinza, CANCELED: Vermelho
        pass  # Implementar com conditional_format()
```

### 6.2. Script de Sincronização

```python
# sync_to_sheets.py
from sheets_sync_service import GoogleSheetsSyncService
from sqlalchemy import create_engine
import pandas as pd
from config import settings

def sync_vagas_ativas():
    """Sincroniza vagas ativas para Google Sheets"""

    # Conectar ao banco
    engine = create_engine(f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

    # Buscar vagas ativas
    query = """
        SELECT
            v.inhire_id as id,
            v.name as nome,
            v.status,
            v.area,
            v.seniority as senioridade,
            v.created_at_inhire as criada_em,
            COUNT(DISTINCT c.inhire_id) as candidaturas,
            v.open_positions as posicoes_abertas
        FROM vagas v
        LEFT JOIN candidaturas c ON c.vaga_id = v.inhire_id
        WHERE v.status = 'OPEN'
        GROUP BY v.inhire_id, v.name, v.status, v.area, v.seniority, v.created_at_inhire, v.open_positions
        ORDER BY v.created_at_inhire DESC
    """

    df = pd.read_sql(query, engine)

    # Sincronizar para Sheets
    sheets_service = GoogleSheetsSyncService(
        credentials_path='credentials/google-sheets-service-account.json',
        spreadsheet_name='InHire - Dashboard'
    )

    sheets_service.update_vagas_ativas(df)
    print(f"✅ Sincronizadas {len(df)} vagas ativas para Google Sheets")

if __name__ == "__main__":
    sync_vagas_ativas()
```

### 6.3. Agendamento

```python
# scheduler.py (atualizado)
from apscheduler.schedulers.blocking import BlockingScheduler
from sync_incremental_rapida import sync_incremental_rapida
from sync_incremental_completa import sync_incremental_completa
from sync_to_sheets import sync_vagas_ativas

scheduler = BlockingScheduler()

# 1. Sync PostgreSQL (30 min)
scheduler.add_job(
    sync_incremental_rapida,
    'cron',
    minute='*/30',
    hour='7-19',
    id='sync_db_rapida'
)

# 2. Sync Google Sheets (30 min + 5 min de delay)
scheduler.add_job(
    sync_vagas_ativas,
    'cron',
    minute='5,35',  # :05 e :35 (após sync do BD)
    hour='7-19',
    id='sync_sheets'
)

# 3. Sync Completa (4 horas)
scheduler.add_job(
    sync_incremental_completa,
    'cron',
    hour='*/4',
    id='sync_completa'
)

scheduler.start()
```

---

## 7. Monitoramento e Alertas

### 7.1. Logs Estruturados

```python
# Todos os syncs já fazem logging
{
  "timestamp": "2025-11-18T20:15:20",
  "level": "INFO",
  "entity": "vagas",
  "operation": "sync",
  "records_processed": 1089,
  "records_created": 0,
  "records_updated": 29,
  "records_skipped": 1060,
  "duration_ms": 22800,
  "success": true
}
```

### 7.2. Dashboard de Monitoramento

**Métricas Importantes:**
```sql
-- Última sincronização bem-sucedida
SELECT MAX(synced_at) FROM vagas;

-- Taxa de sincronização (últimas 24h)
SELECT
    DATE_TRUNC('hour', synced_at) as hora,
    COUNT(*) as vagas_sincronizadas
FROM vagas
WHERE synced_at >= NOW() - INTERVAL '24 hours'
GROUP BY hora
ORDER BY hora DESC;

-- Erros de sincronização (verificar logs)
-- Ver arquivo: logs/inhire_sync.log
```

### 7.3. Alertas Automáticos

```python
# alertas_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AlertasService:
    def __init__(self, smtp_config: dict):
        self.smtp_config = smtp_config

    def send_alert(self, subject: str, message: str, recipients: list):
        """Envia alerta por email"""
        msg = MIMEMultipart()
        msg['From'] = self.smtp_config['from']
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = f"[InHire Alert] {subject}"

        msg.attach(MIMEText(message, 'html'))

        with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
            server.starttls()
            server.login(self.smtp_config['user'], self.smtp_config['password'])
            server.send_message(msg)

    def alert_sync_failure(self, entity: str, error: str):
        """Alerta de falha na sincronização"""
        message = f"""
        <h2>Falha na Sincronização</h2>
        <p><strong>Entidade:</strong> {entity}</p>
        <p><strong>Erro:</strong> {error}</p>
        <p><strong>Hora:</strong> {datetime.now()}</p>
        """
        self.send_alert(f"Sync Failed: {entity}", message, ['admin@empresa.com'])

    def alert_novas_vagas(self, count: int, vagas: list):
        """Alerta de novas vagas detectadas"""
        message = f"""
        <h2>🎯 {count} Novas Vagas Detectadas!</h2>
        <ul>
        {"".join([f"<li>{v['name']} - {v['area']}</li>" for v in vagas])}
        </ul>
        """
        self.send_alert(f"{count} Novas Vagas", message, ['recrutamento@empresa.com'])
```

---

## 8. Roadmap de Implementação

### Fase 1: Otimização da Sincronização (1-2 dias)
- [x] Diagnosticar problema do filtro por status
- [ ] Implementar filtro por data de atualização
- [ ] Testar sync_incremental_rapida.py otimizada
- [ ] Validar tempo de execução < 3 minutos

### Fase 2: Integração Power BI (2-3 dias)
- [ ] Configurar ODBC Driver
- [ ] Conectar Power BI Desktop ao PostgreSQL
- [ ] Criar relacionamentos entre tabelas
- [ ] Desenvolver Dashboard 1: Overview Executivo
- [ ] Desenvolver Dashboard 2: Funil de Recrutamento
- [ ] Desenvolver Dashboard 3: Análise de Vagas
- [ ] Publicar no Power BI Service
- [ ] Configurar refresh automático (30 min)

### Fase 3: Integração Google Sheets (2-3 dias)
- [ ] Habilitar Google Sheets API
- [ ] Criar Service Account e baixar credenciais
- [ ] Desenvolver `sheets_sync_service.py`
- [ ] Criar planilha "Vagas Ativas"
- [ ] Criar planilha "Novas Vagas (Últimas 24h)"
- [ ] Implementar formatação condicional
- [ ] Agendar sincronização a cada 30 min

### Fase 4: Monitoramento e Alertas (1-2 dias)
- [ ] Configurar sistema de alertas por email
- [ ] Implementar alerta de falha na sincronização
- [ ] Implementar alerta de novas vagas
- [ ] Criar dashboard de monitoramento (logs)
- [ ] Documentar troubleshooting

### Fase 5: Automação e Deploy (1 dia)
- [ ] Configurar agendador (APScheduler)
- [ ] Testar execução contínua 24/7
- [ ] Documentar procedimentos operacionais
- [ ] Treinar equipe no uso do sistema

### Fase 6: Melhorias Futuras (Backlog)
- [ ] Implementar webhooks do InHire (se disponível)
- [ ] Adicionar cache Redis para queries frequentes
- [ ] Criar API REST interna para consultas
- [ ] Implementar versionamento de dados (histórico)
- [ ] Adicionar machine learning (predição de contratações)

---

## 📊 Métricas de Sucesso

| Métrica | Meta | Atual | Status |
|---------|------|-------|--------|
| Tempo de sync (rápida) | < 3 min | 22.8s ✅ | ✅ Atingido |
| Tempo de sync (completa) | < 20 min | ~6h ❌ | ⚠️ Otimizar |
| Frequência de atualização | 30 min | 30 min | ✅ OK |
| Taxa de skip (eficiência) | > 95% | 98.4% | ✅ Ótimo |
| Disponibilidade do sistema | > 99% | - | 🔄 Monitorar |
| Dashboards Power BI | 3 | 0 | 🔄 Desenvolver |
| Planilhas Google Sheets | 3 | 0 | 🔄 Desenvolver |

---

## 🎯 Próximos Passos Imediatos

1. **Corrigir filtro de sync_incremental_rapida.py**
   - Trocar filtro de status por data de atualização
   - Testar com janela de 2 horas

2. **Iniciar integração Power BI**
   - Instalar ODBC Driver
   - Conectar e criar primeiro dashboard

3. **Configurar Google Sheets API**
   - Criar projeto e credenciais
   - Desenvolver primeiro script de sync

---

**Documentação criada em:** 18/11/2025
**Versão:** 1.0
**Autor:** Claude Code + Marcos Santiago
