-- Calculates the average similarity score for each offer (per run per batch) in the results table.
-- The average similarity score is the average of all attributes for the offer.
SELECT
    results.batch_id,
    results.run_id,
    runs.input_id, 
    target_row_index AS offer_index,
    AVG(similarity_score) AS similarity_score 
FROM public.results
left join public.runs ON runs.id = results.run_id
GROUP BY
    results.batch_id,
    results.run_id,
    runs.input_id,
    target_row_index
ORDER BY
    results.batch_id DESC,
    results.run_id,
    target_row_index;