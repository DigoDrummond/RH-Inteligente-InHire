# 🚀 Guia de Deploy - AWS

**Sistema:** InHire Sync + Integração
**Data:** 18/11/2025
**Versão:** 1.0

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Opções de Arquitetura AWS](#opções-de-arquitetura-aws)
3. [Opção 1: EC2 (Recomendado)](#opção-1-ec2-recomendado)
4. [Opção 2: ECS Fargate](#opção-2-ecs-fargate)
5. [Opção 3: Lambda + EventBridge](#opção-3-lambda--eventbridge)
6. [RDS PostgreSQL](#rds-postgresql)
7. [Configuração de Segredos](#configuração-de-segredos)
8. [Monitoramento e Logs](#monitoramento-e-logs)
9. [Estimativa de Custos](#estimativa-de-custos)
10. [Checklist de Deploy](#checklist-de-deploy)

---

## 1. Visão Geral

### Componentes do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                          AWS Cloud                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐        ┌──────────────┐        ┌──────────┐  │
│  │   EC2/ECS    │ ────── │ RDS          │        │ S3       │  │
│  │   (Python)   │        │ (PostgreSQL) │        │ (Backup) │  │
│  └──────────────┘        └──────────────┘        └──────────┘  │
│        │                                                        │
│        │                                                        │
│        ▼                                                        │
│  ┌──────────────┐        ┌──────────────┐        ┌──────────┐  │
│  │ CloudWatch   │        │ Secrets      │        │ SNS      │  │
│  │ (Logs)       │        │ Manager      │        │ (Alertas)│  │
│  └──────────────┘        └──────────────┘        └──────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
         │
         │ API Calls
         ▼
┌─────────────────┐
│  API InHire     │
│  (External)     │
└─────────────────┘
```

### Requisitos Mínimos

**Compute:**
- CPU: 2 vCPUs
- RAM: 4 GB
- Storage: 20 GB

**Database:**
- PostgreSQL 13+
- Storage: 50 GB (crescimento: ~5 GB/ano)
- IOPS: 1000 (General Purpose SSD)

**Rede:**
- Outbound HTTPS (443) para api.inhire.app
- Inbound PostgreSQL (5432) apenas da aplicação

---

## 2. Opções de Arquitetura AWS

### Comparação das Opções

| Aspecto | EC2 | ECS Fargate | Lambda |
|---------|-----|-------------|--------|
| **Complexidade** | 🟡 Média | 🟡 Média | 🟢 Baixa |
| **Custo/mês** | $30-50 | $40-60 | $5-15 |
| **Escalabilidade** | Manual | Automática | Automática |
| **Manutenção** | Média | Baixa | Muito Baixa |
| **Controle** | Total | Médio | Limitado |
| **Recomendado para** | Prod (controle) | Prod (escala) | Dev/Teste |

### Recomendação

**✅ EC2 para Produção:**
- Controle total sobre o ambiente
- Custo previsível
- Fácil debug e manutenção
- Ideal para começar

**Quando migrar:**
- ECS Fargate: Quando precisar escalar horizontalmente
- Lambda: Para funções específicas (alertas, webhooks)

---

## 3. Opção 1: EC2 (Recomendado)

### 3.1. Criação da Instância EC2

**Passo 1: Escolher AMI**
```
Região: us-east-1 (N. Virginia) ou sa-east-1 (São Paulo)
AMI: Ubuntu Server 22.04 LTS
Tipo: t3.medium (2 vCPUs, 4 GB RAM)
Storage: 20 GB gp3
```

**Passo 2: Configurar Security Group**
```
Name: inhire-sync-sg

Inbound Rules:
  - Type: SSH
    Port: 22
    Source: Seu IP (para administração)

  - Type: PostgreSQL
    Port: 5432
    Source: RDS Security Group (interno)

Outbound Rules:
  - Type: HTTPS
    Port: 443
    Destination: 0.0.0.0/0 (para API InHire)
```

**Passo 3: Criar Key Pair**
```bash
# Baixar inhire-sync-key.pem
chmod 400 inhire-sync-key.pem
```

### 3.2. Configuração Inicial da Instância

**SSH na instância:**
```bash
ssh -i inhire-sync-key.pem ubuntu@<EC2_PUBLIC_IP>
```

**Atualizar sistema:**
```bash
sudo apt update && sudo apt upgrade -y
```

**Instalar dependências:**
```bash
# Python 3.11+
sudo apt install -y python3.11 python3.11-venv python3-pip

# PostgreSQL client
sudo apt install -y postgresql-client

# Git
sudo apt install -y git

# Utilitários
sudo apt install -y htop vim curl wget
```

### 3.3. Setup da Aplicação

**Clonar/Transferir código:**
```bash
# Criar diretório
mkdir -p /opt/inhire-sync
cd /opt/inhire-sync

# Transferir arquivos (do seu PC para EC2)
# No seu PC:
scp -i inhire-sync-key.pem -r \
  "G:\Meu Drive\Framework_Data\Inhire"/* \
  ubuntu@<EC2_PUBLIC_IP>:/opt/inhire-sync/
```

**Criar ambiente virtual:**
```bash
cd /opt/inhire-sync
python3.11 -m venv venv
source venv/bin/activate
```

**Instalar dependências:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Criar arquivo .env:**
```bash
nano .env
```

```env
# .env
# Database (RDS)
DB_HOST=inhire-sync-db.xxxxxxxxxx.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=inhire
DB_USER=postgres
DB_PASSWORD=<SENHA_SEGURA>

# InHire API
INHIRE_BASE_URL=https://api.inhire.app/
INHIRE_AUTH_URL=https://auth.inhire.app/
INHIRE_EMAIL=service-account-ca4e275d-e401-4c08-8a52-28b251a05840@inhire.app
INHIRE_PASSWORD=A71f9kJqICKPTsdlYhbm
INHIRE_TENANT=ca4e275d-e401-4c08-8a52-28b251a05840

# Pool de conexões
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Timeouts
INHIRE_TIMEOUT_CONNECT=15
INHIRE_TIMEOUT_READ=45

# Sincronização
SYNC_BATCH_SIZE=50
```

### 3.4. Criar Serviço Systemd

**Criar arquivo de serviço:**
```bash
sudo nano /etc/systemd/system/inhire-sync.service
```

```ini
[Unit]
Description=InHire Sync Scheduler
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/inhire-sync
Environment="PATH=/opt/inhire-sync/venv/bin"
ExecStart=/opt/inhire-sync/venv/bin/python /opt/inhire-sync/scheduler.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/inhire-sync/scheduler.log
StandardError=append:/var/log/inhire-sync/scheduler-error.log

[Install]
WantedBy=multi-user.target
```

**Criar diretório de logs:**
```bash
sudo mkdir -p /var/log/inhire-sync
sudo chown ubuntu:ubuntu /var/log/inhire-sync
```

**Habilitar e iniciar serviço:**
```bash
# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar para iniciar no boot
sudo systemctl enable inhire-sync

# Iniciar serviço
sudo systemctl start inhire-sync

# Verificar status
sudo systemctl status inhire-sync
```

**Ver logs:**
```bash
# Logs em tempo real
sudo journalctl -u inhire-sync -f

# Últimas 100 linhas
sudo journalctl -u inhire-sync -n 100

# Logs de hoje
sudo journalctl -u inhire-sync --since today
```

### 3.5. Configurar Auto-Start

O serviço já está configurado para iniciar automaticamente com `systemctl enable`.

**Verificar:**
```bash
sudo systemctl is-enabled inhire-sync
# Output: enabled
```

### 3.6. Backup e Monitoramento

**Script de backup (executar diariamente):**
```bash
nano /opt/inhire-sync/backup.sh
```

```bash
#!/bin/bash
# Backup do banco de dados

BACKUP_DIR="/opt/inhire-sync/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
  | gzip > $BACKUP_DIR/inhire_backup_$DATE.sql.gz

# Manter apenas últimos 7 backups
ls -t $BACKUP_DIR/inhire_backup_*.sql.gz | tail -n +8 | xargs -r rm

# Upload para S3 (opcional)
aws s3 cp $BACKUP_DIR/inhire_backup_$DATE.sql.gz \
  s3://inhire-sync-backups/
```

**Configurar cron:**
```bash
crontab -e
```

```cron
# Backup diário às 03:00
0 3 * * * /opt/inhire-sync/backup.sh

# Verificar status do serviço a cada hora
0 * * * * systemctl is-active --quiet inhire-sync || systemctl restart inhire-sync
```

---

## 4. Opção 2: ECS Fargate

### 4.1. Criar Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV TZ=America/Sao_Paulo

# Comando padrão
CMD ["python", "scheduler.py"]
```

### 4.2. Build e Push para ECR

```bash
# Criar repositório ECR
aws ecr create-repository --repository-name inhire-sync

# Login no ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build
docker build -t inhire-sync .

# Tag
docker tag inhire-sync:latest \
  <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/inhire-sync:latest

# Push
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/inhire-sync:latest
```

### 4.3. Criar Task Definition

```json
{
  "family": "inhire-sync",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "inhire-sync",
      "image": "<AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/inhire-sync:latest",
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/inhire-sync",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "secrets": [
        {
          "name": "DB_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:inhire/db-password"
        }
      ],
      "environment": [
        {"name": "DB_HOST", "value": "inhire-sync-db.xxxxxxxxxx.us-east-1.rds.amazonaws.com"},
        {"name": "DB_PORT", "value": "5432"},
        {"name": "DB_NAME", "value": "inhire"},
        {"name": "DB_USER", "value": "postgres"}
      ]
    }
  ]
}
```

### 4.4. Criar ECS Service

```bash
aws ecs create-service \
  --cluster inhire-sync-cluster \
  --service-name inhire-sync-service \
  --task-definition inhire-sync \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}"
```

---

## 5. Opção 3: Lambda + EventBridge

### 5.1. Criar Lambda Function

**Limitações:**
- Timeout máximo: 15 minutos
- **Não recomendado** para sync completa (~55 min)
- **OK** para sync rápida (< 3 min)

**Estrutura:**
```
lambda/
├── lambda_function.py
├── config.py
├── services/
├── models/
└── requirements.txt
```

**lambda_function.py:**
```python
import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sync_incremental_rapida import sync_incremental_rapida

def lambda_handler(event, context):
    """Handler principal da Lambda"""

    # Setup database
    database_url = os.environ['DATABASE_URL']
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Executar sync
        exit_code = sync_incremental_rapida(session)

        return {
            'statusCode': 200 if exit_code == 0 else 500,
            'body': json.dumps({
                'message': 'Sync completed',
                'exit_code': exit_code
            })
        }

    finally:
        session.close()
```

### 5.2. Deploy com SAM

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  InhireSyncFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: lambda_function.lambda_handler
      Runtime: python3.11
      Timeout: 900  # 15 minutos
      MemorySize: 2048
      Environment:
        Variables:
          DATABASE_URL: !Ref DatabaseURL
      Events:
        ScheduleEvent:
          Type: Schedule
          Properties:
            Schedule: 'rate(30 minutes)'
```

---

## 6. RDS PostgreSQL

### 6.1. Criar Instância RDS

**Console AWS → RDS → Create Database:**

```
Engine: PostgreSQL 15.x
Template: Production (Multi-AZ para HA)

Settings:
  DB instance identifier: inhire-sync-db
  Master username: postgres
  Master password: <SENHA_SEGURA_32_CHARS>

Instance configuration:
  Class: db.t3.small (2 vCPUs, 2 GB RAM)
  Storage: 50 GB gp3
  IOPS: 3000
  Storage autoscaling: Enable (max 100 GB)

Connectivity:
  VPC: default ou custom
  Public access: No (apenas acesso interno)
  VPC security group: Create new (inhire-db-sg)

Database authentication:
  Password authentication

Additional configuration:
  Initial database name: inhire
  Backup retention: 7 days
  Encryption: Enable
  Performance Insights: Enable
  Maintenance window: Sun 03:00-04:00 UTC
```

### 6.2. Configurar Security Group do RDS

```
Name: inhire-db-sg

Inbound Rules:
  - Type: PostgreSQL
    Port: 5432
    Source: EC2 Security Group (inhire-sync-sg)
    Description: Allow from EC2 instances
```

### 6.3. Inicializar Schema

**Conectar ao RDS:**
```bash
# Do EC2
psql -h inhire-sync-db.xxxxxxxxxx.us-east-1.rds.amazonaws.com \
     -U postgres -d inhire
```

**Criar schema:**
```sql
-- Executar scripts de criação das tabelas
-- (mesmas tabelas do local)
```

---

## 7. Configuração de Segredos

### 7.1. AWS Secrets Manager

**Criar secret:**
```bash
aws secretsmanager create-secret \
  --name inhire/database \
  --description "InHire database credentials" \
  --secret-string '{
    "username":"postgres",
    "password":"<SENHA_SEGURA>",
    "engine":"postgres",
    "host":"inhire-sync-db.xxxxxxxxxx.us-east-1.rds.amazonaws.com",
    "port":5432,
    "dbname":"inhire"
  }'

aws secretsmanager create-secret \
  --name inhire/api \
  --description "InHire API credentials" \
  --secret-string '{
    "email":"service-account-ca4e275d-e401-4c08-8a52-28b251a05840@inhire.app",
    "password":"A71f9kJqICKPTsdlYhbm"
  }'
```

### 7.2. Atualizar Aplicação para Usar Secrets

```python
# config.py
import boto3
import json

def get_secret(secret_name):
    """Busca secret do Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Carregar secrets
db_secret = get_secret('inhire/database')
api_secret = get_secret('inhire/api')

# Usar secrets
DB_HOST = db_secret['host']
DB_PASSWORD = db_secret['password']
INHIRE_EMAIL = api_secret['email']
INHIRE_PASSWORD = api_secret['password']
```

---

## 8. Monitoramento e Logs

### 8.1. CloudWatch Logs

**Criar Log Group:**
```bash
aws logs create-log-group --log-group-name /aws/inhire-sync
```

**Configurar Retention:**
```bash
aws logs put-retention-policy \
  --log-group-name /aws/inhire-sync \
  --retention-in-days 30
```

### 8.2. CloudWatch Metrics

**Métricas personalizadas:**
```python
# utils/cloudwatch_metrics.py
import boto3

cloudwatch = boto3.client('cloudwatch')

def put_metric(metric_name, value, unit='Count'):
    """Envia métrica para CloudWatch"""
    cloudwatch.put_metric_data(
        Namespace='InhireSync',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit
            }
        ]
    )

# Uso
put_metric('SyncDuration', 80.1, 'Seconds')
put_metric('VagasSincronizadas', 6, 'Count')
put_metric('TalentosNovos', 40, 'Count')
```

### 8.3. Alarmes

**Criar alarme de falha:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name inhire-sync-failures \
  --alarm-description "Alert when sync fails" \
  --metric-name SyncFailures \
  --namespace InhireSync \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --alarm-actions <SNS_TOPIC_ARN>
```

---

## 9. Estimativa de Custos

### 9.1. Opção EC2 (Recomendada)

| Recurso | Especificação | Custo/mês |
|---------|---------------|-----------|
| EC2 t3.medium | 2 vCPUs, 4GB RAM, on-demand | $30.40 |
| RDS db.t3.small | 2 vCPUs, 2GB RAM, Multi-AZ | $56.58 |
| EBS (EC2) | 20 GB gp3 | $1.60 |
| EBS (RDS) | 50 GB gp3 | $5.75 |
| Backup (S3) | 10 GB (7 dias) | $0.23 |
| Data Transfer | ~5 GB/mês | $0.45 |
| CloudWatch Logs | 5 GB/mês | $2.50 |
| **TOTAL** | | **~$97.51/mês** |

**Otimizações:**
- Reserved Instances (1 ano): -40% = $58.50/mês
- Savings Plans (1 ano): -35% = $63.38/mês

### 9.2. Opção ECS Fargate

| Recurso | Especificação | Custo/mês |
|---------|---------------|-----------|
| Fargate | 1 vCPU, 2GB RAM, 24/7 | $29.55 |
| RDS | Mesmo que EC2 | $56.58 |
| ECR | 1 GB storage | $0.10 |
| EBS (RDS) | 50 GB gp3 | $5.75 |
| CloudWatch Logs | 5 GB/mês | $2.50 |
| **TOTAL** | | **~$94.48/mês** |

### 9.3. Opção Lambda (Apenas Sync Rápida)

| Recurso | Especificação | Custo/mês |
|---------|---------------|-----------|
| Lambda | 2048 MB, 48 execuções/dia, 90s cada | $2.16 |
| RDS | Mesmo que EC2 | $56.58 |
| EBS (RDS) | 50 GB gp3 | $5.75 |
| CloudWatch Logs | 2 GB/mês | $1.00 |
| **TOTAL** | | **~$65.49/mês** |

**Nota:** Lambda não suporta sync completa (>15 min).

---

## 10. Checklist de Deploy

### Pré-Deploy

- [ ] Criar conta AWS
- [ ] Configurar AWS CLI
- [ ] Decidir região (us-east-1 ou sa-east-1)
- [ ] Preparar credenciais InHire API
- [ ] Revisar código local

### Database

- [ ] Criar instância RDS PostgreSQL
- [ ] Configurar Security Group do RDS
- [ ] Criar database "inhire"
- [ ] Executar scripts de schema
- [ ] Testar conexão do local
- [ ] Configurar backups automáticos

### Compute (EC2)

- [ ] Criar instância EC2 t3.medium
- [ ] Configurar Security Group do EC2
- [ ] Criar e baixar Key Pair
- [ ] SSH na instância
- [ ] Instalar dependências (Python, PostgreSQL client)
- [ ] Transferir código para EC2
- [ ] Criar ambiente virtual
- [ ] Instalar requirements
- [ ] Configurar .env
- [ ] Testar sync manual
- [ ] Criar serviço systemd
- [ ] Habilitar auto-start
- [ ] Configurar backup diário (cron)

### Segurança

- [ ] Criar secrets no Secrets Manager
- [ ] Atualizar código para usar Secrets Manager
- [ ] Revisar Security Groups (princípio do menor privilégio)
- [ ] Configurar IAM roles (se usar ECS/Lambda)
- [ ] Habilitar encryption at rest (RDS)
- [ ] Configurar SSL/TLS (RDS connections)

### Monitoramento

- [ ] Criar Log Group no CloudWatch
- [ ] Configurar retention de logs (30 dias)
- [ ] Enviar métricas customizadas
- [ ] Criar alarmes (falhas, latência)
- [ ] Configurar SNS topic para alertas
- [ ] Testar notificações

### Testes

- [ ] Executar sync_incremental_rapida.py
- [ ] Validar tempo < 3 minutos
- [ ] Verificar logs no CloudWatch
- [ ] Validar dados no RDS
- [ ] Testar restart do serviço
- [ ] Simular falha e recovery
- [ ] Validar backup e restore

### Documentação

- [ ] Documentar endpoints RDS
- [ ] Documentar processo de deploy
- [ ] Criar runbook de troubleshooting
- [ ] Documentar procedimentos de backup/restore
- [ ] Compartilhar credenciais de forma segura

---

## 📚 Recursos Adicionais

**AWS Documentation:**
- [EC2 User Guide](https://docs.aws.amazon.com/ec2/)
- [RDS User Guide](https://docs.aws.amazon.com/rds/)
- [ECS User Guide](https://docs.aws.amazon.com/ecs/)
- [Lambda User Guide](https://docs.aws.amazon.com/lambda/)

**Best Practices:**
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Security Best Practices](https://docs.aws.amazon.com/security/)

**Cost Optimization:**
- [AWS Cost Explorer](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/)
- [AWS Pricing Calculator](https://calculator.aws/)

---

**Criado em:** 18/11/2025
**Autor:** Claude Code + Marcos Santiago
**Versão:** 1.0
