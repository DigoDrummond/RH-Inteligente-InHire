# Investigação: Endpoint /referrals na API InHire

**Data:** 2026-02-06
**Objetivo:** Verificar se a API InHire possui endpoints específicos para dados detalhados de indicações/referrals

---

## RESUMO EXECUTIVO

✅ **A API InHire POSSUI endpoints de referrals, mas estão BLOQUEADOS para este tenant/usuário**

### Principais Descobertas

1. **6 endpoints de referrals existem** mas retornam `403 Forbidden` (sem permissão)
2. **3 endpoints retornam erro 500** (Server Error - possível problema de configuração)
3. **2 endpoints não existem** (404 Not Found)

---

## RESULTADOS DOS TESTES

### ✅ ENDPOINTS QUE EXISTEM (Status 403 - Forbidden)

| Endpoint | Método | Status | Descrição |
|----------|--------|--------|-----------|
| `/referrals` | POST | 403 | Referrals paginados |
| `/referrals/paginated` | POST | 403 | Referrals paginados |
| `/job-talents/referrals` | GET | 403 | Referrals de candidaturas |
| `/referral-program` | GET | 403 | Programa de indicação |
| `/referral-links` | GET | 403 | Links de indicação |
| `/referral-bonuses` | GET | 403 | Bônus de indicação |

**Interpretação:** Esses endpoints **EXISTEM** na API, mas:
- Requerem permissões especiais
- Podem estar bloqueados para o tenant atual
- Podem ser features premium/enterprise
- Podem estar em fase beta

### ⚠️ ENDPOINTS COM ERRO (Status 500 - Server Error)

| Endpoint | Método | Status | Descrição |
|----------|--------|--------|-----------|
| `/referrals` | GET | 500 | Lista de referrals |
| `/referrals/paginated` | GET | 500 | Referrals paginados |
| `/referrals/statistics` | GET | 500 | Estatísticas de indicação |

**Interpretação:** Endpoints existem mas:
- Podem não estar configurados no tenant
- Podem ter bug no servidor
- Podem requerer parâmetros específicos

### ❌ ENDPOINTS QUE NÃO EXISTEM (Status 404)

| Endpoint | Método | Status |
|----------|--------|--------|
| `/talents/referrals` | GET | 404 |
| `/jobs/referrals` | GET | 404 |

---

## INTERPRETAÇÃO DOS RESULTADOS

### 🎯 Programa de Indicações na InHire

**Status:** ✅ **EXISTE e está implementado na API**

**Evidências:**
1. Múltiplos endpoints específicos para referrals
2. Endpoints de programa, links e bônus
3. Campo `source` nas candidaturas com valores `referral`, `direct-referral`, `employee`

### 🔒 Acesso Bloqueado

**Razões possíveis:**

1. **Feature Premium/Enterprise**
   - Programa de indicações pode ser recurso pago
   - Tenant atual pode não ter acesso contratado

2. **Permissões de Usuário**
   - Service account atual pode não ter permissão
   - Requer role/permission específica

3. **Tenant não configurado**
   - Tenant pode não ter programa de indicações ativado
   - Configuração necessária no painel InHire

4. **Feature em Beta**
   - Recurso pode estar em desenvolvimento
   - Acesso restrito a clientes específicos

---

## DADOS ATUAIS DISPONÍVEIS

### ✅ O que TEMOS via campo `source`

| Informação | Status | Fonte |
|------------|--------|-------|
| Se é indicação | ✅ Sim | `candidaturas.source IN ('referral', 'direct-referral', 'employee')` |
| Canal de origem | ✅ Sim | `candidaturas.source` (18 valores únicos) |
| Quantidade de indicações | ✅ Sim | 2.040 candidaturas (2.5%) |
| Distribuição por tipo | ✅ Sim | referral: 1.440, direct-referral: 577, employee: 23 |

### ❌ O que NÃO TEMOS (bloqueado)

| Informação | Status | Endpoint bloqueado |
|------------|--------|-------------------|
| Quem indicou | ❌ Não | `/referrals` |
| Nome do indicador | ❌ Não | `/referrals` |
| Bônus de indicação | ❌ Não | `/referral-bonuses` |
| Status do bônus | ❌ Não | `/referral-bonuses` |
| Link usado | ❌ Não | `/referral-links` |
| Configuração do programa | ❌ Não | `/referral-program` |
| Estatísticas de indicação | ❌ Não | `/referrals/statistics` |

---

## PRÓXIMOS PASSOS

### 🔴 ALTA PRIORIDADE

#### 1. Contatar Suporte InHire

**Objetivo:** Solicitar acesso aos endpoints de referrals

**Perguntas para o suporte:**
- Os endpoints de referrals estão disponíveis para nosso tenant?
- Requerem permissões especiais ou upgrade de plano?
- Há documentação específica sobre o programa de indicações?
- Existe um processo de habilitação?

**Contato sugerido:**
- Email: suporte@inhire.app
- Documentação: https://docs.inhire.app (verificar se há seção sobre referrals)
- API Reference: Verificar se há docs dos endpoints bloqueados

#### 2. Verificar Configurações do Tenant

**Onde verificar:**
- Painel administrativo InHire
- Configurações do tenant
- Módulos/features habilitadas
- Permissões de usuários/service accounts

**O que procurar:**
- Módulo "Programa de Indicações" ou "Referral Program"
- Checkbox/toggle para habilitar indicações
- Configurações de bônus/recompensas
- Links de indicação configurados

#### 3. Testar com Usuário Diferente

**Ação:** Criar test account com role de admin e testar endpoints

**Razão:**
- Service account pode ter permissões limitadas
- Admin pode ter acesso total aos endpoints

### 🟡 MÉDIA PRIORIDADE

#### 4. Documentar Dados de Indicação Atuais

**O que já temos implementado:**
- ✅ Campo `source_candidato` na view (88.4% preenchido)
- ✅ Campo `is_referral` (boolean) na view
- ✅ 16 posições identificadas como indicação (1.9%)
- ✅ Análise de conversão por canal
- ✅ Exportação para Google Sheets

**Valor agregado:**
- Análise de ROI por canal
- Taxa de conversão de indicações vs outros canais
- Dashboard de performance de indicações
- Benchmark de canais de aquisição

#### 5. Monitorar Atualizações da API

**Ação:** Verificar periodicamente (mensal) se endpoints foram liberados

**Como:**
- Re-executar `testar_endpoint_referrals.py`
- Verificar changelog da API InHire
- Acompanhar release notes

### 🟢 BAIXA PRIORIDADE

#### 6. Considerar Campo Manual `referred_by`

**Se endpoints não forem liberados:**
- Adicionar campo `referred_by_name` na tabela talentos
- Adicionar campo `referred_by_employee` na tabela candidaturas
- Preenchimento manual via painel InHire ou planilha

**Prós:**
- Permite rastrear quem indicou
- Não depende da API
- Dados controlados internamente

**Contras:**
- Processo manual
- Maior chance de erro
- Não sincronizado automaticamente

---

## CONCLUSÃO

### 📊 Status Atual

| Aspecto | Status |
|---------|--------|
| **Endpoints existem?** | ✅ Sim (6 endpoints confirmados) |
| **Acesso liberado?** | ❌ Não (403 Forbidden) |
| **Dados básicos disponíveis?** | ✅ Sim (via campo `source`) |
| **Dados detalhados disponíveis?** | ❌ Não (bloqueados) |

### 🎯 Recomendação Final

**Curto prazo (já implementado):**
- ✅ Usar campo `source` para identificar indicações
- ✅ Analisar conversão por canal
- ✅ Dashboard de indicações básico

**Médio prazo (próximos passos):**
1. 🔴 **Contatar suporte InHire** para solicitar acesso aos endpoints
2. 🔴 **Verificar configurações** do tenant no painel InHire
3. 🟡 **Documentar decisão** após resposta do suporte

**Longo prazo (se endpoints forem liberados):**
1. Mapear schema completo dos endpoints de referrals
2. Criar tabela `referrals` no banco
3. Implementar sincronização de dados detalhados
4. Criar dashboard avançado de indicações

**Se endpoints não forem liberados:**
- Manter solução atual (campo `source`)
- Considerar campos manuais se necessário
- Monitorar futuras atualizações da API

---

## ANEXO: Detalhes Técnicos

### Teste Executado

```bash
python testar_endpoint_referrals.py
```

**Data:** 2026-02-06 21:47
**Tenant:** ca4e275d-e401-4c08-8a52-28b251a05840
**Usuário:** service-account-ca4e275d-e401-4c08-8a52-28b251a05840@inhire.app

### Endpoints Testados

Total: **11 endpoints**
- ✅ Existem (403): 6
- ⚠️ Erro (500): 3
- ❌ Não existem (404): 2

### Script de Teste

Arquivo: `testar_endpoint_referrals.py`

**Funcionalidade:**
- Autentica na API InHire
- Testa 11 variações de endpoints de referrals
- Classifica respostas (200, 403, 404, 500)
- Gera relatório detalhado

**Como executar novamente:**
```bash
python testar_endpoint_referrals.py
```

---

## VALOR AGREGADO SE ENDPOINTS FOREM LIBERADOS

### Análises Adicionais Possíveis

1. **Tracking de Indicadores**
   - Top indicadores (quem mais indica)
   - Taxa de conversão por indicador
   - Qualidade das indicações por pessoa

2. **ROI do Programa**
   - Custo de bônus vs custo de contratação
   - Tempo de fechamento de indicações
   - Taxa de aprovação de indicados

3. **Otimização do Programa**
   - Identificar melhores canais de divulgação
   - Ajustar bônus conforme performance
   - Gamificação do programa

4. **Compliance e Auditoria**
   - Rastreamento completo de pagamentos
   - Histórico de indicações
   - Relatórios para RH/Financeiro

---

**Status:** 🔴 **BLOQUEADO - AGUARDANDO CONTATO COM SUPORTE**
**Prioridade:** 🔴 **ALTA**
**Próxima ação:** Contatar suporte InHire para solicitar acesso aos endpoints de referrals
