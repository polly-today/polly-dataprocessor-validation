-- Calculates the average similarity score for each offer (per run per batch) in the results table.
-- The average similarity score is the average of all attributes for the offer.
SELECT
    batch_id,
    run_id,
    target_row_index AS offer_index,
    AVG(similarity_score) AS similarity_score 
FROM public.results
GROUP BY
    batch_id,
    run_id,
    target_row_index
ORDER BY
    batch_id DESC,
    run_id,
    target_row_index;