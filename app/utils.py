import os
import pandas as pd
import sys
import argparse
from argparse import RawTextHelpFormatter
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load database URL from .env file
load_dotenv()
database_url = os.getenv("DATABASE_URL")
if database_url is None:
    raise RuntimeError("DATABASE_URL not found—did you create a .env with that variable?")

# Create a SQLAlchemy engine to run SQL queries
engine = create_engine(database_url)

### DATABASE FUNCTIONS ###
def load_inputs():
    """
    Load inputs table from the database and return as a pandas DataFrame.
    """
    # Select all data from the 'inputs' table
    query = "SELECT * FROM inputs;"  

    # Run the query and load into a DataFrame
    try:
        df = pd.read_sql(query, con=engine)
        return df
    except Exception as e:
        print("Error loading inputs from database:", e)
        return None


def insert_run(run_id, input_id, system_prompt, batch_id=None, settings=None):
    """
    Record a run in the database with the given input ID and system prompt.
    Returns True if successful, False otherwise.
    """
    # Prepare the data to insert
    run_data = {
        "id": run_id,
        "input_id": input_id,
        "batch_id": batch_id,
        "system_prompt": system_prompt,
        "status": "pending",
        "settings": None,
        "created_at": pd.Timestamp.now(),
        "updated_at": pd.Timestamp.now(),
        "llm_output": None,
        "settings": settings
    }

    # Create engine and perform INSERT
    insert_sql = text("""
        INSERT INTO public.runs
            (id, input_id, batch_id, system_prompt, status, settings, created_at, updated_at, llm_output)
        VALUES
            (:id, :input_id, :batch_id, :system_prompt, :status, :settings, :created_at, :updated_at, :llm_output)
    """)

    try:
        with engine.begin() as conn: 
            conn.execute(insert_sql, run_data)
    except Exception as e:
        print("Error inserting into runs table:", e)
        return False

    return True


def update_run(batch_id, input_id, status, llm_output=None, error_message=None, system_prompt=None):
    """
    Update the status (and LLM output) of the most recent run for the given input ID.
    Returns True if successful, False otherwise.
    """
    # Prepare the data to update
    update_data = {
        "batch_id": batch_id,
        "input_id": input_id,
        "status": status,
        "llm_output": llm_output,
        "updated_at": pd.Timestamp.now(),
        "error_message": error_message,
        "system_prompt": system_prompt
    }

    # Create engine and perform UPDATE
    update_sql = text("""
        UPDATE public.runs
            SET status     = :status,
                llm_output = :llm_output,
                updated_at = :updated_at,
                error_message = :error_message,
                system_prompt = :system_prompt
            WHERE input_id = :input_id AND batch_id = :batch_id
    """)

    try:
        with engine.begin() as conn: 
            conn.execute(update_sql, update_data)
    except Exception as e:
        print("Error updating runs table:", e)
        return False
    return True


def update_results(value_comparison_df):
    # Finally, push it to the `results` table.  This will INSERT all rows in one go.
    value_comparison_df.to_sql(
        "results", 
        con=engine, 
        if_exists="append", 
        index=False  # don’t write the DataFrame’s index as a separate column
    )
    return


def dispose_engine():
    """
    Dispose the SQLAlchemy engine to release resources.
    """
    if engine:
        engine.dispose()
        print("Database engine disposed.")
    else:
        print("No database engine to dispose.")


### FILE LOADING FUNCTIONS ###
def load_csv(file_path):
    """
    Load a CSV file into a pandas DataFrame.
    """
    #print(f"Loading {file_path}...")
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        if file_path == "../data/labeled_data.csv":
            df['phone_number'] = df['phone_number'].astype(str)  # Ensure phone numbers are strings

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


### ARGUMENT PARSER FUNCTION ###
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
            "  python main.py -p manual -i 101 203 305 -s 'Added product type rule for Aubergine'\n"
        )
    )

    # — Prompt choice: built-in or manual  —
    parser.add_argument(
        "-p", "--prompt",
        choices=["default", "manual", "dynamic"],
        default="default",
        help=(
            "Choose which prompt to use:\n"
             "  default → use the default prompt in default_prompt.txt\n"
             "  manual  → use your adjusted prompt in manual_prompt.txt\n"
             "  dynamic → build a prompt dynamically based on product types within the input data\n"
        )
    )
    # — Settings description, required if manual prompt selected  —
    parser.add_argument(
        "-s", "--settings",
        type=str,
        help=(
            "When using manual prompt, describe what you adjusted "
            "compared to the default (e.g. added product types, re-ordered rules)"
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

    # If manual prompt, settings description is mandatory
    if args.prompt == "manual" and not args.settings:
        parser.error("When using `-p manual`, you must also pass `-s 'description of adjustments'`.\n"
                     "Example: `python main.py -p manual -s 'Added product type rule for Aubergine.'`")

    # Set args.inputs to an ordered list of unique items to maintain order
    if args.inputs is not None:
        args.inputs = sorted(set(args.inputs))

    return args



