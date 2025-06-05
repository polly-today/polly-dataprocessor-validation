-- Retrieves all records from the `results` table where the `target_value` does not match the `llm_value`.
SELECT 
    batch_id,
    run_id,
    attribute,
    target_value,
    llm_value
FROM 
    public.results
WHERE 
    target_value <> llm_value
   AND  attribute = 'country'
ORDER BY 
    batch_id DESC, 
    run_id, 
    attribute;