from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd
import os

# Load database URL from .env file
load_dotenv()
database_url = os.getenv("DATABASE_URL")
if database_url is None:
    raise RuntimeError("DATABASE_URL not found—did you create a .env with that variable?")

# Create a SQLAlchemy engine to run SQL queries
engine = create_engine(database_url)

def load_inputs():
    """
    Load inputs from the database and return as a pandas DataFrame.
    """
    # Select all data from the 'inputs' table
    query = "SELECT * FROM inputs;"  

    # Run the query and load into a DataFrame
    try:
        df = pd.read_sql(query, con=engine)
        print(df)
        return df
    except Exception as e:
        print("Error loading inputs from database:", e)
        return None
    finally:
        engine.dispose()


def insert_run(run_id, input_id, system_prompt, batch_id=None):
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
        "llm_output": None
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
    finally:
        engine.dispose()

    return True

def update_run(run_id, input_id, status, llm_output=None, error_message=None):
    """
    Update the status (and LLM output) of the most recent run for the given input ID.
    Returns True if successful, False otherwise.
    """
    # Prepare the data to update
    update_data = {
        "run_id": run_id,   
        "input_id": input_id,
        "status": status,
        "llm_output": llm_output,
        "updated_at": pd.Timestamp.now(),
        "error_message": error_message
    }

    # Create engine and perform UPDATE
    update_sql = text("""
        UPDATE public.runs AS r
            SET status     = :status,
                llm_output = :llm_output,
                updated_at = :updated_at,
                error_message = :error_message     
            FROM (
                    SELECT id
                    FROM public.runs
                    WHERE input_id = :input_id
                    ORDER BY created_at DESC
                    LIMIT 1
                ) AS latest
            WHERE r.id = :run_id
    """)

    try:
        with engine.begin() as conn: 
            conn.execute(update_sql, update_data)
    except Exception as e:
        print("Error updating runs table:", e)
        return False
    finally:
        engine.dispose()

    return True
