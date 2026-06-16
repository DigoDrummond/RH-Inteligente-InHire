/*
================================================================================
MIGRATION 071 - STEP 1: Dropar View Existente
================================================================================

IMPORTANTE: Executar este script PRIMEIRO antes do STEP 2

Este script remove a view vw_analise_posicoes para permitir a recriação
com as correções de SLA para posições pausadas.

Após executar este script, execute imediatamente o STEP 2.

================================================================================
*/

DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;
