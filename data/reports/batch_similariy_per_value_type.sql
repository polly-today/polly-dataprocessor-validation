-- -----------------------------------------------------------------------------
-- Stepwise aggregation of similarity_score by:
--   1) Offer (target_row_index) × value_type  → per‐offer metrics
--   2) Run (run_id) × value_type             → per‐run metrics
--   3) Batch (batch_id) × value_type         → per‐batch metrics,
--      now including counts of runs and offers per (batch_id, value_type)
-- -----------------------------------------------------------------------------

WITH per_offer AS (
  ---------------------------------------------------------------------------------
  -- 1) Compute each offer’s statistics for a given value_type.
  --    “Offer” is identified by (run_id, target_row_index).
  ---------------------------------------------------------------------------------
  SELECT
    r.run_id,
    rn.batch_id,
    i.value_type,
    r.target_row_index,

    -- Average similarity across all attributes of this one offer (within a single run).
    AVG(r.similarity_score)        AS offer_avg_similarity,

    -- How many attribute‐level rows contributed to this offer+value_type.
    COUNT(*)                       AS offer_count,

    -- Population standard deviation of similarity_score within this offer+value_type.
    STDDEV_POP(r.similarity_score) AS offer_stddev_similarity

  FROM public.results AS r
  LEFT JOIN public.runs    AS rn ON r.run_id    = rn.id
  LEFT JOIN public.inputs  AS i  ON rn.input_id = i.id
  WHERE i.value_type IS NOT NULL
    -- Only include rows that have a non-null value_type
  GROUP BY
    r.run_id,
    rn.batch_id,
    i.value_type,
    r.target_row_index
    -- Group by run_id, batch_id, value_type, and target_row_index so that
    -- each row here represents metrics for one distinct offer within one run.
),

per_run AS (
  ---------------------------------------------------------------------------------
  -- 2) Collapse per_offer up to run × value_type.
  --    Each row in per_offer is one (run_id, target_row_index, value_type).
  --    We want:
  --      • num_offers_in_run: the number of distinct offers for this run×value_type
  --      • run_avg_of_offer_avgs: average of those offer_avg_similarity values
  --      • run_stddev_of_offer_avgs: stddev of those offer_avg_similarity values
  --      • (Optionally) run_avg_offer_count and run_avg_offer_stddev for further insight
  ---------------------------------------------------------------------------------
  SELECT
    run_id,
    batch_id,
    value_type,

    COUNT(*)                              AS num_offers_in_run,
      -- “per_offer” has one row per (run_id, target_row_index, value_type),
      -- so COUNT(*) gives the number of distinct offers for this run×value_type.

    AVG(offer_avg_similarity)            AS run_avg_of_offer_avgs,
      -- Treat each offer’s average as a single data point, so each offer
      -- contributes equally, regardless of how many attributes it had.

    STDDEV_POP(offer_avg_similarity)      AS run_stddev_of_offer_avgs,
      -- Stddev of those offer-level averages within this run×value_type.

    AVG(offer_count)                      AS run_avg_offer_count,
      -- (Optional) Average number of attributes per offer within this run×value_type.

    AVG(offer_stddev_similarity)          AS run_avg_offer_stddev
      -- (Optional) Average of per-offer attribute-level stddevs.

  FROM per_offer
  GROUP BY
    run_id,
    batch_id,
    value_type
),

per_batch AS (
  ---------------------------------------------------------------------------------
  -- 3) Finally, roll per_run up to batch × value_type.
  --    Each row in per_run is one (run_id, batch_id, value_type).
  --    We want:
  --      • num_runs_in_batch:    how many runs contributed for this (batch_id, value_type)
  --      • total_offers_in_batch: total number of offers across those runs
  --      • batch_avg_of_run_avgs: average of run_avg_of_offer_avgs across all runs
  --      • batch_stddev_of_run_avgs: stddev of run_avg_of_offer_avgs across runs
  ---------------------------------------------------------------------------------
  SELECT
    batch_id,
    value_type,

    COUNT(*)                             AS num_runs_in_batch,
      -- Count how many distinct (run_id)s exist per batch×value_type.

    SUM(num_offers_in_run)               AS total_offers_in_batch,
      -- Sum up the number of offers from each run, giving the total offers
      -- across all runs in this batch×value_type.

    AVG(run_avg_of_offer_avgs)           AS batch_avg_of_run_avgs,
      -- Average across all run-level averages for this batch×value_type.
      -- Each run contributes one run_avg_of_offer_avgs.

    STDDEV_POP(run_avg_of_offer_avgs)     AS batch_stddev_of_run_avgs
      -- Stddev of those run-level averages within this batch×value_type.

  FROM per_run
  GROUP BY
    batch_id,
    value_type
)

-- Final SELECT: show per-batch × value_type aggregation with counts of runs and offers
SELECT
  batch_id,
  value_type,
  num_runs_in_batch,             -- How many runs contributed to this batch×value_type
  total_offers_in_batch,         -- Total offers across all those runs
  batch_avg_of_run_avgs  AS mean_similarity_across_runs,   -- Mean of per-run offer averages
  batch_stddev_of_run_avgs AS stddev_similarity_across_runs  -- Stddev of per-run offer averages
FROM per_batch
ORDER BY
  batch_id DESC,
  value_type;
