# Estratégia Recomendada para Sincronização - InHire

## 🎯 Melhor Estratégia Baseada em Dados Reais

Após analisar:
- Volume atual do BD (~1.138 vagas, ~104.558 registros totais)
- Performance dos syncs em execução
- Limitações da API InHire
- Padrão de atualização dos dados

**A melhor estratégia para ter TODOS os dados atualizados e sincronizados é:**

---

## ✅ ESTRATÉGIA HÍBRIDA RECOMENDADA

### 1. SYNC INCREMENTAL OTIMIZADO (Diário - 2h da manhã)

**Objetivo:** Manter dados sempre atualizados com mínimo overhead

**Configuração:**
```bash
# Cron: Executar diariamente às 2h da manhã
0 2 * * * cd /app && python run_sync.py --incremental
```

**O que sincroniza:**
- ✅ TODAS as vagas (API não suporta filtro de data, mas é rápido ~1 min)
- ✅ Posições de vagas atualizadas nos últimos 7 dias (~50-100 vagas vs 1.138)
- ✅ Candidaturas de vagas ativas OU atualizadas nos últimos 7 dias
- ✅ Talentos vinculados às candidaturas sincronizadas
- ✅ Requisições (endpoint paginado super eficiente)
- ✅ Timeline de posições abertas

**Tempo estimado:** ~10-15 minutos

**Benefícios:**
- Dados sempre atualizados (defasagem máxima 24h)
- 50% mais rápido que incremental atual
- Reduz carga na API
- Foca em dados que realmente mudaram

---

### 2. SYNC FULL (Mensal - 1º domingo às 3h)

**Objetivo:** Garantir consistência completa e capturar dados órfãos

**Configuração:**
```bash
# Cron: Primeiro domingo do mês às 3h
0 3 * * 0 [ $(date +\%d) -le 7 ] && cd /app && python run_sync.py --full
```

**O que sincroniza:**
- ✅ TUDO completo (vagas, posições, candidaturas, talentos, requisições)
- ✅ Captura dados órfãos ou inconsistências
- ✅ Validação completa de integridade

**Tempo estimado:** ~40-55 minutos

**Benefícios:**
- Garantia de consistência total
- Backup completo mensal
- Captura edge cases

---

### 3. SYNC EXPRESS (NOVO - A cada 2-4 horas durante horário comercial)

**Objetivo:** Dados críticos super atualizados para operação diária

**Configuração:**
```bash
# Cron: A cada 2 horas das 8h às 20h (horário comercial)
0 8-20/2 * * * cd /app && python run_sync.py --express
```

**O que sincroniza:**
- ✅ Apenas vagas com posições abertas (~200-300 vagas)
- ✅ Candidaturas ativas dessas vagas
- ✅ Talentos vinculados
- ✅ Timeline das posições abertas

**Tempo estimado:** ~3-5 minutos

**Benefícios:**
- Dados operacionais sempre frescos (defasagem máxima 2h)
- Super rápido
- Ideal para dashboards e relatórios do dia

---

## 📊 Comparação das Estratégias

| Estratégia | Frequência | Tempo | Volume | Uso |
|------------|------------|-------|--------|-----|
| **EXPRESS** | 2-4h | ~5 min | 20% dos dados | Operação diária |
| **INCREMENTAL** | Diária | ~10-15 min | 40% dos dados | Atualização geral |
| **FULL** | Mensal | ~40-55 min | 100% dos dados | Consistência total |

---

## 🎯 Por Que Esta Estratégia é a Melhor?

### 1. **Performance vs Consistência Balanceados**
- EXPRESS: dados críticos ultra-atualizados
- INCREMENTAL: cobertura ampla diária
- FULL: garantia mensal de consistência

### 2. **Adaptado às Limitações da API**
- API não suporta filtros de data em vários endpoints
- Solução: filtrar localmente após buscar
- Paginação eficiente aproveitada ao máximo

### 3. **Baseado em Padrões Reais de Uso**
- Dashboards precisam de dados frescos (EXPRESS)
- Relatórios gerenciais precisam de completude (INCREMENTAL)
- Auditoria e compliance precisam de tudo (FULL)

### 4. **Otimizado para o Volume Atual**
- ~1.138 vagas (crescendo lentamente)
- ~104.558 registros totais
- Maioria das vagas está fechada (só ~200-300 ativas)

### 5. **Reduz Carga na API**
- EXPRESS: ~300 requests
- INCREMENTAL: ~2.000 requests
- FULL: ~8.000 requests
- vs Estratégia atual: ~10.000 requests diários

---

## 🛠️ Implementação Prática

### Passo 1: Implementar SYNC EXPRESS (Prioridade ALTA)

```python
# services/sync_service.py

def sync_express(self) -> Dict:
    """
    Sync EXPRESS: apenas dados críticos operacionais

    Foco: vagas abertas + candidaturas ativas + talentos vinculados
    Tempo: ~5 min
    """
    self.logger.info("=== SYNC EXPRESS INICIADO ===")

    stats = {
        'processed': 0,
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'failed': 0
    }

    # 1. Buscar vagas com posições abertas (do BD)
    vagas_ativas = self.db.get_vagas_com_posicoes_abertas()
    self.logger.info(f"Vagas com posições abertas: {len(vagas_ativas)}")

    # 2. Para cada vaga ativa, sincronizar candidaturas
    talent_ids = set()
    for vaga in vagas_ativas:
        try:
            # Buscar candidaturas via API
            candidaturas = list(self.api_client.get_all_candidaturas(vaga.inhire_id))

            for cand in candidaturas:
                # Salvar candidatura
                self.db.upsert_candidatura(cand)
                stats['processed'] += 1

                # Coletar talent_id para buscar depois
                if cand.talentId:
                    talent_ids.add(cand.talentId)

        except Exception as e:
            self.logger.error(f"Erro vaga {vaga.inhire_id}: {e}")
            stats['failed'] += 1

    # 3. Sincronizar talentos vinculados
    for talent_id in talent_ids:
        try:
            talento = self.api_client.get_talento_by_id(talent_id)
            self.db.upsert_talento(talento)
            stats['processed'] += 1
        except Exception as e:
            self.logger.error(f"Erro talento {talent_id}: {e}")
            stats['failed'] += 1

    self.logger.info(f"=== SYNC EXPRESS CONCLUÍDO: {stats} ===")
    return stats
```

### Passo 2: Otimizar SYNC INCREMENTAL

```python
def sync_incremental_optimized(self, days: int = 7) -> Dict:
    """
    Sync INCREMENTAL otimizado: últimos N dias

    Foco: vagas + posições + candidaturas + talentos atualizados
    Tempo: ~10-15 min
    """
    cutoff = datetime.now() - timedelta(days=days)

    # 1. Vagas - buscar todas (API não filtra) mas filtrar localmente
    all_vagas = list(self.api_client.get_all_vagas())
    vagas_recentes = [v for v in all_vagas if v.updatedAt > cutoff]

    self.logger.info(f"Vagas atualizadas: {len(vagas_recentes)}/{len(all_vagas)}")

    # Salvar todas (upsert inteligente: só atualiza se mudou)
    for vaga in all_vagas:
        self.db.upsert_vaga(vaga)

    # 2. Posições - APENAS de vagas recentes
    for vaga in vagas_recentes:
        posicoes = list(self.api_client.get_all_posicoes(vaga.id))
        for pos in posicoes:
            self.db.upsert_posicao(pos)

    # 3. Candidaturas - vagas ativas OU recentes
    vagas_filtradas = self.db.get_vagas_ativas_ou_recentes(days=days)
    talent_ids = set()

    for vaga in vagas_filtradas:
        candidaturas = list(self.api_client.get_all_candidaturas(vaga.inhire_id))
        for cand in candidaturas:
            self.db.upsert_candidatura(cand)
            if cand.talentId:
                talent_ids.add(cand.talentId)

    # 4. Talentos - apenas IDs coletados (evitar duplicatas)
    for talent_id in talent_ids:
        talento = self.api_client.get_talento_by_id(talent_id)
        self.db.upsert_talento(talento)

    return stats
```

### Passo 3: Adicionar Método Helper no DatabaseService

```python
# services/database_service.py

def get_vagas_com_posicoes_abertas(self) -> List[Vaga]:
    """Retorna vagas que têm pelo menos 1 posição aberta"""
    return (
        self.session.query(Vaga)
        .join(Posicao, Vaga.id == Posicao.vaga_id)
        .filter(Posicao.status == 'open')
        .distinct()
        .all()
    )

def get_vagas_ativas_ou_recentes(self, days: int = 7) -> List[Vaga]:
    """Retorna vagas ativas OU atualizadas nos últimos N dias"""
    cutoff = datetime.now() - timedelta(days=days)

    return (
        self.session.query(Vaga)
        .filter(
            or_(
                Vaga.status == 'open',
                Vaga.updated_at_inhire > cutoff
            )
        )
        .all()
    )
```

### Passo 4: Atualizar run_sync.py

```python
# run_sync.py

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ['--full', '--incremental', '--express']:
        print("Uso: python run_sync.py [--full|--incremental|--express]")
        print()
        print("  --full          Sincronizacao completa (~55 min)")
        print("  --incremental   Sincronizacao incremental (~15 min)")
        print("  --express       Sincronizacao express (~5 min)")
        return

    sync_type = sys.argv[1].replace('--', '')

    # ... (código de conexão BD)

    if sync_type == 'full':
        result = sync_service.sync_full()

    elif sync_type == 'incremental':
        result = sync_service.sync_incremental_optimized(days=7)

    elif sync_type == 'express':
        result = sync_service.sync_express()
```

---

## 📅 Cronograma de Implementação

### Semana 1: Implementar EXPRESS
- [ ] Criar método `sync_express()` no `SyncService`
- [ ] Adicionar helpers no `DatabaseService`
- [ ] Atualizar `run_sync.py` para aceitar `--express`
- [ ] Testar manualmente
- [ ] Configurar cron (a cada 2h)

### Semana 2: Otimizar INCREMENTAL
- [ ] Refatorar `sync_incremental()` para filtrar localmente
- [ ] Adicionar filtros de vagas ativas/recentes
- [ ] Testar com volume real
- [ ] Ajustar configuração de cron (diário)

### Semana 3: Validação e Monitoramento
- [ ] Comparar dados entre EXPRESS, INCREMENTAL e FULL
- [ ] Validar consistência
- [ ] Criar dashboard de métricas de sync
- [ ] Documentar processos

### Semana 4: Ajustes Finais
- [ ] Configurar alertas de falhas
- [ ] Otimizar rate limiting
- [ ] Documentação final
- [ ] Treinamento da equipe

---

## ⚠️ Problemas Identificados e Soluções

### Problema 1: FULL Sync falhando com erro de constraint
```
ERRO: a nova linha da relação "vagas" viola a restrição de verificação "chk_vaga_dates_logical"
```

**Causa:** Campo `updated_at_inhire` posterior ao `created_at` local (bug de timezone)

**Solução:**
```python
# Ajustar timezone antes de inserir
if vaga.updatedAt:
    vaga.updatedAt = vaga.updatedAt.replace(tzinfo=None)
if vaga.createdAt:
    vaga.createdAt = vaga.createdAt.replace(tzinfo=None)
```

### Problema 2: Rate Limiting agressivo

**Observado:**
```
Rate limit excedido: 30/30
Aguardando 40-54s backoff
```

**Causa:** API InHire limita a 30 req/min

**Solução:**
- Rate limiter adaptativo já implementado
- Configurar `INHIRE_API_RATE_LIMIT=25` (margem de segurança)
- Usar workers paralelos com cuidado (max 3)

### Problema 3: Position Timeline com newStatus NULL

**Erro:**
```
1 validation error for PositionTimelineEventAPI
newStatus: Input should be a valid string
```

**Causa:** API retorna `newStatus: null` em alguns eventos históricos

**Solução:**
```python
# models/new_api_schemas.py
class PositionTimelineEventAPI(BaseModel):
    newStatus: Optional[str] = None  # Permitir NULL
```

---

## 📊 Métricas Esperadas

### EXPRESS (A cada 2h)
- Vagas processadas: ~200-300
- Candidaturas: ~5.000-8.000
- Talentos: ~3.000-5.000
- Requests API: ~300-500
- Tempo: 3-5 min
- Defasagem: máx 2h

### INCREMENTAL (Diário)
- Vagas processadas: 1.138 (todas)
- Posições: ~50-100 vagas × avg 2 posições = ~100-200
- Candidaturas: ~15.000-20.000
- Talentos: ~8.000-12.000
- Requests API: ~1.500-2.500
- Tempo: 10-15 min
- Defasagem: máx 24h

### FULL (Mensal)
- TUDO: 100% dos dados
- Requests API: ~8.000-10.000
- Tempo: 40-55 min
- Garantia: consistência total

---

## ✅ Conclusão e Recomendação Final

**Para ter TODOS os dados atualizados e sincronizados, a melhor estratégia é:**

1. **IMPLEMENTAR EXPRESS imediatamente** (~1 dia de dev)
   - Maior impacto com menor esforço
   - Dados críticos sempre atualizados
   - Execução a cada 2h no horário comercial

2. **OTIMIZAR INCREMENTAL** (~2 dias de dev)
   - Melhorar filtros de vagas
   - Reduzir tempo de 20 min para 10-15 min
   - Manter execução diária

3. **MANTER FULL como backup mensal**
   - Garantia de consistência total
   - Captura edge cases
   - 1x por mês é suficiente

**Cronograma de Execução Recomendado:**
```bash
# EXPRESS: A cada 2h das 8h às 20h (seg-sex)
0 8-20/2 * * 1-5 cd /app && python run_sync.py --express

# INCREMENTAL: Diariamente às 2h
0 2 * * * cd /app && python run_sync.py --incremental

# FULL: 1º domingo do mês às 3h
0 3 * * 0 [ $(date +\%d) -le 7 ] && cd /app && python run_sync.py --full
```

**Benefícios desta estratégia:**
- ✅ Dados sempre atualizados (defasagem máx 2h)
- ✅ Performance otimizada (5 min vs 20 min vs 55 min)
- ✅ Redução de 60% no volume de requests da API
- ✅ Escalável para crescimento futuro
- ✅ Consistência garantida mensalmente

**Esforço de Implementação:**
- EXPRESS: 1 dia de dev + 1 dia de testes
- INCREMENTAL otimizado: 2 dias de dev + 1 dia de testes
- Total: ~1 semana para implementação completa

---

## 🚀 Próximos Passos

1. **Aprovar estratégia** com time de produto/negócio
2. **Priorizar implementação** de EXPRESS (maior ROI)
3. **Planejar sprint** de otimização (1 semana)
4. **Executar implementação** seguindo roadmap
5. **Monitorar resultados** por 2 semanas
6. **Ajustar configurações** baseado em métricas reais
