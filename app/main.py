import pandas as pd
import sys
import argparse
import base64
import json
from io import BytesIO
import asyncio
import os
from dataprocessor import get_chat_gpt_response
from utils import get_args, load_prompt, load_csv, get_image_from_base64
from database import load_inputs, insert_run, update_run

labeled_data_path = "../database/labeled_data.csv"
prompt_path = "../database/prompt.txt"
schema_path = "../database/product_offers_schema.json"

async def main():
    # Fetch all possible inputs to validate
    inputs = load_inputs()

    # Get command line arguments and provide inputs to specify the option to choose from
    args = get_args(inputs=inputs)

    # Get prompt based on user choice
    if args.prompt == "default":
        print("Using default prompt.")
        return
    elif args.prompt == "manual":
        print(f"Using manual prompt from {prompt_path}.")
        system_prompt = load_prompt(prompt_path)

    # Get inputs to validate
    if args.inputs is not None:
        print(f"Validating inputs: {args.inputs}")
        input_ids_to_validate = inputs[inputs["id"].isin(args.inputs)]["id"].tolist()
    else:
        # to check: this does not seem to print when no inputs are specified in command line
        print("Validating all labeled inputs.")
        input_ids_to_validate = inputs["id"].tolist()
    
    # Insert the runs in the database with status "pending"
    for input_id in input_ids_to_validate:
        insert_run(input_id, system_prompt)
    
    # Perform validation for each input
    for input_id in input_ids_to_validate:
        
        # Update the status to running of the most recent run for the given input ID.
        update_run(input_id, status="running", llm_output=None)

        # Get the value and value type for the input ID
        value = inputs[inputs["id"] == input_id]["value"].values[0]
        value_type = inputs[inputs["id"] == input_id]["value_type"].values[0]

        # If the value is None, skip this input_id
        if pd.isna(value):
            print(f"Input ID {input_id} has no value. Skipping.")
            update_run(input_id, status="failed", llm_output=None, error_message="No value provided in inputs table.")
            continue

        # Get the user prompt based on the value type
        if value_type == "img" or value_type == "pdf":
            user_prompt = value
        elif value_type == "txt":
            user_prompt = value
        elif value_type == "xlsx":
            continue
        else:
            print(f"Unsupported value type: {value_type}. Skipping input ID {input_id}.")
            continue

        # Load response schema for the LLM output
        with open(schema_path, 'r') as file:
            product_offers_schema = json.load(file)
        
        # Now call the LLM inside a try/except
        try:
            response = await get_chat_gpt_response(
                system_prompt=system_prompt,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "product_offers_schema",
                        "schema": product_offers_schema
                    }
                },
                model="gpt-4o",
                text_to_analize=(user_prompt if value_type == "txt" else None),
                encoded_image=(user_prompt if value_type in ["img", "pdf"] else None),
                encoded_file_type=None,
                encoded_filename=None,
                encoded_file=None,
            )

            # 7e) If we got a valid response, mark this run completed
            print(f"LLM response for input {input_id}:\n{json.dumps(response, indent=2)}")
            update_run(input_id, status="completed", llm_output=json.dumps(response))

        except Exception as e:
            # 7f) Something went wrong in the LLM call or post‐processing:
            print(f"Error processing input {input_id}: {e}")
            # Mark the most‐recent run for this input_id as 'failed'
            update_run(input_id, status="failed", llm_output=None, error_message=str(e))
            # And move on to the next input_id
            continue

    # Fetch all labeled data (FUTURE: direct connection with Google Sheets)
    target_output = load_csv(labeled_data_path)


    return

if __name__ == "__main__":
    asyncio.run(main())
