-- Migration 079: Decodificar entidades HTML na descrição
-- Data: 2026-07-22
-- Autor: Claude Code
-- Descrição:
--   Criar função para decodificar entidades HTML e aplicar na view vw_relatorio_requisicoes

-- ============================================================================
-- 1. CRIAR FUNÇÃO PARA DECODIFICAR ENTIDADES HTML
-- ============================================================================

CREATE OR REPLACE FUNCTION decode_html_entities(input_text TEXT)
RETURNS TEXT AS $$
DECLARE
    result TEXT;
BEGIN
    IF input_text IS NULL THEN
        RETURN NULL;
    END IF;

    result := input_text;

    -- Entidades básicas
    result := REPLACE(result, '&nbsp;', ' ');
    result := REPLACE(result, '&amp;', '&');
    result := REPLACE(result, '&lt;', '<');
    result := REPLACE(result, '&gt;', '>');
    result := REPLACE(result, '&quot;', '"');
    result := REPLACE(result, '&apos;', '''');

    -- Vogais com acento agudo (minúsculas)
    result := REPLACE(result, '&aacute;', 'á');
    result := REPLACE(result, '&eacute;', 'é');
    result := REPLACE(result, '&iacute;', 'í');
    result := REPLACE(result, '&oacute;', 'ó');
    result := REPLACE(result, '&uacute;', 'ú');

    -- Vogais com acento agudo (maiúsculas)
    result := REPLACE(result, '&Aacute;', 'Á');
    result := REPLACE(result, '&Eacute;', 'É');
    result := REPLACE(result, '&Iacute;', 'Í');
    result := REPLACE(result, '&Oacute;', 'Ó');
    result := REPLACE(result, '&Uacute;', 'Ú');

    -- Vogais com acento circunflexo (minúsculas)
    result := REPLACE(result, '&acirc;', 'â');
    result := REPLACE(result, '&ecirc;', 'ê');
    result := REPLACE(result, '&icirc;', 'î');
    result := REPLACE(result, '&ocirc;', 'ô');
    result := REPLACE(result, '&ucirc;', 'û');

    -- Vogais com acento circunflexo (maiúsculas)
    result := REPLACE(result, '&Acirc;', 'Â');
    result := REPLACE(result, '&Ecirc;', 'Ê');
    result := REPLACE(result, '&Icirc;', 'Î');
    result := REPLACE(result, '&Ocirc;', 'Ô');
    result := REPLACE(result, '&Ucirc;', 'Û');

    -- Vogais com til (minúsculas)
    result := REPLACE(result, '&atilde;', 'ã');
    result := REPLACE(result, '&otilde;', 'õ');
    result := REPLACE(result, '&ntilde;', 'ñ');

    -- Vogais com til (maiúsculas)
    result := REPLACE(result, '&Atilde;', 'Ã');
    result := REPLACE(result, '&Otilde;', 'Õ');
    result := REPLACE(result, '&Ntilde;', 'Ñ');

    -- Vogais com crase (minúsculas)
    result := REPLACE(result, '&agrave;', 'à');
    result := REPLACE(result, '&egrave;', 'è');
    result := REPLACE(result, '&igrave;', 'ì');
    result := REPLACE(result, '&ograve;', 'ò');
    result := REPLACE(result, '&ugrave;', 'ù');

    -- Vogais com crase (maiúsculas)
    result := REPLACE(result, '&Agrave;', 'À');
    result := REPLACE(result, '&Egrave;', 'È');
    result := REPLACE(result, '&Igrave;', 'Ì');
    result := REPLACE(result, '&Ograve;', 'Ò');
    result := REPLACE(result, '&Ugrave;', 'Ù');

    -- Cedilha
    result := REPLACE(result, '&ccedil;', 'ç');
    result := REPLACE(result, '&Ccedil;', 'Ç');

    RETURN result;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION decode_html_entities(TEXT) IS
'Decodifica entidades HTML comuns para caracteres UTF-8.
Suporta acentos portugueses (á, é, í, ó, ú, â, ê, ô, ã, õ, ç, etc.)
Migration 079 (2026-07-22)';


-- ============================================================================
-- 2. ATUALIZAR VIEW DE REQUISIÇÕES
-- ============================================================================

DROP VIEW IF EXISTS vw_relatorio_requisicoes CASCADE;

CREATE OR REPLACE VIEW vw_relatorio_requisicoes AS
SELECT
    r.id,
    r.inhire_id,
    v.name AS titulo,
    cl.name AS cliente,
    get_custom_field_value(r.custom_fields, 'Empresa') AS empresa,
    r.approval_workflow->>'name' AS nome_workflow_aprovacao,

    -- Descrição limpa (sem HTML) e com entidades decodificadas
    TRIM(
        decode_html_entities(
            REGEXP_REPLACE(
                REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        COALESCE(r.description, ''),
                        '<[^>]+>', '', 'g'
                    ),
                    '&nbsp;', ' ', 'g'
                ),
                '\s+', ' ', 'g'
            )
        )
    ) AS descricao,

    r.requested_at AT TIME ZONE 'America/Sao_Paulo' AS data_solicitacao,
    r.status,
    r.created_at,
    r.updated_at

FROM requisicoes r
INNER JOIN vagas v ON r.job_inhire_id = v.inhire_id
LEFT JOIN clientes cl ON cl.inhire_id = v.tenant_client_id
WHERE r.requested_at IS NOT NULL
  AND v.name IS NOT NULL
  AND TRIM(v.name) != ''
ORDER BY r.requested_at DESC;

COMMENT ON VIEW vw_relatorio_requisicoes IS
'Relatório de requisições - TODAS as empresas e workflows.

 Colunas disponíveis para filtro:
 - cliente: Nome do cliente (via clientes.name)
 - empresa: Empresa da requisição (via requisicoes.custom_fields.Empresa)
 - nome_workflow_aprovacao: Nome do workflow (via requisicoes.approval_workflow->>"name")

 Filtros básicos:
 - Apenas requisições com data de solicitação
 - Apenas vagas com título preenchido

 Migration 079 (2026-07-22):
 - ADICIONADO: Função decode_html_entities() para decodificar entidades HTML
 - CORRIGIDO: Campo descricao agora retorna texto legível (sem &oacute;, &ecirc;, etc.)
 - Remove tags HTML e decodifica entidades para UTF-8';
