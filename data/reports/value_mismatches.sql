-- Retrieves all records from the `results` table where the `target_value` does not match the `llm_value`.
SELECT 
    runs.batch_id,
    run_id,
    input_id,
    target_row_index as offer_index,
    attribute,
    target_value,
    llm_value
FROM 
    public.results
left join public.runs ON runs.id = results.run_id
WHERE 
    target_value <> llm_value
ORDER BY 
    batch_id DESC,
    input_id asc,
    run_id,
    target_row_index
    --attribute;