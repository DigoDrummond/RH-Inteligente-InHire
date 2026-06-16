# Índice de Documentação - InHire Sync

**Última atualização:** 2026-02-06
**Versão do Sistema:** 1.3.0

## 🚀 Início Rápido

### Novo no Projeto?
1. Leia: **[README.md](README.md)** - Visão geral do sistema
2. Configure: Siga instruções de instalação no README
3. Execute: `python run_sync.py --incremental-complete`
4. Dashboard: Consulte **[DASHBOARD_FUNIL_README.md](DASHBOARD_FUNIL_README.md)**

### Dashboard de Funil v2 (Atualizado 02/12/2025)
- **📊 Guia Completo:** [DASHBOARD_FUNIL_README.md](DASHBOARD_FUNIL_README.md)
- **⏭️ Próximas Ações:** [PROXIMAS_ACOES_DASHBOARD.txt](PROXIMAS_ACOES_DASHBOARD.txt)
- **📄 Mudanças Recentes:** [docs/reports/RELATORIO_MUDANCAS_2025-12-02.md](docs/reports/RELATORIO_MUDANCAS_2025-12-02.md)
- **✨ Novidade:** 100% dos endpoints com filtro de mês implementado!

### 🔍 Views de Análise (NOVO - 03/02/2026)
- **📖 [README_VIEWS.md](../README_VIEWS.md)** - ⭐ Referência Rápida
- **📚 [VIEWS_ANALISE_POSICOES.md](VIEWS_ANALISE_POSICOES.md)** - Documentação Completa
- **📝 [CHANGELOG_2026-02-03_VIEWS_ANALISE.md](changelogs/CHANGELOG_2026-02-03_VIEWS_ANALISE.md)** - Log de Mudanças
- **✨ Views Disponíveis:**
  - `vw_posicoes_fechadas` - 664 contratações realizadas
  - `vw_analise_posicoes` - 1.385 posições com métricas de SLA

### 🎯 Investigações de Alta Prioridade (NOVO - 06/02/2026)
- **📊 [RELATORIO_FINAL_INVESTIGACAO_ALTA_PRIORIDADE.md](../RELATORIO_FINAL_INVESTIGACAO_ALTA_PRIORIDADE.md)** - ⭐ RELATÓRIO CONSOLIDADO
- **🔐 [INVESTIGACAO_ENDPOINT_REFERRALS.md](INVESTIGACAO_ENDPOINT_REFERRALS.md)** - Endpoints /referrals bloqueados
- **📉 [INVESTIGACAO_POSICOES_SEM_SOURCE.md](INVESTIGACAO_POSICOES_SEM_SOURCE.md)** - 96 posições sem source explicadas
- **🔍 [RELATORIO_COBERTURA_API_INHIRE.md](../RELATORIO_COBERTURA_API_INHIRE.md)** - Análise completa da cobertura da API
- **📝 [CHANGELOG_2026-02-06_CAMPOS_ORIGEM_INDICACAO.md](changelogs/CHANGELOG_2026-02-06_CAMPOS_ORIGEM_INDICACAO.md)** - Campos source_candidato e is_referral
- **📝 [CHANGELOG_2026-02-06_INVESTIGACAO_REFERRALS.md](changelogs/CHANGELOG_2026-02-06_INVESTIGACAO_REFERRALS.md)** - Investigação de endpoints
- **✨ Status:**
  - ✅ Campos `source_candidato` e `is_referral` implementados (88.4% cobertura)
  - 🔴 Endpoints `/referrals` existem mas bloqueados (403) - **AÇÃO: Contatar suporte InHire**
  - ✅ 96 posições sem source explicadas (sem candidatos - normal)

---

## Documentação Principal

### 📋 Status e Relatórios (docs/reports/)
- **[RELATORIO_MUDANCAS_2025-12-02.md](docs/reports/RELATORIO_MUDANCAS_2025-12-02.md)** - Mudanças em 02/12/2025 (MAIS RECENTE)
- **[STATUS_ATUAL.md](docs/reports/STATUS_ATUAL.md)** - Estado atual do sistema (27/11/2025)
- **[RESUMO_SESSAO_2025-11-27.md](docs/reports/RESUMO_SESSAO_2025-11-27.md)** - Resumo da sessão 27/11
- **[SCRIPTS_ANALISE_CORRECAO.md](docs/reports/SCRIPTS_ANALISE_CORRECAO.md)** - Guia de scripts
- **[COMANDOS_UTEIS.md](docs/reports/COMANDOS_UTEIS.md)** - Referência rápida de comandos
- **[INDICE_DOCUMENTACAO.md](docs/reports/INDICE_DOCUMENTACAO.md)** - Índice anterior

### 📖 Guias (docs/guides/)
- **Arquitetura do Sistema** - Visão geral da arquitetura
- **Guia de 3 Tipos de Sync** - Comparação entre tipos de sincronização
- **Deploy AWS** - Guia de deploy em produção

### 🔍 Análises (docs/analysis/)
- **Comparação de Sync** - Análise comparativa completa
- **Limitações** - Limitações do sync incremental

### 📝 Changelogs (docs/changelogs/)
- **[CHANGELOG_2026-02-06_INVESTIGACAO_REFERRALS.md](changelogs/CHANGELOG_2026-02-06_INVESTIGACAO_REFERRALS.md)** - Investigação de endpoints (06/02/2026) ⭐ NOVO
- **[CHANGELOG_2026-02-06_CAMPOS_ORIGEM_INDICACAO.md](changelogs/CHANGELOG_2026-02-06_CAMPOS_ORIGEM_INDICACAO.md)** - Campos de origem e indicação (06/02/2026) ⭐ NOVO
- **[CHANGELOG_2026-02-03_VIEWS_ANALISE.md](changelogs/CHANGELOG_2026-02-03_VIEWS_ANALISE.md)** - Views de Análise (03/02/2026)
- **[CHANGELOG_2025-11-27.md](changelogs/CHANGELOG_2025-11-27.md)** - Mudanças em 27/11/2025

### 📚 Documentação Técnica (docs/)
- **[README.md](docs/README.md)** - Índice da documentação técnica
- **[PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - Estrutura do projeto
- **[VIEWS_ANALISE_POSICOES.md](docs/VIEWS_ANALISE_POSICOES.md)** - Views de Análise ⭐ NOVO
- **[TROUBLESHOOTING_ENUM_DECLINED.md](docs/TROUBLESHOOTING_ENUM_DECLINED.md)** - Solução enum declined
- **[CORRECOES_2025-11-11.md](docs/CORRECOES_2025-11-11.md)** - Correções anteriores

### 📦 Arquivo (docs/archive/)
Documentação desatualizada ou de sessões específicas:
- **ESTADO_ATUAL_PROJETO.md** (19/11/2025 - substituído por STATUS_ATUAL)
- **LEIA-ME_PRIMEIRO_2025-11-27.md** (guia específico de sessão)
- **EXECUTAR_MIGRATIONS.md** (processo antigo)
- **analise_talentos_api.md** (análise antiga)
- Documentos movidos em 02/12/2025 durante limpeza do projeto

### 🗑️ Deprecated (deprecated/)
Arquivos obsoletos movidos durante limpeza (02/12/2025):
- **scripts_antigos/** - Scripts Python não mais utilizados (temp_*, debug_*, test_*)
- **documentos_obsoletos/** - Documentos antigos (correções antigas, bugs, explorações)
- **arquivos_teste/** - Arquivos de teste temporários

---

## Estrutura do Projeto

```
Inhire/
├── README.md                           ← COMECE AQUI
├── DOCUMENTATION_INDEX.md              ← Este arquivo
│
├── docs/                               ← Documentação
│   ├── README.md                       ← Índice documentação técnica
│   ├── reports/                        ← Status e relatórios
│   ├── guides/                         ← Guias de uso
│   ├── analysis/                       ← Análises técnicas
│   ├── changelogs/                     ← Histórico de mudanças
│   ├── archive/                        ← Documentação antiga
│   └── notes/                          ← Anotações
│
├── dashboard/                          ← Dashboard V2
│   ├── docs/                           ← Documentação do dashboard
│   │   ├── DASHBOARD_START_HERE.md
│   │   ├── DASHBOARD_V2_INDEX.md
│   │   └── TODO_DASHBOARD_V2.md
│   ├── *.html                          ← Páginas do dashboard
│   └── *.js, *.css                     ← Assets
│
├── scripts/                            ← Scripts auxiliares
│   ├── README.md                       ← Documentação de scripts
│   ├── diagnostics/                    ← Scripts de diagnóstico
│   ├── maintenance/                    ← Scripts de manutenção
│   ├── utilities/                      ← Utilitários
│   └── sql/                            ← Scripts SQL
│
├── tests/                              ← Testes
├── relatorios/                         ← Relatórios gerados
├── models/                             ← Modelos de dados
├── services/                           ← Serviços
├── utils/                              ← Utilitários
└── logs/                               ← Arquivos de log
```

---

## Fluxos Comuns

### Sincronização de Dados
```bash
# 1. Status atual
python scripts/utilities/check_sync_status.py

# 2. Sincronização completa
python run_sync.py --full

# 3. Sincronização incremental
python run_sync.py --incremental

# 4. Verificar resultado
python scripts/diagnostics/verificar_funil_completo.py
```

### Correção de Dados
```bash
# Corrigir FK talento_id
python scripts/maintenance/fix_candidatura_talento_id.py

# Padronizar nomes de etapas
python scripts/maintenance/padronizar_stage_names_fixed.py
```

### Análise de Dados
```bash
# Análise do funil
python relatorios/analise_funil_kanban.py

# Verificação completa
python relatorios/verificar_funil_completo.py
```

### Dashboard
```bash
# Iniciar backend
python dashboard_api.py

# Abrir dashboard
start dashboard/index.html
```

---

## Comandos SQL Úteis

### Estatísticas Gerais
```sql
SELECT
    'Vagas' as entidade, COUNT(*) as total FROM vagas
UNION ALL SELECT 'Posições', COUNT(*) FROM posicoes
UNION ALL SELECT 'Candidaturas', COUNT(*) FROM candidaturas
UNION ALL SELECT 'Talentos', COUNT(*) FROM talentos;
```

### Últimas Sincronizações
```sql
SELECT sync_type, sync_entity, status, start_time, records_processed
FROM sync_log
ORDER BY start_time DESC
LIMIT 10;
```

### Status do Funil
```sql
SELECT
    status,
    COUNT(*) as total,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentual
FROM candidaturas
GROUP BY status
ORDER BY total DESC;
```

---

## Problemas Conhecidos

### 1. Sync de Talentos (RESOLVIDO)
- **Problema:** Erro `url NOT NULL` em talento_arquivos
- **Solução:** Aplicar migration em docs/archive/EXECUTAR_MIGRATIONS.md
- **Status:** ✅ Resolvido

### 2. Candidaturas Órfãs (0.4%)
- **Problema:** 330 candidaturas sem talento_id
- **Causa:** Talentos deletados da API
- **Impacto:** Baixo (0.4% dos dados)
- **Ação:** Documentado em STATUS_ATUAL.md

### 3. Etapas com Múltiplas Ordens
- **Problema:** Mesma etapa em diferentes posições
- **Causa:** Comportamento intencional da API
- **Impacto:** Análises de conversão linear mais complexas
- **Ação:** Aceitar ou criar view com ordem canônica

---

## Recursos Adicionais

### Scripts Principais
- **run_sync.py** - Sincronização principal
- **scheduler.py** - Agendador automático
- **dashboard_api.py** - API do dashboard
- **config.py** - Configurações centralizadas

### Logs
- **logs/inhire_sync.log** - Log principal do sistema
- **logs/inhire_sync_backup_YYYYMMDD.log** - Backups de logs

### Configuração
- **.env** - Variáveis de ambiente (não versionado)
- **.env.example** - Template de configuração
- **.gitignore** - Arquivos ignorados pelo Git
- **requirements.txt** - Dependências Python

---

## Manutenção

### Backups
- Logs são arquivados automaticamente
- Banco de dados: usar `pg_dump` manualmente
- Backups salvos em `database_backups/`

### Limpeza
- Cache Python: removido automaticamente
- Logs antigos: arquivados em `logs/`
- Relatórios temporários: salvos em `relatorios/`

---

## Contribuindo

### Adicionar Nova Documentação
1. Determine a categoria (reports, guides, analysis)
2. Crie o arquivo na pasta apropriada
3. Atualize este índice (DOCUMENTATION_INDEX.md)
4. Atualize docs/README.md se for documentação técnica

### Arquivar Documentação Antiga
1. Mova para `docs/archive/`
2. Adicione data ao nome do arquivo
3. Atualize referências
4. Documente em changelog

---

## Suporte

### Para Problemas
1. Verificar logs: `logs/inhire_sync.log`
2. Consultar: `docs/reports/STATUS_ATUAL.md`
3. Executar diagnóstico: `python scripts/diagnostics/`
4. Consultar troubleshooting em docs/

### Recursos
- **Documentação InHire API:** (verificar docs/)
- **PostgreSQL:** localhost:5432/inhire
- **Dashboard:** http://localhost:5000 (API) + dashboard/index.html

---

**Última revisão:** 2026-02-06
**Responsável:** Sistema de Documentação Automatizado
**Versão:** 1.3.0 (investigação de alta prioridade: endpoints /referrals + posições sem source)
