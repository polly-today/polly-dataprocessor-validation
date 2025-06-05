import pandas as pd
import uuid
import json
import asyncio
from utils import get_args, load_prompt, load_inputs, insert_run, update_run, dispose_engine, update_results
import os
import json
import numpy as np
import openai
from Levenshtein import ratio as levenshtein_ratio
import pandas as pd
from utils import load_csv, load_inputs
from datetime import datetime, timedelta
from scipy.optimize import linear_sum_assignment
from config import (
    REQUIRED_COLUMNS_TARGET,
    REQUIRED_COLUMNS_COMPARISON,
    NUMERIC_COLUMNS,
    SIMILARITY_WEIGHTS,
    labeled_data_path
)


### Helper Functions ###
def check_required_columns(llm_output_df, target_output_df):
    """
    Check if the required columns are present in both DataFrames.
    """
    print("Checking for missing columns...")
    missing_llm = set(REQUIRED_COLUMNS_COMPARISON) - set(llm_output_df.columns)
    missing_target = set(REQUIRED_COLUMNS_TARGET) - set(target_output_df.columns)

    if missing_llm or missing_target:
        raise ValueError(
            f"Missing required columns:\n"
            f" - In llm_output: {missing_llm if missing_llm else 'None'}\n"
            f" - In target_output: {missing_target if missing_target else 'None'}"
        )
    else:
        print("Both DataFrames contain all required columns.")
        return llm_output_df, target_output_df

def select_comparison_columns(llm_output_df, target_output_df):
    """
    Select only the columns required for comparison from both DataFrames.
    """
    target_output_df = target_output_df[REQUIRED_COLUMNS_COMPARISON]
    llm_output_df = llm_output_df[REQUIRED_COLUMNS_COMPARISON]
    return llm_output_df, target_output_df
    
def preprocess_data(llm_output_df, target_output_df):
    """
    Preprocess the DataFrames by replacing 'unspecified' with NaN,
    converting numeric fields, and normalizing date fields.
    """
    print("Replacing missing values with 'unspecified'...")
    llm_output_df.fillna('unspecified', inplace=True)
    target_output_df.fillna('unspecified', inplace=True)
    llm_output_df.replace('N/A - unspecified', 'unspecified', inplace=True)
    target_output_df.replace('N/A - unspecified', 'unspecified', inplace=True)    

    print("Converting numeric fields...")
    for col in ['product_class', 'net_weight', 'qty_per_pallet', 'price']:
        is_int = col in {'product_class', 'qty_per_pallet'}
        for df in [llm_output_df, target_output_df]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            if is_int:
                df[col] = df[col].astype('Int64')
            else:
                df[col] = df[col].round(2)
    
    # Ensure date_of_sending is a datetime object in the same time zone
    target_output_df["date_of_sending"] = pd.to_datetime(
        target_output_df["date_of_sending"],
        format="%d-%m-%Y %H:%M:%S",  # or omit format and use dayfirst=True
        errors="coerce"
    )
    return llm_output_df, target_output_df


def get_value_similarity(target_value, llm_value, column):
    """
    Returns a similarity score between two values based on their type:
    - For numeric columns: 1.0 if exactly equal, else 0
    - For NaN values:
        - If both are NaN, score is 1.0 (perfect match)
        - If LLM value is NaN and target is not NaN, score is 0.5 (partial match)
        - If target is NaN and LLM value is not NaN, score is 0.0 (mismatch)
    - For string columns: Levenshtein ratio (0–100)/100
    """
    # If one of the values is NaN, we handle it separately
    if pd.isna(target_value) or pd.isna(llm_value):
        # When both values are NaN, we treat it as a perfect match
        if pd.isna(target_value) and pd.isna(llm_value):
            similarity = 1.0
        # When LLM value is NaN and target is not NaN, we treat it as a partial match
        elif pd.isna(llm_value) and not pd.isna(target_value):
            similarity = 0.5
        # When target is NaN and LLM value is not NaN, we treat it as a mismatch
        elif pd.isna(target_value) and not pd.isna(llm_value):
            similarity = 0.0
        else:
            raise ValueError(f"Unexpected NaN handling for column '{column}': target={target_value}, llm={llm_value}")
    # For numeric columns, check for exact match
    elif column in NUMERIC_COLUMNS:
        similarity = 1.0 if target_value == llm_value else 0.0
    else:
        s_target, s_llm = str(target_value), str(llm_value)
        similarity = levenshtein_ratio(s_target, s_llm)
    return similarity

def get_row_similarity(target_row, llm_row, columns, SIMILARITY_WEIGHTS=None):
    """
    Returns a weighted average per‐column similarity score
    between two rows, based on the specified columns.
    If weights are provided, they are used to weight the similarity scores.
    If no weights are provided, each column is equally weighted.
    """
    scores = {}
    total_weight = 0
    weighted_sum = 0

    for col in columns:
        target_value = target_row[col]
        llm_value = llm_row[col]

        # Default weight = 1 if not specified
        weight = SIMILARITY_WEIGHTS.get(col, 1.0) if SIMILARITY_WEIGHTS else 1.0

        similarity = get_value_similarity(target_value, llm_value, col)

        scores[col] = similarity
        weighted_sum += weight * similarity
        total_weight += weight

    final_score = weighted_sum / total_weight if total_weight > 0 else 0

    return final_score

def link_rows_hungarian(llm_output_df, target_output_df, min_score=0.0):
    """
    Build a similarity matrix between every target_i and llm_j,
    then solve the one‐to‐one assignment that maximizes total similarity.
    Optionally discard any matched pair whose sim < min_score.
    """
    n_targets = len(target_output_df)
    n_llm     = len(llm_output_df)

    # 1) Build similarity matrix S (shape: n_targets × n_llm)
    S = np.zeros((n_targets, n_llm), dtype=float)
    for i, target_row in target_output_df.iterrows():
        for j, llm_row in llm_output_df.iterrows():
            S[i, j] = get_row_similarity(
                target_row,
                llm_row,
                REQUIRED_COLUMNS_COMPARISON,
                SIMILARITY_WEIGHTS
            )

    # 2) Solve assignment on -S to MAXIMIZE similarity
    row_idx, col_idx = linear_sum_assignment(-S)

    # 3) Filter out any pairs below min_score
    target_llm_links = {i: None for i in range(n_targets)}
    for i, j in zip(row_idx, col_idx):
        if S[i, j] >= min_score:
            target_llm_links[i] = int(j)
        else:
            # below threshold → leave unmatched
            target_llm_links[i] = None

    return target_llm_links

def get_value_comparison_df(llm_output_df, target_output_df, target_llm_links):
    """
    Create a DataFrame with the following columns: run_id, target_row_index, llm_row_index, column_name, target_value, llm_value, similarity_score
    """
    comparison_data = []

    # Iterate through the linked rows and calculate similarity for each required column
    for i, j in target_llm_links.items():
        target_row = target_output_df.iloc[i]
        llm_row = llm_output_df.iloc[j] if j is not None else None

        for col in REQUIRED_COLUMNS_COMPARISON:
            target_value = target_row[col]
            llm_value = llm_row[col] if llm_row is not None else None

            similarity = get_value_similarity(target_value, llm_value, col)
            comparison_data.append({
                "target_row_index": i,
                "llm_row_index": j,
                "attribute": col,
                "target_value": target_value,
                "llm_value": llm_value,
                "similarity_score": similarity
            })

    return pd.DataFrame(comparison_data)

### Main Comparison Function ###
def compare_llm_to_target_output(input, response):
    """
    Validate the LLM output DataFrame against the target output.
    This function will check for required columns, preprocess data, and calculate similarity scores.
    """
    # Retrieve metadata from the input DataFrame in order to match the target output with the LLM output
    input_id = input["id"].values[0]
    supplier_name = input["supplier_name"].values[0]
    date_of_sending = input["date_of_sending"].values[0]
    email_adress = input["email_address"].values[0]
    phone_number = input["phone_number"].values[0]
    email_subject = input["email_subject"].values[0]

    # Ensure date_of_sending is a datetime object and in the correct time zone
    date_of_sending = pd.to_datetime(date_of_sending, errors="coerce") + pd.Timedelta(hours=1)

    # ───── Parse the JSON‐string into a Python object ─────────────────────────────
    if isinstance(response, str):
        try:
            llm_output = json.loads(response)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Could not decode LLM response as JSON: {e}")
    else:
        llm_output = response

    try:
        llm_output_df = pd.DataFrame(llm_output["product_offers"])
    except Exception as e:
        raise ValueError(f"Could not convert LLM output to DataFrame: {e}")

    print(llm_output_df.head())

    # Load the target output from the labeled data CSV
    if not os.path.exists(labeled_data_path):
        raise FileNotFoundError(f"Labeled data file not found: {labeled_data_path}")
    target_output_df = load_csv(labeled_data_path)

    # Ensure both DataFrames have the required columns and preprocess them
    llm_output_df, target_output_df = check_required_columns(llm_output_df, target_output_df)
    llm_output_df, target_output_df = preprocess_data(llm_output_df, target_output_df)

    # Get rows from target_output where supplier_name, date_of_sending, email_adress, phone_number, email_subject match the input_id
    relevant_target_rows = target_output_df[
        (target_output_df["supplier_name"] == supplier_name) &
        (target_output_df["date_of_sending"] == date_of_sending) &
        (target_output_df["email_address"] == email_adress) &
        #(target_output_df["phone_number"] == phone_number) & TO DO: be able to match phone numbers
        (target_output_df["email_subject"] == email_subject)
    ]

    # If no matching rows are found, raise an error
    if relevant_target_rows.empty:
        raise ValueError(f"No matching rows found in target output for input ID {input_id}.")
    print("Found matching rows in target output for the given input_id.")
    print(relevant_target_rows)

    # print shape of relevant_target_rows
    print(f"Number of matching rows in target output: {relevant_target_rows.shape[0]}")
    # print shape of llm_output_df
    print(f"Number of rows in LLM output: {llm_output_df.shape[0]}")

    target_output_df = relevant_target_rows.reset_index(drop=True)

    # Select the relevant columns for comparison
    llm_output_df, target_output_df = select_comparison_columns(llm_output_df, target_output_df)


    # Link rows between the LLM output and the target output
    target_llm_links = link_rows_hungarian(llm_output_df, target_output_df, min_score=0.0)

    # Create a DataFrame with the value comparisons 
    value_comparison_df = get_value_comparison_df(llm_output_df, target_output_df, target_llm_links)

    return value_comparison_df








async def main():
    inputs = load_inputs()
    input_id = 3
    run_id = '3944962e-5a5c-4f83-ad1a-db315958c52e'
    batch_id = '20250605101729'

    # # For now, we will use a hardcoded response to simulate the LLM output
    response = """
    {\"product_offers\":[{\"product_type\":\"Cauliflower\",\"variety\":\"White Naked\",\"sub_variety\":\"unspecified\",\"size\":\"6\",\"brand\":\"unspecified\",\"package_type\":\"Wooden Crate\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"FR - France\",\"piece\":\"6pc\",\"price\":9.75,\"net_weight\":10.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Cauliflower\",\"variety\":\"White Filmed\",\"sub_variety\":\"unspecified\",\"size\":\"8\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"ES - Spain\",\"piece\":\"8pc\",\"price\":7.95,\"net_weight\":0.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Broccoli\",\"variety\":\"On Ice\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Styro Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"ES - Spain\",\"piece\":\"unspecified\",\"price\":11.5,\"net_weight\":8.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Broccoli\",\"variety\":\"Green Naked\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"ES - Spain\",\"piece\":\"10x500\",\"price\":8.75,\"net_weight\":0.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Pointed Cabbage Green\",\"variety\":\"Naked\",\"sub_variety\":\"unspecified\",\"size\":\"9-11\",\"brand\":\"unspecified\",\"package_type\":\"Plastic Crate\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"PT - Portugal\",\"piece\":\"9-11pc\",\"price\":7.5,\"net_weight\":10.0,\"qty_per_pallet\":0,\"remarks\":\"With outer leaves\"},{\"product_type\":\"Pointed Cabbage Green\",\"variety\":\"Naked\",\"sub_variety\":\"unspecified\",\"size\":\"8\",\"brand\":\"unspecified\",\"package_type\":\"Plastic Crate\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"PT - Portugal\",\"piece\":\"8pc\",\"price\":8.95,\"net_weight\":9.0,\"qty_per_pallet\":0,\"remarks\":\"Without outer leaves\"},{\"product_type\":\"Pointed Cabbage Green\",\"variety\":\"Industry\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Big Bag\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"PT - Portugal\",\"piece\":\"2x350kg\",\"price\":0.65,\"net_weight\":700.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Pointed Cabbage Red\",\"variety\":\"Naked\",\"sub_variety\":\"unspecified\",\"size\":\"8\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"8pc\",\"price\":17.0,\"net_weight\":7.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Pointed Cabbage Red\",\"variety\":\"Industry\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Big Bag\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"1x900kg\",\"price\":1.75,\"net_weight\":900.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Savoy Cabbage\",\"variety\":\"Industry\",\"sub_variety\":\"unspecified\",\"size\":\"8\",\"brand\":\"unspecified\",\"package_type\":\"Plastic Crate\",\"pallet\":\"unspecified\",\"product_class\":\"Industry\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"PT - Portugal\",\"piece\":\"8pc\",\"price\":7.75,\"net_weight\":9.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Savoy Cabbage\",\"variety\":\"Industry\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Big Bag\",\"pallet\":\"unspecified\",\"product_class\":\"Industry\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"PT - Portugal\",\"piece\":\"2x350kg\",\"price\":0.7,\"net_weight\":700.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Chinese Cabbage\",\"variety\":\"Naked\",\"sub_variety\":\"unspecified\",\"size\":\"8\",\"brand\":\"unspecified\",\"package_type\":\"Wooden Crate\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"8pc\",\"price\":9.5,\"net_weight\":8.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Chinese Cabbage\",\"variety\":\"Naked\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"unspecified\",\"price\":0.9,\"net_weight\":10.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Red Cabbage\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"6\",\"brand\":\"unspecified\",\"package_type\":\"Net Bag\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"6pc\",\"price\":8.25,\"net_weight\":10.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Red Cabbage\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Big Bag\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"1x1150kg\",\"price\":0.82,\"net_weight\":1150.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Green Cabbage\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"6\",\"brand\":\"unspecified\",\"package_type\":\"Net Bag\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"6pc\",\"price\":5.95,\"net_weight\":10.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Green Cabbage\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Big Bag\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"1x1150kg\",\"price\":0.59,\"net_weight\":1150.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Kale\",\"variety\":\"On Ice\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"unspecified\",\"price\":7.5,\"net_weight\":4.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Celeriac\",\"variety\":\"Washed\",\"sub_variety\":\"unspecified\",\"size\":\"10\",\"brand\":\"unspecified\",\"package_type\":\"Net Bag\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"10pc\",\"price\":7.25,\"net_weight\":10.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Celeriac\",\"variety\":\"Washed\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Big Bag\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"1x1150kg\",\"price\":0.79,\"net_weight\":1150.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Celery\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"16\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"ES - Spain\",\"piece\":\"16pc\",\"price\":11.25,\"net_weight\":10.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Celery\",\"variety\":\"Naked\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"ES - Spain\",\"piece\":\"unspecified\",\"price\":1.25,\"net_weight\":11.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Leek\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Net Bag\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"unspecified\",\"price\":4.95,\"net_weight\":5.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Leek\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"unspecified\",\"price\":11.0,\"net_weight\":10.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Leek\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"unspecified\",\"price\":12.0,\"net_weight\":10.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Brussels Sprouts\",\"variety\":\"Cleaned Loose\",\"sub_variety\":\"unspecified\",\"size\":\"30-35\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"unspecified\",\"price\":9.95,\"net_weight\":0.0,\"qty_per_pallet\":0,\"remarks\":\"Prepared\"},{\"product_type\":\"Brussels Sprouts\",\"variety\":\"Cleaned Loose\",\"sub_variety\":\"unspecified\",\"size\":\"B\",\"brand\":\"unspecified\",\"package_type\":\"Net Bag\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"unspecified\",\"price\":8.5,\"net_weight\":0.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Pak Choi\",\"variety\":\"Naked\",\"sub_variety\":\"unspecified\",\"size\":\"10\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"10pc\",\"price\":7.95,\"net_weight\":3.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Pak Choi Shanghai\",\"variety\":\"Naked\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"unspecified\",\"price\":11.5,\"net_weight\":8.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Radish\",\"variety\":\"Red Bunch\",\"sub_variety\":\"unspecified\",\"size\":\"G\",\"brand\":\"unspecified\",\"package_type\":\"Bag\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"unspecified\",\"price\":13.75,\"net_weight\":10.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Radish\",\"variety\":\"Red Bunch\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Bag\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"10x1kg\",\"price\":15.5,\"net_weight\":10.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Radish\",\"variety\":\"Daikon\",\"sub_variety\":\"unspecified\",\"size\":\"XL\",\"brand\":\"unspecified\",\"package_type\":\"Wooden Crate\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"IT - Italy\",\"piece\":\"unspecified\",\"price\":0.75,\"net_weight\":15.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Fennel\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"14\",\"brand\":\"unspecified\",\"package_type\":\"Plastic Crate\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"IT - Italy\",\"piece\":\"unspecified\",\"price\":6.5,\"net_weight\":5.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Herbs\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Wooden Crate\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"IT - Italy\",\"piece\":\"unspecified\",\"price\":9.95,\"net_weight\":5.0,\"qty_per_pallet\":0,\"remarks\":\"Curley Parsley\"},{\"product_type\":\"Herbs\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Plastic Crate\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"IT - Italy\",\"piece\":\"unspecified\",\"price\":9.95,\"net_weight\":5.0,\"qty_per_pallet\":0,\"remarks\":\"Flat Parsley\"},{\"product_type\":\"Lettuce\",\"variety\":\"Iceberg\",\"sub_variety\":\"unspecified\",\"size\":\"10\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"ES - Spain\",\"piece\":\"10pc\",\"price\":0.0,\"net_weight\":0.0,\"qty_per_pallet\":0,\"remarks\":\"Price on request\"},{\"product_type\":\"Lettuce\",\"variety\":\"Romana\",\"sub_variety\":\"unspecified\",\"size\":\"10\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"ES - Spain\",\"piece\":\"10pc\",\"price\":9.5,\"net_weight\":0.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Lettuce\",\"variety\":\"Iceberg\",\"sub_variety\":\"unspecified\",\"size\":\"10\",\"brand\":\"unspecified\",\"package_type\":\"EPS\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"ES - Spain\",\"piece\":\"10pc\",\"price\":1.2,\"net_weight\":10.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Lettuce\",\"variety\":\"Iceberg\",\"sub_variety\":\"unspecified\",\"size\":\"10\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"ES - Spain\",\"piece\":\"10pc\",\"price\":0.0,\"net_weight\":10.0,\"qty_per_pallet\":0,\"remarks\":\"Price on request\"},{\"product_type\":\"Lettuce\",\"variety\":\"Little Gem\",\"sub_variety\":\"unspecified\",\"size\":\"10x6\",\"brand\":\"unspecified\",\"package_type\":\"Carton Box\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"ES - Spain\",\"piece\":\"10x6pc\",\"price\":19.0,\"net_weight\":0.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Lettuce\",\"variety\":\"Romaine\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"ES - Spain\",\"piece\":\"unspecified\",\"price\":1.4,\"net_weight\":7.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Lettuce\",\"variety\":\"Frisee\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"ES - Spain\",\"piece\":\"unspecified\",\"price\":1.3,\"net_weight\":8.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Lettuce\",\"variety\":\"Endive\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"ES - Spain\",\"piece\":\"unspecified\",\"price\":1.2,\"net_weight\":8.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Lettuce\",\"variety\":\"Bionda\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"ES - Spain\",\"piece\":\"unspecified\",\"price\":0.0,\"net_weight\":4.5,\"qty_per_pallet\":0,\"remarks\":\"Price on request\"},{\"product_type\":\"Lettuce\",\"variety\":\"Bionda\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"unspecified\",\"price\":2.1,\"net_weight\":4.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Lettuce\",\"variety\":\"Rossa\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"ES - Spain\",\"piece\":\"unspecified\",\"price\":0.0,\"net_weight\":4.5,\"qty_per_pallet\":0,\"remarks\":\"Price on request\"},{\"product_type\":\"Lettuce\",\"variety\":\"Rossa\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"unspecified\",\"price\":2.1,\"net_weight\":4.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Lettuce\",\"variety\":\"Sugerhood\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"IT - Italy\",\"piece\":\"unspecified\",\"price\":1.5,\"net_weight\":10.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Spinach\",\"variety\":\"Baby\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"ES - Spain\",\"piece\":\"unspecified\",\"price\":2.25,\"net_weight\":6.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Spinach\",\"variety\":\"Baby\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"unspecified\",\"price\":1.95,\"net_weight\":5.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Mache\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"EPS\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"IT - Italy\",\"piece\":\"unspecified\",\"price\":2.75,\"net_weight\":5.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Rucola\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Plastic Crate\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"IT - Italy\",\"piece\":\"unspecified\",\"price\":2.95,\"net_weight\":5.0,\"qty_per_pallet\":0,\"remarks\":\"\"},{\"product_type\":\"Rucola\",\"variety\":\"unspecified\",\"sub_variety\":\"unspecified\",\"size\":\"unspecified\",\"brand\":\"unspecified\",\"package_type\":\"Plastic Crate\",\"pallet\":\"unspecified\",\"product_class\":\"unspecified\",\"unit_type\":\"BOX\",\"unit_trade_type\":\"unspecified\",\"country\":\"NL - Netherlands\",\"piece\":\"unspecified\",\"price\":1.95,\"net_weight\":4.0,\"qty_per_pallet\":0,\"remarks\":\"\"}]}
    """
    # Compare the LLM output to the target output
    # TODO: Adjust country code within labeled_data.csv to match the country codes in the LLM output
    value_comparison_df = compare_llm_to_target_output(inputs[inputs["id"] == input_id], response)
    print(f"Validation results for input ID {input_id}:\n{value_comparison_df}")

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
