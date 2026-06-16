# Por que Posições e Candidaturas não estão na Sync Incremental?

## Resposta Rápida

A sincronização incremental atual foi **simplificada** e só inclui Vagas e Talentos por 3 motivos principais:

1. ❌ **Candidaturas não comparam datas** - sempre atualizam (ineficiente)
2. ⚠️ **Dependem de Vagas** - precisa buscar por `jobId` (não há endpoint global)
3. 🎯 **Otimização** - implementação focou em entidades que mudam mais

---

## Análise Detalhada

### 1. Comparação de Datas (UPSERT)

Verifiquei o código de cada entidade:

```
VAGAS (database_service.py:76-79)
├─ Compara: data_API > data_BD ✅
├─ Se menor ou igual: SKIP
└─ Status: NA INCREMENTAL ✅

POSIÇÕES (database_service.py:156-159)
├─ Compara: data_API > data_BD ✅
├─ Se menor ou igual: SKIP
└─ Status: NÃO está na incremental ⚠️ (MAS PODERIA!)

CANDIDATURAS (database_service.py:214-229)
├─ Compara: NENHUMA ❌
├─ Sempre atualiza
└─ Status: NÃO está na incremental ⚠️

TALENTOS (database_service.py:269-272)
├─ Compara: data_API > data_BD ✅
├─ Se menor ou igual: SKIP
└─ Status: NA INCREMENTAL ✅
```

**Conclusão:**
- ✅ Posições TÊM comparação → podem ser adicionadas
- ❌ Candidaturas NÃO TÊM → sempre atualizam (ineficiente)

---

### 2. Dependência de Vagas

Diferente de Vagas e Talentos, Posições e Candidaturas **dependem** de uma vaga:

```python
# API Inhire - Endpoints

# ✅ Buscar todas as vagas (independente)
POST /jobs/paginated/lean
{
  "tenantId": "xxx",
  "limit": 50
}

# ✅ Buscar todos os talentos (independente)
POST /talents/list
{
  "tenantId": "xxx",
  "limit": 50,
  "filter": {"updatedAt": {"gte": "2025-11-16T10:00:00"}}  # ← filtro possível
}

# ⚠️ Buscar posições (DEPENDE de vaga)
POST /positions/get-all-from-job
{
  "jobId": "vaga123",  # ← OBRIGATÓRIO
  "tenantId": "xxx"
}

# ⚠️ Buscar candidaturas (DEPENDE de vaga)
POST /talent/get-applications-from-job
{
  "jobId": "vaga123",  # ← OBRIGATÓRIO
  "tenantId": "xxx"
}
```

**Problema:**
Não há endpoint tipo `GET /positions?updatedAt>=2025-11-16` para buscar "todas as posições modificadas".

Você precisa:
1. Iterar por cada vaga
2. Buscar posições/candidaturas de cada uma

**Opções:**
- ❌ Buscar de TODAS as vagas → lento (volta a ser sync completa)
- ✅ Buscar apenas de vagas modificadas → inteligente
- ✅ Buscar apenas de vagas ativas → otimizado

---

### 3. Implementação Simplificada

A versão atual prioriza **velocidade** e **simplicidade**:

```
SYNC COMPLETA (~55 min)
├─ Vagas: TODAS
├─ Posições: TODAS (de cada vaga)
├─ Candidaturas: TODAS (de cada vaga)
└─ Talentos: IDs coletados

SYNC INCREMENTAL (~2-5 min)
├─ Vagas: todas (compara datas individualmente)
├─ Posições: ❌ NÃO (para economizar tempo)
├─ Candidaturas: ❌ NÃO (para economizar tempo)
└─ Talentos: apenas modificados
```

**Trade-off:**
- ⚡ Mais rápida (2-5 min vs 55 min)
- 📉 Dados de posições/candidaturas podem ficar desatualizados até próxima full

---

## Impacto Prático

### Cenário Real:

```
10:00 - Sync Completa
  └─ Candidatura001: etapa "Triagem"

14:00 - Candidatura muda para "Entrevista" (na API)

15:00 - Sync Incremental
  └─ Candidatura001: NÃO atualiza ❌
      (continua "Triagem" no BD)

02:00 (dia seguinte) - Sync Completa
  └─ Candidatura001: FINALMENTE "Entrevista" ✓
```

**Resultado:**
Candidaturas podem ficar **desatualizadas por até 24 horas**.

---

## Soluções Propostas

### Solução 1: Sync Incremental MELHORADA ⭐ (Recomendada)

Incluir Posições e Candidaturas, mas apenas de vagas ativas:

```python
def sync_incremental_melhorada(self) -> Dict:
    # 1. VAGAS (todas, compara datas)
    vagas_modificadas_ids = set()
    for vaga in self.api_client.get_all_vagas():
        is_new, operation = self.db.upsert_vaga(vaga)
        if operation in ['created', 'updated']:
            vagas_modificadas_ids.add(vaga.id)

    # 2. BUSCAR VAGAS ATIVAS do banco (com candidatos ativos)
    vagas_ativas = self.session.query(Vaga).filter(
        Vaga.status.in_(['open', 'active']),
        Vaga.active_talents > 0  # Apenas vagas com candidatos
    ).all()

    # Combinar: vagas modificadas + vagas ativas
    vagas_para_sincronizar = vagas_modificadas_ids.union(
        {v.inhire_id for v in vagas_ativas}
    )

    # 3. POSIÇÕES (apenas dessas vagas)
    for vaga_id in vagas_para_sincronizar:
        for posicao in self.api_client.get_all_posicoes(vaga_id):
            is_new, operation = self.db.upsert_posicao(posicao)
            # Compara data_API > data_BD ✓

    # 4. CANDIDATURAS (apenas dessas vagas)
    talent_ids = set()
    for vaga_id in vagas_para_sincronizar:
        for cand in self.api_client.get_all_candidaturas(vaga_id):
            is_new, operation = self.db.upsert_candidatura(cand, vaga_id)
            # Sempre atualiza (sem comparação)
            if cand.talentId:
                talent_ids.add(cand.talentId)

    # 5. TALENTOS (modificados + IDs coletados)
    filter_date = {"updatedAt": {"gte": last_sync.isoformat()}}
    for talento in self.api_client.get_all_talentos(filter_dict=filter_date):
        is_new, operation = self.db.upsert_talento(talento)

    # Talentos das candidaturas
    for talent_id in talent_ids:
        if not self.session.query(Talento).filter_by(inhire_id=talent_id).first():
            talento = self.api_client.get_talento_by_id(talent_id)
            is_new, operation = self.db.upsert_talento(talento)
```

**Vantagens:**
- ✅ Sincroniza posições/candidaturas de vagas relevantes
- ✅ Mantém dados críticos atualizados (vagas ativas)
- ✅ Ainda mais rápido que sync completa
- ✅ Foca em vagas com candidatos (otimizado)

**Tempo estimado:** ~5-10 minutos (vs 2-5 min atual, mas muito menos que 55 min)

---

### Solução 2: Adicionar Comparação em Candidaturas

Corrigir `upsert_candidatura()`:

```python
def upsert_candidatura(self, cand_api: CandidaturaAPI, job_id: str) -> tuple[bool, str]:
    existing = self.session.query(Candidatura).filter_by(inhire_id=cand_api.id).first()

    if existing:
        # ADICIONAR COMPARAÇÃO (igual Vagas e Posições)
        if cand_api.updatedAt and existing.updated_at_inhire:
            updated_at_normalized = self._normalize_datetime(cand_api.updatedAt)
            if updated_at_normalized <= existing.updated_at_inhire:
                return False, 'skipped'  # ✅ Pula se não mudou

        # Atualizar...
        existing.status = status_normalized
        existing.updated_at_inhire = updated_at_normalized
        return False, 'updated'
```

**Vantagens:**
- ✅ Consistente com outras entidades
- ✅ Eficiente (pula candidaturas não modificadas)

---

### Solução 3: Modo "Híbrido"

Criar 2 modos de sincronização incremental:

```bash
# Incremental LEVE (atual - só vagas/talentos)
python sync_incremental.py --light

# Incremental COMPLETA (com posições/candidaturas)
python sync_incremental.py --full
```

---

## Recomendação Final

### Estratégia Ideal:

1. **Implementar Solução 1** (Sync Incremental Melhorada)
   - Adiciona Posições/Candidaturas de vagas ativas
   - Tempo: ~5-10 min (aceitável)

2. **Implementar Solução 2** (Comparação em Candidaturas)
   - Torna candidaturas eficientes
   - Evita atualizações desnecessárias

3. **Manter Sync Completa Mensal**
   - Garantir consistência total
   - 1x por mês ou sob demanda

### Código de Agendamento:

```python
# Incremental melhorada: A cada 2 horas
scheduler.add_job(
    sync_incremental_melhorada,
    'interval',
    hours=2,
    id='sync_incremental'
)

# Completa: 1x por semana (domingo 02:00)
scheduler.add_job(
    sync_full,
    'cron',
    day_of_week='sun',
    hour=2,
    minute=0,
    id='sync_full'
)
```

---

## Quer que eu implemente?

Posso criar:

1. ✅ `sync_incremental_melhorada.py` - Versão otimizada com Posições/Candidaturas
2. ✅ Correção em `database_service.py` - Adicionar comparação em Candidaturas
3. ✅ Testes comparativos - Comparar tempo/eficiência das versões

Me avise qual solução prefere! 🚀
