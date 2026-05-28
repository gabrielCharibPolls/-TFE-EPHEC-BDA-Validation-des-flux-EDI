-- Vues KPI (make views, docker init, sync Railway)

CREATE OR REPLACE VIEW v_kpi_status AS
SELECT status, COUNT(*) AS nb_fichiers,
       ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0), 2) AS pct
FROM validation_runs GROUP BY status;

CREATE OR REPLACE VIEW v_errors_by_rule AS
SELECT e.rule_id, COUNT(*) AS nb_violations
FROM validation_errors e JOIN validation_runs r ON r.id = e.run_id
GROUP BY e.rule_id ORDER BY nb_violations DESC;

CREATE OR REPLACE VIEW v_daily_volume AS
SELECT DATE(started_at) AS jour, COUNT(*) AS total,
       COUNT(*) FILTER (WHERE status = 'OK') AS nb_ok,
       COUNT(*) FILTER (WHERE status = 'KO') AS nb_ko,
       COUNT(*) FILTER (WHERE status = 'PARSE_ERROR') AS nb_parse_error,
       ROUND(COUNT(*) FILTER (WHERE status = 'OK') * 100.0 / NULLIF(COUNT(*), 0), 2) AS taux_conformite
FROM validation_runs GROUP BY DATE(started_at) ORDER BY jour DESC;

-- Enrichissement runs + faits commande (buyer_* = SCA)
DROP VIEW IF EXISTS v_lines_enriched;
DROP VIEW IF EXISTS v_runs_enriched;

CREATE VIEW v_runs_enriched AS
SELECT
    r.id                                            AS run_id,
    r.filename,
    r.file_sha256,
    r.status,
    r.error_count,
    r.started_at,
    r.finished_at,
    f.interchange_ref,
    f.message_ref,
    f.document_date,
    DATE(r.started_at)                              AS jour_traitement,
    f.buyer_name                                    AS sca_name,
    f.buyer_gln                                     AS sca_gln,
    f.buyer_city                                    AS sca_city,
    f.buyer_postal                                  AS sca_postal,
    f.supplier_name,
    f.supplier_gln,
    f.delivery_name,
    f.delivery_datetime_raw,
    COALESCE(f.line_count, 0)                       AS line_count,
    COALESCE(f.distinct_gtin_count, 0)              AS distinct_gtin_count
FROM validation_runs r
LEFT JOIN order_facts f ON f.run_id = r.id;

CREATE VIEW v_lines_enriched AS
SELECT
    r.id            AS run_id,
    r.filename,
    r.status,
    f.buyer_name    AS sca_name,
    f.supplier_name,
    f.document_date,
    l.line_number,
    l.gtin,
    l.description,
    l.qty_ordered,
    l.qty_unit,
    NULLIF(l.price_amount, '')::numeric             AS price_amount,
    l.price_qualifier
FROM order_lines l
JOIN validation_runs r ON r.id = l.run_id
LEFT JOIN order_facts f ON f.run_id = r.id;

CREATE OR REPLACE VIEW v_conformite_par_sca AS
SELECT
    f.buyer_name                                    AS sca_name,
    COUNT(*)                                        AS nb_fichiers,
    COUNT(*) FILTER (WHERE r.status = 'OK')         AS nb_ok,
    ROUND(100.0 * COUNT(*) FILTER (WHERE r.status = 'OK')
          / NULLIF(COUNT(*), 0), 1)                 AS taux_conformite_pct,
    SUM(f.line_count)                               AS nb_lignes
FROM validation_runs r
JOIN order_facts f ON f.run_id = r.id
WHERE f.buyer_name IS NOT NULL
GROUP BY f.buyer_name;

CREATE OR REPLACE VIEW v_errors_weekly_matrix AS
SELECT
    DATE_TRUNC('week', r.started_at)::date          AS semaine,
    e.rule_id,
    COUNT(*)                                        AS nb_violations
FROM validation_errors e
JOIN validation_runs r ON r.id = e.run_id
GROUP BY DATE_TRUNC('week', r.started_at)::date, e.rule_id;
