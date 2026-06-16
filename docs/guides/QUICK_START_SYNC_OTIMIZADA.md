# Quick Start: Sincronização Incremental Otimizada

## 🚀 Início Rápido

### 1. Testar a Nova Implementação

```bash
# Teste 1: Verificar queries de identificação
python scripts/debug/test_sync_optimized.py

# Teste 2: Executar sincronização otimizada
python sync_incremental_optimized.py
```

### 2. Validar Resultados

```bash
# Verificar logs
Get-Content "G:\Meu Drive\Framework_Data\Inhire\logs\inhire_sync.log" -Tail 100

# Verificar contagens no banco
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d inhire -c "
SELECT
    'vagas' as tabela, COUNT(*) as total
FROM vagas
UNION ALL
SELECT 'posicoes', COUNT(*) FROM posicoes
UNION ALL
SELECT 'candidaturas', COUNT(*) FROM candidaturas
UNION ALL
SELECT 'talentos', COUNT(*) FROM talentos;
"
```

### 3. Substituir no Scheduler (Opcional)

Editar `scheduler.py`:

```python
# ADICIONAR NO TOPO
from sync_incremental_optimized import sync_incremental_optimized

# SUBSTITUIR
scheduler.add_job(
    sync_incremental_optimized,  # ← Nova função
    'cron',
    hour='8-18/2',  # A cada 2 horas
    id='sync_incremental_optimized'
)
```

## 📋 Comparação Rápida

| Aspecto | Atual | Otimizada | Ganho |
|---------|-------|-----------|-------|
| Tempo | 10-20 min | 2-5 min | **3-4x mais rápido** |
| Chamadas API | ~2.900 | ~100-200 | **93% menos** |
| Frequência | 2-4 horas | 1-2 horas | **2x mais frequente** |

## 🎯 Principais Diferenças

### Estratégia Atual
```
1. Busca TUDO da API
2. Compara datas individualmente
3. Atualiza apenas modificados
```

### Estratégia Otimizada
```
1. Query BD para identificar modificados
2. Busca APENAS dados relevantes da API
3. Atualiza apenas modificados
```

## 📊 Campos de Data Utilizados

```
candidatura_timeline → stage_updated_at
candidaturas → updated_at_inhire
clientes → updated_at_inhire
posicoes → updated_at_inhire
position_timeline → changed_at
requisicoes → status_updated_at
talentos → updated_at_inhire
vaga_tags → updated_at
vagas → updated_at_inhire
```

## ✅ Checklist de Validação

- [ ] Script de teste executado sem erros
- [ ] Sync otimizada completou em < 10 minutos
- [ ] Contagens das tabelas estão corretas
- [ ] Logs não mostram erros críticos
- [ ] Performance melhorou vs sync atual

## 📚 Documentação Completa

- **Estratégia:** `docs/guides/ESTRATEGIA_SYNC_BASEADA_EM_TABELAS.md`
- **Changelog:** `docs/changelogs/CHANGELOG_2026-02-11_SYNC_INCREMENTAL_OTIMIZADA.md`
- **Código:** `sync_incremental_optimized.py`
- **Testes:** `scripts/debug/test_sync_optimized.py`

## 🆘 Troubleshooting

### Erro: "Nenhuma sincronização anterior encontrada"

**Solução:** Execute sync completa primeiro
```bash
python sync_completa.py
```

### Performance não melhorou

**Verificar:**
```bash
# Quantas vagas foram modificadas?
python -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from models.database import Vaga, SyncConfiguration

engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

config = session.query(SyncConfiguration).first()
last_sync = config.last_incremental_sync

vagas_mod = session.query(Vaga).filter(
    Vaga.updated_at_inhire > last_sync
).count()

print(f'Vagas modificadas: {vagas_mod}')
"
```

**Se > 200 vagas modificadas:** Performance será similar à atual

**Solução:** Executar sync completa e aumentar frequência de sync incremental

## 💡 Dicas

1. **Aumentar Frequência:** Com a otimização, pode executar a cada 1-2 horas
2. **Monitorar:** Verificar logs regularmente para identificar padrões
3. **Ajustar:** Se muitas mudanças, considerar sync completa

## 🔄 Próximos Passos

1. ✅ Testar manualmente 3-5 vezes
2. ✅ Validar resultados
3. ✅ Configurar scheduler
4. ✅ Monitorar execuções automáticas
