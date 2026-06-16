# Guia de Monitoramento e Alertas - InHire Sync

**Data de criação:** 16/01/2026
**Versão:** 1.0

---

## 📋 Visão Geral

Sistema completo de monitoramento e alertas para InHire Sync usando Prometheus + Alertmanager + Grafana.

### Componentes

```
┌──────────────────┐
│  InHire Sync     │ → Métricas (porta 8000)
│  (Aplicação)     │ → Health Check (porta 8080)
└────────┬─────────┘
         │
         ↓ scrape (15s)
┌────────────────────┐
│   Prometheus       │ → Coleta e armazena métricas
│   (porta 9090)     │ → Avalia regras de alerta
└────────┬───────────┘
         │
         ↓ alertas
┌────────────────────┐
│  Alertmanager      │ → Agrupa e roteia alertas
│  (porta 9093)      │ → Envia para Slack/Email/PagerDuty
└────────────────────┘
         │
         ↓
┌────────────────────┐
│   Grafana          │ → Dashboards visuais
│   (porta 3000)     │ → Gráficos e análises
└────────────────────┘
```

---

## 🚀 Setup Rápido

### 1. Instalar Dependências

#### Windows (via Chocolatey)
```powershell
# Instalar Chocolatey (se não tiver)
Set-ExecutionPolicy Bypass -Scope Process -Force
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Instalar Prometheus, Alertmanager, Grafana
choco install prometheus -y
choco install prometheus-alertmanager -y
choco install grafana -y

# Instalar Node Exporter (métricas do sistema)
choco install prometheus-node-exporter -y
```

#### Linux (Ubuntu/Debian)
```bash
# Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*
./prometheus --config.file=prometheus.yml

# Alertmanager
wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
tar xvfz alertmanager-*.tar.gz
cd alertmanager-*
./alertmanager --config.file=alertmanager.yml

# Grafana
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana

# Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
tar xvfz node_exporter-*.tar.gz
cd node_exporter-*
./node_exporter
```

### 2. Configurar Arquivos

```bash
# Copiar arquivos de configuração
cp monitoring/prometheus.yaml /etc/prometheus/prometheus.yml
cp monitoring/alerts.yaml /etc/prometheus/alerts.yml
cp monitoring/alertmanager.yaml /etc/alertmanager/alertmanager.yml
```

### 3. Iniciar Serviços

```bash
# Prometheus
prometheus --config.file=/etc/prometheus/prometheus.yml

# Alertmanager
alertmanager --config.file=/etc/alertmanager/alertmanager.yml

# Grafana
systemctl start grafana-server

# InHire Sync (métricas + health)
python metrics_server.py &  # Porta 8000
python health_check.py &    # Porta 8080
```

### 4. Verificar

```bash
# Prometheus UI
http://localhost:9090

# Alertmanager UI
http://localhost:9093

# Grafana
http://localhost:3000
# Login padrão: admin/admin
```

---

## 📊 Configuração do Grafana

### 1. Adicionar Data Source

```
Grafana UI → Configuration → Data Sources → Add data source
  Type: Prometheus
  URL: http://localhost:9090
  Access: Server (default)
  Save & Test
```

### 2. Importar Dashboard

#### Opção A: Dashboard Pronto
```
Grafana UI → Dashboards → Import
  ID: 1860  # Node Exporter Full
  ID: 7587  # PostgreSQL Database
```

#### Opção B: Dashboard Customizado (JSON)
```json
{
  "dashboard": {
    "title": "InHire Sync Monitoring",
    "panels": [
      {
        "title": "Sync Status",
        "targets": [{
          "expr": "sync_status{status='SUCCESS'}"
        }]
      },
      {
        "title": "Sync Duration",
        "targets": [{
          "expr": "sync_duration_seconds"
        }]
      },
      {
        "title": "Records Processed",
        "targets": [{
          "expr": "rate(records_processed_total[5m])"
        }]
      },
      {
        "title": "Database Latency",
        "targets": [{
          "expr": "database_latency_ms"
        }]
      },
      {
        "title": "API Latency",
        "targets": [{
          "expr": "api_latency_seconds"
        }]
      },
      {
        "title": "System Resources",
        "targets": [
          {"expr": "cpu_usage_pct"},
          {"expr": "memory_usage_pct"},
          {"expr": "disk_usage_pct"}
        ]
      }
    ]
  }
}
```

---

## 🚨 Alertas Configurados

### Alertas Críticos (Notificação Imediata)

| Alerta | Condição | Ação |
|--------|----------|------|
| **SyncFailed** | Sync com erro por 5 min | Email + Slack + PagerDuty |
| **DatabaseDown** | DB indisponível por 2 min | Email + Slack + PagerDuty |
| **InhireAPIDown** | API falhou por 5 min | Email + Slack |

### Alertas de Warning (Notificação Agrupada)

| Alerta | Condição | Ação |
|--------|----------|------|
| **SyncDurationHigh** | Sync > 30 min (normal: 9.5 min) | Slack |
| **DataStale** | Última sync > 3 horas | Slack + Email |
| **DiskSpaceHigh** | Uso disco > 80% | Slack |
| **MemoryUsageHigh** | Uso RAM > 85% | Slack |
| **CPUUsageHigh** | Uso CPU > 90% por 10 min | Slack |

### Alertas Informativos (Notificação Diária)

| Alerta | Condição | Ação |
|--------|----------|------|
| **DatabaseLatencyHigh** | Latência DB > 100ms | Slack (diário) |
| **HighErrorRate** | Taxa erro > 5% | Slack (diário) |

---

## 📧 Configuração de Notificações

### Slack

1. **Criar Webhook:**
   ```
   Slack → Apps → Incoming Webhooks → Add to Slack
   Canal: #inhire-alerts
   Copiar Webhook URL
   ```

2. **Configurar Alertmanager:**
   ```yaml
   # monitoring/alertmanager.yaml
   global:
     slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
   ```

3. **Testar:**
   ```bash
   curl -X POST http://localhost:9093/-/reload
   ```

### Email

1. **Configurar SMTP:**
   ```yaml
   # monitoring/alertmanager.yaml
   email_configs:
     - to: 'devops@framework.com'
       from: 'alertmanager@framework.com'
       smarthost: 'smtp.gmail.com:587'
       auth_username: 'your-email@gmail.com'
       auth_password: 'your-app-password'
   ```

2. **Gmail App Password:**
   ```
   Google Account → Security → 2-Step Verification
   → App passwords → Generate
   ```

### PagerDuty (Opcional)

1. **Criar Integration:**
   ```
   PagerDuty → Services → Add Integration
   Type: Prometheus
   Copiar Integration Key
   ```

2. **Configurar Alertmanager:**
   ```yaml
   pagerduty_configs:
     - service_key: 'YOUR_PAGERDUTY_KEY'
   ```

---

## 🔍 Queries Úteis (PromQL)

### Sync Performance
```promql
# Taxa de sucesso de sync (últimas 24h)
sum(rate(sync_total{status="SUCCESS"}[24h])) /
sum(rate(sync_total[24h])) * 100

# Duração média de sync por tipo
avg(sync_duration_seconds) by (sync_type)

# Sync mais recente
max(sync_last_success_timestamp)

# Tempo desde última sync
time() - max(sync_last_success_timestamp)
```

### Database Performance
```promql
# Latência do banco (p95)
histogram_quantile(0.95, database_latency_ms)

# Pool de conexões em uso
db_connection_pool_size{state="checked_out"} /
db_connection_pool_size{state="size"} * 100

# Conexões ociosas
db_connection_pool_size{state="checked_in"}
```

### API Performance
```promql
# Taxa de erros da API
rate(api_requests_total{status_code!~"2.."}[5m])

# Latência da API por endpoint
avg(api_latency_seconds) by (endpoint)

# Rate limit status
api_rate_limit_remaining
```

### System Resources
```promql
# CPU usage
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory usage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disk usage
(node_filesystem_size_bytes - node_filesystem_free_bytes) /
node_filesystem_size_bytes * 100
```

---

## 📈 Dashboards Recomendados

### Dashboard 1: Sync Overview
```
┌─────────────────────────────────────────┐
│ Sync Success Rate (24h): 99.95%        │
│ Last Sync: 15 minutes ago               │
│ Records Processed: 1,953                │
└─────────────────────────────────────────┘

[Gráfico: Sync Duration Over Time]
[Gráfico: Records Processed per Sync]
[Gráfico: Success vs Failure Rate]
```

### Dashboard 2: System Health
```
┌─────────────────────────────────────────┐
│ Database: ✅ OK (5ms)                   │
│ API: ✅ OK (234ms)                      │
│ CPU: 25% | RAM: 45% | Disk: 65%        │
└─────────────────────────────────────────┘

[Gráfico: CPU Usage]
[Gráfico: Memory Usage]
[Gráfico: Disk Usage]
[Gráfico: Network I/O]
```

### Dashboard 3: Performance Metrics
```
[Gráfico: API Latency by Endpoint]
[Gráfico: Database Query Time]
[Gráfico: Connection Pool Usage]
[Gráfico: Error Rate]
```

---

## 🔧 Troubleshooting

### Prometheus não está coletando métricas

```bash
# Verificar se aplicação está expondo métricas
curl http://localhost:8000/metrics

# Verificar targets no Prometheus
http://localhost:9090/targets

# Ver logs do Prometheus
journalctl -u prometheus -f
```

### Alertas não estão sendo enviados

```bash
# Verificar se Alertmanager está rodando
curl http://localhost:9093/-/healthy

# Ver alertas ativos
http://localhost:9093/#/alerts

# Testar envio manual
curl -X POST http://localhost:9093/api/v1/alerts -d '[
  {
    "labels": {"alertname": "test", "severity": "warning"},
    "annotations": {"summary": "Test alert"}
  }
]'

# Ver logs do Alertmanager
journalctl -u alertmanager -f
```

### Grafana não conecta ao Prometheus

```bash
# Verificar conectividade
curl http://localhost:9090/-/healthy

# Verificar configuração do data source
Grafana → Configuration → Data Sources → Test
```

---

## 🎯 Checklist de Implementação

### Fase 1: Setup Básico
- [ ] Instalar Prometheus
- [ ] Instalar Alertmanager
- [ ] Instalar Grafana
- [ ] Copiar arquivos de configuração
- [ ] Iniciar todos os serviços

### Fase 2: Configuração de Alertas
- [ ] Configurar Webhook do Slack
- [ ] Configurar SMTP para email
- [ ] Testar alerta crítico
- [ ] Testar alerta warning
- [ ] Configurar PagerDuty (opcional)

### Fase 3: Dashboards
- [ ] Adicionar Prometheus como data source
- [ ] Importar dashboard Node Exporter
- [ ] Criar dashboard InHire Sync
- [ ] Configurar refresh automático

### Fase 4: Validação
- [ ] Simular falha de sync
- [ ] Verificar recebimento de alerta
- [ ] Validar métricas no Grafana
- [ ] Documentar runbooks

---

## 📚 Recursos Adicionais

- **Prometheus Docs:** https://prometheus.io/docs/
- **Alertmanager Docs:** https://prometheus.io/docs/alerting/latest/alertmanager/
- **Grafana Docs:** https://grafana.com/docs/
- **PromQL Tutorial:** https://prometheus.io/docs/prometheus/latest/querying/basics/

---

**Documentação criada em:** 16/01/2026
**Última atualização:** 16/01/2026
**Responsável:** Framework Digital DevOps Team
