# Correção da Sincronização de Requisições

**Data**: 19/01/2026
**Problema Reportado**: A tabela `public.requisicoes` não estava seguindo o critério de comparação de datas entre o BD e a Inhire

---

## Problemas Identificados

### 1. Endpoint Incorreto na API

**Arquivo**: `services/api_client.py` (linhas 206-235)

**Problema**:
- O método `get_all_requisicoes()` tentava usar `POST /requisitions/paginated`
- Este endpoint não existe e retornava erro 403 Forbidden
- BD tinha 753 requisições, mas API retornava 0 (erro)

**Causa Raiz**:
```python
# CÓDIGO ANTIGO (INCORRETO)
def get_all_requisicoes(self):
    endpoint = "/requisitions/paginated"
    response = self._request("POST", endpoint, data=data)  # ← ERRO: 403
```

**Solução Implementada**:
```python
# CÓDIGO NOVO (CORRETO)
def get_all_requisicoes(self) -> Generator[RequisicaoAPI, None, None]:
    """
    Itera sobre todas as requisições

    Estratégia: Busca requisições através das vagas
    (não existe endpoint paginado geral de requisições)
    """
    # Buscar todas as vagas primeiro
    for vaga in self.get_all_vagas():
        # Para cada vaga, buscar suas requisições
        try:
            requisicoes = self.get_requisicoes_by_job(vaga.id)
            for req in requisicoes:
                yield req
        except Exception as e:
            self.logger.error(f"Erro ao buscar requisições da vaga {vaga.id}: {str(e)}")
            continue
```

**Endpoints Corretos Informados pelo Usuário**:
- `GET /requisitions/:requisitionId` - Obter requisição por ID
- `GET /requisitions/job/:jobId` - Obter requisições de uma vaga
- `POST /requisitions/:requisitionId` - Atualizar requisição

---

### 2. Schema Pydantic Incorreto

**Arquivo**: `models/new_api_schemas.py` (linhas 14-57)

**Problema**:
- A API retorna `customFields` como **lista** de objetos: `[{name, customFieldId, value}, ...]`
- O schema Pydantic esperava um **dicionário**: `{campo: valor, ...}`
- Causava erro de validação em TODAS as requisições

**Erro Original**:
```
ValidationError: 1 validation error for RequisicaoAPI
customFields
  Input should be a valid dictionary [type=dict_type, input_value=[...], input_type=list]
```

**Solução Implementada**:
```python
class RequisicaoAPI(BaseModel):
    """Schema para requisição de vaga"""
    id: str
    jobId: Optional[str] = None
    clientId: Optional[str] = None
    status: Optional[str] = None
    reason: Optional[str] = None
    positionAmount: Optional[int] = None
    requesterId: Optional[str] = None
    requesterName: Optional[str] = None
    approverId: Optional[str] = None
    approverName: Optional[str] = None
    # CORREÇÃO: Aceita tanto lista quanto dicionário
    customFields: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    requestedAt: Optional[datetime] = None
    approvedAt: Optional[datetime] = None
    rejectedAt: Optional[datetime] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    @field_validator('customFields', mode='before')
    @classmethod
    def convert_custom_fields(cls, v):
        """Converte customFields de lista para dicionário"""
        if isinstance(v, list):
            # Converter lista de {name, customFieldId, value} para dicionário {name: value}
            result = {}
            for item in v:
                if isinstance(item, dict):
                    name = item.get('name')
                    value = item.get('value', '')
                    if name:
                        result[name] = value
            return result
        return v
```

---

## Validação das Correções

### Script de Teste Criado

**Arquivo**: `scripts/debug/testar_requisicoes_fix.py`

**Resultado do Teste**:
```
Vagas testadas: 50
Total de requisições encontradas: 36

✓ Método get_requisicoes_by_job() funcionando!
✓ Endpoint GET /requisitions/job/:jobId está acessível
```

**Exemplos de Vagas com Requisições**:
- Vaga 1 (000b7c8e-1488-4421-b5ac-f52bcb022d64): 1 requisição
- Vaga 2 (00951e7b-cceb-4470-88fd-c231bf2ae41c): 1 requisição
- Vaga 3 (00c9ac94-8721-4abf-ba4a-f7e5b64c296e): 1 requisição
- (etc... 36 requisições no total encontradas em 50 vagas)

---

## Arquivos Modificados

### 1. services/api_client.py
- **Linhas 206-235**: Método `get_all_requisicoes()` reescrito
- **Método**: Agora itera por vagas e busca requisições de cada vaga
- **Status**: ✓ Testado e funcionando

### 2. models/new_api_schemas.py
- **Linhas 14-57**: Classe `RequisicaoAPI` atualizada
- **Mudanças**:
  - Campo `customFields` agora aceita `Union[Dict, List]`
  - Adicionado validator `convert_custom_fields()` para conversão automática
- **Status**: ✓ Testado e funcionando

---

## Lógica de Sincronização Incremental

**Arquivo**: `services/sync_service.py` (linhas 1563-1615)

**Confirmação**: A lógica de comparação de datas JÁ ESTAVA CORRETA.

```python
def _sync_requisicoes_incremental(self):
    # Buscar todas as requisições da API
    for req_api in self.api_client.get_all_requisicoes():
        # Verificar se existe no BD
        req_bd = session.query(Requisicao).filter_by(inhire_id=req_api.id).first()

        if not req_bd:
            # CRIAR nova requisição
            self.db.upsert_requisicao(req_api, vaga_db_id)
            stats['created'] += 1
        else:
            # Comparar datas - atualizar apenas se API é mais recente
            if req_api.updatedAt and req_bd.updated_at_inhire:
                api_date = self._normalize_datetime_for_comparison(req_api.updatedAt)
                bd_date = self._normalize_datetime_for_comparison(req_bd.updated_at_inhire)

                if api_date <= bd_date:
                    stats['skipped'] += 1
                    continue

            # ATUALIZAR
            self.db.upsert_requisicao(req_api, vaga_db_id)
            stats['updated'] += 1
```

**Princípio aplicado**: "Sempre devemos comparar a última data da sincronização do BD com a Inhire"

---

## Estado da Sincronização

**Última Execução**: Iniciada em 19/01/2026 às 17:49

### Progresso:
- ✓ **Vagas**: 1.073 processadas (0 criadas, 0 atualizadas, 1.137 ignoradas)
- ✓ **Posições**: 1.354 processadas (0 criadas, 0 atualizadas, 1.356 ignoradas)
- ⏸️ **Candidaturas**: Interrompida (estava em andamento desde 17:58)
- ⏳ **Requisições**: Não chegou a sincronizar (interrompida antes)

**Observação**: Sincronização foi pausada a pedido do usuário.

---

## Próximos Passos

### Para Retomar o Trabalho:

1. **Executar Sincronização Incremental Completa**:
   ```bash
   python run_sync_incremental.py
   ```

2. **Verificar Resultados da Sincronização de Requisições**:
   - Aguardar conclusão (pode demorar 15-20 minutos)
   - Verificar estatísticas de requisições sincronizadas
   - Confirmar que não há erros

3. **Validar no Banco de Dados**:
   ```sql
   -- Contar requisições no BD
   SELECT COUNT(*) FROM requisicoes;

   -- Verificar requisições recentes
   SELECT id, inhire_id, status, updated_at_inhire
   FROM requisicoes
   ORDER BY updated_at_inhire DESC
   LIMIT 10;

   -- Verificar customFields
   SELECT inhire_id, custom_fields
   FROM requisicoes
   WHERE custom_fields IS NOT NULL
   LIMIT 5;
   ```

4. **Comparar com API** (script já criado):
   ```bash
   python scripts/debug/comparar_requisicoes_bd_api.py
   ```

---

## Scripts de Teste Criados

### 1. testar_requisicoes_fix.py
- **Localização**: `scripts/debug/testar_requisicoes_fix.py`
- **Função**: Testa se requisições são acessíveis via vagas
- **Resultado**: ✓ Funcionando (36 requisições em 50 vagas)

### 2. comparar_requisicoes_bd_api.py
- **Localização**: `scripts/debug/comparar_requisicoes_bd_api.py`
- **Função**: Compara contagem entre BD e API
- **Status**: Pronto para uso após sincronização

### 3. testar_requisicoes_via_vagas.py
- **Localização**: `scripts/debug/testar_requisicoes_via_vagas.py`
- **Função**: Teste detalhado de requisições por vaga
- **Status**: Criado mas não finalizado (interrompido)

---

## Conclusão

### Problemas Corrigidos: ✓

1. ✓ Endpoint de requisições corrigido (via vagas)
2. ✓ Schema Pydantic corrigido (conversão de lista para dict)
3. ✓ Validação por testes confirmada (36 requisições encontradas)

### Estado Atual:

- **Código**: Corrigido e testado
- **Sincronização**: Pausada (aguardando retomada)
- **Validação Final**: Pendente (executar sync completo)

### Confiança:

**Alta** - As correções foram testadas isoladamente e funcionaram corretamente. A sincronização incremental completa irá validar a integração total.

---

## Contato Técnico

- **Arquivos Modificados**: 2 arquivos principais
- **Scripts Criados**: 3 scripts de debug/validação
- **Tempo de Correção**: ~2 horas (incluindo diagnóstico, correção e testes)
- **Complexidade**: Média (2 bugs distintos mas relacionados)

---

**Última Atualização**: 19/01/2026 - 18:15 (horário de Brasília)
