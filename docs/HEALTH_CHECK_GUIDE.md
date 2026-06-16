# Guia de Health Check - InHire Sync

**Data de criação:** 16/01/2026
**Versão:** 1.0

---

## 📋 Visão Geral

Sistema de health check para monitoramento da saúde do InHire Sync.

### Endpoints Disponíveis

| Endpoint | Propósito | Uso |
|----------|-----------|-----|
| `/health` | Health check completo | Monitoramento geral |
| `/health/live` | Liveness probe | Kubernetes/Docker |
| `/health/ready` | Readiness probe | Load balancers |

---

## 🚀 Uso Básico

### Iniciar Serviço

```bash
# Instalar dependências
pip install flask psutil

# Rodar health check service
python health_check.py

# Acesso
# http://localhost:8080/health
```

### Testar Endpoints

```bash
# Health check completo
curl http://localhost:8080/health

# Liveness probe
curl http://localhost:8080/health/live

# Readiness probe
curl http://localhost:8080/health/ready
```

---

## 📊 Verificações Realizadas

### 1. Database (CRÍTICO)
```json
{
  "status": "ok|warning|error",
  "latency_ms": 5.23,
  "host": "localhost:5432",
  "database": "inhire",
  "pool": {
    "size": 10,
    "checked_in": 8,
    "checked_out": 2
  }
}
```

**Alertas:**
- ❌ `error`: Conexão falhou
- ✅ `ok`: Conexão OK, latência < 100ms

### 2. InHire API (CRÍTICO)
```json
{
  "status": "ok|error",
  "authenticated": true,
  "latency_ms": 234.56,
  "base_url": "https://api.inhire.app/",
  "tenant": "framework-digital"
}
```

**Alertas:**
- ❌ `error`: Autenticação falhou
- ✅ `ok`: Autenticado com sucesso

### 3. Last Sync
```json
{
  "status": "ok|warning|error",
  "last_sync": "2026-01-16T10:30:00",
  "age_hours": 1.5,
  "sync_type": "INCREMENTAL",
  "records_processed": 1953
}
```

**Alertas:**
- ✅ `ok`: Última sync < 2 horas
- ⚠️ `warning`: Última sync 2-6 horas
- ❌ `error`: Última sync > 6 horas

### 4. Disk Space
```json
{
  "status": "ok|warning|error",
  "disk_usage_pct": 65.3,
  "disk_free_gb": 234.5,
  "disk_total_gb": 500.0
}
```

**Alertas:**
- ✅ `ok`: Uso < 80%
- ⚠️ `warning`: Uso 80-90%
- ❌ `error`: Uso > 90%

### 5. Memory
```json
{
  "status": "ok|warning|error",
  "memory_usage_pct": 45.2,
  "memory_available_gb": 8.5,
  "memory_total_gb": 16.0
}
```

**Alertas:**
- ✅ `ok`: Uso < 80%
- ⚠️ `warning`: Uso 80-90%
- ❌ `error`: Uso > 90%

### 6. CPU
```json
{
  "status": "ok|warning|error",
  "cpu_usage_pct": 25.3,
  "cpu_count": 8
}
```

**Alertas:**
- ✅ `ok`: Uso < 80%
- ⚠️ `warning`: Uso 80-95%
- ❌ `error`: Uso > 95%

---

## 🎯 Status Geral

### HTTP Status Codes

```
200 OK - Sistema saudável ou degradado mas operacional
  {
    "status": "healthy",      # Todos checks OK
    "status": "degraded"      # Checks críticos OK, mas warnings
  }

503 Service Unavailable - Sistema indisponível
  {
    "status": "unhealthy"     # Checks críticos falharam
  }
```

### Resposta Completa

```json
{
  "status": "healthy",
  "timestamp": "2026-01-16T13:45:23Z",
  "version": "2.1",
  "checks": {
    "database": { ... },
    "inhire_api": { ... },
    "last_sync": { ... },
    "disk": { ... },
    "memory": { ... },
    "cpu": { ... }
  }
}
```

---

## 🔧 Integração com Ferramentas

### UptimeRobot

```yaml
Monitor Configuration:
  Type: HTTP(s)
  URL: http://inhire-sync.framework.com/health
  Interval: 5 minutes
  Alert When: HTTP Status != 200
  Notifications: Email, Slack
```

### AWS Application Load Balancer

```yaml
Health Check:
  Protocol: HTTP
  Path: /health/ready
  Port: 8080
  Interval: 30 seconds
  Timeout: 5 seconds
  Healthy Threshold: 2
  Unhealthy Threshold: 2
```

### Kubernetes

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: inhire-sync
    image: inhire-sync:latest
    livenessProbe:
      httpGet:
        path: /health/live
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 2
```

### Docker Compose

```yaml
services:
  inhire-sync:
    image: inhire-sync:latest
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 40s
```

### Prometheus

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'inhire-health'
    metrics_path: '/health'
    static_configs:
      - targets: ['localhost:8080']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'inhire-sync'
```

---

## 📈 Monitoramento Contínuo

### Script de Verificação

```bash
#!/bin/bash
# check_health.sh

HEALTH_URL="http://localhost:8080/health"
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Verificar health
response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $response -ne 200 ]; then
  # Enviar alerta para Slack
  curl -X POST $SLACK_WEBHOOK \
    -H 'Content-Type: application/json' \
    -d "{
      \"text\": \"⚠️ InHire Sync UNHEALTHY\",
      \"attachments\": [{
        \"color\": \"danger\",
        \"text\": \"HTTP $response - Sistema não está saudável\"
      }]
    }"
fi
```

### Cron Job

```bash
# Verificar a cada 5 minutos
*/5 * * * * /path/to/check_health.sh
```

---

## 🚨 Troubleshooting

### Health Check não responde

```bash
# Verificar se serviço está rodando
ps aux | grep health_check.py

# Verificar logs
tail -f logs/inhire_sync.log

# Reiniciar serviço
pkill -f health_check.py
python health_check.py &
```

### Database check falhando

```bash
# Testar conexão direta
psql -h localhost -U postgres -d inhire -c "SELECT 1"

# Verificar pool de conexões
# Ver logs do PostgreSQL
```

### API check falhando

```bash
# Testar autenticação manualmente
python -c "
from services.auth_service import AuthService
auth = AuthService()
auth.ensure_authenticated()
print('Auth OK')
"
```

---

## 📝 Logs

O health check service registra eventos importantes:

```bash
# Ver logs do health check
tail -f logs/health_check.log

# Filtrar por erros
grep "ERROR" logs/health_check.log

# Ver últimas 50 linhas
tail -50 logs/health_check.log
```

---

## 🔐 Segurança

### Considerações

1. **Exposição pública:** Não expor `/health` publicamente sem autenticação
2. **Informações sensíveis:** Endpoint não expõe senhas ou tokens
3. **Rate limiting:** Considerar limitar requisições (opcional)

### Autenticação Básica (Opcional)

```python
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    if username == 'monitor' and password == 'secret':
        return username

@app.route('/health')
@auth.login_required
def health():
    # ...
```

---

## 📊 Métricas Coletadas

O health check pode ser integrado com Prometheus para coletar métricas:

- `health_check_duration_seconds` - Duração de cada verificação
- `health_check_status` - Status de cada check (0=ok, 1=warning, 2=error)
- `database_latency_ms` - Latência do banco de dados
- `api_latency_ms` - Latência da API InHire
- `last_sync_age_hours` - Idade da última sincronização

---

## 🎯 Próximos Passos

1. ✅ Health check implementado
2. ⏳ Configurar UptimeRobot ou similar
3. ⏳ Integrar com Slack para alertas
4. ⏳ Adicionar métricas Prometheus
5. ⏳ Configurar dashboards Grafana

---

**Documentação criada em:** 16/01/2026
**Última atualização:** 16/01/2026
**Responsável:** Framework Digital DevOps Team
