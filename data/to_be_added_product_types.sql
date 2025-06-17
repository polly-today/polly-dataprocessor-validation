CREATE TABLE public.to_be_added_product_types (
    batch_id      TEXT        NOT NULL,
    input_id      INTEGER     NOT NULL   REFERENCES public.inputs(id) ON DELETE CASCADE,
    product_type TEXT        NOT NULL
    );