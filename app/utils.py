import os
import pandas as pd
import sys
import argparse
from argparse import RawTextHelpFormatter
import base64
import json
import openai
from io import BytesIO
from PIL import Image

def load_csv(file_path):
    """
    Load a CSV file into a pandas DataFrame.
    """
    #print(f"Loading {file_path}...")
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        #print(f"Loaded {file_path} with shape: {df.shape}")
        return df
    else:
        raise FileNotFoundError(f"{file_path} not found")

def load_prompt(file_path: str) -> str:
    """
    Load a prompt from a text file.
    """
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return file.read()
    else:
        raise FileNotFoundError(f"{file_path} not found")

def get_args(inputs) -> argparse.Namespace:
    """
    Build and return the ArgumentParser namespace.
    If run with no flags, prints help and exits.
    
    Assumes `inputs` is a pandas DataFrame with columns:
      - id
      - supplier_name
      - source_type
      - date_of_sending
    """
    # ——————————————
    # 1. Prepare the list of valid IDs + metadata for help text
    # ——————————————
    # Sort by 'id' so the help listing appears in ascending order
    # sorted_df = inputs.sort_values("id").reset_index(drop=True)
    sorted_df = inputs
    all_ids = sorted_df["id"].tolist()

    # Build one formatted line per row:
    #   “  • 101 (SupplierA, TypeX, 2025-05-20)”
    lines = []
    for _, row in sorted_df.iterrows():
        id_val = row["id"]
        supplier = row["supplier_name"]
        src_type = row["source_type"]
        date_sent = row["date_of_sending"]
        value_type = row["value_type"] 
        date_str = str(date_sent)  # In case it's a Timestamp
        lines.append(f"  • {id_val} ({supplier}, {src_type}, {date_str}, {value_type})")

    formatted_ids = "\n".join(lines)

    # ——————————————
    # 2. Create the ArgumentParser, including the epilog with ID list
    # ——————————————
    parser = argparse.ArgumentParser(
        description=(
            "Process inputs by ID, using either a default prompt or a manual prompt "
            "loaded from `prompt.txt`."
        ),
        formatter_class=RawTextHelpFormatter,
        epilog=(
            "Available input IDs:\n"
            f"{formatted_ids}\n\n"
            "If you omit -i/--inputs, the script will validate ALL inputs.\n"
            "Example usage:\n"
            "  python main.py -p manual -i 101 203 305\n"
        )
    )

    # — Prompt choice: built-in or manual  —
    parser.add_argument(
        "-p", "--prompt",
        choices=["default", "manual"],
        default="default",
        help=(
            "Choose which prompt to use:\n"
            "  default → use the built-in prompt hardcoded in the script\n"
            "  manual  → load the prompt text from `prompt.txt`"
        )
    )

    # — Inputs to validate: zero or more IDs  —
    parser.add_argument(
        "-i", "--inputs",
        metavar="ID",
        type=int,
        nargs="*",
        choices=all_ids,
        default=all_ids,
        help=(
            "Specify one or more input IDs to validate (e.g. `-i 1 2 3`).\n"
            "If omitted, all available IDs will be validated."
        )
    )

    # — If no flags are provided, show help and exit  —
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(0)
    
    # Return the parsed arguments as a Namespace 
    args = parser.parse_args()
    
    # Set argse.inputs to set to ensure uniqueness
    args.inputs = set(args.inputs) if args.inputs else None

    return args

def get_image_from_base64(b64_string):
    # 1) Decode the Base64 string into bytes
    try:
        raw = base64.b64decode(b64_string)
    except Exception as e:
        print(f"ERROR decoding Base64: {e}")
        return None

    # 2) Load those bytes into a PIL Image
    try:
        img = Image.open(BytesIO(raw))
    except Exception as e:
        print(f"ERROR loading image from bytes: {e}")
        return None
    return img




