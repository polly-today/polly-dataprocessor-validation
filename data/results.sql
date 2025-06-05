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




