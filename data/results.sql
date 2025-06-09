create table public.results (
    run_id       UUID        NOT NULL REFERENCES public.runs(id) ON DELETE CASCADE, 
    batch_id     TEXT       NOT NULL,
    target_row_index  INTEGER,
    llm_row_index     INTEGER,
    attribute   TEXT       NOT NULL,
    target_value TEXT       NOT NULL,
    llm_value   TEXT       NOT NULL,
    similarity_score    FLOAT8 DEFAULT NULL
);



WITH aubergine_rows AS (
  SELECT DISTINCT run_id, target_row_index
    FROM public.results
   WHERE target_value LIKE '%Aubergine%' and batch_id = '20250609162700'
)
SELECT r.*
  FROM public.results r
  JOIN aubergine_rows ar
    ON r.run_id            = ar.run_id
   AND r.target_row_index = ar.target_row_index
   --WHERE r.target_value LIKE 'Cherry Tomat%' 


