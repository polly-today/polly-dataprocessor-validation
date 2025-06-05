import pandas as pd
import uuid
import json
import asyncio
from llm_data_extractor import get_chat_gpt_response
from utils import get_args, load_prompt, load_inputs, insert_run, update_run, dispose_engine, update_results
from comparator import compare_llm_to_target_output
from config import (
    manual_prompt_path,
    response_schema_path
)

async def main():
    # Fetch all possible inputs to validate
    # TODO: Add missing values to the inputs table
    inputs = load_inputs()

    # Get command line arguments and provide inputs to specify the option to choose from
    args = get_args(inputs=inputs)
    # Get prompt based on user choice
    if args.prompt == "default":
        print("Using default prompt.")
        return
    elif args.prompt == "manual":
        print(f"Using manual prompt from {manual_prompt_path}.")
        system_prompt = load_prompt(manual_prompt_path)
    # Get inputs to validate
    if args.inputs is not None:
        print(f"Validating inputs: {args.inputs}")
        input_ids_to_validate = inputs[inputs["id"].isin(args.inputs)]["id"].tolist()
    
    # Generate a batch ID
    batch_id = pd.Timestamp.now().strftime("%Y%m%d%H%M%S")
    
    # Insert all the runs in the database with a unique run ID and the system prompt, 
    # starting with a status of "pending"
    for input_id in input_ids_to_validate:
        run_id = str(uuid.uuid4())
        insert_run(run_id, input_id, system_prompt, batch_id=batch_id)
    
    # Perform LLM data extraction and validation for each input
    for input_id in input_ids_to_validate:
        print(f"Processing input ID: {input_id}")
        # Update the status to running for the given input ID
        update_run(run_id, input_id, status="running", llm_output=None)
        # Get the value and value type for the input ID
        value = inputs[inputs["id"] == input_id]["value"].values[0]
        value_type = inputs[inputs["id"] == input_id]["value_type"].values[0]
        # If the value is None, skip this input_id
        if pd.isna(value):
            print(f"Input ID {input_id} has no value. Skipping.")
            update_run(run_id, input_id, status="failed", llm_output=None, error_message="No value provided in inputs table.")
            continue
        else:
            # Get the user prompt based on the value type
            if value_type == "img" or value_type == "pdf" or value_type == "txt":
                # TODO: Handle image and PDF files
                user_prompt = value
            elif value_type == "xlsx":
                # TODO: Handle Excel files
                print(f"Input ID {input_id} is an Excel file. Skipping.")
                update_run(run_id, input_id, status="failed", llm_output=None, error_message="Excel files are not supported for this run.")
                continue 
            else:
                print(f"Input ID {input_id} has an unsupported value type: {value_type}.")
                update_run(run_id, input_id, status="failed", llm_output=None, error_message=f"Unsupported value type: {value_type}.")
                continue

        # Load response schema for the LLM output
        with open(response_schema_path, 'r') as file:
            response_schema = json.load(file)
        
        # Now call the LLM 
        try:
            response = await get_chat_gpt_response(
                system_prompt=system_prompt,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "response_schema",
                        "schema": response_schema
                    }
                },
                model="gpt-4o",
                text_to_analize=(user_prompt if value_type == "txt" else None),
                encoded_image=(user_prompt if value_type == "img" else None),
                encoded_pdf=(user_prompt if value_type == "pdf" else None),
            )

            # If we got a valid response, mark this run completed
            update_run(run_id, input_id, status="completed", llm_output=json.dumps(response), error_message=None)

        except Exception as e:
            # Something went wrong in the LLM call or post‐processing:
            print(f"Error processing input {input_id}: {e}")
            # Mark the most‐recent run for this input_id as 'failed'
            update_run(run_id, input_id, status="failed", llm_output=None, error_message=str(e))
            # And move on to the next input_id
            continue

        # Compare the LLM output to the target output
        # TODO: Adjust country code within labeled_data.csv to match the country codes in the LLM output
        try:
            value_comparison_df = compare_llm_to_target_output(inputs[inputs["id"] == input_id], response)
        except Exception as e:
            print(f"Error comparing LLM output to target output for input ID {input_id}: {e}")
            # Mark the most‐recent run for this input_id as 'failed'
            update_run(run_id, input_id, status="failed", llm_output=json.dumps(response), error_message=str(e))
            continue

        # Save the validation results to database
        value_comparison_df["run_id"] = run_id
        value_comparison_df["batch_id"] = batch_id
        # Set all target_value and llm_value to string type so they can be stored in the database
        # This is necessary because the database does not support numerical and string values in the same column
        value_comparison_df["target_value"] = value_comparison_df["target_value"].astype(str)
        value_comparison_df["llm_value"] = value_comparison_df["llm_value"].astype(str)
        update_results(value_comparison_df)
        # TODO: Create summary reports based on the validation results

        # After processing, dispose of the database engine
        dispose_engine()

    return

if __name__ == "__main__":
    asyncio.run(main())
