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
            if value_type == "img" or value_type == "pdf":
                # TODO: Handle image and PDF files
                user_prompt = value
                #print(f"Input ID {input_id} is an image or PDF file. Skipping.")
                # update_run(run_id, input_id, status="failed", llm_output=None, error_message="Image and PDF types are not supported for this run.")
                # continue 
            elif value_type == "txt":
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
                encoded_image=(user_prompt if value_type in ["img", "pdf"] else None),
                encoded_file_type=None,
                encoded_filename=None,
                encoded_file=None,
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

        # # For now, we will use a hardcoded response to simulate the LLM output
        # response = """
        # {\"product_offers\":[{\"product_type\":\"Celery\",\"variety\":\"Washed\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Wooden Crate\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"unspecified\",\"country\":\"unspecified\",\"piece\":\"16stk\",\"price\":9.0,\"net_weight\":0.4,\"qty_per_pallet\":null,\"remarks\":\"\"},{\"product_type\":\"Celery\",\"variety\":\"Washed\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Wooden Crate\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"unspecified\",\"country\":\"unspecified\",\"piece\":\"12stk\",\"price\":7.0,\"net_weight\":0.5,\"qty_per_pallet\":null,\"remarks\":\"\"},{\"product_type\":\"Celeriac\",\"variety\":\"Naked\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"EPS 186\",\"country\":\"unspecified\",\"piece\":\"8-12stk\",\"price\":7.5,\"net_weight\":10.0,\"qty_per_pallet\":null,\"remarks\":\"\"},{\"product_type\":\"Carrot\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"EPS 186\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":7.0,\"net_weight\":12.5,\"qty_per_pallet\":null,\"remarks\":\"Peen B fijn 50-150/grof 125-250\"},{\"product_type\":\"Carrot\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"EPS 186\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":7.0,\"net_weight\":12.5,\"qty_per_pallet\":null,\"remarks\":\"Peen C 175-325 gram\"},{\"product_type\":\"Carrot\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"unspecified\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":5.0,\"net_weight\":5.0,\"qty_per_pallet\":null,\"remarks\":\"Peen Geel (morgen laden)\"},{\"product_type\":\"Carrot\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"unspecified\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":5.0,\"net_weight\":5.0,\"qty_per_pallet\":null,\"remarks\":\"Peen Paars (morgen laden)\"},{\"product_type\":\"Pumpkin\",\"variety\":\"Butternut\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"EPS 186\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":9.5,\"net_weight\":0.8,\"qty_per_pallet\":null,\"remarks\":\"Pompoen Flespompoen 500-800 gr\"},{\"product_type\":\"Pumpkin\",\"variety\":\"Butternut\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"EPS 186\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":9.5,\"net_weight\":1.2,\"qty_per_pallet\":null,\"remarks\":\"Pompoen Flespompoen 800-1200 gr\"},{\"product_type\":\"Pumpkin\",\"variety\":\"Butternut\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"EPS 186\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":11.5,\"net_weight\":1.3,\"qty_per_pallet\":null,\"remarks\":\"Pompoen Flespompoen 800 -1300 gr\"},{\"product_type\":\"Pumpkin\",\"variety\":\"Hokaido\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"EPS 186\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":9.5,\"net_weight\":0.8,\"qty_per_pallet\":null,\"remarks\":\"Pompoen Hokkaido 500-800 gr\"},{\"product_type\":\"Pumpkin\",\"variety\":\"Hokaido\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"EPS 186\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":9.5,\"net_weight\":1.2,\"qty_per_pallet\":null,\"remarks\":\"Pompoen Hokkaido 800-1200 gr\"},{\"product_type\":\"Pumpkin\",\"variety\":\"Hokaido\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"EPS 186\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":11.5,\"net_weight\":1.3,\"qty_per_pallet\":null,\"remarks\":\"Pompoen Hokkaido 1300 gr\"},{\"product_type\":\"Fennel\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"unspecified\",\"country\":\"unspecified\",\"piece\":\"60ers\",\"price\":16.0,\"net_weight\":null,\"qty_per_pallet\":null,\"remarks\":\"\"},{\"product_type\":\"Chicory\",\"variety\":\"White\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"unspecified\",\"country\":\"unspecified\",\"piece\":\"10x500g\",\"price\":16.0,\"net_weight\":null,\"qty_per_pallet\":null,\"remarks\":\"\"},{\"product_type\":\"Chicory\",\"variety\":\"White\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"unspecified\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":6.0,\"net_weight\":5.0,\"qty_per_pallet\":null,\"remarks\":\"Witlof kort-grof / lang 5 kg\"},{\"product_type\":\"Sweet Potato\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"S\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"unspecified\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":6.45,\"net_weight\":6.0,\"qty_per_pallet\":null,\"remarks\":\"Zoete Aardappelen S 50-150 gram / 6 kg\"},{\"product_type\":\"Sweet Potato\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"M\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"unspecified\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":6.75,\"net_weight\":6.0,\"qty_per_pallet\":null,\"remarks\":\"Zoete Aardappelen M 150-300 gram / 6 kg\"},{\"product_type\":\"Sweet Potato\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"L1\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"unspecified\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":6.75,\"net_weight\":6.0,\"qty_per_pallet\":null,\"remarks\":\"Zoete Aardappelen L1 300-450 gram / 6 kg\"},{\"product_type\":\"Sweet Potato\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"L2\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"unspecified\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":6.75,\"net_weight\":6.0,\"qty_per_pallet\":null,\"remarks\":\"Zoete Aardappelen L2 450-600 gram / 6 kg\"},{\"product_type\":\"Sweet Potato\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"XL\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"unspecified\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":6.75,\"net_weight\":6.0,\"qty_per_pallet\":null,\"remarks\":\"Zoete Aardappelen XL 600-750 gram / 6 kg\"},{\"product_type\":\"Pumpkin\",\"variety\":\"Butternut\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"EPS 186\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":0.0,\"net_weight\":0.8,\"qty_per_pallet\":null,\"remarks\":\"BIO Flespompoen per stuk 800 gram +\"},{\"product_type\":\"Pumpkin\",\"variety\":\"Hokaido\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"EPS 186\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":11.5,\"net_weight\":0.8,\"qty_per_pallet\":null,\"remarks\":\"BIO Hokkaido 500-800 gram +\"},{\"product_type\":\"Pumpkin\",\"variety\":\"Hokaido\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"EPS 186\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":11.5,\"net_weight\":1.2,\"qty_per_pallet\":null,\"remarks\":\"BIO Hokkaido 800-1200 gram +\"},{\"product_type\":\"Pumpkin\",\"variety\":\"Hokaido\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"EPS 186\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":11.5,\"net_weight\":1.3,\"qty_per_pallet\":null,\"remarks\":\"BIO Hokkaido 1300 gram +\"},{\"product_type\":\"Leek\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS24603\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"unspecified\",\"price\":0.0,\"net_weight\":10.0,\"qty_per_pallet\":null,\"remarks\":\"BIO Prei 10 kg\"},{\"product_type\":\"Leek\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"unspecified\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":0.0,\"net_weight\":10.0,\"qty_per_pallet\":null,\"remarks\":\"BIO Prei 10 kg\"},{\"product_type\":\"Leek\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS 186\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"unspecified\",\"unit_trade_type\":\"unspecified\",\"country\":\"unspecified\",\"piece\":\"unspecified\",\"price\":0.0,\"net_weight\":5.0,\"qty_per_pallet\":null,\"remarks\":\"BIO Prei 5 kg\"}]}
        # """

        # Compare the LLM output to the target output
        # TODO: Adjust country code within labeled_data.csv to match the country codes in the LLM output
        try:
            value_comparison_df = compare_llm_to_target_output(inputs[inputs["id"] == input_id], response)
        except Exception as e:
            print(f"Error comparing LLM output to target output for input ID {input_id}: {e}")
            # Mark the most‐recent run for this input_id as 'failed'
            update_run(run_id, input_id, status="failed", llm_output=None, error_message=str(e))
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
