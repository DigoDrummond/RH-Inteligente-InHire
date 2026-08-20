# ⚠️ Nota Sobre Entidades HTML nas Descrições

## Situação Atual

As descrições das requisições ainda contêm **entidades HTML** como:
- `&eacute;` → é
- `&aacute;` → á
- `&iacute;` → í
- `&ocirc;` → ô
- `&ccedil;` → ç
- `&atilde;` → ã

**Exemplo:**
```
"Experi&ecirc;ncia com .NET Framework"
```

Deveria ser:
```
"Experiência com .NET Framework"
```

## Por Que Não Foi Corrigido?

O PostgreSQL **não tem função nativa** para converter entidades HTML para caracteres Unicode.

As regex do PostgreSQL removem as **tags HTML** (`<p>`, `<br>`, etc.), mas não convertem entidades.

## Soluções Disponíveis

### Opção 1: Aceitar as Entidades (Mais Simples)

As entidades são legíveis e não quebram o formato. Muitas ferramentas (Excel, Power BI) interpretam corretamente.

### Opção 2: Pós-Processar em Python (Recomendado)

Usar o script `exportar_views_simples.py` que converte automaticamente:

```bash
python reports/exportar_views_simples.py
```

O Python tem a biblioteca `html.unescape()` que converte automaticamente.

### Opção 3: Criar Função PostgreSQL Personalizada

Criar uma função PL/Python no PostgreSQL:

```sql
CREATE OR REPLACE FUNCTION html_unescape(text TEXT)
RETURNS TEXT AS $$
    import html
    return html.unescape(text)
$$ LANGUAGE plpython3u;
```

**Problemas:**
- Requer instalação de PL/Python no PostgreSQL
- Permissões de superuser
- Complexidade adicional

## Recomendação

**Use a Opção 2 (Python)** para exportar os dados:

```bash
cd reports
python exportar_views_simples.py
```

Os arquivos Excel/CSV gerados terão as entidades convertidas automaticamente.

## Arquivo Atualizado

O script `exportar_views_simples.py` foi atualizado para incluir a conversão de entidades HTML automaticamente.

---

**Data:** 2026-07-21
