# CHANGELOG - 2026-02-06 - Correção Indicador Prazo

## Problema Identificado

O campo `indicador_prazo` na view `vw_analise_posicoes` não estava sendo preenchido para todas as posições que tinham `sla_geral` calculado.

### Situação Anterior
- **831 posições** totais com `sla_geral` preenchido (100%)
- **638 posições** (76.8%) com `indicador_prazo` preenchido
- **193 posições** (23.2%) com `indicador_prazo` NULL (mesmo tendo `sla_geral`)

### Causa Raiz
A lógica do campo `indicador_prazo` só calculava o indicador quando a vaga tinha uma meta de prazo definida (`sla_days_goal` não NULL). Quando `sla_days_goal` era NULL, o campo ficava NULL mesmo havendo `sla_geral` calculado.

### Exemplo Reportado
**Posição 1532:**
- `prazo_processo_seletivo` (sla_days_goal): NULL
- `sla_geral`: 19 dias
- `indicador_prazo`: NULL ❌

## Solução Implementada

Modificada a lógica do campo `indicador_prazo` para preencher **todas** as posições:

### Lógica Antiga
```sql
CASE
    WHEN v.sla_days_goal IS NOT NULL
    THEN CASE
        WHEN (COALESCE(DATE(p.hired_at), CURRENT_DATE) - DATE(COALESCE(r.requested_at, p.opened_at))) <= v.sla_days_goal
        THEN 'Dentro do Prazo'
        ELSE 'Fora do Prazo'
    END
    ELSE NULL  -- ❌ Ficava NULL quando não havia meta
END AS indicador_prazo
```

### Lógica Nova
```sql
CASE
    WHEN v.sla_days_goal IS NOT NULL THEN
        CASE
            WHEN (COALESCE(DATE(p.hired_at), CURRENT_DATE) - DATE(COALESCE(r.requested_at, p.opened_at))) <= v.sla_days_goal
            THEN 'Dentro do Prazo'
            ELSE 'Fora do Prazo'
        END
    ELSE 'Sem Meta Definida'  -- ✅ Retorna "Sem Meta Definida" quando não há meta
END AS indicador_prazo
```

## Resultados

### Após Correção
- **831 posições** (100%) com `indicador_prazo` preenchido ✅
- **0 posições** (0%) com `indicador_prazo` NULL ✅

### Distribuição de Indicadores
- **Dentro do Prazo:** 58 posições (7.0%)
- **Fora do Prazo:** 580 posições (69.8%)
- **Sem Meta Definida:** 193 posições (23.2%)

### Posição 1532 (Exemplo Corrigido)
- `prazo_processo_seletivo`: NULL
- `sla_geral`: 19 dias
- `indicador_prazo`: "Sem Meta Definida" ✅

## Arquivos Modificados

1. **View `vw_analise_posicoes`**
   - Arquivo: `migrations/022_update_view_analise_posicoes_completa.sql` (será criada nova migration)
   - Alteração: Campo `indicador_prazo` com nova lógica

2. **Script de Correção**
   - Arquivo: `corrigir_indicador_prazo.py`
   - Função: Aplica a correção e valida os resultados

3. **Script de Análise**
   - Arquivo: `analisar_indicador_prazo.py`
   - Função: Diagnostica o problema antes da correção

## Exportação

Dados corrigidos exportados para Google Sheets:
- URL: https://docs.google.com/spreadsheets/d/1wo59dVv72jpbeyG95Lfp4jIoUhS_ILyqA96_Oe-9sYw/
- Aba: Teste_API
- Registros: 831 posições + header
- Células: 24.128 atualizadas

## Impacto

### Positivo
- ✅ 100% das posições agora têm indicador de prazo
- ✅ Visibilidade de quais vagas não têm meta definida
- ✅ Consistência: todas as posições com `sla_geral` têm `indicador_prazo`
- ✅ Facilita análises e filtros na planilha

### Sem Impacto Negativo
- Não altera o cálculo de `sla_geral`
- Não altera dados das posições que já tinham meta definida
- Apenas preenche o campo que estava NULL com informação útil

## Validação

### Testes Realizados
1. ✅ Verificação estatística (831/831 posições com indicador)
2. ✅ Validação da posição 1532 (exemplo reportado)
3. ✅ Exemplos de cada tipo de indicador
4. ✅ Exportação bem-sucedida para Google Sheets

### Casos de Teste
```
Posição 1532: Sem meta → "Sem Meta Definida" ✅
Posição 1539: SLA 13d, Meta 15d → "Dentro do Prazo" ✅
Posição 65: SLA 760d, Meta 15d → "Fora do Prazo" ✅
```

## Observações

1. **"Sem Meta Definida"** não é um erro - indica que a vaga foi criada sem `sla_days_goal`
2. O campo `sla_geral` continua sendo calculado normalmente mesmo sem meta
3. Filtros e análises agora podem usar `indicador_prazo` sem preocupação com NULLs
4. 23.2% das vagas não têm meta definida - pode indicar oportunidade de melhoria no processo de criação de vagas

## Próximos Passos Sugeridos

1. ✅ Criar migration SQL para documentar a mudança na view
2. ⏳ Considerar estabelecer meta padrão para vagas sem `sla_days_goal`
3. ⏳ Analisar por que 193 vagas não têm meta definida
4. ⏳ Atualizar documentação da view (VIEWS_ANALISE_POSICOES.md)

---

**Data:** 2026-02-06
**Autor:** Claude Code
**Tipo:** Correção de Bug
**Prioridade:** Alta
**Status:** ✅ Concluído e Exportado
