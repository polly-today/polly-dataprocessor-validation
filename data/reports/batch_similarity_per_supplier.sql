-- Calculate average similarity score per attribute per batch
SELECT
    runs.batch_id,
    inputs.id, 
    inputs.supplier_name AS supplier_name,  -- Include supplier name for better context
    COUNT(DISTINCT (results.run_id, results.target_row_index)) AS num_offers,
    COUNT(DISTINCT results.run_id) AS num_runs,    -- Number of unique runs for this attribute in this batch
    AVG(results.similarity_score) AS mean_similarity_score,
    STDDEV_POP(results.similarity_score) AS stddev_similarity_score  -- Population stddev of similarity scores for this attribute
FROM
    public.results AS results
    LEFT JOIN public.runs AS runs ON results.run_id = runs.id
    LEFT JOIN public.inputs AS inputs ON runs.input_id = inputs.id
GROUP BY
    runs.batch_id,
    inputs.supplier_name,
    inputs.id
ORDER BY
    runs.batch_id DESC,
    inputs.id asc;