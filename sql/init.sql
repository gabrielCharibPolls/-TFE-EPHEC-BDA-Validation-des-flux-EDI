-- Schéma minimal pour le TFE : traçabilité des validations EDI (.ORO / ORDERS)

CREATE TABLE IF NOT EXISTS validation_runs (
    id              BIGSERIAL PRIMARY KEY,
    filename        TEXT NOT NULL,
    file_sha256     CHAR(64) NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('OK', 'KO', 'PARSE_ERROR')),
    error_count     INT NOT NULL DEFAULT 0,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS validation_errors (
    id              BIGSERIAL PRIMARY KEY,
    run_id          BIGINT NOT NULL REFERENCES validation_runs (id) ON DELETE CASCADE,
    rule_id         TEXT NOT NULL,
    message         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_validation_errors_run ON validation_errors (run_id);
CREATE INDEX IF NOT EXISTS idx_validation_runs_status ON validation_runs (status);
CREATE INDEX IF NOT EXISTS idx_validation_runs_started ON validation_runs (started_at DESC);
