-- Retrieves all records from the `results` table where the `target_value` does not match the `llm_value`.
SELECT 
    batch_id,
    run_id,
    target_row_index as offer_index,
    attribute,
    target_value,
    llm_value
FROM 
    public.results
WHERE 
    target_value <> llm_value
ORDER BY 
    batch_id DESC, 
    run_id, 
    attribute;