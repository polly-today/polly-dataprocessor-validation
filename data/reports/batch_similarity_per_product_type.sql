-- This SQL query calculates the average similarity score for attribute per batch in the results table.
SELECT
  batch_id,
  target_value                         AS product_type,
  COUNT(DISTINCT run_id)               AS num_runs,  -- how many runs scored this "product_type" in this batch
  COUNT(*)                             AS num_offers,             -- how many rows scored "product_type" in this batch
  AVG(similarity_score)                AS avg_similarity_score,    -- mean of those similarity scores
  STDDEV_POP(similarity_score)         AS stddev_similarity_score  -- population‐stddev of those similarity scores
FROM public.results
WHERE attribute = 'product_type'       -- keep only rows where we’re comparing “product_type”
GROUP BY
  batch_id,
  target_value
ORDER BY
  batch_id,
  target_value;