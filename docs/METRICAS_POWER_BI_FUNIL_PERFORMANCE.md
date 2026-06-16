# 📊 Métricas e Indicadores para Dashboard Power BI
## View: vw_funil_performance

---

## 🎯 **1. MÉTRICAS PRINCIPAIS (KPIs)**

### 1.1. Volume de Candidaturas
```DAX
Total Candidaturas = COUNT('Funil_API'[candidatura_id])
```

### 1.2. Taxa de Conversão Geral
```DAX
Taxa Conversão =
DIVIDE(
    COUNTROWS(FILTER('Funil_API', 'Funil_API'[foi_contratado] = 1)),
    COUNTROWS('Funil_API'),
    0
) * 100
```

### 1.3. Taxa de Rejeição
```DAX
Taxa Rejeição =
DIVIDE(
    COUNTROWS(FILTER('Funil_API', 'Funil_API'[foi_reprovado] = 1)),
    COUNTROWS('Funil_API'),
    0
) * 100
```

### 1.4. Taxa de Desistência
```DAX
Taxa Desistência =
DIVIDE(
    COUNTROWS(FILTER('Funil_API', 'Funil_API'[foi_desistente] = 1)),
    COUNTROWS('Funil_API'),
    0
) * 100
```

### 1.5. Tempo Médio no Processo
```DAX
Tempo Médio Processo = AVERAGE('Funil_API'[dias_no_processo])
```

---

## 📈 **2. ANÁLISE DO FUNIL**

### 2.1. Candidatos por Etapa
```DAX
Candidatos por Etapa =
SUMMARIZE(
    'Funil_API',
    'Funil_API'[etapa_funil],
    'Funil_API'[ordem_etapa],
    "Total", COUNT('Funil_API'[candidatura_id])
)
```

**Visualização**: Gráfico de funil vertical
- Eixo Y: Etapas (ordem_etapa)
- Valores: Total de candidatos
- Cores: Por status (ativo, rejeitado, desistente)

### 2.2. Taxa de Conversão por Etapa
```DAX
Conversão por Etapa =
VAR EtapaAtual = MAX('Funil_API'[etapa_funil])
VAR TotalEtapa = CALCULATE(
    COUNT('Funil_API'[candidatura_id]),
    'Funil_API'[etapa_funil] = EtapaAtual
)
VAR ProximaEtapa = CALCULATE(
    MIN('Funil_API'[ordem_etapa]),
    'Funil_API'[ordem_etapa] > MAX('Funil_API'[ordem_etapa])
)
VAR TotalProxima = CALCULATE(
    COUNT('Funil_API'[candidatura_id]),
    'Funil_API'[ordem_etapa] = ProximaEtapa
)
RETURN
DIVIDE(TotalProxima, TotalEtapa, 0) * 100
```

### 2.3. Drop-off por Etapa
```DAX
Drop Off = 100 - [Conversão por Etapa]
```

**Visualização**: Gráfico de cascata (Waterfall Chart)

---

## 👥 **3. ANÁLISE POR DIMENSÕES**

### 3.1. Performance por Recrutadora
```DAX
Candidaturas por Recrutadora =
SUMMARIZE(
    'Funil_API',
    'Funil_API'[recrutadora],
    "Total Candidaturas", COUNT('Funil_API'[candidatura_id]),
    "Contratações", COUNTROWS(FILTER('Funil_API', 'Funil_API'[foi_contratado] = 1)),
    "Taxa Conversão", DIVIDE(
        COUNTROWS(FILTER('Funil_API', 'Funil_API'[foi_contratado] = 1)),
        COUNT('Funil_API'[candidatura_id]),
        0
    ) * 100
)
```

**Visualização**:
- Gráfico de barras horizontais (ranking)
- Tabela com drill-down

### 3.2. Performance por Cliente
```DAX
Candidaturas por Cliente =
SUMMARIZE(
    'Funil_API',
    'Funil_API'[cliente],
    "Total Candidaturas", COUNT('Funil_API'[candidatura_id]),
    "Vagas Ativas", DISTINCTCOUNT('Funil_API'[vaga_id]),
    "Contratações", COUNTROWS(FILTER('Funil_API', 'Funil_API'[foi_contratado] = 1))
)
```

### 3.3. Performance por Torre
```DAX
Candidaturas por Torre =
SUMMARIZE(
    'Funil_API',
    'Funil_API'[torre],
    "Total", COUNT('Funil_API'[candidatura_id]),
    "% Total", DIVIDE(
        COUNT('Funil_API'[candidatura_id]),
        CALCULATE(COUNT('Funil_API'[candidatura_id]), ALL('Funil_API')),
        0
    ) * 100
)
```

**Visualização**: Gráfico de rosca (Donut Chart)

### 3.4. Performance por Área da Vaga
```DAX
Candidaturas por Área =
SUMMARIZE(
    'Funil_API',
    'Funil_API'[area_vaga],
    "Total", COUNT('Funil_API'[candidatura_id]),
    "Taxa Contratação", DIVIDE(
        COUNTROWS(FILTER('Funil_API', 'Funil_API'[foi_contratado] = 1)),
        COUNT('Funil_API'[candidatura_id]),
        0
    ) * 100
)
```

---

## 📅 **4. ANÁLISE TEMPORAL**

### 4.1. Candidaturas por Período
```DAX
Candidaturas por Mês =
SUMMARIZE(
    'Funil_API',
    "Ano", YEAR('Funil_API'[data_criacao_candidatura]),
    "Mês", MONTH('Funil_API'[data_criacao_candidatura]),
    "Total", COUNT('Funil_API'[candidatura_id]),
    "Contratações", COUNTROWS(FILTER('Funil_API', 'Funil_API'[foi_contratado] = 1))
)
```

**Visualização**: Gráfico de linhas com duplo eixo

### 4.2. Sazonalidade
```DAX
Média Mensal =
AVERAGEX(
    VALUES('Calendario'[Mês]),
    CALCULATE(COUNT('Funil_API'[candidatura_id]))
)
```

### 4.3. Tendência (YoY, MoM)
```DAX
Variação MoM =
VAR MesAtual = COUNT('Funil_API'[candidatura_id])
VAR MesAnterior = CALCULATE(
    COUNT('Funil_API'[candidatura_id]),
    DATEADD('Calendario'[Data], -1, MONTH)
)
RETURN
DIVIDE(MesAtual - MesAnterior, MesAnterior, 0) * 100
```

---

## ⏱️ **5. ANÁLISE DE TEMPO**

### 5.1. Tempo Médio por Etapa
```DAX
Tempo Médio Etapa =
AVERAGE('Funil_API'[dias_no_processo])
// Filtrar por etapa específica
```

### 5.2. Distribuição de Tempo
```DAX
Faixas Tempo =
SWITCH(
    TRUE(),
    'Funil_API'[dias_no_processo] <= 7, "0-7 dias",
    'Funil_API'[dias_no_processo] <= 15, "8-15 dias",
    'Funil_API'[dias_no_processo] <= 30, "16-30 dias",
    'Funil_API'[dias_no_processo] <= 60, "31-60 dias",
    "60+ dias"
)
```

**Visualização**: Histograma

### 5.3. SLA de Processo
```DAX
Dentro do SLA =
COUNTROWS(
    FILTER(
        'Funil_API',
        'Funil_API'[dias_no_processo] <= 30 // Definir SLA
    )
)

Taxa SLA = DIVIDE([Dentro do SLA], [Total Candidaturas], 0) * 100
```

---

## 🎯 **6. INDICADORES DE QUALIDADE**

### 6.1. Taxa de Ativação (Hunting → Inscrição)
```DAX
Taxa Ativação =
VAR Hunting = CALCULATE(
    COUNT('Funil_API'[candidatura_id]),
    'Funil_API'[etapa_funil] = "Hunting"
)
VAR Inscricao = CALCULATE(
    COUNT('Funil_API'[candidatura_id]),
    'Funil_API'[ordem_etapa] >= 3
)
RETURN
DIVIDE(Inscricao, Hunting, 0) * 100
```

### 6.2. Taxa de Aprovação Técnica
```DAX
Taxa Aprovação Técnica =
VAR EtapaTecnica = CALCULATE(
    COUNT('Funil_API'[candidatura_id]),
    'Funil_API'[etapa_funil] = "Etapa técnica | Talent IA"
)
VAR Aprovados = CALCULATE(
    COUNT('Funil_API'[candidatura_id]),
    'Funil_API'[etapa_funil] = "Etapa técnica | Talent IA",
    'Funil_API'[foi_reprovado] = 0
)
RETURN
DIVIDE(Aprovados, EtapaTecnica, 0) * 100
```

### 6.3. Taxa de Fechamento (Cliente → Contratação)
```DAX
Taxa Fechamento =
VAR BatePapoCliente = CALCULATE(
    COUNT('Funil_API'[candidatura_id]),
    'Funil_API'[etapa_funil] = "Bate Papo | Cliente"
)
VAR Contratados = CALCULATE(
    COUNT('Funil_API'[candidatura_id]),
    'Funil_API'[foi_contratado] = 1
)
RETURN
DIVIDE(Contratados, BatePapoCliente, 0) * 100
```

---

## 📊 **7. GRÁFICOS E DASHBOARDS SUGERIDOS**

### 7.1. Dashboard Executivo
**Componentes:**
1. **Card KPIs** (4 cards no topo):
   - Total Candidaturas
   - Taxa de Conversão
   - Tempo Médio Processo
   - Taxa de Rejeição

2. **Funil Visual** (centro):
   - Gráfico de funil com todas as etapas
   - Hover mostra taxa de conversão entre etapas

3. **Tendência Mensal** (linha do tempo):
   - Gráfico de linhas: Candidaturas vs Contratações
   - Filtro de período

4. **Top Performers** (lateral):
   - Top 5 Recrutadoras
   - Top 5 Clientes
   - Top 5 Talentos (candidatos ativos em múltiplas vagas)

### 7.2. Dashboard Operacional
**Componentes:**
1. **Distribuição por Etapa** (matriz):
   - Linhas: Etapas
   - Colunas: Status (Ativo, Rejeitado, Desistente)
   - Valores: Contagem

2. **Análise de Gargalos**:
   - Etapas com maior drop-off
   - Etapas com maior tempo médio

3. **Performance por Torre/Área**:
   - Matriz com drill-down
   - Heatmap de conversão

4. **Timeline de Processos**:
   - Gantt chart de candidaturas em andamento

### 7.3. Dashboard Estratégico
**Componentes:**
1. **Análise de Sazonalidade**:
   - Padrões mensais/semanais
   - Comparação YoY

2. **Benchmark de Recrutadoras**:
   - Scatter plot: Volume vs Taxa de Conversão
   - Quadrantes de performance

3. **Análise de Clientes**:
   - Matriz: Cliente vs Indicadores
   - Drill-through para detalhes

4. **Previsões**:
   - Forecast de candidaturas
   - Projeção de contratações

---

## 🔢 **8. MEDIDAS AVANÇADAS**

### 8.1. Índice de Eficiência de Recrutamento
```DAX
Índice Eficiência =
VAR TaxaConversão = [Taxa Conversão]
VAR TempoMédio = AVERAGE('Funil_API'[dias_no_processo])
VAR TaxaRejeição = [Taxa Rejeição]
RETURN
(TaxaConversão * 0.5) + ((100 - TempoMédio) * 0.3) + ((100 - TaxaRejeição) * 0.2)
```

### 8.2. Score de Qualidade do Funil
```DAX
Score Qualidade =
VAR AtivosNoFunil = COUNTROWS(FILTER('Funil_API', 'Funil_API'[esta_ativo] = 1))
VAR TotalCandidaturas = COUNT('Funil_API'[candidatura_id])
VAR TaxaAtivos = DIVIDE(AtivosNoFunil, TotalCandidaturas, 0)
VAR TaxaContratação = [Taxa Conversão] / 100
RETURN
(TaxaAtivos * 0.4) + (TaxaContratação * 0.6) * 100
```

### 8.3. NPS de Candidatos (se houver dados)
```DAX
// Requer campo de satisfação
NPS =
VAR Promotores = COUNTROWS(FILTER('Funil_API', 'Funil_API'[satisfacao] >= 9))
VAR Detratores = COUNTROWS(FILTER('Funil_API', 'Funil_API'[satisfacao] <= 6))
VAR Total = COUNT('Funil_API'[candidatura_id])
RETURN
((Promotores - Detratores) / Total) * 100
```

---

## 📋 **9. FILTROS E SLICERS RECOMENDADOS**

1. **Período**:
   - Últimos 30 dias
   - Últimos 3 meses
   - Últimos 6 meses
   - YTD
   - Custom

2. **Recrutadora** (multi-seleção)

3. **Cliente** (multi-seleção)

4. **Torre** (multi-seleção)

5. **Área da Vaga**

6. **Status**:
   - Ativo
   - Contratado
   - Rejeitado
   - Desistente

7. **Etapa do Funil**

---

## 🎨 **10. PALETA DE CORES SUGERIDA**

```
Sucesso (Contratado):    #4CAF50
Ativo (Em andamento):    #2196F3
Atenção (Desistente):    #FF9800
Erro (Rejeitado):        #F44336
Neutro:                  #9E9E9E
Principal (InHire):      #667eea
Secundária:              #764ba2
```

---

## 📦 **11. ESTRUTURA DE DADOS RECOMENDADA**

### Tabela Fato: Funil_API
- candidatura_id (PK)
- vaga_id (FK)
- talent_inhire_id (FK)
- data_criacao_candidatura (FK para Calendário)
- etapa_funil
- ordem_etapa
- status_candidatura
- foi_contratado
- foi_reprovado
- foi_desistente
- esta_ativo
- dias_no_processo
- recrutadora
- cliente
- torre
- area_vaga

### Tabela Dimensão: Calendario
- Data (PK)
- Ano
- Trimestre
- Mês
- Semana
- Dia Semana
- É Feriado

### Tabela Dimensão: Vagas
- vaga_id (PK)
- nome_vaga
- area_vaga
- torre
- cliente
- data_criacao_vaga
- data_encerramento_vaga

### Tabela Dimensão: Etapas_Funil
- ordem_etapa (PK)
- etapa_funil
- categoria (Triagem, Avaliação, Fechamento)

---

## 🚀 **12. ROADMAP DE IMPLEMENTAÇÃO**

### Fase 1: Fundação (Semana 1)
- [ ] Configurar fonte de dados (Google Sheets API ou export CSV)
- [ ] Criar modelo de dados no Power BI
- [ ] Implementar KPIs principais
- [ ] Dashboard Executivo básico

### Fase 2: Expansão (Semana 2)
- [ ] Dashboard Operacional
- [ ] Filtros e slicers
- [ ] Gráficos de funil
- [ ] Análise temporal

### Fase 3: Avançado (Semana 3)
- [ ] Dashboard Estratégico
- [ ] Medidas avançadas
- [ ] Benchmarks
- [ ] Alertas e notificações

### Fase 4: Otimização (Semana 4)
- [ ] Performance tuning
- [ ] Testes de usuário
- [ ] Ajustes de UX
- [ ] Documentação final

---

## 📞 **SUPORTE**

Para dúvidas sobre implementação ou métricas adicionais:
- Documentação view: `docs/VIEWS_ANALISE_POSICOES.md`
- Dados fonte: Planilha `Funil_API`
- Migration: `migrations/037_update_view_funil_performance.sql`
