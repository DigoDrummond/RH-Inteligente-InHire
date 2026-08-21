# CHANGELOG - 2026-02-06 - Investigação de Endpoints de Referrals

## Contexto

Após implementar campos `source_candidato` e `is_referral` na view de análise de posições, identificamos que:
- 88.4% das posições têm source identificado
- 16 posições (1.9%) são indicações
- **MAS: Não temos dados detalhados** (quem indicou, bônus, etc.)

**Objetivo desta investigação:** Verificar se a API InHire possui endpoints específicos para dados detalhados de indicações.

---

## Ações Realizadas

### 1. Análise do Código Existente

**Arquivos verificados:**
- `services/api_client.py` - Métodos da API
- `models/api_schemas.py` - Schemas de dados
- `models/new_api_schemas.py` - Schemas novos
- `config.py` - Endpoints mapeados

**Resultado:** ❌ Nenhum endpoint ou schema de referrals mapeado

### 2. Teste Direto da API

**Script criado:** `testar_endpoint_referrals.py`

**Endpoints testados:** 11 variações
- `/referrals` (GET/POST)
- `/referrals/paginated` (GET/POST)
- `/talents/referrals`
- `/jobs/referrals`
- `/job-talents/referrals`
- `/referral-program`
- `/referral-links`
- `/referral-bonuses`
- `/referrals/statistics`

**Método:**
1. Autentica na API InHire
2. Testa cada endpoint
3. Classifica resposta: 200 (OK), 403 (Forbidden), 404 (Not Found), 500 (Error)

---

## Resultados

### ✅ ENDPOINTS EXISTEM!

**6 endpoints confirmados** (Status 403 - Forbidden):

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/referrals` | POST | Referrals paginados |
| `/referrals/paginated` | POST | Referrals paginados |
| `/job-talents/referrals` | GET | Referrals de candidaturas |
| `/referral-program` | GET | Programa de indicação |
| `/referral-links` | GET | Links de indicação |
| `/referral-bonuses` | GET | Bônus de indicação |

**Interpretação:**
- ✅ API InHire **TEM** endpoints de referrals
- ❌ **BLOQUEADOS** para o tenant/usuário atual
- ⚠️ Requerem permissões especiais ou feature premium

### ⚠️ Endpoints com Erro (Status 500)

3 endpoints retornam erro de servidor:
- GET `/referrals`
- GET `/referrals/paginated`
- GET `/referrals/statistics`

**Possíveis causas:**
- Endpoint existe mas não está configurado no tenant
- Requer parâmetros específicos
- Bug no servidor

### ❌ Endpoints que Não Existem (Status 404)

2 endpoints não existem:
- GET `/talents/referrals`
- GET `/jobs/referrals`

---

## Conclusão

### 🎯 Status do Programa de Indicações InHire

**A API InHire POSSUI programa de indicações implementado, mas o acesso está BLOQUEADO.**

**Evidências:**
1. 6 endpoints específicos de referrals
2. Endpoints de programa, links e bônus
3. Campo `source` nas candidaturas com valores de indicação

**Bloqueio:**
- Status 403 (Forbidden) indica falta de permissão
- Pode ser feature premium/enterprise
- Pode requerer habilitação no tenant

---

## Próximos Passos Definidos

### 🔴 ALTA PRIORIDADE (Ação Imediata)

#### 1. Contatar Suporte InHire ⏰ URGENTE

**Objetivo:** Solicitar acesso aos endpoints de referrals

**Perguntas:**
- Os endpoints de referrals estão disponíveis para nosso tenant?
- Requerem upgrade de plano ou permissões especiais?
- Há documentação específica sobre o programa?
- Como habilitar o acesso?

**Contato:**
- Email: suporte@inhire.app
- Docs: https://docs.inhire.app
- Mencionar endpoints específicos: `/referrals`, `/referral-program`, `/referral-bonuses`

#### 2. Verificar Configurações do Tenant

**Onde:**
- Painel administrativo InHire
- Configurações > Módulos/Features
- Permissões de usuários/service accounts

**O que procurar:**
- Módulo "Programa de Indicações"
- Toggle para habilitar indicações
- Configurações de bônus
- Links de indicação

#### 3. Testar com Usuário Admin

**Ação:** Criar test account com role de admin

**Razão:**
- Service account pode ter permissões limitadas
- Admin pode ter acesso completo aos endpoints

### 🟡 MÉDIA PRIORIDADE

#### 4. Investigar 96 Posições Sem Source (11.6%)

**Problema identificado:**
- 735 posições com source (88.4%)
- 96 posições sem source (11.6%)

**Investigar:**
- São posições antigas?
- Problema de sincronização?
- Falta de preenchimento na origem?
- Candidaturas sem source?

**Próxima ação:** Criar script de análise

### 🟢 BAIXA PRIORIDADE

#### 5. Monitorar Atualizações da API

**Frequência:** Mensal

**Como:**
- Re-executar `testar_endpoint_referrals.py`
- Verificar changelog da API InHire
- Acompanhar release notes

---

## Valor Agregado (SE Endpoints Forem Liberados)

### Dados Adicionais Disponíveis

| Dado | Disponível Hoje | Com Endpoints |
|------|-----------------|---------------|
| Se é indicação | ✅ Sim | ✅ Sim |
| Canal de origem | ✅ Sim | ✅ Sim |
| **Quem indicou** | ❌ Não | ✅ **SIM** |
| **Nome do indicador** | ❌ Não | ✅ **SIM** |
| **Bônus de indicação** | ❌ Não | ✅ **SIM** |
| **Status do bônus** | ❌ Não | ✅ **SIM** |
| **Link usado** | ❌ Não | ✅ **SIM** |

### Análises Possibilitadas

**Com acesso aos endpoints:**

1. **ROI do Programa**
   - Custo de bônus vs custo de contratação
   - Tempo de fechamento de indicações
   - Taxa de aprovação de indicados

2. **Top Indicadores**
   - Quem mais indica
   - Taxa de conversão por indicador
   - Qualidade das indicações

3. **Otimização**
   - Ajustar bônus conforme performance
   - Identificar melhores canais de divulgação
   - Gamificação do programa

4. **Compliance**
   - Rastreamento de pagamentos
   - Histórico completo
   - Relatórios para RH/Financeiro

---

## Impacto

### ✅ Situação Atual (Implementado)

**Dados disponíveis:**
- Campo `source_candidato` (88.4% cobertura)
- Campo `is_referral` (boolean)
- 16 indicações identificadas (1.9%)
- Análise de conversão por canal
- Dashboard básico de indicações

**Limitações:**
- ❌ Não sabemos QUEM indicou
- ❌ Não sabemos VALOR do bônus
- ❌ Não sabemos STATUS da indicação
- ❌ Não sabemos LINK usado

### 🎯 Situação Futura (Se Liberado)

**Dados completos:**
- ✅ Todos os dados atuais +
- ✅ Identificação do indicador
- ✅ Bônus e status
- ✅ Link de referral usado
- ✅ Histórico completo

**Análises avançadas:**
- ROI completo do programa
- Gamificação de indicadores
- Previsão de bônus
- Auditoria financeira

---

## Arquivos Criados/Modificados

### Novos Arquivos

1. **`testar_endpoint_referrals.py`**
   - Script de teste dos endpoints
   - Testa 11 variações de endpoints
   - Gera relatório detalhado
   - **Como executar:** `python testar_endpoint_referrals.py`

2. **`docs/INVESTIGACAO_ENDPOINT_REFERRALS.md`**
   - Relatório completo da investigação
   - Detalhamento dos resultados
   - Próximos passos definidos
   - Valor agregado se liberado

3. **`docs/changelogs/CHANGELOG_2026-02-06_INVESTIGACAO_REFERRALS.md`**
   - Este arquivo
   - Registro da investigação
   - Decisões tomadas

---

## Observações Técnicas

### Teste Realizado

**Data:** 2026-02-06 21:47
**Tenant:** ca4e275d-e401-4c08-8a52-28b251a05840
**Usuário:** service-account-ca4e275d-e401-4c08-8a52-28b251a05840@inhire.app

### Status HTTP Observados

| Status | Significado | Qtd |
|--------|-------------|-----|
| 200 | OK - Endpoint funciona | 0 |
| 403 | Forbidden - Sem permissão | 6 |
| 404 | Not Found - Não existe | 2 |
| 500 | Server Error - Erro no servidor | 3 |

### Interpretação dos Status

**403 (Forbidden):**
- Endpoint EXISTE
- Requer permissão especial
- Pode ser feature premium
- Pode estar desabilitado no tenant

**500 (Server Error):**
- Endpoint EXISTE
- Pode ter bug
- Pode requerer parâmetros
- Pode não estar configurado

**404 (Not Found):**
- Endpoint NÃO EXISTE
- Não implementado na API

---

## Decisão

### Status Atual: 🔴 BLOQUEADO

**Ação prioritária:** Contatar suporte InHire

**Timeline sugerido:**
- **Semana 1:** Contatar suporte + Verificar configurações do tenant
- **Semana 2:** Aguardar resposta do suporte
- **Semana 3:** Se liberado: implementar sincronização
- **Semana 3:** Se não liberado: manter solução atual

**Responsável:** Aguardando definição

---

## Status

✅ **INVESTIGAÇÃO CONCLUÍDA**

- Data: 2026-02-06
- Tipo: Investigação de API
- Prioridade: Alta
- Status: Endpoints identificados, acesso bloqueado
- Próxima ação: Contatar suporte InHire

---

**Resumo:** Investigação confirmou que a API InHire possui endpoints de referrals (/referrals, /referral-program, /referral-bonuses) mas o acesso está bloqueado (403 Forbidden). Próximo passo é contatar suporte InHire para solicitar habilitação. Enquanto isso, continuamos usando campo 'source' para análise básica de indicações (16 posições identificadas, 1.9% do total).
