-- Calculate average similarity score per attribute per batch
SELECT
    runs.batch_id,
    results.attribute,
    COUNT(DISTINCT results.run_id) AS num_runs,    -- Number of unique runs for this attribute in this batch
    COUNT(*) AS num_offers,                          -- Number of rows for this attribute in this batch
    AVG(results.similarity_score) AS mean_similarity_score,
    STDDEV_POP(results.similarity_score) AS stddev_similarity_score  -- Population stddev of similarity scores for this attribute
FROM
    public.results AS results
    LEFT JOIN public.runs AS runs ON results.run_id = runs.id
    LEFT JOIN public.inputs AS inputs ON runs.input_id = inputs.id
WHERE runs.batch_id = '20250617153247'  -- Filter for a specific batch
GROUP BY
    runs.batch_id,
    results.attribute
ORDER BY
    runs.batch_id DESC,
    results.attribute;