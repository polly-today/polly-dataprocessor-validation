CREATE TABLE public.runs (
    id                  SERIAL PRIMARY KEY,                                   
    input_id            INTEGER NOT NULL REFERENCES public.inputs(id) ON DELETE CASCADE,
    system_prompt       TEXT NOT NULL,
    status              TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    settings            TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    LLM_output          jsonb DEFAULT '{}'::jsonb    
);



