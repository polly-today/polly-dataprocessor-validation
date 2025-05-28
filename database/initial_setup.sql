-- CREATE TABLE IF NOT EXISTS public.inputs (
--     id UUID NOT NULL DEFAULT gen_random_uuid(),
--     supplier_name TEXT NOT NULL,
--     sender TEXT NOT NULL,
--     date TIMESTAMP NULL,
--     subject TEXT NULL,
--     type TEXT NOT NULL, -- txt, pdf, xlsx, image
--     source TEXT NOT NULL, -- email, whatsapp
--     value TEXT NOT NULL,
--     s3_url TEXT NULL,
--     created_at timestamp with time zone NOT NULL DEFAULT now(),
--     updated_at timestamp with time zone NOT NULL DEFAULT now(),

--     CONSTRAINT inputs_pk PRIMARY KEY (id)
-- );

-- CREATE TABLE IF NOT EXISTS public.runs (
--     id UUID NOT NULL DEFAULT gen_random_uuid(),
--     input_id UUID NOT NULL,
--     status TEXT NOT NULL, -- pending, processing, completed, failed
--     result TEXT NULL,
--     created_at timestamp with time zone NOT NULL DEFAULT now(),
--     updated_at timestamp with time zone NOT NULL DEFAULT now(),

--     CONSTRAINT runs_pk PRIMARY KEY (id),
--     CONSTRAINT runs_input_id_fk FOREIGN KEY (input_id) REFERENCES public.inputs(id) ON DELETE CASCADE
-- );


