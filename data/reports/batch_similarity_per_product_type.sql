-- This SQL query calculates the average similarity score for attribute per batch in the results table.
SELECT
  batch_id,
  target_value                         AS product_type,
  COUNT(DISTINCT run_id)               AS num_runs,  -- how many runs scored this "product_type" in this batch
  COUNT(*)                             AS num_offers,             -- how many rows scored "product_type" in this batch
  AVG(similarity_score)                AS avg_similarity_score,    -- mean of those similarity scores
  STDDEV_POP(similarity_score)         AS stddev_similarity_score  -- population‐stddev of those similarity scores
FROM public.results
WHERE attribute = 'product_type'   -- keep only rows where we’re comparing “product_type”
  and (target_value in (
    'Aubergine',
    'Cucumber',
    'Cherry Tomato',
    'Broccoli',
    'Brussels Sprouts',
    'Cauliflower',
    'Kale',
    'Kohlrabi',
    'Pak Choi',
    'Pak Choi Shanghai',
    'Pointed Cabbage Green',
    'Pointed Cabbage Red',
    'Red Cabbage',
    'Savoy Cabbage',
    'Spring Cabbage',
    'Cavolo Nero',
    'Chinese Cabbage',
    'Flat Cabbage',
    'Green Cabbage',
    'Lettuce',
    'Capsicum',
    'Radish',
    'Onion',
    'Zucchini',
    'Rhubarb',
    'Celeriac',
    'Pointed Pepper',
    'Chili Pepper',
    'Chicory'))
GROUP BY
  batch_id,
  target_value
ORDER BY
  target_value,
  batch_id desc;

