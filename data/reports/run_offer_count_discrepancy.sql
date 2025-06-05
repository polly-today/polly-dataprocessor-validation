-- -----------------------------------------------------------------------------
-- Query: For each run_id, count how many distinct LLM‐extracted offers (llm_row_index)
-- and how many distinct target offers (target_row_index) exist, then compute their difference.
-- -----------------------------------------------------------------------------
SELECT
  run_id,

  -- Count distinct llm_row_index values to see how many offers the LLM output contained
  COUNT(DISTINCT llm_row_index)   AS num_llm_offers,

  -- Count distinct target_row_index values to see how many offers the target output contained
  COUNT(DISTINCT target_row_index) AS num_target_offers,

  -- Compute the difference between LLM‐offer count and target‐offer count
  (COUNT(DISTINCT llm_row_index) - COUNT(DISTINCT target_row_index)) AS difference
FROM public.results
GROUP BY
  batch_id, run_id
ORDER BY
  batch_id DESC, run_id;
