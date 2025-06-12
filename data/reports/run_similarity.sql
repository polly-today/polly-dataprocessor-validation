-- -----------------------------------------------------------------------------
-- Script: Calculate per-run statistics based on per-offer similarity scores
-- -----------------------------------------------------------------------------
-- This script first aggregates similarity scores at the "offer" level (i.e., 
-- grouping by run_id and target_row_index), computing each offer’s average, count,
-- and standard deviation of attribute‐level similarity scores. Then, it aggregates 
-- those per-offer averages up to the "run" level, yielding one row per run_id 
-- with:
--   1) num_offers:    how many distinct offers (target_row_index) exist in that run
--   2) run_avg_of_offer_avgs:  the mean of all offers’ average similarity scores
--   3) run_stddev_of_offer_avgs: the standard deviation of those offer‐level averages
-- -----------------------------------------------------------------------------

WITH per_offer AS (
  -- Step 1: Aggregate at the offer level for each email (run_id)
  SELECT
    runs.batch_id,
    run_id,
    runs.input_id, 
    target_row_index,
    AVG(similarity_score)        AS offer_avg_similarity,   
      -- Compute the average similarity across all attributes for this single offer.
      -- Each offer may have multiple rows (one per attribute), so we collapse them here.

    COUNT(*)                     AS offer_count,            
      -- Count how many attribute‐level rows contributed to this offer’s average.
      -- This tells us how many attributes were scored for this offer.

    STDDEV_POP(similarity_score) AS offer_stddev_similarity
      -- Compute the population standard deviation of similarity_score within this offer.
      -- If you prefer the sample standard deviation, use STDDEV_SAMP(similarity_score) instead.

  FROM public.results
  left join public.runs ON runs.id = results.run_id
  WHERE
    runs.status = 'completed'  -- Only consider completed runs to ensure data integrity.
    -- You can adjust this condition based on your needs, e.g., to include only certain batches.
  GROUP BY
    runs.batch_id,
    run_id,
    runs.input_id,
    target_row_index
    -- Grouping by both run_id and target_row_index so that each combination
    -- (i.e., each offer within each email) becomes one aggregated row.
)

-- Step 2: Aggregate these per-offer results up to the run (email) level
SELECT
  batch_id,
  run_id,
  input_id,
  COUNT(*)                         AS num_offers,               
    -- Count how many rows exist in the CTE per_offer for this run_id.
    -- Since each row in per_offer represents a unique (run_id, target_row_index),
    -- this effectively counts the number of distinct offers per run.

  AVG(offer_avg_similarity)        AS avg_similarity_across_offers,    
    -- Compute the average of all offer‐level means. This treats each offer’s 
    -- average similarity as one data point, so all offers weight equally, 
    -- regardless of how many attributes each had.

  STDDEV_POP(offer_avg_similarity) AS stddev_similarity_across_offers    
    -- Compute the population standard deviation of the offer‐level averages.
    -- This measures how much “spread” there is between each offer’s average 
    -- similarity within the run. If you want the sample standard deviation,
    -- replace this with STDDEV_SAMP(offer_avg_similarity).

FROM per_offer
-- At this point, per_offer contains one row per (run_id, target_row_index) 
-- with the aggregated metrics for that offer.
GROUP BY
  batch_id,
  input_id,
  run_id
  -- Group by run_id so that the outer query produces one row per email/run.
ORDER BY
  batch_id DESC,
  input_id;
  -- Sort output by run_id for readability. You can change the ordering if needed, 
  -- e.g., ORDER BY run_avg_of_offer_avgs DESC to see the runs with highest 
  -- average offer scores first.

-- End of script
