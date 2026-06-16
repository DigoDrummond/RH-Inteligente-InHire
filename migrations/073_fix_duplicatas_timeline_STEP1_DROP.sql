/*
================================================================================
MIGRATION 073 - STEP 1: Dropar View Existente
================================================================================

IMPORTANTE: Executar este script PRIMEIRO antes do STEP 2

OBJETIVO DA MIGRATION 073:
  Corrigir duplicatas na tabela position_timeline que causam SLA negativo.

PROBLEMA IDENTIFICADO:
  - 3 posições com SLA negativo após Migrations 071 e 072
  - Posições: 782, 914, 1274
  - Eventos duplicados na position_timeline com:
    * Mesmo timestamp, IDs diferentes (ex: 3320/5355)
    * previous_status=NULL criando transições fantasmas
    * Múltiplos INICIO_PAUSA sem FIM_PAUSA correspondente
  - Resultado: períodos de pausa contados múltiplas vezes

EXEMPLO (Posição 782):
  - 8 eventos na timeline, 6 com sequências quebradas (75%)
  - Duplicatas: IDs 3320/5355, 3321/5356, 3322/5357
  - 3 períodos calculados = 64 dias
  - Esperado: 1 período = ~26 dias

SOLUÇÃO:
  Deduplicação conservadora usando DISTINCT ON:
  - Agrupa por: posicao_id, previous_status, new_status, DATE(changed_at)
  - Prioridade: eventos com notes > timestamp mais antigo > ID menor
  - Preserva mudanças legítimas de status

Após executar este script, execute imediatamente o STEP 2.

================================================================================
*/

DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;
