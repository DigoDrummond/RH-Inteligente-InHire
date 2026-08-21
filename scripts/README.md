# Scripts Inhire

Diretório com scripts utilitários organizados por funcionalidade.

## 📁 Estrutura

### `/export` - Exportação para Google Sheets
Scripts para exportar views do PostgreSQL para Google Sheets usando OAuth2.

**Scripts principais:**
- `export_analise_posicoes.py` - Exporta vw_analise_posicoes (1.383 registros)
- `export_dados_jade.py` - Exporta vw_dados_jade (dados customizados)
- `export_funil_performance.py` - Exporta vw_funil_performance (85k+ registros)
- `export_relatorio_candidaturas.py` - Exporta vw_relatorio_candidaturas (35k+ registros)

**Uso:**
```bash
python scripts/export/export_analise_posicoes.py
```

---

### `/sync` - Sincronização API Inhire
Scripts especializados de sincronização.

**Scripts principais:**
- `sync_talent_pool.py` - Sincroniza talentos SEM candidaturas (~470 talentos)

**Nota:** Sincronizações principais estão em `run_sync.py` (raiz) e `sync_incremental_completo.py` (raiz).

---

### `/webhooks` - Notificações Google Chat
Scripts para enviar notificações via webhook.

**Scripts principais:**
- `send_candidaturas_webhook.py` - Notifica após export de candidaturas

**Uso:**
```bash
python scripts/webhooks/send_candidaturas_webhook.py
```

---

### `/monitoring` - Monitoramento e Métricas
Scripts para monitoramento do sistema.

**Scripts principais:**
- `metrics_server.py` - Servidor Prometheus de métricas

**Uso:**
```bash
python scripts/monitoring/metrics_server.py
```

---

### `/migration` - Gerenciamento de Migrations
Scripts para executar migrations SQL.

**Scripts principais:**
- `run_migrations_direct.py` - Executa migrations via psycopg2

**Uso:**
```bash
python scripts/migration/run_migrations_direct.py
```

---

### `/analise` - Análises de Dados
Scripts de análise e geração de relatórios.

**Scripts principais:**
- `analise_funil_performance.py` - Análise de funil de candidaturas
- `analise_contratacoes_pretensao.py` - Análise de contratações vs pretensão

---

### `/backup` - Backup de Dados
Scripts de backup do banco de dados.

---

### `/cleanup` - Limpeza e Manutenção
Scripts de manutenção do banco.

**Scripts principais:**
- `deduplicate_position_timeline.py` - Remove duplicatas na timeline

---

### `/validacao` - Validações e Testes
Scripts de validação de dados e integridade.

---

### `/debug` - Debug e Troubleshooting

**IMPORTANTE:** Diretório deve estar vazio em produção.

**Subpasta:**
- `/archive_2026-08/` - Scripts de debug arquivados (80 arquivos)

---

## 🔧 Convenções

- Scripts Python seguem snake_case
- Cada script deve ter docstring explicativa
- Logs salvos em `logs/` (raiz do projeto)
- Credenciais via `.env` (nunca hardcoded)

---

## 📝 Uso Geral

Para executar qualquer script:

```bash
# Da raiz do projeto
python scripts/<categoria>/<script>.py

# Exemplo
python scripts/export/export_analise_posicoes.py
```

---

**Última atualização:** 2026-08-21
