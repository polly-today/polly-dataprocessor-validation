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

select * from public.results
where run_id = '71116e15-8f0c-47a8-9d61-5bb25b88bf42' and llm_value = '7.0'
order by batch_id desc;

select * from inputs
order by id asc;

