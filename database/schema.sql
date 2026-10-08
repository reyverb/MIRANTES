-- Schema para banco de dados de descargas
-- Execute este SQL no Supabase SQL Editor

-- Criar tabela de descargas
CREATE TABLE IF NOT EXISTS descargas (
    id SERIAL PRIMARY KEY,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data DATE NOT NULL,
    volume DECIMAL(10,2) NOT NULL,
    produto VARCHAR(100) NOT NULL,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar índice para consultas por data
CREATE INDEX IF NOT EXISTS idx_descargas_data ON descargas(data DESC);

-- Criar índice para consultas por produto
CREATE INDEX IF NOT EXISTS idx_descargas_produto ON descargas(produto);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_descargas_updated_at
    BEFORE UPDATE ON descargas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comentários nas colunas
COMMENT ON TABLE descargas IS 'Registro histórico de descargas de produtos';
COMMENT ON COLUMN descargas.data_hora IS 'Data e hora do registro';
COMMENT ON COLUMN descargas.data IS 'Data da descarga';
COMMENT ON COLUMN descargas.volume IS 'Volume descarregado (unidade)';
COMMENT ON COLUMN descargas.produto IS 'Nome do produto descarregado';
COMMENT ON COLUMN descargas.observacoes IS 'Observações adicionais sobre a descarga';