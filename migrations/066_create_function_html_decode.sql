-- ===============================================================
-- Migration 066: Criar Função para Decodificar Entidades HTML
-- ===============================================================
-- Cria função que converte entidades HTML para caracteres Unicode
-- Exemplos: &eacute; → é, &aacute; → á, &atilde; → ã
--
-- Data: 2026-07-21
-- ===============================================================

-- Criar função para decodificar entidades HTML
CREATE OR REPLACE FUNCTION html_decode(text_input TEXT)
RETURNS TEXT AS $$
DECLARE
    result TEXT;
BEGIN
    result := text_input;

    -- Entidades HTML mais comuns em português
    result := REPLACE(result, '&aacute;', 'á');
    result := REPLACE(result, '&Aacute;', 'Á');
    result := REPLACE(result, '&acirc;', 'â');
    result := REPLACE(result, '&Acirc;', 'Â');
    result := REPLACE(result, '&agrave;', 'à');
    result := REPLACE(result, '&Agrave;', 'À');
    result := REPLACE(result, '&atilde;', 'ã');
    result := REPLACE(result, '&Atilde;', 'Ã');

    result := REPLACE(result, '&eacute;', 'é');
    result := REPLACE(result, '&Eacute;', 'É');
    result := REPLACE(result, '&ecirc;', 'ê');
    result := REPLACE(result, '&Ecirc;', 'Ê');

    result := REPLACE(result, '&iacute;', 'í');
    result := REPLACE(result, '&Iacute;', 'Í');

    result := REPLACE(result, '&oacute;', 'ó');
    result := REPLACE(result, '&Oacute;', 'Ó');
    result := REPLACE(result, '&ocirc;', 'ô');
    result := REPLACE(result, '&Ocirc;', 'Ô');
    result := REPLACE(result, '&otilde;', 'õ');
    result := REPLACE(result, '&Otilde;', 'Õ');

    result := REPLACE(result, '&uacute;', 'ú');
    result := REPLACE(result, '&Uacute;', 'Ú');
    result := REPLACE(result, '&ucirc;', 'û');
    result := REPLACE(result, '&Ucirc;', 'Û');

    result := REPLACE(result, '&ccedil;', 'ç');
    result := REPLACE(result, '&Ccedil;', 'Ç');

    -- Entidades HTML especiais
    result := REPLACE(result, '&nbsp;', ' ');
    result := REPLACE(result, '&quot;', '"');
    result := REPLACE(result, '&apos;', '''');
    result := REPLACE(result, '&lt;', '<');
    result := REPLACE(result, '&gt;', '>');
    result := REPLACE(result, '&amp;', '&');

    RETURN result;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Comentário
COMMENT ON FUNCTION html_decode(TEXT) IS 'Converte entidades HTML para caracteres Unicode (ex: &eacute; → é)';

-- Log
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 066: Função html_decode() criada com sucesso';
    RAISE NOTICE '   Exemplo de uso: SELECT html_decode(''Experi&ecirc;ncia'') → Experiência';
END $$;
