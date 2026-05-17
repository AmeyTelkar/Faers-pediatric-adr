-- Run this to create the stored procedure
CREATE OR REPLACE FUNCTION compute_faers_report(
    p_quarter    TEXT DEFAULT NULL,   -- NULL = ALL quarters
    p_age_group  TEXT DEFAULT NULL    -- NULL = All Age Groups
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_total_patients    BIGINT;
    v_signal_count      BIGINT;
    v_suspect_drugs     BIGINT;
    v_unique_adrs       BIGINT;
    v_age_groups        INT;
    v_age_dist          JSONB;
    v_sex_dist          JSONB;
    v_top_drugs         JSONB;
    v_top_reactions     JSONB;
    v_outcomes          JSONB;
    v_signals           JSONB;
    v_quarter_cond      TEXT;
    v_age_cond          TEXT;
BEGIN
    -- Build filter conditions
    IF p_quarter IS NOT NULL THEN
        v_quarter_cond := format('AND source_quarter = %L', p_quarter);
    ELSE
        v_quarter_cond := 'AND is_superseded = false';
    END IF;

    IF p_age_group IS NOT NULL AND p_age_group != 'all' THEN
        v_age_cond := format('AND age_group = %L', p_age_group);
    ELSE
        v_age_cond := '';
    END IF;

    -- 1. Total patients
    SELECT COUNT(*)
    INTO v_total_patients
    FROM demographics
    WHERE is_superseded = FALSE
      AND (p_quarter IS NULL OR source_quarter = p_quarter)
      AND (p_age_group IS NULL OR p_age_group = 'all' OR age_group = p_age_group);

    -- 2. Signal count (correct: sum across individual quarters, not the ALL row)
    SELECT COUNT(*)
    INTO v_signal_count
    FROM signal_cache
    WHERE is_signal = true
      AND n11 >= 3
      AND (
          CASE WHEN p_quarter IS NOT NULL
               THEN quarter_filter = p_quarter
               ELSE quarter_filter NOT IN ('ALL') AND quarter_filter NOT LIKE '%!_ALL' ESCAPE '!'
          END
      )
      AND (p_age_group IS NULL OR p_age_group = 'all' OR age_group = p_age_group);

    -- 3. Unique suspect drugs count
    SELECT COUNT(DISTINCT drugname_normalized)
    INTO v_suspect_drugs
    FROM signal_cache
    WHERE is_signal = true AND n11 >= 3
      AND (p_quarter IS NULL OR quarter_filter = p_quarter)
      AND (p_age_group IS NULL OR p_age_group = 'all' OR age_group = p_age_group);

    -- 4. Unique ADRs count
    SELECT COUNT(DISTINCT pt_term)
    INTO v_unique_adrs
    FROM signal_cache
    WHERE is_signal = true AND n11 >= 3
      AND (p_quarter IS NULL OR quarter_filter = p_quarter)
      AND (p_age_group IS NULL OR p_age_group = 'all' OR age_group = p_age_group);

    -- 5. Age group count
    SELECT COUNT(DISTINCT age_group)
    INTO v_age_groups
    FROM signal_cache
    WHERE is_signal = true;

    -- 6. Age distribution (build an object like {"CHILD": 123})
    SELECT jsonb_object_agg(COALESCE(age_group, 'UNK'), count)
    INTO v_age_dist
    FROM (
        SELECT age_group, COUNT(*) as count
        FROM demographics
        WHERE is_superseded = false
          AND (p_quarter IS NULL OR source_quarter = p_quarter)
        GROUP BY age_group
    ) sub;

    -- 7. Sex distribution
    SELECT jsonb_object_agg(COALESCE(sex, 'UNK'), count)
    INTO v_sex_dist
    FROM (
        SELECT sex, COUNT(*) as count
        FROM demographics
        WHERE is_superseded = false
          AND (p_quarter IS NULL OR source_quarter = p_quarter)
        GROUP BY sex
    ) sub;

    -- 8. Top 10 suspect drugs
    SELECT jsonb_agg(row_to_json(t))
    INTO v_top_drugs
    FROM (
        SELECT d.drugname_normalized as drug, COUNT(*) as count
        FROM drugs d
        JOIN demographics dem ON d.primaryid = dem.primaryid
        WHERE dem.is_superseded = false
          AND d.role_cod = 'PS'
          AND (p_quarter IS NULL OR dem.source_quarter = p_quarter)
        GROUP BY d.drugname_normalized
        ORDER BY count DESC
        LIMIT 10
    ) t;

    -- 9. Top 10 adverse reactions
    SELECT jsonb_agg(row_to_json(t))
    INTO v_top_reactions
    FROM (
        SELECT r.pt_term as adr, COUNT(*) as count
        FROM reactions r
        JOIN demographics dem ON r.primaryid = dem.primaryid
        WHERE dem.is_superseded = false
          AND (p_quarter IS NULL OR dem.source_quarter = p_quarter)
        GROUP BY r.pt_term
        ORDER BY count DESC
        LIMIT 10
    ) t;

    -- 10. Outcome distribution
    SELECT jsonb_object_agg(outc_cod, count)
    INTO v_outcomes
    FROM (
        SELECT o.outc_cod, COUNT(*) as count
        FROM outcomes o
        JOIN demographics dem ON o.primaryid = dem.primaryid
        WHERE dem.is_superseded = false
          AND (p_quarter IS NULL OR dem.source_quarter = p_quarter)
        GROUP BY o.outc_cod
    ) sub;

    -- 11. ALL signals (no limit — this is the full list for PDF)
    SELECT jsonb_agg(row_to_json(t))
    INTO v_signals
    FROM (
        SELECT
            drugname_normalized,
            pt_term,
            age_group,
            n11,
            is_signal,
            ROUND(prr::numeric, 3)   AS prr,
            ROUND(ror::numeric, 3)   AS ror,
            ROUND(ic025::numeric, 3) AS ic025,
            ROUND(ebgm::numeric, 3)  AS ebgm
        FROM signal_cache
        WHERE (p_quarter IS NULL OR quarter_filter = p_quarter)
          AND (p_age_group IS NULL OR age_group = p_age_group)
          -- Strictly filter to only mathematically confirmed signals
          AND is_signal = true
          AND n11 >= 3
        ORDER BY prr DESC NULLS LAST
    ) t;

    -- Assemble final JSON
    RETURN jsonb_build_object(
        'summary', jsonb_build_object(
            'total_patients',   v_total_patients,
            'total_signals',    v_signal_count,
            'total_suspect_drugs', v_suspect_drugs,
            'total_adverse_reactions', v_unique_adrs,
            'age_distribution', COALESCE(v_age_dist, '{}'::jsonb),
            'sex_distribution', COALESCE(v_sex_dist, '{}'::jsonb)
        ),
        'outcomes',          COALESCE(v_outcomes, '{}'::jsonb),
        'top_drugs',         COALESCE(v_top_drugs, '[]'::jsonb),
        'top_suspect_drugs', COALESCE(v_top_drugs, '[]'::jsonb),
        'top_signals',       COALESCE(v_signals, '[]'::jsonb),
        'top_adverse_reactions', COALESCE(v_top_reactions, '[]'::jsonb),
        'top_reactions',     COALESCE(v_top_reactions, '[]'::jsonb)
    );
END;
$$;
