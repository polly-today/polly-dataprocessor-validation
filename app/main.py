import pandas as pd
import sys
import argparse
import uuid
import base64
import json
import numpy as np
from io import BytesIO
import asyncio
import os
from dataprocessor import get_chat_gpt_response
from utils import get_args, load_prompt, load_csv, get_image_from_base64
from database import load_inputs, insert_run, update_run
from validation import validate_llm_output

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
    
    # Generate one batch_id for this execution of main
    batch_id = pd.Timestamp.now().strftime("%Y%m%d%H%M%S")
    run_id = str(uuid.uuid4())
    
    # Insert all the runs in the database with status "pending"
    for input_id in input_ids_to_validate:
        insert_run(run_id, input_id, system_prompt, batch_id=batch_id)
    
    # Perform validation for each input
    for input_id in input_ids_to_validate:
        
        # Update the status to running of the most recent run for the given input ID.
        update_run(run_id, input_id, status="running", llm_output=None)

        # Get the value and value type for the input ID
        value = inputs[inputs["id"] == input_id]["value"].values[0]
        value_type = inputs[inputs["id"] == input_id]["value_type"].values[0]

        # If the value is None, skip this input_id
        if pd.isna(value):
            print(f"Input ID {input_id} has no value. Skipping.")
            update_run(run_id, input_id, status="failed", llm_output=None, error_message="No value provided in inputs table.")
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
        
        # # Now call the LLM inside a try/except
        # try:
        #     response = await get_chat_gpt_response(
        #         system_prompt=system_prompt,
        #         response_format={
        #             "type": "json_schema",
        #             "json_schema": {
        #                 "name": "product_offers_schema",
        #                 "schema": product_offers_schema
        #             }
        #         },
        #         model="gpt-4o",
        #         text_to_analize=(user_prompt if value_type == "txt" else None),
        #         encoded_image=(user_prompt if value_type in ["img", "pdf"] else None),
        #         encoded_file_type=None,
        #         encoded_filename=None,
        #         encoded_file=None,
        #     )

        #     # 7e) If we got a valid response, mark this run completed
        #     update_run(input_id, status="completed", llm_output=json.dumps(response), error_message=None)

        # except Exception as e:
        #     # 7f) Something went wrong in the LLM call or post‐processing:
        #     print(f"Error processing input {input_id}: {e}")
        #     # Mark the most‐recent run for this input_id as 'failed'
        #     update_run(input_id, status="failed", llm_output=None, error_message=str(e))
        #     # And move on to the next input_id
        #     continue

        # print(response)

        # For now, we will use a hardcoded response to simulate the LLM output
        response = """
        {"product_offers":[{"product_type":"Cherry Plum Tomato","variety":"Red Triangle","sub_variety":"unspecified","size":"unspecified","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"N/A - unspecified","piece":"unspecified","price":10.5,"net_weight":4,"qty_per_pallet":0,"remarks":"Snack tomatoes: Babyplum 4kg"},{"product_type":"Cherry Plum Tomato","variety":"Red Triangle","sub_variety":"unspecified","size":"unspecified","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"MA - Morocco","piece":"unspecified","price":11.0,"net_weight":4,"qty_per_pallet":0,"remarks":"Snack tomatoes: Sweetelle 4kg MA"},{"product_type":"Cherry Plum Tomato","variety":"Red Triangle","sub_variety":"unspecified","size":"unspecified","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"N/A - unspecified","piece":"12x250g","price":7.95,"net_weight":3,"qty_per_pallet":0,"remarks":"Snack tomatoes: Babyplum triangle 12x250gr"},{"product_type":"Cherry Plum Tomato","variety":"Red Shaker","sub_variety":"unspecified","size":"unspecified","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"N/A - unspecified","piece":"12x250g","price":8.95,"net_weight":3,"qty_per_pallet":0,"remarks":"Snack tomatoes: Babyplum Shaker 12x250gr"},{"product_type":"Cherry Tomato","variety":"Red Loose","sub_variety":"unspecified","size":"unspecified","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"MA - Morocco","piece":"9x250g","price":5.5,"net_weight":2.25,"qty_per_pallet":0,"remarks":"Cherry tomatoes: Cherry 9x250gr MA"},{"product_type":"Cherry Tomato","variety":"Red Loose","sub_variety":"unspecified","size":"unspecified","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"N/A - unspecified","piece":"unspecified","price":8.5,"net_weight":4,"qty_per_pallet":0,"remarks":"Cherry tomatoes: Cherry 4kg kroonloos"},{"product_type":"Cherry Tomato","variety":"Yellow Loose","sub_variety":"unspecified","size":"unspecified","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"N/A - unspecified","piece":"9x250g","price":18.5,"net_weight":2.25,"qty_per_pallet":0,"remarks":"Cherry tomatoes: Yellow cherry 9x250gr"},{"product_type":"Cherry Tomato","variety":"Mix Loose","sub_variety":"unspecified","size":"unspecified","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"N/A - unspecified","piece":"unspecified","price":12.5,"net_weight":3,"qty_per_pallet":0,"remarks":"Cherry tomatoes: Classic tomaten mix 3kg"},{"product_type":"Cherry Tomato","variety":"Mix Loose","sub_variety":"unspecified","size":"unspecified","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"MA - Morocco","piece":"unspecified","price":9.5,"net_weight":3,"qty_per_pallet":0,"remarks":"Cherry tomatoes: Cherry mix 3kg MA (3 colors)"},{"product_type":"Cherry Tomato","variety":"Mix Shaker","sub_variety":"unspecified","size":"unspecified","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"N/A - unspecified","piece":"12x250g","price":0,"net_weight":3,"qty_per_pallet":0,"remarks":"Cherry tomatoes: Cherry mix 12x250gr shakers"},{"product_type":"Cherry Vine Tomato","variety":"Korino","sub_variety":"unspecified","size":"unspecified","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"NL - Netherlands","piece":"unspecified","price":9.95,"net_weight":3,"qty_per_pallet":0,"remarks":"Cherry tomatoes: Cherry vine 3kg NL"},{"product_type":"Round Tomato","variety":"unspecified","sub_variety":"unspecified","size":"M","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"MA - Morocco","piece":"unspecified","price":9.5,"net_weight":6,"qty_per_pallet":0,"remarks":"Round tomatoes 6kg: Tomatoes Premium MA M"},{"product_type":"Round Tomato","variety":"unspecified","sub_variety":"unspecified","size":"M","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"MA - Morocco","piece":"unspecified","price":9.95,"net_weight":6,"qty_per_pallet":0,"remarks":"Round tomatoes 6kg: Tomatoes Premium MA M (57-62)"},{"product_type":"Round Tomato","variety":"unspecified","sub_variety":"unspecified","size":"M","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"MA - Morocco","piece":"unspecified","price":9.95,"net_weight":6,"qty_per_pallet":0,"remarks":"Round tomatoes 6kg: Tomatoes Premium MA M (62-67)"},{"product_type":"Round Tomato","variety":"unspecified","sub_variety":"unspecified","size":"MM","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"MA - Morocco","piece":"unspecified","price":9.95,"net_weight":6,"qty_per_pallet":0,"remarks":"Round tomatoes 6kg: Tomatoes Premium MA MM"},{"product_type":"Round Tomato","variety":"unspecified","sub_variety":"unspecified","size":"MMM","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"ES - Spain","piece":"unspecified","price":7.5,"net_weight":6,"qty_per_pallet":0,"remarks":"Round tomatoes 6kg: Tomatoes Premium ES MMM"},{"product_type":"Round Tomato","variety":"unspecified","sub_variety":"unspecified","size":"G","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"MA - Morocco","piece":"unspecified","price":8.5,"net_weight":6,"qty_per_pallet":0,"remarks":"Round tomatoes 6kg: Tomatoes Premium MA G"},{"product_type":"Plum Tomato","variety":"unspecified","sub_variety":"unspecified","size":"MMM","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"N/A - unspecified","piece":"unspecified","price":0,"net_weight":6,"qty_per_pallet":0,"remarks":"Plum tomatoes 6kg: Plum tomatoes 6kg MMM"},{"product_type":"Plum Tomato","variety":"unspecified","sub_variety":"unspecified","size":"MM","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"N/A - unspecified","piece":"unspecified","price":0,"net_weight":6,"qty_per_pallet":0,"remarks":"Plum tomatoes 6kg: Plum premium 6kg MM"},{"product_type":"Plum Tomato","variety":"unspecified","sub_variety":"unspecified","size":"M","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"N/A - unspecified","piece":"unspecified","price":0,"net_weight":6,"qty_per_pallet":0,"remarks":"Plum tomatoes 6kg: Plum premium 6kg M"},{"product_type":"Vine Tomato","variety":"unspecified","sub_variety":"unspecified","size":"unspecified","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"NL - Netherlands","piece":"unspecified","price":10.5,"net_weight":5,"qty_per_pallet":0,"remarks":"Vine tomatoes: Vine tomatoes NL 5kg"},{"product_type":"Vine Tomato","variety":"unspecified","sub_variety":"unspecified","size":"M","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"ES - Spain","piece":"unspecified","price":8.5,"net_weight":5,"qty_per_pallet":0,"remarks":"Vine tomatoes: Vine tomatoes ES 5kg M"},{"product_type":"Beef Tomato","variety":"unspecified","sub_variety":"unspecified","size":"BBB","brand":"unspecified","package_type":"unspecified","pallet":"unspecified","product_class":"unspecified","unit_type":"unspecified","unit_trade_type":"unspecified","country":"MA - Morocco","piece":"unspecified","price":17.5,"net_weight":7,"qty_per_pallet":0,"remarks":"Beef tomatoes: Beef tomatoes 7kg BBB MA"}]}
        """

        value_comparison_df = validate_llm_output(inputs[inputs["id"] == input_id], response)
        print(f"Validation results for input ID {input_id}:\n{value_comparison_df}")



            # for i, j in target_llm_matches.items():
            #     target_row = target_output_df.iloc[i]
            #     llm_row = llm_output_df.iloc[j] if j is not None else None

            #     for col in REQUIRED_COLUMNS_COMPARISON:
            #         target_value = target_row[col]
            #         llm_value = llm_row[col] if llm_row is not None else None
            #         similarity = get_value_similarity(target_value, llm_value, col)
            #         print(f"Row {i} (target) vs Row {j} (LLM) - Column '{col}': "
            #             f"Target: {target_value}, LLM: {llm_value}, "
            #             f"Similarity: {similarity}")
    



    # Fetch all labeled data (FUTURE: direct connection with Google Sheets)
    target_output = load_csv(labeled_data_path)


    return

if __name__ == "__main__":
    asyncio.run(main())
