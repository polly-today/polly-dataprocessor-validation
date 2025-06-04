

CREATE TABLE public.runs (
    id            UUID        PRIMARY KEY    DEFAULT gen_random_uuid(),   -- or no DEFAULT if you supply it
    batch_id      TEXT        NOT NULL,
    input_id      INTEGER     NOT NULL   REFERENCES public.inputs(id) ON DELETE CASCADE,
    system_prompt TEXT        NOT NULL,
    status        TEXT        NOT NULL   CHECK (status IN ('pending','running','completed','failed')),
    settings      TEXT,
    created_at    TIMESTAMPTZ NOT NULL   DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL   DEFAULT now(),
    LLM_output    JSONB       DEFAULT '{}'::jsonb,
    error_message TEXT        DEFAULT NULL
);


select * from inputs;

select * from runs;


