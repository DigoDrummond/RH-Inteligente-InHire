# Relatório de Investigação - 2026-02-13

## 1. Divergência: 120 vs 506 Posições Fechadas

### Problema Identificado
- **View `vw_analise_posicoes`**: mostra 120 posições com `status_atual='closed'`
- **Planilha externa (Acompanhamento Vagas)**: menciona 506 posições fechadas

### Investigação Realizada

#### Distribuição de Status (2024-2026)
```
Status      | Quantidade
------------|------------
canceled    | 496
closed      | 136
open        | 32
paused      | 13
archived    | 2
TOTAL       | 679
```

#### Posições por Ano
```
Ano  | Total | Status=closed | Com hired_at
-----|-------|---------------|-------------
2026 |   54  |      10       |     10
2025 |  289  |      51       |     51
2024 |  295  |      35       |     35
2023 |  111  |      11       |     11
2022 |   82  |      11       |     11
```

### Conclusão

**A combinação mais próxima de 506 é:**
- **496 posições com status "canceled"** (2024-2026)
- Diferença: apenas -10 posições

**Hipóteses:**
1. A planilha externa está contando posições "canceled" como "fechadas"
2. A view atual conta apenas posições "closed" (120 posições)
3. Possível diferença de 10 posições devido a:
   - Filtros adicionais na planilha externa
   - Posições de 2023 incluídas
   - Critérios de data diferentes (opened_at vs changed_at)

### Recomendação

**Definir critério claro de "posição fechada":**

**Opção 1: Apenas Contratadas**
```sql
hired_at IS NOT NULL
-- Resultado: 118 posições (todos os anos)
```

**Opção 2: Closed + Canceled**
```sql
status IN ('closed', 'canceled')
-- Resultado 2024-2026: 592 posições
```

**Opção 3: Apenas Closed**
```sql
status = 'closed'
-- Resultado 2024-2026: 136 posições (view mostra 120)
```

**Opção 4: Apenas Canceled** (mais próximo da planilha)
```sql
status = 'canceled'
-- Resultado 2024-2026: 496 posições (~506)
```

---

## 2. Análise de Custom Fields

### Resumo Geral
- **Requisições**: 18 campos únicos (739 array + 95 object)
- **Vagas**: 27 campos únicos (1166 registros)

### Campos Úteis de REQUISIÇÕES (ainda não utilizados)

#### Alta Prioridade (>400 registros)
| Campo | Qtd | Tipo | Exemplos | Utilidade |
|-------|-----|------|----------|-----------|
| **Área** | 834 | select | Operação, Financeiro | Classificação organizacional |
| **Senioridade** | 834 | select | Sênior, Pleno | Complementa senioridade da vaga |
| **Cliente** | 453 | select,text | Localiza, Localiza&CO | Nome do cliente final |
| **Torre** | 413 | select | Varejo e Finanças | Classificação estratégica |

#### Média Prioridade (300-400 registros)
| Campo | Qtd | Tipo | Exemplos | Utilidade |
|-------|-----|------|----------|-----------|
| **Sub-motivo da Requisição** | 381 | select | Não há, Cliente em prospecção | Detalhamento do motivo |
| **Empresa** | 381 | select | Framework, Rethink | **JÁ ADICIONADO (col 30)** |
| **Cliente Framework** | 381 | select | Syngenta, Pottencial | Cliente atendido pela Framework |
| **Cliente Rethink** | 381 | select | EDGE, NECTA | Cliente atendido pela Rethink |
| **Vertical** | 345 | select | Delivery, Product | Área de atuação |
| **Custo Hora (máximo)** | 345 | text | 47,50, R$ 119,50 | Limite de custo |

#### Campos Específicos
| Campo | Qtd | Utilidade |
|-------|-----|-----------|
| **Tipo de Serviço** | 31 | Alocação Gerenciada, Projeto |

### Campos Úteis de VAGAS (ainda não utilizados)

#### Alta Prioridade
| Campo | Qtd | Exemplos | Utilidade |
|-------|-----|----------|-----------|
| **Área** | 500 | Operação, Tecnologia | Área funcional da vaga |
| **Motivo de Congelamento** | 344 | N/A, Aguardando decisão | Rastreio de pausas |
| **Responsável** | 172 | Daniel Ricardo, Lidiane Alves | Gestor responsável |
| **Recrutador da vaga** | 172 | Dandara Ramalho, Jenyfer Carvalho | Recruiter atribuído |

#### Diversidade e Inclusão
| Campo | Qtd | Exemplos |
|-------|-----|----------|
| **Vaga PCD** | 172 | Apta, Não apta |
| **Vaga afirmativa** | 172 | Não, Sim |

#### Requisitos
| Campo | Qtd | Exemplos |
|-------|-----|----------|
| **Idioma** | 289 | Inglês avançado, N/A |
| **Certificação** | 289 | AWS, N/A |
| **Formação Acadêmica** | 289 | Superior completo, N/A |

#### Histórico
| Campo | Qtd | Exemplos |
|-------|-----|----------|
| **Cancelamento** | 172 | 18-03-2024 - Mudança de perfil |

### Campos Já Utilizados ✓

#### De Requisições (7 campos)
- Email do responsável por parte do cliente
- Modalidade de Contratação
- Time Rethink (Empresa)
- Tipo de Posição
- Custo Hora (ideal)
- Valor da venda
- Salário acordado com o talento

#### De Vagas (7 campos)
- Torre
- Motivo de Cancelamento
- Senioridade
- Modalidade de Contratação
- Gestor
- Se substituição, informar o nome do colaborador
- Tipo

---

## 3. SLAs - Correção Necessária

### Situação Atual (INCORRETO)
```sql
-- SLA Geral (dias corridos)
sla_geral = data_encerramento - data_publicacao

-- SLA Recrutamento (dias corridos)
sla_recrutamento = data_publicacao - data_abertura

-- SLA Pendência Cliente (dias corridos)
sla_pendencia_cliente = SUM(data_fim - data_inicio)
```

### Correção Necessária (dias úteis)

#### Regras Corretas:
```
sla_geral = data_encerramento_ou_atualizacao - data_publicacao
sla_pendencia_cliente = fim_pendencia_cliente - inicio_pendencia_cliente
sla_recrutamento = sla_geral - sla_pendencia_cliente
```

**IMPORTANTE:**
- Todos devem usar **dias úteis**
- Excluir feriados nacionais
- Excluir feriados municipais/estaduais de BH/MG

#### Tabela de Feriados
Já existe: `feriados` (criada na migration 030)

#### Função Necessária
Criar função para calcular dias úteis entre duas datas:
```sql
CREATE FUNCTION calcular_dias_uteis(
    data_inicio DATE,
    data_fim DATE
) RETURNS INTEGER
```

A função deve:
1. Contar apenas dias de segunda a sexta
2. Excluir sábados e domingos
3. Excluir feriados da tabela `feriados`

---

## 4. Campos Sugeridos para Próxima Migration

### Migration 050: Adicionar Campos Complementares

**Campos a Adicionar (ordem de prioridade):**

1. **Área** (de requisicoes.custom_fields)
   - 834 registros preenchidos
   - Complementa informação organizacional

2. **Cliente Framework / Cliente Rethink**
   - 381 registros cada
   - Identifica cliente final por empresa

3. **Vertical** (de requisicoes.custom_fields)
   - 345 registros
   - Área de atuação do projeto

4. **Custo Hora (máximo)**
   - 345 registros
   - Complementa informação de custo mínimo

5. **Vaga PCD** e **Vaga afirmativa** (de vagas.custom_fields)
   - 172 registros
   - Importante para diversidade e inclusão

6. **Motivo de Congelamento** (de vagas.custom_fields)
   - 344 registros
   - Rastreamento de posições pausadas

### Estrutura Recomendada

**Após email_pessoal (cols 27-29):**
- modalidade_contratacao_req (já existe - col 27)
- **area** (novo)
- **vertical** (novo)
- **cliente_framework** (novo)
- **cliente_rethink** (novo)

**No final (após tipo_posicao):**
- empresa (já existe - col 30)
- tipo_posicao (já existe - col 31)
- **custo_hora_maximo** (novo - col 32)
- **vaga_pcd** (novo - col 33)
- **vaga_afirmativa** (novo - col 34)
- **motivo_congelamento** (novo - col 35)

---

## 5. Próximos Passos

### Ação Imediata
1. ✅ **Corrigir cálculo de SLAs** (Migration 050)
   - Implementar função `calcular_dias_uteis()`
   - Atualizar view com SLAs corretos

2. ✅ **Adicionar campos complementares** (Migration 050)
   - Área, Vertical, Clientes, etc.

3. ✅ **Definir critério de "posição fechada"**
   - Ajustar view ou criar campo calculado

### Discussão Necessária
- **Critério de "posição fechada"**: qual usar?
  - Apenas `closed`? (136 posições)
  - `closed + canceled`? (592 posições)
  - Apenas `canceled`? (496 ~ 506 posições)

- **Campos prioritários**: quais adicionar primeiro?
  - Diversidade (PCD, afirmativa)?
  - Financeiro (custo hora máximo)?
  - Organizacional (área, vertical)?

---

## Anexos

### Queries Úteis

**Verificar posições "fechadas" (diversos critérios):**
```sql
-- Critério 1: Apenas contratadas
SELECT COUNT(*) FROM vw_analise_posicoes WHERE nome_pessoa_contratada IS NOT NULL;

-- Critério 2: Closed
SELECT COUNT(*) FROM vw_analise_posicoes WHERE status_atual = 'closed';

-- Critério 3: Closed + Canceled
SELECT COUNT(*) FROM vw_analise_posicoes WHERE status_atual IN ('closed', 'canceled');

-- Critério 4: Não abertas
SELECT COUNT(*) FROM vw_analise_posicoes WHERE status_atual NOT IN ('open', 'paused');
```

**Testar função get_custom_field_value:**
```sql
-- Requisição com array
SELECT
    id,
    get_custom_field_value(custom_fields, 'Área') as area,
    get_custom_field_value(custom_fields, 'Vertical') as vertical
FROM requisicoes
WHERE id = 29;

-- Requisição com object
SELECT
    id,
    get_custom_field_value(custom_fields, 'Área') as area,
    get_custom_field_value(custom_fields, 'Vertical') as vertical
FROM requisicoes
WHERE id = 811;
```
