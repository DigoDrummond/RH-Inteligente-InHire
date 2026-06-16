/*
================================================================================
MIGRATION 060: Cria tabela de tradução para motivo_status (notes)
================================================================================

Data: 2026-02-19
Descrição:
  Cria tabela 'motivo_status_traducao' para traduzir códigos de motivo
  (notes) em descrições legíveis em português.

PROBLEMA IDENTIFICADO:
  - API retorna códigos em inglês: 'waiting_schedule', 'feedback_received_from_client'
  - Interface web InHire mostra descrições traduzidas
  - Usuário espera ver: "Cartas enviadas, aguardando retorno de agenda"
  - Mas view mostra apenas: "waiting_schedule"

SOLUÇÃO:
  1. Criar tabela de tradução
  2. Popular com códigos mais comuns e suas traduções
  3. Próxima migration atualizará a view para usar as traduções

COBERTURA INICIAL:
  - Traduções confirmadas: 1 (waiting_schedule)
  - Códigos distintos no banco: 325
  - Estratégia: traduzir os mais comuns primeiro

NOTAS:
  - Traduções podem ser adicionadas manualmente via INSERT
  - Códigos sem tradução serão exibidos como estão (fallback)

================================================================================
*/

-- Criar tabela de tradução
CREATE TABLE IF NOT EXISTS motivo_status_traducao (
    codigo VARCHAR(255) PRIMARY KEY,
    descricao_pt TEXT NOT NULL,
    descricao_en TEXT,
    categoria VARCHAR(100),  -- Ex: 'pausa', 'cancelamento', 'mudanca_estrategia'
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para busca rápida
CREATE INDEX IF NOT EXISTS idx_motivo_traducao_ativo ON motivo_status_traducao(ativo);

-- Popular com traduções conhecidas (baseadas na interface InHire)
INSERT INTO motivo_status_traducao (codigo, descricao_pt, descricao_en, categoria) VALUES
    -- PAUSAS E PENDÊNCIAS
    ('waiting_schedule', 'Cartas enviadas, aguardando retorno de agenda', 'Letters sent, awaiting response regarding scheduling', 'pausa'),
    ('no_client_response', 'Aguardando resposta do cliente', 'Waiting for client response', 'pausa'),
    ('pending_candidate', 'Aguardando candidato', 'Waiting for candidate', 'pausa'),
    ('manager_vacation', 'Gestor em férias', 'Manager on vacation', 'pausa'),

    -- FEEDBACKS E MUDANÇAS
    ('feedback_received_from_client', 'Feedback recebido do cliente', 'Feedback received from client', 'atualizacao'),
    ('strategy_change', 'Mudança de estratégia', 'Strategy change', 'atualizacao'),
    ('profile_change', 'Mudança de perfil', 'Profile change', 'atualizacao'),

    -- FECHAMENTOS
    ('closed_other_vendor', 'Fechado com outro fornecedor', 'Closed with another vendor', 'fechamento'),
    ('closed_internally', 'Fechado internamente', 'Closed internally', 'fechamento'),
    ('client_cancel_no_reason', 'Cliente cancelou sem motivo informado', 'Client canceled without reason', 'cancelamento'),

    -- ORÇAMENTO E PLANEJAMENTO
    ('no_budget', 'Sem orçamento', 'No budget', 'cancelamento'),
    ('budget_review', 'Revisão de orçamento', 'Budget review', 'pausa'),

    -- CONTRATUAIS
    ('contract_issue', 'Problema contratual', 'Contract issue', 'pendencia'),
    ('internal_reallocation', 'Realocação interna', 'Internal reallocation', 'fechamento'),

    -- DERIVADOS (gerados automaticamente pelo sistema)
    ('Derivado da mudança de status da vaga', 'Derivado da mudança de status da vaga', 'Derived from job status change', 'sistema'),
    ('Derivado da contratação na posição', 'Derivado da contratação na posição', 'Derived from position hire', 'sistema')
ON CONFLICT (codigo) DO NOTHING;

-- Comentários
COMMENT ON TABLE motivo_status_traducao IS
'Tabela de tradução dos códigos de motivo (notes) da timeline de posições.
API retorna códigos em inglês, esta tabela fornece as descrições em português.
Criada em 2026-02-19 (Migration 060).';

COMMENT ON COLUMN motivo_status_traducao.codigo IS 'Código retornado pela API (ex: waiting_schedule)';
COMMENT ON COLUMN motivo_status_traducao.descricao_pt IS 'Descrição em português exibida ao usuário';
COMMENT ON COLUMN motivo_status_traducao.descricao_en IS 'Descrição em inglês (referência)';
COMMENT ON COLUMN motivo_status_traducao.categoria IS 'Categoria do motivo: pausa, cancelamento, fechamento, etc.';
COMMENT ON COLUMN motivo_status_traducao.ativo IS 'Se FALSE, tradução não será usada';

-- Trigger para atualizar timestamp
CREATE OR REPLACE FUNCTION update_motivo_traducao_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_motivo_traducao_timestamp
    BEFORE UPDATE ON motivo_status_traducao
    FOR EACH ROW
    EXECUTE FUNCTION update_motivo_traducao_timestamp();

-- ================================================================================
-- ESTATÍSTICAS E VALIDAÇÃO
-- ================================================================================

-- Mostrar traduções criadas
SELECT
    'Total de traduções criadas: ' || COUNT(*) AS info
FROM motivo_status_traducao;

-- Mostrar códigos sem tradução (top 10 mais frequentes)
SELECT
    'Códigos SEM tradução (top 10):' AS info,
    pt.notes AS codigo,
    COUNT(*) AS qtd,
    ROUND(COUNT(*)::NUMERIC / (SELECT COUNT(*) FROM position_timeline WHERE notes IS NOT NULL) * 100, 1) || '%' AS percentual
FROM position_timeline pt
LEFT JOIN motivo_status_traducao mst ON mst.codigo = pt.notes
WHERE pt.notes IS NOT NULL
  AND pt.notes NOT LIKE '%@%'  -- Ignorar emails/nomes
  AND mst.codigo IS NULL
GROUP BY pt.notes
ORDER BY COUNT(*) DESC
LIMIT 10;
