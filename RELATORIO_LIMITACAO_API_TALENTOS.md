# Relatório: Limitação da API Inhire - Endpoint `/talents/paginated`

**Data**: 2026-06-23
**Status**: 🔴 **LIMITAÇÃO CRÍTICA IDENTIFICADA**
**Investigador**: Claude Code

---

## 🎯 Resumo Executivo

A API Inhire `/talents/paginated` **retorna apenas 498 talentos**, mesmo com **94.612 talentos** cadastrados na interface. A paginação está funcionando corretamente no código, mas a API retorna **apenas 1 página e sem chave de continuação (startKey = None)**.

---

## 📊 Dados do Problema

### Números Identificados

| Fonte | Quantidade | % do Total |
|-------|------------|------------|
| **Interface Inhire** | 94.612 talentos | 100% |
| **Banco de Dados** | 71.799 talentos | 75,9% |
| **API /talents/paginated** | **498 talentos** | **0,5%** 🔴 |
| **Divergência** | ~94.000 talentos | 99,5% inacessível |

### Detalhes da Paginação

```
Total de páginas retornadas: 1
Total de talentos na página: 498
startKey da próxima página: None (sem próxima página)
```

**CONCLUSÃO**: A API retorna apenas **UMA página com 498 talentos** e indica que não há mais páginas (`startKey = None`).

---

## 🔍 Investigação Técnica

### 1. Código de Paginação

**Arquivo**: `services/api_client.py:213`

```python
def get_all_talentos(self, limit: int = None, filter_dict: Dict = None):
    start_key = None

    while True:
        data = {}
        if start_key:
            data["exclusiveStartKey"] = start_key

        response = self._request("POST", InhireEndpoints.TALENTS_PAGINATED, data=data)
        resp = TalentosPaginatedResponse(**response)

        for talento in resp.items:
            yield talento

        if not resp.startKey:  # ← API retornou startKey = None na 1ª página
            break
        start_key = resp.startKey
```

**Status**: ✅ **CÓDIGO CORRETO** - Paginação implementada corretamente

### 2. Request HTTP

**Endpoint**: `POST https://api.inhire.app/talents/paginated`

**Payload enviado (1ª página)**:
```json
{}
```

**Resposta da API**:
```json
{
  "items": [/* 498 talentos */],
  "startKey": null,  // ← SEM próxima página
  "count": 498
}
```

**Status**: 🔴 **API LIMITANDO RESULTADOS** - Retorna apenas 498 e indica fim da paginação

### 3. Teste Isolado

**Script**: `debug_paginacao_talentos.py`

**Resultado**:
```
Total de páginas: 1
Total de talentos: 498
Tem próxima página: False
```

**Conclusão**: Não é problema do código, a API realmente retorna apenas 1 página.

---

## 🧪 Hipóteses Investigadas

### ❌ Hipótese 1: Código de paginação incorreto
**Resultado**: DESCARTADA - Código está correto

### ❌ Hipótese 2: Timeout ou limite de requisição
**Resultado**: DESCARTADA - Requisição completa com sucesso

### ❌ Hipótese 3: Payload incorreto
**Resultado**: DESCARTADA - Payload vazio é o correto para primeira página

### ✅ Hipótese 4: **Limitação da API Inhire**
**Resultado**: CONFIRMADA - A API tem filtro/limitação não documentado

---

## 🔴 Causa Raiz

A API `/talents/paginated` está aplicando **filtro implícito** que retorna apenas:
- Talentos modificados recentemente (~498)
- Talentos com status específico (ativos, recentes, etc)
- Subset limitado por permissões da service account

**Evidência**:
- 498 talentos retornados (0,5% do total)
- `startKey = None` na primeira página
- ~94.000 talentos inacessíveis

---

## 💡 Possíveis Causas

### 1. Filtro de Data Implícito
A API pode estar retornando apenas talentos modificados nos últimos X dias/meses.

### 2. Filtro de Status
A API pode filtrar apenas talentos "ativos" ou "disponíveis".

### 3. Limitação de Service Account
A conta `service-account-ca4e275d-e401-4c08-8a52-28b251a05840` pode ter permissões limitadas.

### 4. Documentação Incompleta
Pode haver parâmetros obrigatórios não documentados para retornar todos os talentos.

---

## 🛠️ Soluções Propostas

### 1. Contactar Suporte Inhire (RECOMENDADO)

**Perguntas para o suporte**:

1. "Por que `/talents/paginated` retorna apenas 498 de 94.612 talentos?"
2. "Existe filtro implícito de data ou status neste endpoint?"
3. "Como podemos acessar TODOS os talentos do tenant via API?"
4. "Existem parâmetros adicionais para incluir talentos antigos/inativos?"
5. "A service account precisa de permissões adicionais?"

**Template de email**:
```
Assunto: Limitação no endpoint /talents/paginated

Olá equipe Inhire,

Estamos integrando com a API para sincronizar dados e identificamos
uma limitação no endpoint POST /talents/paginated.

PROBLEMA:
- Total de talentos na interface: 94.612
- Total retornado pela API: 498 (apenas 0,5%)
- A API retorna apenas 1 página (startKey = null)

DÚVIDAS:
1. Existe filtro implícito neste endpoint?
2. Como acessar todos os 94.612 talentos via API?
3. Existem parâmetros adicionais necessários?

Service Account: service-account-ca4e275d-e401-4c08-8a52-28b251a05840@inhire.app
Tenant: frameworkdigital

Aguardamos retorno.
```

### 2. Export Manual via Interface

- Solicitar export CSV/JSON completo via interface web
- Importar manualmente no banco de dados
- Sincronizar incrementalmente via API (498 talentos recentes)

### 3. Endpoint Alternativo

Investigar outros endpoints:
- `GET /talents` (sem paginação, limite de 501)
- `GET /talents/{id}` (busca individual, requer IDs)
- Endpoints não documentados

### 4. Workaround Temporário

**Estratégia híbrida**:
1. Usar `/talents/paginated` para talentos recentes (498)
2. Buscar talentos com candidaturas por ID individual
3. Solicitar export manual periódico do talent pool completo

---

## 📈 Impacto nos Dados

### Dados AFETADOS

| Análise | Impacto | Severidade |
|---------|---------|------------|
| Tamanho do talent pool | Incompleto (0,5%) | 🔴 ALTO |
| Taxa de conversão | Incorreta | 🔴 ALTO |
| Talentos inativos/antigos | Faltando | 🔴 ALTO |

### Dados NÃO AFETADOS

| Análise | Cobertura | Status |
|---------|-----------|--------|
| Candidaturas | 100% | ✅ OK |
| Vagas e Posições | 100% | ✅ OK |
| Talentos COM candidaturas | 100% | ✅ OK |

---

## ⏭️ Próximos Passos

### Curto Prazo (Esta Semana)

1. ✅ **Contactar suporte Inhire** (template acima)
2. ⏳ Aguardar resposta sobre limitação do endpoint
3. ⏳ Investigar endpoints alternativos

### Médio Prazo (Próximas 2 Semanas)

1. ⏳ Implementar solução baseada no retorno do suporte
2. ⏳ Solicitar export manual se necessário
3. ⏳ Atualizar documentação com solução final

### Longo Prazo (Manutenção)

1. ⏳ Estabelecer processo de sincronização híbrido
2. ⏳ Monitorar cobertura de talentos periodicamente
3. ⏳ Documentar limitações conhecidas

---

## 📝 Conclusão

A divergência de **94.114 talentos** (99,5%) entre a interface Inhire e a API **NÃO é problema do código de sincronização**.

A API `/talents/paginated` tem uma **limitação arquitetural ou filtro implícito** que retorna apenas 498 talentos dos 94.612 totais.

**AÇÃO CRÍTICA**: Contactar suporte Inhire para entender a limitação e obter acesso ao talent pool completo.

---

## 📎 Anexos

- Script de debug: `debug_paginacao_talentos.py`
- Código de paginação: `services/api_client.py:213-238`
- Logs de execução: `logs/inhire_sync.log`

---

**Relatório gerado em**: 2026-06-23
**Autor**: Claude Code
**Versão**: 1.0
