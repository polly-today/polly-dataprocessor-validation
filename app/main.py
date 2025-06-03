import pandas as pd
import sys
import argparse
import base64
import json
from io import BytesIO
from PIL import Image

from utils import get_args, load_prompt, load_csv, load_inputs, get_image_from_base64

labeled_data_path = "../database/labeled_data.csv"
prompt_path = "../database/prompt.txt"
schema_path = "../database/product_offers_schema.json"

def main():
    # Fetch inputs to validate
    inputs = load_inputs()
    # Fetch labeled data (FUTURE: direct connection with Google Sheets)
    target_output = load_csv(labeled_data_path)

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
        print("Validating all labeled inputs.")
        input_ids_to_validate = inputs["id"].tolist()

    # Get metadata for the input ids to validate as a dictionary
    input_to_validate = {}
    for input_id in input_ids_to_validate:
        row = inputs[inputs["id"] == input_id].iloc[0]
        input_to_validate[input_id] = {
            "supplier_name": row["supplier_name"],
            "phone_number": row["phone_number"],
            "date_of_sending": row["date_of_sending"],
            "email_subject": row["email_subject"],
            "email_address": row["email_address"],
            "source_type": row["source_type"],
            "value_type": row["value_type"],
            "value": row["value"]
        }

        # Get the user prompt based on the value type
        if input_to_validate[input_id]["value_type"] == "img":
            b64_string = input_to_validate[input_id]["value"]
            user_prompt = get_image_from_base64(b64_string)
            # print(f"Displaying image for ID {input_id} …")
            # img.show()
        # elif input_to_validate[input_id]["value_type"] == "txt":
        # elif input_to_validate[input_id]["value_type"] == "xlsx":
        # elif input_to_validate[input_id]["value_type"] == "pdf":
        # else:



    return

if __name__ == "__main__":
    main()
 for batch processing each scenario
