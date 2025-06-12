import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load database URL from .env file
load_dotenv()
database_url = os.getenv("DATABASE_URL_STG")
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
    query = "SELECT * FROM product_types;"  

    # Run the query and load into a DataFrame
    try:
        df = pd.read_sql(query, con=engine)
        print(df)
        return df
    except Exception as e:
        print("Error loading inputs from database:", e)
        return None

df = load_inputs()
print(df)