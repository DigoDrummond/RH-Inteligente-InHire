# ============================================================================
# Multi-stage Dockerfile para InHire Sync
# ============================================================================
# Stage 1: Base image com dependências do sistema
# Stage 2: Builder - instala dependências Python
# Stage 3: Runtime - imagem final otimizada
# ============================================================================

# ============================================================================
# STAGE 1: Base
# ============================================================================
FROM python:3.11-slim as base

# Metadados
LABEL maintainer="Framework Digital <devops@framework.com>"
LABEL version="2.1"
LABEL description="InHire Sync - Sistema de sincronização InHire → PostgreSQL"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# STAGE 2: Builder
# ============================================================================
FROM base as builder

# Instalar dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar apenas requirements primeiro (layer caching)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --user --no-warn-script-location -r requirements.txt

# ============================================================================
# STAGE 3: Runtime
# ============================================================================
FROM base as runtime

# Criar usuário não-root
RUN groupadd -r inhire && useradd -r -g inhire inhire

# Criar diretórios
RUN mkdir -p /app /app/logs /app/backups && \
    chown -R inhire:inhire /app

# Copiar dependências Python do builder
COPY --from=builder /root/.local /home/inhire/.local

# Configurar PATH
ENV PATH=/home/inhire/.local/bin:$PATH

# Definir diretório de trabalho
WORKDIR /app

# Copiar código da aplicação
COPY --chown=inhire:inhire . .

# Mudar para usuário não-root
USER inhire

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expor portas
EXPOSE 8080 8000

# Comando padrão (pode ser sobrescrito)
CMD ["python", "run_sync.py", "--incremental"]

# ============================================================================
# Build instructions:
# docker build -t inhire-sync:latest .
# docker build -t inhire-sync:2.1 .
#
# Run:
# docker run -d --name inhire-sync \
#   -e DB_HOST=postgres \
#   -e DB_PASSWORD=secret \
#   inhire-sync:latest
# ============================================================================
