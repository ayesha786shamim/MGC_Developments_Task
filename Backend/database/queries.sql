-- Query 1: conversion rate by lead source.
-- Only sources with at least 200 leads.
-- Best conversion rate first.

SELECT
    source,
    COUNT(*) AS total_leads,
    SUM(converted) AS conversions,
    ROUND(100.0 * SUM(converted) / COUNT(*), 2) AS conversion_rate
FROM leads
GROUP BY source
HAVING COUNT(*) >= 200
ORDER BY conversion_rate DESC;


-- Query 2: find duplicate leads.
-- Same crm_record_hash = same person entered more than once
-- (often by different agents).
-- Prevent this at schema level with UNIQUE (crm_record_hash)
-- in schema.sql.

SELECT
    crm_record_hash,
    COUNT(*) AS times_entered,
    GROUP_CONCAT(lead_id) AS lead_ids
FROM leads
GROUP BY crm_record_hash
HAVING COUNT(*) > 1
ORDER BY times_entered DESC;
