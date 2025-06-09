-- -----------------------------------------------------------------------------
-- Stepwise aggregation of similarity_score by:
--   1) Offer (target_row_index) → per‐offer metrics
--   2) Run (run_id)           → per‐run metrics
--   3) Batch (batch_id)       → per‐batch metrics,
--      now without grouping by value_type
-- -----------------------------------------------------------------------------

WITH per_offer AS (
  ---------------------------------------------------------------------------------
  -- 1) Compute statistics for each offer within a run.
  --    “Offer” is identified by (run_id, target_row_index).
  ---------------------------------------------------------------------------------
  SELECT
    r.run_id,
    rn.batch_id,
    r.target_row_index,

    -- Average similarity across all attributes of this one offer.
    AVG(r.similarity_score)        AS offer_avg_similarity,

    -- How many attribute‐level rows contributed to this offer’s average.
    COUNT(*)                       AS offer_count,

    -- Population standard deviation of similarity_score within this offer.
    STDDEV_POP(r.similarity_score) AS offer_stddev_similarity

  FROM public.results AS r
  LEFT JOIN public.runs AS rn
    ON r.run_id = rn.id
  GROUP BY
    r.run_id,
    rn.batch_id,
    r.target_row_index
    -- Group by run_id, batch_id, and target_row_index so each row in per_offer
    -- represents one distinct offer within a specific run.
),

per_run AS (
  ---------------------------------------------------------------------------------
  -- 2) Collapse per_offer up to the run level.
  --    Each row in per_offer corresponds to one (run_id, target_row_index).
  --    We want:
  --      • num_offers_in_run: number of offers in this run
  --      • run_avg_of_offer_avgs: average of offer_avg_similarity across offers
  --      • run_stddev_of_offer_avgs: stddev of offer_avg_similarity across offers
  ---------------------------------------------------------------------------------
  SELECT
    run_id,
    batch_id,

    COUNT(*)                              AS num_offers_in_run,
      -- per_offer has one row per offer, so COUNT(*) gives how many offers in this run.

    AVG(offer_avg_similarity)            AS run_avg_of_offer_avgs,
      -- Treat each offer’s average as a data point so every offer counts equally.

    STDDEV_POP(offer_avg_similarity)      AS run_stddev_of_offer_avgs,
      -- Stddev of those offer-level averages within this run.

    AVG(offer_count)                      AS run_avg_offer_count,
      -- (Optional) Average number of attributes per offer in this run.

    AVG(offer_stddev_similarity)          AS run_avg_offer_stddev
      -- (Optional) Average of per-offer stddevs (attribute-level spread).

  FROM per_offer
  GROUP BY
    run_id,
    batch_id
    -- Group by run_id and batch_id so that each row here represents one run.
),

per_batch AS (
  ---------------------------------------------------------------------------------
  -- 3) Finally, roll per_run up to the batch level.
  --    Each row in per_run corresponds to one run.
  --    We want:
  --      • num_runs_in_batch: how many runs in this batch
  --      • total_offers_in_batch: sum of all offers across runs
  --      • batch_avg_of_run_avgs: average of run_avg_of_offer_avgs across runs
  --      • batch_stddev_of_run_avgs: stddev of run_avg_of_offer_avgs across runs
  ---------------------------------------------------------------------------------
  SELECT
    batch_id,

    COUNT(*)                             AS num_runs_in_batch,
      -- Count how many runs contributed to this batch.

    SUM(num_offers_in_run)               AS total_offers_in_batch,
      -- Sum of offers across all runs in this batch.

    AVG(run_avg_of_offer_avgs)           AS batch_avg_of_run_avgs,
      -- Average across all run-level averages for this batch.

    STDDEV_POP(run_avg_of_offer_avgs)     AS batch_stddev_of_run_avgs
      -- Stddev of those run-level averages within this batch.

  FROM per_run
  GROUP BY
    batch_id
    -- Group by batch_id so each row here represents one batch.
)

-- Final SELECT: per-batch aggregation with counts of runs and offers
SELECT
  batch_id,
  num_runs_in_batch,             -- Number of runs contributing to this batch
  total_offers_in_batch,         -- Total offers across all those runs
  batch_avg_of_run_avgs   AS mean_similarity_across_runs,   -- Mean of per-run offer averages
  batch_stddev_of_run_avgs AS stddev_similarity_across_runs  -- Stddev of per-run offer averages
FROM per_batch
where batch_id = '20250609191603'
ORDER BY
  batch_id DESC;
