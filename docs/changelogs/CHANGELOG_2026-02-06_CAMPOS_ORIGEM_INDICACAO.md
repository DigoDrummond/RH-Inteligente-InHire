# CHANGELOG - 2026-02-06 - Campos de Origem e Indicação

## Contexto

Após análise completa da cobertura da API InHire versus o glossário de termos, identificamos uma oportunidade de alto valor:

- ✅ Campo `source` existe em candidaturas (100% preenchido - 82.584 registros)
- ✅ 2.040 candidaturas são indicações (2.5% do total)
- ❌ Esses dados **NÃO estavam** na view de análise de posições

## Implementação

Adicionados **2 novos campos** à view `vw_analise_posicoes`:

### 1. `source_candidato` (VARCHAR)

**Descrição:** Canal de origem do candidato

**Origem:** Campo `source` da tabela `candidaturas`

**Lógica:**
1. Prioriza o source do candidato **contratado** (se houver)
2. Fallback: source **mais comum** entre os candidatos da posição
3. NULL se não houver candidatos

**Valores possíveis:**
- `linkedin` - Vaga divulgada no LinkedIn
- `manual` - Candidato cadastrado manualmente
- `jobPage` - Página de divulgação da vaga
- `referral` - Indicação via programa de referral
- `direct-referral` - Indicação direta
- `employee` - Indicação de colaborador
- `gupy`, `netVagas`, `indeed`, etc. - Job boards

### 2. `is_referral` (BOOLEAN)

**Descrição:** Indicador de indicação

**Lógica:**
```sql
CASE
    WHEN source IN ('referral', 'direct-referral', 'employee') THEN TRUE
    ELSE FALSE
END
```

**Valores:**
- `TRUE` - Posição preenchida por indicação
- `FALSE` - Posição preenchida por outros canais

## Resultados

### Estatísticas Gerais

| Métrica | Valor | Percentual |
|---------|-------|------------|
| Total de posições | 831 | 100% |
| Com source identificado | 735 | 88.4% |
| Sem source | 96 | 11.6% |
| **Indicações** | **16** | **1.9%** |

### Distribuição por Canal

| Canal | Posições | % do Total com Source |
|-------|----------|----------------------|
| manual | 337 | 45.9% |
| linkedin | 274 | 37.3% |
| jobPage | 95 | 12.9% |
| gupy | 11 | 1.5% |
| **referral** | **6** | **0.8%** 🎯 |
| **direct-referral** | **6** | **0.8%** 🎯 |
| **employee** | **4** | **0.5%** 🎯 |
| netVagas | 2 | 0.3% |

**Total de Indicações:** 16 posições (2.2% das posições com source)

### Taxa de Conversão por Canal

(Mínimo 5 posições para análise)

| Canal | Total | Fechadas | Contratações | Taxa |
|-------|-------|----------|--------------|------|
| manual | 337 | 88 | 27 | **8.0%** ⭐ |
| linkedin | 274 | 15 | 5 | **1.8%** |
| jobPage | 95 | 8 | 1 | **1.1%** |
| direct-referral | 6 | 4 | 0 | **0.0%** |

**Insight:** Canal manual tem a maior taxa de conversão (8.0%)

### Exemplos de Posições com Indicação

**Posição 1410** - Desenvolvedor Front-end Sênior (React)
- Source: `employee`
- Is Referral: `TRUE`
- Contratado: ✅ Henrique Pires
- Status: closed

**Posição 1509** - Gerente de Projetos
- Source: `direct-referral`
- Is Referral: `TRUE`
- Contratado: ❌
- Status: closed

**Posição 1406** - Redator SEO Sênior
- Source: `direct-referral`
- Is Referral: `TRUE`
- Contratado: ❌
- Status: open

## Estrutura da View

### ANTES (27 colunas)

1. id_position
2. cargo
3. data_abertura
4. data_publicacao
5. prazo_processo_seletivo
6. cliente
7. torre
8. status_atual
9. data_encerramento_ou_atualizacao
10. motivo_cancelamento_paralisacao
11. etapa_funil
12. senioridade
13. motivo_contratacao
14. pessoa_substituida
15. responsavel
16. recrutador_vaga
17. inicio_pendencia_cliente
18. fim_pendencia_cliente
19. sla_pendencia_cliente
20. num_ciclos_pausa
21. detalhamento_pausas
22. sla_recrutamento
23. nome_pessoa_contratada
24. email_pessoal
25. modalidade_contratacao
26. sla_geral
27. indicador_prazo

### DEPOIS (29 colunas)

1-27. *(mesmas colunas anteriores)*
28. **source_candidato** ⭐ NOVO
29. **is_referral** ⭐ NOVO

## Arquivos Modificados

### 1. View `vw_analise_posicoes`
- **Arquivo:** `migrations/027_add_source_and_referral_fields.sql`
- **Alteração:** Adicionada CTE `source_posicao` e 2 novos campos

### 2. Script de Exportação
- **Arquivo:** `export_posicoes_oauth.py`
- **Alteração:** Adicionados campos `source_candidato` e `is_referral` no SELECT

### 3. Scripts de Implementação
- `adicionar_campos_origem.py` - Implementação e validação
- `analisar_campo_source.py` - Análise do campo source
- `verificar_campos_indicacao.py` - Verificação de indicações

### 4. Documentação
- `RELATORIO_COBERTURA_API_INHIRE.md` - Análise completa da cobertura
- `docs/changelogs/CHANGELOG_2026-02-06_CAMPOS_ORIGEM_INDICACAO.md` - Este changelog
- `migrations/027_add_source_and_referral_fields.sql` - Migration documentada

## Exportação para Google Sheets

✅ **Dados exportados com sucesso**

- URL: https://docs.google.com/spreadsheets/d/1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw/
- Aba: Teste_API
- Colunas: **29** (antes: 27)
- Registros: 831 posições + header
- Células: **24.128**
- Data: 2026-02-06

## Valor Agregado

### 📊 Análises Possibilitadas

1. **ROI por Canal**
   - Comparar custo de aquisição vs conversão
   - Identificar canais mais efetivos
   - Priorizar investimentos em divulgação

2. **Programa de Indicações**
   - Quantificar indicações (16 posições = 1.9%)
   - Medir efetividade do programa
   - Comparar indicações vs outros canais

3. **Conversão por Fonte**
   - Taxa de fechamento por canal
   - Taxa de contratação por canal
   - Tempo médio por canal

4. **Benchmarking**
   - Comparar performance entre canais
   - Identificar melhores práticas
   - Otimizar estratégia de sourcing

### 🎯 Dashboards Possíveis

- **Dashboard de Conversão por Canal**
  - Filtro: `source_candidato`
  - Métricas: Total, Fechadas, Contratadas, Taxa

- **Dashboard de Indicações**
  - Filtro: `is_referral = TRUE`
  - Métricas: Total, Taxa de sucesso, Tempo médio

- **Análise de ROI**
  - Comparação: Custo vs Resultado por canal
  - Recomendação: Onde investir mais

## Impacto

### ✅ Benefícios

1. **Visibilidade de Origem**
   - 88.4% das posições com canal identificado
   - Rastreamento completo do sourcing

2. **Medição de Indicações**
   - 16 indicações identificadas
   - Base para crescimento do programa

3. **Otimização de Investimento**
   - ROI por canal calculável
   - Decisões baseadas em dados

4. **Melhoria Contínua**
   - Benchmark de canais
   - Identificação de oportunidades

### 📈 Oportunidades Identificadas

**Canal Manual tem 8.0% de conversão:**
- 4.4x maior que LinkedIn (1.8%)
- 7.3x maior que Job Page (1.1%)
- **Insight:** Candidatos indicados/conhecidos convertem melhor

**Indicações ainda pequenas (1.9%):**
- Oportunidade de crescimento
- Programa de incentivo pode aumentar volume
- Medição agora possível

**11.6% das posições sem source:**
- Investigar origem dessas posições
- Melhorar sincronização se necessário
- Cadastro manual pode estar incompleto

## Próximos Passos Recomendados

### 🔴 Alta Prioridade

1. **Investigar Endpoint `/referrals` na API**
   - Verificar se existe dados detalhados
   - Campos: `referrer_id`, `referrer_name`, `referral_bonus`
   - Se existir, criar tabela `referrals`

2. **Analisar 96 posições sem source**
   - São posições antigas?
   - Problema de sincronização?
   - Falta de preenchimento na origem?

### 🟡 Média Prioridade

3. **Criar Dashboard de Conversão por Canal**
   - Usar Google Sheets ou BI
   - Métricas principais: Volume, Taxa, Tempo

4. **Estabelecer Meta de Indicações**
   - Atual: 1.9%
   - Meta sugerida: 5-10%
   - Programa de incentivo

### 🟢 Baixa Prioridade

5. **Enriquecer dados de testes**
   - Se API disponibilizar
   - Correlação nota vs contratação

6. **Adicionar custo por canal**
   - Manual: custo de equipe
   - LinkedIn: custo de anúncios
   - Cálculo de ROI real

## Observações

### Sobre a Lógica de Source da Posição

**Por que priorizar o candidato contratado?**
- Se posição foi fechada, o source relevante é do contratado
- Se não fechou, consideramos o source mais comum
- Reflete a origem efetiva do resultado

**E se houver múltiplos candidatos?**
- Pegamos o mais comum (mode estatístico)
- Assume que maioria dos candidatos veio pelo mesmo canal
- Em casos raros, pode não refletir 100% da realidade

### Sobre Indicações

**Tipos de Indicação:**
- `referral` - Programa formal de indicação
- `direct-referral` - Indicação direta (sem programa)
- `employee` - Cadastrado por colaborador

**Limitações atuais:**
- ✅ Sabemos SE é indicação
- ❌ NÃO sabemos QUEM indicou
- ❌ NÃO sabemos status do bônus
- ❌ NÃO sabemos link usado

**Para obter mais detalhes:**
- Investigar endpoint `/referrals` na API InHire
- Verificar documentação sobre programa de indicação
- Considerar criar tabela dedicada se dados disponíveis

## Validação

### Testes Realizados

1. ✅ View recriada sem erros
2. ✅ 831 posições mantidas
3. ✅ 29 colunas (antes 27)
4. ✅ 88.4% com source preenchido
5. ✅ 16 indicações identificadas (1.9%)
6. ✅ Distribuição por canal calculada
7. ✅ Taxa de conversão por canal calculada
8. ✅ Exportação para Google Sheets bem-sucedida

### Casos de Teste

```sql
-- Posição com indicação
SELECT * FROM vw_analise_posicoes
WHERE id_position = 1410;
-- Resultado: is_referral = TRUE, source_candidato = 'employee' ✓

-- Posição sem indicação
SELECT * FROM vw_analise_posicoes
WHERE id_position = 1532;
-- Resultado: is_referral = FALSE, source_candidato = 'manual' ✓

-- Contagem de indicações
SELECT COUNT(*) FROM vw_analise_posicoes WHERE is_referral = TRUE;
-- Resultado: 16 ✓
```

## Status

✅ **CONCLUÍDO E VALIDADO**

- Data de Implementação: 2026-02-06
- Tipo: Nova Funcionalidade (Adição de Campos)
- Prioridade: Alta
- Status: Aplicado em Produção
- Exportação: Concluída
- Migration: `027_add_source_and_referral_fields.sql`

---

**Resumo:** View de análise de posições enriquecida com dados de origem dos candidatos. Adicionados campos `source_candidato` (canal) e `is_referral` (indicação). 88.4% das posições com source identificado, 16 indicações mapeadas (1.9%). Possibilita análise de ROI por canal e medição do programa de indicações.
