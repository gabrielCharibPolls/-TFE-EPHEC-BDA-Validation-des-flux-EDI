-- Faits commande extraits des .ORO (schéma aligné sur le validateur / Qlik)

CREATE TABLE IF NOT EXISTS order_facts (
    run_id                  BIGINT PRIMARY KEY REFERENCES validation_runs (id) ON DELETE CASCADE,
    interchange_ref         TEXT,
    message_ref             TEXT,
    document_ref            TEXT,
    message_type            TEXT,
    message_version         TEXT,
    document_date           DATE,
    delivery_datetime_raw   TEXT,
    unb_date                DATE,
    unb_time                TEXT,
    unb_emitter_gln         TEXT,
    unb_recipient_gln       TEXT,
    header_sent_at          TEXT,
    header_from_gln         TEXT,
    header_to_gln           TEXT,
    buyer_gln               TEXT,
    buyer_name              TEXT,
    buyer_city              TEXT,
    buyer_postal            TEXT,
    supplier_gln            TEXT,
    supplier_name           TEXT,
    delivery_gln            TEXT,
    delivery_name           TEXT,
    invoice_gln             TEXT,
    invoice_name            TEXT,
    line_count              INT NOT NULL DEFAULT 0,
    distinct_gtin_count     INT NOT NULL DEFAULT 0,
    dtm_json                TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS order_lines (
    id              BIGSERIAL PRIMARY KEY,
    run_id          BIGINT NOT NULL REFERENCES validation_runs (id) ON DELETE CASCADE,
    line_number     TEXT,
    gtin            TEXT,
    description     TEXT,
    qty_ordered     TEXT,
    qty_unit        TEXT,
    price_amount    TEXT,
    price_qualifier TEXT
);

CREATE INDEX IF NOT EXISTS idx_order_lines_run ON order_lines (run_id);
CREATE INDEX IF NOT EXISTS idx_order_lines_gtin ON order_lines (gtin);
CREATE INDEX IF NOT EXISTS idx_order_facts_buyer ON order_facts (buyer_name);
CREATE INDEX IF NOT EXISTS idx_order_facts_document_date ON order_facts (document_date);
CREATE INDEX IF NOT EXISTS idx_order_facts_supplier ON order_facts (supplier_name);
