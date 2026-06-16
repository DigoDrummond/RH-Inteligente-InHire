# Documentação das Views de Análise - InHire

**Data de Criação:** 2026-02-03
**Última Atualização:** 2026-02-03

## Resumo

Este documento descreve as views criadas para análise de dados de posições e contratações no sistema InHire. Foram criadas duas views principais para facilitar consultas e análises de dados.

---

## 1. View: `vw_posicoes_fechadas`

### Propósito
View consolidada com informações sobre posições fechadas/preenchidas e os talentos contratados.

### Dados Disponíveis
- **Total de registros:** 664 posições fechadas

### Colunas Principais

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `codigo_posicao` | String | Código da posição no InHire |
| `data_fechamento` | Date | Data em que a posição foi fechada/preenchida |
| `status_fechado` | String | Status final (closed, filled ou hired) |
| `nome_contratado` | String | Nome completo do talento contratado |
| `email_contratado` | String | E-mail do talento contratado |

### Colunas Adicionais

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `vaga_id` | BigInt | ID interno da vaga |
| `nome_vaga` | String | Nome da vaga |
| `area_vaga` | String | Área da vaga |
| `data_abertura` | DateTime | Data de abertura da posição |
| `dias_para_preencher` | Integer | Tempo em dias entre abertura e fechamento |
| `responsavel_contratacao` | String | Nome do responsável pela contratação |
| `created_at` | DateTime | Data de criação do registro |
| `updated_at` | DateTime | Data de última atualização |

### Filtros Aplicados
- Apenas posições com status: `filled`, `hired` ou `closed`
- Apenas posições com `hired_at` preenchido (data de contratação)
- Ordenado por `data_fechamento` (mais recentes primeiro)

### Exemplos de Uso

```sql
-- Ver todas as posições fechadas
SELECT * FROM vw_posicoes_fechadas;

-- Ver contratações do último mês
SELECT
    codigo_posicao,
    nome_vaga,
    nome_contratado,
    email_contratado,
    data_fechamento
FROM vw_posicoes_fechadas
WHERE data_fechamento >= CURRENT_DATE - INTERVAL '30 days';

-- Análise de tempo para preenchimento
SELECT
    nome_vaga,
    AVG(dias_para_preencher) as media_dias,
    MIN(dias_para_preencher) as minimo_dias,
    MAX(dias_para_preencher) as maximo_dias,
    COUNT(*) as total_contratacoes
FROM vw_posicoes_fechadas
WHERE dias_para_preencher IS NOT NULL
GROUP BY nome_vaga
ORDER BY total_contratacoes DESC;

-- Contratações por área
SELECT
    area_vaga,
    COUNT(*) as total_contratacoes
FROM vw_posicoes_fechadas
GROUP BY area_vaga
ORDER BY total_contratacoes DESC;
```

### Arquivos Relacionados
- **Migration SQL:** `migrations/018_create_view_posicoes_fechadas.sql`
- **Script de Criação:** `create_view_posicoes_fechadas.py`
- **Script de Teste:** `test_view.py`

---

## 2. View: `vw_analise_posicoes`

### Propósito
View consolidada para análise abrangente de posições, incluindo status, etapas do funil, prazos, clientes e métricas calculadas.

### Dados Disponíveis
- **Total de registros:** 1.385 posições

### Colunas de Identificação

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id_position` | BigInt | ID interno da posição |
| `codigo_posicao` | String | Código da posição no InHire |

### Colunas de Informação da Vaga

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `cargo` | String | Nome do cargo/vaga |
| `area_vaga` | String | Área da vaga |
| `cliente` | String | Nome do cliente |

### Colunas de Datas e Prazos

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `data_abertura` | Date | Data de abertura da requisição |
| `data_publicacao` | Date | Data de publicação da posição |
| `data_encerramento` | Date | Data de encerramento/última atualização |
| `prazo_processo_seletivo` | Integer | Prazo em dias (SLA configurado) |

### Colunas de Status

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `status_atual` | String | Status atual da posição (open, closed, paused, etc.) |
| `status_requisicao` | String | Status da requisição |
| `motivo_cancelamento_paralisacao` | JSONB | Metadados com motivo (se houver) |

### Colunas do Funil de Candidatos

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `etapa_funil` | String | Nome da última etapa do funil de candidatos |
| `id_etapa_funil` | Integer | Ordem/ID da etapa no funil |

### Métricas Calculadas

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `dias_em_aberto` | Integer | Número de dias que a posição está/esteve aberta |
| `indicador_prazo` | String | "Dentro do Prazo" ou "Fora do Prazo" |

### Outras Colunas

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `responsavel_posicao` | String | Nome do responsável pela posição |
| `quantidade_posicoes_requisicao` | Integer | Quantidade de posições na requisição |
| `created_at` | DateTime | Data de criação do registro |
| `updated_at` | DateTime | Data de última atualização |

### Lógica de CTEs (Common Table Expressions)

A view utiliza duas CTEs para otimizar as consultas:

1. **`ultima_etapa`**: Identifica a última etapa do funil para cada vaga
   - Agrupa por `vaga_id`
   - Ordena por `stage_order` DESC
   - Usa ROW_NUMBER() para pegar apenas a última

2. **`ultimo_status`**: Identifica o último status de cada posição
   - Agrupa por `posicao_id`
   - Ordena por `changed_at` DESC
   - Usa ROW_NUMBER() para pegar apenas o último

### Cálculos Implementados

#### Dias em Aberto
```sql
CASE
    WHEN us.changed_at IS NOT NULL
    THEN EXTRACT(DAY FROM (us.changed_at - COALESCE(r.requested_at, p.created_at_inhire)))
    ELSE EXTRACT(DAY FROM (CURRENT_DATE - COALESCE(r.requested_at, p.created_at_inhire)))
END AS dias_em_aberto
```

#### Indicador de Prazo
```sql
CASE
    WHEN v.sla_days_goal IS NOT NULL AND us.changed_at IS NOT NULL
    THEN CASE
        WHEN EXTRACT(DAY FROM (us.changed_at - COALESCE(r.requested_at, p.created_at_inhire))) <= v.sla_days_goal
        THEN 'Dentro do Prazo'
        ELSE 'Fora do Prazo'
    END
    WHEN v.sla_days_goal IS NOT NULL AND us.changed_at IS NULL
    THEN CASE
        WHEN EXTRACT(DAY FROM (CURRENT_DATE - COALESCE(r.requested_at, p.created_at_inhire))) <= v.sla_days_goal
        THEN 'Dentro do Prazo'
        ELSE 'Fora do Prazo'
    END
    ELSE NULL
END AS indicador_prazo
```

### Exemplos de Uso

#### 1. Análise de Posições Abertas
```sql
SELECT
    cargo,
    cliente,
    data_abertura,
    dias_em_aberto,
    prazo_processo_seletivo,
    indicador_prazo,
    etapa_funil
FROM vw_analise_posicoes
WHERE status_atual = 'open'
ORDER BY dias_em_aberto DESC;
```

#### 2. Posições Fora do Prazo
```sql
SELECT
    codigo_posicao,
    cargo,
    cliente,
    dias_em_aberto,
    prazo_processo_seletivo,
    responsavel_posicao
FROM vw_analise_posicoes
WHERE indicador_prazo = 'Fora do Prazo'
ORDER BY dias_em_aberto DESC;
```

#### 3. Análise por Cliente
```sql
SELECT
    cliente,
    COUNT(*) as total_posicoes,
    SUM(CASE WHEN status_atual = 'open' THEN 1 ELSE 0 END) as abertas,
    SUM(CASE WHEN status_atual = 'closed' THEN 1 ELSE 0 END) as fechadas,
    AVG(dias_em_aberto) as media_dias,
    SUM(CASE WHEN indicador_prazo = 'Fora do Prazo' THEN 1 ELSE 0 END) as fora_prazo
FROM vw_analise_posicoes
GROUP BY cliente
ORDER BY total_posicoes DESC;
```

#### 4. Distribuição por Status
```sql
SELECT
    status_atual,
    COUNT(*) as total,
    ROUND(AVG(dias_em_aberto), 2) as media_dias
FROM vw_analise_posicoes
GROUP BY status_atual
ORDER BY total DESC;
```

#### 5. Performance por Responsável
```sql
SELECT
    responsavel_posicao,
    COUNT(*) as total_posicoes,
    AVG(dias_em_aberto) as media_dias,
    SUM(CASE WHEN indicador_prazo = 'Dentro do Prazo' THEN 1 ELSE 0 END) as dentro_prazo,
    SUM(CASE WHEN indicador_prazo = 'Fora do Prazo' THEN 1 ELSE 0 END) as fora_prazo
FROM vw_analise_posicoes
WHERE responsavel_posicao IS NOT NULL
GROUP BY responsavel_posicao
ORDER BY total_posicoes DESC
LIMIT 20;
```

#### 6. Análise Temporal (Últimos 3 meses)
```sql
SELECT
    DATE_TRUNC('month', data_publicacao) as mes,
    COUNT(*) as total_publicadas,
    AVG(dias_em_aberto) as media_dias,
    COUNT(DISTINCT cliente) as clientes_distintos
FROM vw_analise_posicoes
WHERE data_publicacao >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY DATE_TRUNC('month', data_publicacao)
ORDER BY mes DESC;
```

#### 7. Análise do Funil
```sql
SELECT
    etapa_funil,
    id_etapa_funil,
    COUNT(*) as total_posicoes,
    AVG(dias_em_aberto) as media_dias
FROM vw_analise_posicoes
WHERE etapa_funil IS NOT NULL
GROUP BY etapa_funil, id_etapa_funil
ORDER BY id_etapa_funil;
```

### Arquivos Relacionados
- **Migration SQL:** `migrations/019_create_view_analise_posicoes.sql`
- **Script de Criação:** `create_view_analise_posicoes.py`

---

## Como Executar os Scripts

### Opção 1: Via PostgreSQL (psql)
```bash
# Para a view de posições fechadas
psql -U postgres -d inhire -f migrations/018_create_view_posicoes_fechadas.sql

# Para a view de análise de posições
psql -U postgres -d inhire -f migrations/019_create_view_analise_posicoes.sql
```

### Opção 2: Via Python
```bash
# Para a view de posições fechadas
python create_view_posicoes_fechadas.py

# Para a view de análise de posições
python create_view_analise_posicoes.py

# Para testar a view de posições fechadas
python test_view.py
```

---

## Estrutura de Dados

### Tabelas Base Utilizadas

As views fazem JOIN com as seguintes tabelas:

1. **posicoes** - Tabela principal de posições
2. **vagas** - Informações das vagas
3. **talentos** - Dados dos candidatos/talentos
4. **requisicoes** - Requisições de abertura de vagas
5. **clientes** - Informações dos clientes
6. **candidaturas** - Candidaturas dos talentos
7. **position_timeline** - Histórico de mudanças de status

### Relacionamentos

```
posicoes
├── INNER JOIN vagas (p.vaga_id = v.id)
├── LEFT JOIN talentos (p.talent_id = t.inhire_id)
├── LEFT JOIN requisicoes (r.job_inhire_id = v.inhire_id)
├── LEFT JOIN clientes (c.inhire_id = v.tenant_client_id)
└── LEFT JOIN position_timeline (via CTE ultimo_status)

candidaturas
└── Agregada em CTE ultima_etapa (por vaga_id)
```

---

## Próximos Passos Sugeridos

### 1. Análises Recomendadas

- [ ] **Análise de SLA por Cliente**: Identificar clientes com maior taxa de posições fora do prazo
- [ ] **Time to Hire**: Análise do tempo médio de contratação por área/cargo
- [ ] **Eficiência do Funil**: Análise das etapas onde há mais travamento
- [ ] **Análise de Sazonalidade**: Identificar padrões temporais nas contratações
- [ ] **Performance de Recrutadores**: Análise por responsável

### 2. Visualizações a Criar

- [ ] Dashboard de posições abertas vs fechadas
- [ ] Gráfico de evolução temporal (contratações por mês)
- [ ] Heatmap de SLA por cliente
- [ ] Funil de conversão por etapa
- [ ] Distribuição geográfica das contratações (se disponível)

### 3. Melhorias Futuras

- [ ] **Índices**: Criar índices para otimizar performance das views
- [ ] **Materialized Views**: Considerar transformar em materialized views para queries mais rápidas
- [ ] **Refresh Automático**: Implementar refresh automático das materialized views
- [ ] **Views Adicionais**:
  - View de métricas de candidatos
  - View de análise de diversidade
  - View de análise de salários (se disponível)
- [ ] **Alertas**: Implementar alertas para posições fora do prazo

### 4. Integrações

- [ ] Conectar com ferramenta de BI (PowerBI, Tableau, Metabase)
- [ ] Exportar dados para Google Sheets
- [ ] Criar API REST para acesso aos dados
- [ ] Implementar dashboards em tempo real

---

## Troubleshooting

### Problema: View não retorna dados
**Solução:** Verificar se as tabelas base têm dados:
```sql
SELECT COUNT(*) FROM posicoes;
SELECT COUNT(*) FROM vagas;
SELECT COUNT(*) FROM talentos;
```

### Problema: Performance lenta
**Soluções:**
1. Criar índices nas colunas de JOIN
2. Transformar em materialized view
3. Adicionar filtros nas queries (WHERE)
4. Limitar resultados com LIMIT

### Problema: Erro de coluna não encontrada
**Solução:** Verificar o schema das tabelas:
```sql
\d posicoes
\d position_timeline
```

---

## Contato e Suporte

Para dúvidas ou problemas:
- Verificar a documentação completa em `docs/`
- Consultar os scripts de exemplo neste documento
- Revisar os logs de sincronização em `logs/`

---

## Changelog

### 2026-02-03
- ✅ Criação da view `vw_posicoes_fechadas`
- ✅ Criação da view `vw_analise_posicoes`
- ✅ Documentação completa das views
- ✅ Scripts de criação e teste

---

## Referências

- **Documentação do Projeto**: `docs/PROJECT_STRUCTURE.md`
- **Schema do Banco**: `models/database.py`
- **API InHire**: `docs/ANALISE_ENDPOINTS_API_INHIRE.md`
