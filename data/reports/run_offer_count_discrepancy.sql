-- -----------------------------------------------------------------------------
-- Query: For each run_id, count how many distinct LLM‐extracted offers (llm_row_index)
-- and how many distinct target offers (target_row_index) exist, then compute their difference.
-- -----------------------------------------------------------------------------
SELECT
  runs.batch_id,          -- The batch identifier for grouping runs
  results.run_id,
  runs.input_id,

  -- Count distinct llm_row_index values to see how many offers the LLM output contained
  COUNT(DISTINCT llm_row_index)   AS num_llm_offers,

  -- Count distinct target_row_index values to see how many offers the target output contained
  COUNT(DISTINCT target_row_index) AS num_target_offers,

  -- Compute the difference between LLM‐offer count and target‐offer count
  (COUNT(DISTINCT llm_row_index) - COUNT(DISTINCT target_row_index)) AS difference
FROM public.results
left join public.runs ON runs.id = results.run_id
GROUP BY
  runs.batch_id, results.run_id, runs.input_id
ORDER BY
  runs.batch_id DESC, runs.input_id;
