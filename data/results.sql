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

select * from inputs





WITH aubergine_rows AS (
  SELECT DISTINCT run_id, target_row_index, runs.input_id--, inputs.value
    FROM public.results
    left join public.runs ON runs.id = results.run_id
    left join public.inputs ON runs.input_id = inputs.id
   WHERE target_value LIKE '%Cucumber%' and runs.batch_id = '20250610131111'
)
SELECT r.*, 
       ar.input_id
       --ar.value 
  FROM public.results r
  JOIN aubergine_rows ar
    ON r.run_id            = ar.run_id
   AND r.target_row_index = ar.target_row_index
   --WHERE attribute = 'variety' and similarity_score != 1


