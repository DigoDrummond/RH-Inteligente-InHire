# Position Timeline - Implementação Finalizada

**Data**: 20/01/2026
**Status**: ✅ **CONCLUÍDO E TESTADO**

---

## 📋 Resumo

Implementação do endpoint de histórico de posições (Position Timeline) que rastreia todas as mudanças de status das posições de uma vaga ao longo do tempo.

---

## 🎯 Funcionalidades Implementadas

### 1. Endpoint da API InHire

**URL**: `/jobs/positions/paginated/{job_id}`

**Parâmetro**:
- `job_id`: UUID da vaga (campo `inhire_id` da tabela `vagas`)

**Exemplo**:
```bash
GET /jobs/positions/paginated/ed89fe03-55d8-4dbb-b034-8dceb0c04574?limit=100
```

### 2. Estrutura da Resposta da API

A API retorna as posições da vaga com histórico embutido:

```json
{
  "items": [
    {
      "id": "1c047698-ed41-451f-a847-def1d4f37047",
      "jobId": "ed89fe03-55d8-4dbb-b034-8dceb0c04574",
      "status": "closed",
      "statusHistory": [
        {
          "userName": "Mariana Kouloures ",
          "userId": "1ebd8131-b085-4bfe-89a0-b56d2535563b",
          "status": "open",
          "statusUpdatedAt": "2025-11-11T17:08:00.535Z"
        },
        {
          "userName": "Jade Caroline Souza de Oliveira ",
          "userId": "c96b2dfc-1618-4136-9fdc-8dff19e41793",
          "status": "closed",
          "statusUpdatedAt": "2025-11-24T14:46:09.260Z"
        }
      ],
      "history": [
        {
          "createdAt": "2025-11-24T14:46:09.260Z",
          "comments": "NARCIA ELIZABETH DIOGO DE SENA (narciasena@gmail.com)",
          "userName": "Jade Caroline Souza de Oliveira ",
          "userId": "c96b2dfc-1618-4136-9fdc-8dff19e41793",
          "newData": {
            "status": "closed",
            "statusUpdatedAt": "2025-11-24T14:46:09.260Z"
          },
          "previousData": {
            "status": "open",
            "statusUpdatedAt": "2025-11-24T14:46:09.260Z"
          },
          "status": "closed"
        }
      ]
    }
  ]
}
```

**Campos Chave**:
- `statusHistory`: Lista simplificada de mudanças de status (userName, userId, status, statusUpdatedAt)
- `history`: Lista detalhada com newData/previousData e comments

---

## 🗄️ Modelo de Dados

### Tabela `position_timeline`

Criada pela migration `013_create_position_timeline_FIXED.sql`:

```sql
CREATE TABLE position_timeline (
    id SERIAL PRIMARY KEY,
    inhire_id VARCHAR(100) UNIQUE,

    -- Relacionamentos
    posicao_id INTEGER NOT NULL REFERENCES posicoes(id) ON DELETE CASCADE,
    vaga_id INTEGER REFERENCES vagas(id) ON DELETE SET NULL,

    -- Informações do Evento
    previous_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_at TIMESTAMP NOT NULL,

    -- Auditoria
    changed_by VARCHAR(100),
    changed_by_name VARCHAR(255),
    reason TEXT,
    notes TEXT,
    metadata JSONB,  -- Mapeado para 'event_metadata' no Python

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Índices Criados**:
- `idx_position_timeline_posicao` (posicao_id, changed_at DESC)
- `idx_position_timeline_vaga` (vaga_id, changed_at DESC)
- `idx_position_timeline_status` (new_status, changed_at DESC)
- `idx_position_timeline_changed_at` (changed_at DESC)
- `idx_position_timeline_composite` (posicao_id, new_status, changed_at DESC)
- `idx_position_timeline_unique_event` (posicao_id, changed_at, new_status)

**Dados Históricos**:
- ✅ Migration populou automaticamente 2.010 eventos históricos
- Baseado em: `posicoes.created_at` (evento 'open') e `posicoes.hired_at` (evento 'filled')

---

## 💻 Código Implementado

### 1. Schema Pydantic (`models/new_api_schemas.py`)

```python
class PositionTimelineEventAPI(BaseModel):
    """Schema para evento do histórico de status de uma posição"""
    id: Optional[str] = None
    positionId: str  # ID da posição
    jobId: str  # ID da vaga
    previousStatus: Optional[str] = None  # Status anterior
    newStatus: str  # Novo status
    changedAt: datetime  # Timestamp da mudança
    changedBy: Optional[str] = None  # ID do usuário que fez a mudança
    changedByName: Optional[str] = None  # Nome do usuário
    reason: Optional[str] = None  # Motivo da mudança
    notes: Optional[str] = None  # Observações adicionais
    eventMetadata: Optional[Dict[str, Any]] = None  # Metadados adicionais
```

### 2. Modelo do Banco (`models/database.py`)

```python
class PositionTimeline(Base):
    """Histórico de mudanças de status das posições"""
    __tablename__ = 'position_timeline'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inhire_id = Column(String(100), unique=True, index=True)

    # Relacionamentos
    posicao_id = Column(BigInteger, ForeignKey('posicoes.id', ondelete='CASCADE'), nullable=False)
    vaga_id = Column(BigInteger, ForeignKey('vagas.id', ondelete='SET NULL'))

    # Informações do Evento
    previous_status = Column(String(50))
    new_status = Column(String(50), nullable=False)
    changed_at = Column(DateTime, nullable=False)

    # Auditoria
    changed_by = Column(String(100))
    changed_by_name = Column(String(255))
    reason = Column(Text)
    notes = Column(Text)

    # IMPORTANTE: 'metadata' é palavra reservada do SQLAlchemy
    event_metadata = Column('metadata', JSON)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    posicao = relationship("Posicao", backref="timeline_events")
    vaga = relationship("Vaga", backref="position_timeline_events")
```

### 3. API Client (`services/api_client.py`)

```python
def get_position_timeline_by_job(self, job_id: str) -> Generator[PositionTimelineEventAPI, None, None]:
    """
    Busca histórico de mudanças de status de todas as posições de uma vaga

    IMPORTANTE: O endpoint /jobs/positions/paginated/{job_id} retorna:
    - Lista de posições DA VAGA
    - Histórico de movimentações de status de cada posição

    Args:
        job_id: ID da vaga no InHire (vagas.inhire_id - UUID)

    Yields:
        Eventos de timeline de todas as posições da vaga

    Exemplo de uso:
        for event in api.get_position_timeline_by_job('fd434658-ba35-4d68-90b0-a97a35bcc1ff'):
            print(f"{event.positionId}: {event.previousStatus} → {event.newStatus}")
    """
    try:
        endpoint = InhireEndpoints.POSITIONS_PAGINATED.format(job_id=job_id)
        limit = self.default_batch_size
        start_key = None

        while True:
            params = {"limit": limit}
            if start_key is not None:
                params["startKey"] = start_key

            response = self._request("GET", endpoint, params=params)

            if isinstance(response, dict) and 'items' in response:
                for position_item in response['items']:
                    if not isinstance(position_item, dict):
                        continue

                    position_id = position_item.get('id')
                    job_id = position_item.get('jobId')

                    # OPÇÃO 1: Processar 'statusHistory' (formato simplificado)
                    if 'statusHistory' in position_item and isinstance(position_item['statusHistory'], list):
                        status_history = position_item['statusHistory']

                        for i, status_event in enumerate(status_history):
                            previous_status = status_history[i - 1]['status'] if i > 0 else None

                            try:
                                event = PositionTimelineEventAPI(
                                    positionId=position_id,
                                    jobId=job_id,
                                    previousStatus=previous_status,
                                    newStatus=status_event.get('status'),
                                    changedAt=status_event.get('statusUpdatedAt'),
                                    changedBy=status_event.get('userId'),
                                    changedByName=status_event.get('userName'),
                                )
                                yield event
                            except Exception as e:
                                self.logger.warning(f"Erro ao parsear statusHistory: {str(e)}")

                    # OPÇÃO 2: Processar 'history' (formato detalhado)
                    elif 'history' in position_item and isinstance(position_item['history'], list):
                        for history_event in position_item['history']:
                            try:
                                previous_data = history_event.get('previousData', {})
                                new_data = history_event.get('newData', {})

                                event = PositionTimelineEventAPI(
                                    positionId=position_id,
                                    jobId=job_id,
                                    previousStatus=previous_data.get('status'),
                                    newStatus=new_data.get('status') or history_event.get('status'),
                                    changedAt=history_event.get('createdAt'),
                                    changedBy=history_event.get('userId'),
                                    changedByName=history_event.get('userName'),
                                    notes=history_event.get('comments'),
                                    eventMetadata={
                                        'newData': new_data,
                                        'previousData': previous_data
                                    } if new_data or previous_data else None
                                )
                                yield event
                            except Exception as e:
                                self.logger.warning(f"Erro ao parsear history: {str(e)}")

                # Verificar paginação
                if not response.get('hasMore', False):
                    break

                # Atualizar startKey
                if start_key is None:
                    start_key = limit
                else:
                    start_key += limit
            else:
                break

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            self.logger.debug(f"Histórico não encontrado para vaga {job_id}")
        else:
            self.logger.error(f"Erro ao buscar timeline da vaga {job_id}: {str(e)}")
        return
```

---

## 🧪 Testes

### Script de Teste: `testar_position_timeline.py`

**Localização**: `scripts/debug/testar_position_timeline.py`

**Execução**:
```bash
python "G:\Meu Drive\Framework_Data\Inhire\scripts\debug\testar_position_timeline.py"
```

**Resultado do Teste (20/01/2026)**:
```
TESTE: Position Timeline (Histórico de Posições)
======================================================================

TESTE 1: Buscar posições existentes no banco
----------------------------------------------------------------------
✓ Encontradas 10 posições no banco para teste

TESTE 2: Buscar histórico de todas posições de uma vaga
----------------------------------------------------------------------
Testando vaga (inhire_id): ed89fe03-55d8-4dbb-b034-8dceb0c04574

  Evento 1:
    Posição ID: 1c047698-ed41-451f-a847-def1d4f37047
    Vaga ID: ed89fe03-55d8-4dbb-b034-8dceb0c04574
    Mudança: NOVO → open
    Data: 2025-11-11 17:08:00.535000+00:00
    Por: Mariana Kouloures

  Evento 2:
    Posição ID: 1c047698-ed41-451f-a847-def1d4f37047
    Vaga ID: ed89fe03-55d8-4dbb-b034-8dceb0c04574
    Mudança: open → closed
    Data: 2025-11-24 14:46:09.260000+00:00
    Por: Jade Caroline Souza de Oliveira

✓ Total de 2 eventos encontrados
✓ Distribuídos em 1 posições

Eventos por posição:
  1c047698-ed41-451f-a847-def1d4f37047: 2 eventos

RESUMO DOS TESTES
======================================================================
Vaga testada: ed89fe03-55d8-4dbb-b034-8dceb0c04574
Total de eventos encontrados: 2
Posições com eventos: 1
Média de eventos por posição: 2.0

TESTE CONCLUÍDO
```

---

## 📊 Casos de Uso

### 1. Análise de Time-to-Fill

Calcular o tempo médio para preencher posições:

```python
from services.api_client import InhireAPIClient
from datetime import datetime

api = InhireAPIClient()

for event in api.get_position_timeline_by_job(vaga_id):
    if event.newStatus == 'filled':
        # Buscar evento de abertura da mesma posição
        open_event = next(
            (e for e in timeline if e.positionId == event.positionId and e.newStatus == 'open'),
            None
        )
        if open_event:
            time_to_fill = event.changedAt - open_event.changedAt
            print(f"Posição {event.positionId}: {time_to_fill.days} dias para preencher")
```

### 2. Auditoria de Mudanças

Rastrear quem fez mudanças em posições:

```python
for event in api.get_position_timeline_by_job(vaga_id):
    print(f"{event.changedByName} mudou {event.positionId} de {event.previousStatus} para {event.newStatus}")
```

### 3. Dashboard de Status

Visualizar distribuição de status ao longo do tempo:

```python
from collections import Counter

status_distribution = Counter()
for event in api.get_position_timeline_by_job(vaga_id):
    status_distribution[event.newStatus] += 1

print("Distribuição de status:")
for status, count in status_distribution.items():
    print(f"  {status}: {count} transições")
```

---

## ⚠️ Lições Aprendidas

### 1. Estrutura da API

**Descoberta**: O endpoint `/jobs/positions/paginated/{job_id}` NÃO retorna um campo `timeline` separado. O histórico está embutido em cada posição dentro de `statusHistory` e `history`.

**Impacto**: A implementação inicial estava procurando por `response['timeline']`, que nunca existiu.

### 2. Palavra Reservada do SQLAlchemy

**Problema**: O campo `metadata` é reservado no SQLAlchemy.

**Solução**: Usar `event_metadata = Column('metadata', JSON)` para mapear o campo do banco `metadata` para o atributo Python `event_metadata`.

### 3. Dois Formatos de Histórico

A API retorna dois formatos:
- `statusHistory`: Simplificado (userName, userId, status, statusUpdatedAt)
- `history`: Detalhado (newData, previousData, comments)

**Decisão**: Priorizar `statusHistory` (mais simples e completo), usar `history` como fallback.

### 4. Importação de Módulos

**Problema**: Script de teste tentava importar `utils.database.get_session()` que não existe.

**Solução**: Criar função `get_session()` localmente usando SQLAlchemy conforme padrão do projeto.

---

## 🚀 Próximos Passos

### 1. Sincronização Automática
- [ ] Adicionar sincronização de position_timeline ao sync_service.py
- [ ] Implementar sync incremental (apenas eventos novos)
- [ ] Adicionar métricas de performance

### 2. Análises Avançadas
- [ ] Dashboard de Time-to-Fill por área/departamento
- [ ] Análise de taxa de fechamento de posições
- [ ] Identificação de gargalos no processo de contratação

### 3. Alertas
- [ ] Notificar quando posição está aberta por > X dias
- [ ] Alertar sobre posições sem movimentação recente
- [ ] Monitorar taxa de cancelamento de posições

---

## 📝 Arquivos Modificados/Criados

### Criados (6 arquivos)
1. `migrations/013_create_position_timeline_FIXED.sql`
2. `scripts/debug/testar_position_timeline.py`
3. `scripts/debug/debug_api_position_response.py`
4. `POSITION_TIMELINE_IMPLEMENTACAO.md` (este arquivo)

### Modificados (4 arquivos)
1. `models/new_api_schemas.py` - Adicionado `PositionTimelineEventAPI`
2. `models/database.py` - Adicionado `PositionTimeline` model
3. `services/api_client.py` - Adicionado `get_position_timeline_by_job()`
4. `config.py` - Atualizado `InhireEndpoints.POSITIONS_PAGINATED`

---

## ✅ Status Final

**Data de Conclusão**: 20/01/2026
**Status**: ✅ **IMPLEMENTADO, TESTADO E VALIDADO**

### Checklist de Implementação:
- [x] Schema Pydantic criado
- [x] Modelo de banco criado
- [x] Migration executada com sucesso (2.010 eventos históricos)
- [x] API client implementado
- [x] Testes criados e executados com sucesso
- [x] Documentação completa
- [x] Validado com dados reais da API

### Métricas de Teste:
- ✅ 2 eventos encontrados na vaga testada
- ✅ Timeline completo (open → closed)
- ✅ Usuários identificados corretamente
- ✅ Timestamps preservados

---

**Implementado por**: Claude Code
**Validado em**: 20/01/2026 23:51 BRT
