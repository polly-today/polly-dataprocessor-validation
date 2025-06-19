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
    TEXT_COLUMNS,
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
    # 1) Coerce everything in numeric_cols to float64 (NaN for bad/non-numeric)
    for df in (llm_output_df, target_output_df):
        df[list(NUMERIC_COLUMNS)] = df[list(NUMERIC_COLUMNS)].apply(pd.to_numeric, errors='coerce')
    
    # 2) In the LLM frame: mask zeros and NaNs → <NA>
    for col in NUMERIC_COLUMNS:
        llm_output_df[col] = (
            llm_output_df[col]
            .mask(llm_output_df[col].isna() | (llm_output_df[col] == 0))  # NaN or zero → NA
            .astype('Float64')                                          # ensure nullable float
        )

    # 3) In the target frame: mask NaNs → <NA> (but leave real zeros)
    for col in NUMERIC_COLUMNS:
        target_output_df[col] = (
            target_output_df[col]
            .mask(target_output_df[col].isna())  # only NaN → NA
            .astype('Float64')
        )
    
    # 4) Replace 'N/A - unspecified' with 'unspecified' in string columns
    for col in TEXT_COLUMNS:
        llm_output_df[col] = llm_output_df[col].replace('N/A - unspecified', 'unspecified')
    
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
    if column in TEXT_COLUMNS:
        if target_value == 'unspecified' or llm_value == 'unspecified':
            # When both values are 'unspecified', we treat it as a perfect match
            if target_value == 'unspecified' and llm_value == 'unspecified':
                similarity = 1.0
            # When LLM value is 'unspecified' and target is not, we treat it as a partial match
            elif llm_value == 'unspecified' and target_value != 'unspecified':
                similarity = 0.5
            # When target is 'unspecified' and LLM value is not, we treat it as a mismatch
            elif target_value == 'unspecified' and llm_value != 'unspecified':
                similarity = 0.0
            else:
                raise ValueError(f"Unexpected NaN handling for column '{column}': target={target_value}, llm={llm_value}")
        else:
            # For string columns, calculate the Levenshtein ratio
            s_target, s_llm = str(target_value), str(llm_value)
            similarity = levenshtein_ratio(s_target, s_llm)
    
    # For numeric columns, check for exact match
    elif column in NUMERIC_COLUMNS:
        if pd.isna(target_value) or pd.isna(llm_value):
            if pd.isna(target_value) and pd.isna(llm_value):
                similarity = 1.0
            elif not pd.isna(target_value) and pd.isna(llm_value):
                # Target is not NaN, LLM value is NaN
                similarity = 0.5
            elif pd.isna(target_value) and not pd.isna(llm_value):
                # Target is NaN, LLM value is not NaN
                similarity = 0.0
        elif target_value == llm_value:
            similarity = 1.0
        else:
            similarity = 0.0
    else:
        raise ValueError(f"Unsupported column type for similarity calculation: {column}")
    
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

def get_unmatched_llm_rows(target_llm_links, llm_output_df):
    """
    Get the indices of LLM rows that are not matched to any target row.
    """
    # Get the indices of matched rows from the target_llm_links dictionary
    matched_indices = set(target_llm_links.values())
    unmatched_llm_indices = [i for i in range(len(llm_output_df)) if i not in matched_indices]
    return unmatched_llm_indices

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
            if llm_row is None:
                # If the LLM row is None, set llm_value to NaN or 'unspecified' based on column type
                if col in NUMERIC_COLUMNS:
                    llm_value = pd.NA
                else:
                    llm_value = 'unspecified'
            else:
                llm_value = llm_row[col]

            similarity = get_value_similarity(target_value, llm_value, col)
            comparison_data.append({
                "target_row_index": i,
                "llm_row_index": j,
                "attribute": col,
                "target_value": target_value,
                "llm_value": llm_value,
                "similarity_score": similarity
            })

    # Add unmatched LLM rows with NaN values for target_value and similarity_score 
    unmatched_llm_indices= get_unmatched_llm_rows(target_llm_links, llm_output_df)
    for k in unmatched_llm_indices:
        llm_row = llm_output_df.iloc[k]
        for col in REQUIRED_COLUMNS_COMPARISON:
            # Determine target_value default based on column type
            if col in NUMERIC_COLUMNS:
                target_value = pd.NA
            else:
                target_value = 'unspecified'
            comparison_data.append({
                "target_row_index": None,
                "llm_row_index": k,
                "attribute": col,
                "target_value": target_value,
                "llm_value": llm_row[col],
                "similarity_score": 0
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
        ((target_output_df["email_address"] == email_adress) | (target_output_df["phone_number"] == phone_number)) &
        (target_output_df["email_subject"] == email_subject)
    ]
    
    # If no matching rows are found, raise an error
    if relevant_target_rows.empty:
        raise ValueError(f"No matching rows found in target output for input ID {input_id}.")
    print("Found matching rows in target output for the given input_id.")
    print(relevant_target_rows)

    target_output_df = relevant_target_rows.reset_index(drop=True)

    # Select the relevant columns for comparison
    llm_output_df, target_output_df = select_comparison_columns(llm_output_df, target_output_df)

    # Link rows between the LLM output and the target output
    target_llm_links = link_rows_hungarian(llm_output_df, target_output_df, min_score=0.0)

    # Create a DataFrame with the value comparisons 
    value_comparison_df = get_value_comparison_df(llm_output_df, target_output_df, target_llm_links)

    # Print rows where target_value and llm_value are not equal
    mismatches = value_comparison_df[
        (value_comparison_df["target_value"] != value_comparison_df["llm_value"])
    ]
    return value_comparison_df