# Documentação da Sincronização de Posições - Para Discussão com InHire

## 1. Como Funciona a Sincronização de Posições

### 1.1 Fluxo Geral

```
┌─────────────┐
│   API       │
│  InHire     │  ──────> GET /jobs/positions/paginated/{job_id}
└─────────────┘
      │
      ├─> Parâmetros: ?limit=50&startKey=xxx (paginação)
      ├─> Headers: Authorization: Bearer {token}
      │
      v
┌─────────────┐
│   Sistema   │
│   Python    │  ──────> Processa e valida dados
└─────────────┘
      │
      v
┌─────────────┐
│  Banco de   │
│   Dados     │  ──────> Armazena na tabela 'posicoes'
└─────────────┘
```

---

## 2. Endpoint da API Usado

### 2.1 Endpoint de Posições
```
URL: https://api.inhire.app/jobs/positions/paginated/{job_id}
Método: GET
Autenticação: Bearer Token (obrigatório)
```

### 2.2 Parâmetros da Requisição
```python
params = {
    "limit": 50,              # Número de registros por página
    "startKey": "xxx"         # Chave para próxima página (opcional)
}
```

### 2.3 Exemplo de Requisição Real
```bash
GET https://api.inhire.app/jobs/positions/paginated/d6f7c052-7d70-43b7-a704-e98f77decd61?limit=50
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
Content-Type: application/json
```

---

## 3. Estrutura da Resposta Esperada

### 3.1 Formato JSON da API
```json
{
  "results": [
    {
      "id": "position-uuid-123",
      "status": "open",
      "requisitionId": "req-456",
      "createdAt": "2025-01-10T10:00:00Z",
      "updatedAt": "2025-01-12T14:00:00Z"
    }
  ],
  "startKey": "next-page-key-or-null"
}
```

### 3.2 Campos Importantes
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | String | ID único da posição (UUID) |
| `status` | String | Status da posição (`"open"`, `"closed"`, etc) |
| `requisitionId` | String | ID da requisição associada |
| `createdAt` | ISO DateTime | Data/hora de criação |
| `updatedAt` | ISO DateTime | Data/hora da última atualização |

---

## 4. Código de Sincronização (Localização e Lógica)

### 4.1 Arquivo Principal
**Arquivo:** `services/sync_service.py`

### 4.2 Método de Sincronização INCREMENTAL de Posições
**Método:** `_sync_posicoes_incremental()` (linha 900)

```python
def _sync_posicoes_incremental(self) -> Dict:
    """
    Sincroniza apenas posições com status='open' e updated_at mais recente que o BD
    """

    # PASSO 1: Buscar vagas abertas do banco local
    vagas = self.session.query(Vaga).filter_by(status='open').all()

    # PASSO 2: Para cada vaga, buscar posições da API
    for vaga in vagas:

        # PASSO 2.1: Chamar API
        for posicao_api in self.api_client.get_all_posicoes(vaga.inhire_id):

            # FILTRO 1: Apenas posições ABERTAS
            if posicao_api.status and posicao_api.status.lower() != 'open':
                stats['skipped'] += 1
                continue

            # PASSO 2.2: Buscar posição no BD
            posicao_bd = self.session.query(Posicao).filter_by(
                inhire_id=posicao_api.id
            ).first()

            # PASSO 2.3: Decidir ação
            if not posicao_bd:
                # Não existe no BD → CRIAR
                self.db.upsert_posicao(posicao_api)
                stats['created'] += 1

            else:
                # Existe no BD → COMPARAR DATAS
                if posicao_api.updatedAt > posicao_bd.updated_at_inhire:
                    # API mais recente → ATUALIZAR
                    self.db.upsert_posicao(posicao_api)
                    stats['updated'] += 1
                else:
                    # BD igual ou mais recente → IGNORAR
                    stats['skipped'] += 1

    return stats
```

---

## 5. Critérios de Filtragem

### 5.1 Filtros Aplicados PELO NOSSO CÓDIGO

```python
# FILTRO 1: Status da vaga
vagas = session.query(Vaga).filter_by(status='open').all()
# ✓ Apenas vagas com status='open'

# FILTRO 2: Status da posição
if posicao_api.status and posicao_api.status.lower() != 'open':
    skip()
# ✓ Apenas posições com status='open'

# FILTRO 3: Comparação de datas
if posicao_api.updatedAt > posicao_bd.updated_at_inhire:
    update()
# ✓ Atualiza apenas se API tem versão mais recente
```

### 5.2 Filtros NÃO Aplicados pela API

⚠️ **IMPORTANTE:** A API **NÃO** filtra por status automaticamente!

```python
# A API retorna TODAS as posições da vaga
# O filtro por status='open' é feito PELO NOSSO CÓDIGO
```

---

## 6. Divergências Encontradas

### 6.1 Resumo das Divergências
```
API:   18 posições abertas
Banco: 22 posições abertas
Diferença: 4 posições a mais no banco
```

### 6.2 Vagas Específicas com Divergência

| Vaga | API | BD | Diferença |
|------|-----|-----|-----------|
| People Manager | 0 | 1 | -1 |
| Tech Lead React | 0 | 1 | -1 |
| Desenvolvedor Angular - Pleno | 0 | 1 | -1 |
| UX Designer - Sênior | 0 | 1 | -1 |

---

## 7. Possíveis Causas das Divergências

### 7.1 Hipótese 1: API não retorna posições fechadas recentemente
```
Cenário:
1. Posição foi fechada na InHire (status alterado para "closed")
2. API deixou de retornar essa posição
3. BD ainda tem a posição com status "open" (não foi atualizada)

Solução: Sincronização deveria marcar posições ausentes como fechadas
```

### 7.2 Hipótese 2: Filtro de status case-sensitive
```python
# Nosso código verifica:
if posicao_api.status.lower() != 'open':

# Mas a API pode retornar variações:
# "open", "Open", "OPEN", "active", etc.

Solução: Verificar valores exatos que a API retorna
```

### 7.3 Hipótese 3: Paginação incompleta
```
Cenário:
1. API tem bug de paginação
2. Algumas posições não são retornadas em nenhuma página
3. BD mantém posições que existiam antes

Solução: Verificar se startKey está funcionando corretamente
```

### 7.4 Hipótese 4: Delay na sincronização
```
Cenário:
1. Posições foram fechadas há < 24h
2. Sincronização incremental não capturou mudança
3. BD ainda mostra como "open"

Solução: Verificar timestamps de updated_at
```

---

## 8. Perguntas para a InHire

### 8.1 Sobre o Endpoint
```
1. O endpoint /jobs/positions/paginated/{job_id} retorna TODAS as posições
   da vaga ou apenas as abertas?

2. Existe algum parâmetro para filtrar por status na API?
   Exemplo: ?status=open

3. A paginação está funcionando corretamente? O startKey retorna todas
   as páginas?
```

### 8.2 Sobre Status de Posições
```
4. Quais são os valores possíveis para o campo "status" de uma posição?
   Valores conhecidos: "open", "closed", ???

5. O status é case-sensitive? "open" vs "Open" vs "OPEN"?

6. Quando uma posição é fechada, ela ainda aparece no endpoint ou
   é removida completamente?
```

### 8.3 Sobre Sincronização
```
7. Existe algum delay entre fechar uma posição na InHire e ela aparecer
   como fechada na API?

8. O campo "updatedAt" é atualizado quando o status muda?

9. Posições podem ser deletadas permanentemente ou sempre mantém histórico?
```

---

## 9. Como Testar e Validar

### 9.1 Teste Manual - Posição Específica

Para uma das 4 vagas divergentes, fazer:

```bash
# 1. Verificar na interface InHire:
# - Quantas posições abertas existem?
# - Quais os IDs dessas posições?

# 2. Verificar no BD:
SELECT id, inhire_id, status, updated_at_inhire
FROM posicoes
WHERE vaga_id = (SELECT id FROM vagas WHERE inhire_id = 'job-id-aqui')
  AND status = 'open';

# 3. Verificar na API (usar debug_posicoes.py):
python debug_posicoes.py
# Escolher opção 1, informar job_id

# 4. Comparar os 3 resultados:
# Interface InHire  vs  BD  vs  API
```

### 9.2 Exemplo Prático - People Manager

```
Job ID: 5f8ec764-69f0-4d09-870d-369cdce5d183

Verificações:
1. ✓ Interface InHire mostra: ___ posições abertas
2. ✓ Banco de dados tem: 1 posição aberta
3. ✓ API retorna: 0 posições abertas

Conclusão possível:
- Se interface mostra 0: BD está desatualizado
- Se interface mostra 1: API não está retornando a posição
```

---

## 10. Código para Debug

### 10.1 Script Criado: `debug_posicoes.py`
```python
# Execução:
python debug_posicoes.py

# Opção 1: Testar vaga específica
# - Informa job_id
# - Mostra: URL, headers, params, response completa

# Opção 2: Testar 5 vagas automaticamente
```

### 10.2 Script Criado: `comparar_posicoes_abertas.py`
```python
# Execução:
python comparar_posicoes_abertas.py

# Output:
# - Extrai posições da API para TODAS as vagas abertas
# - Extrai posições do BD
# - Compara e gera relatório JSON completo
# - Identifica divergências
```

---

## 11. Dados Reais para Discussão

### 11.1 Exemplo de Requisição Real
```
Vaga: People Manager
Job ID: 5f8ec764-69f0-4d09-870d-369cdce5d183

Requisição feita:
GET https://api.inhire.app/jobs/positions/paginated/5f8ec764-69f0-4d09-870d-369cdce5d183?limit=50

Resposta:
{
  "results": [],      ← 0 posições retornadas
  "startKey": null
}

Banco de dados:
SELECT * FROM posicoes WHERE vaga_id = XXX AND status = 'open'
→ 1 posição encontrada

Divergência: API retorna 0, BD tem 1
```

---

## 12. Proposta de Solução

### 12.1 Implementar Soft Delete
```python
# Marcar posições não retornadas pela API como fechadas
# ao invés de apenas criar/atualizar

def sync_posicoes_with_soft_delete(vaga_id):
    # 1. Buscar todas posições da API
    posicoes_api_ids = {pos.id for pos in api_client.get_all_posicoes(vaga_id)}

    # 2. Buscar posições abertas do BD
    posicoes_bd = query(Posicao).filter_by(
        vaga_id=vaga_id,
        status='open'
    ).all()

    # 3. Identificar posições que sumiram da API
    for posicao_bd in posicoes_bd:
        if posicao_bd.inhire_id not in posicoes_api_ids:
            # Posição não está mais na API → Fechar
            posicao_bd.status = 'closed'
            posicao_bd.closed_at = datetime.now()
```

---

## 13. Checklist para Reunião com InHire

- [ ] Confirmar estrutura exata da resposta do endpoint
- [ ] Confirmar valores possíveis de status
- [ ] Confirmar se paginação está completa
- [ ] Confirmar se posições fechadas somem da API
- [ ] Solicitar logs/audit trail de mudanças de status
- [ ] Validar timestamps de updatedAt
- [ ] Testar em conjunto uma vaga divergente específica

---

## 14. Arquivos Importantes

| Arquivo | Localização | Descrição |
|---------|-------------|-----------|
| `sync_service.py` | `services/` | Lógica principal de sincronização |
| `api_client.py` | `services/` | Cliente da API InHire |
| `config.py` | raiz | Endpoints e configurações |
| `database.py` | `models/` | Modelo de dados (Posicao, Vaga) |
| `debug_posicoes.py` | raiz | Script de debug da API |
| `comparar_posicoes_abertas.py` | raiz | Script de comparação completa |

---

## 15. Contato Técnico

Para discussão técnica detalhada, compartilhar:
1. Este documento
2. Logs de uma requisição específica (debug_posicoes.py)
3. Relatório JSON gerado (relatorio_posicoes_*.json)
4. SQL query mostrando divergência no BD

**Pergunta chave para InHire:**
> "Por que o endpoint GET /jobs/positions/paginated/{job_id} retorna 0 posições
> para a vaga 'People Manager' (ID: 5f8ec764-69f0-4d09-870d-369cdce5d183)
> sendo que o banco de dados tem 1 posição com status='open' para essa vaga?"
