# Import libraries
import numpy as np
import pandas as pd
import os
from rapidfuzz import fuzz
from datetime import datetime


# ---------- Configuration ----------
REQUIRED_COLUMNS = [
    'type', 'variety',
    'subvariety', 'size', 'piece', 'brand', 'package_type', 'class',
    'origin_country_code', 'net_weight', 'quantity_per_pallet', 'price',
    'remarks'
]

COMPARED_COLUMNS = ['type', 'variety', 'subvariety', 'size', 'piece', 'brand',
                   'package_type', 'class', 'origin_country_code', 
                   'net_weight', 'quantity_per_pallet', 'price']

# explicitly list which of your COMPARED_COLUMNS are numeric
NUMERIC_COLUMNS = {'net_weight', 'quantity_per_pallet', 'price', 'piece'}

# Set weights for similarity calculation
# The weights are used to adjust the importance of each column in the similarity calculation.
# Higher weights indicate more importance.
# The default weight for all columns is 1.0.
weights = {
    "type": 2.0,      # more important
    "price": 2.0,     # moderately important
}

# ---------- Functions ----------

def save_with_history(df: pd.DataFrame, base_filename: str):
    """
    Prepends a timestamp column, writes latest_<base> (overwrite) and 
    appends to all_<base> (create or append).
    """
    # 1. Insert timestamp column
    ts = datetime.now().isoformat()
    df.insert(0, 'timestamp_of_validation', ts)

    # 2. Prepare filenames
    today_file = f"latest_{base_filename}"
    all_file   = f"all_{base_filename}"

    # 3. Write the 'latest' file (always overwrite)
    df.to_csv(today_file, index=False)
    print(f"✅ Wrote {today_file} ({df.shape[0]} rows).")

    # 4. Write the 'all' file (append, no header if exists)
    if os.path.exists(all_file):
        df.to_csv(all_file, mode='a', index=False, header=False)
        print(f"✅ Appended {df.shape[0]} rows to {all_file}.")
    else:
        df.to_csv(all_file, index=False)
        print(f"✅ Created {all_file} with {df.shape[0]} rows.")

def load_data(file_path):
    """
    Get csv file as dataframe
    """
    print(f"Loading {file_path}...")
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        print(f"Loaded {file_path} with shape: {df.shape}")
        return df
    else:
        raise FileNotFoundError(f"{file_path} not found")

def check_required_columns(llm_output_df, target_output_df):
    """
    Check if the required columns are present in both DataFrames.
    """
    print("Checking for missing columns...")
    missing_llm = set(REQUIRED_COLUMNS) - set(llm_output_df.columns)
    missing_target = set(REQUIRED_COLUMNS) - set(target_output_df.columns)

    if missing_llm or missing_target:
        raise ValueError(
            f"Missing required columns:\n"
            f" - In llm_output: {missing_llm if missing_llm else 'None'}\n"
            f" - In target_output: {missing_target if missing_target else 'None'}"
        )
    else:
        print("Both DataFrames contain all required columns.")
        target_output_df = target_output_df[REQUIRED_COLUMNS]
        llm_output_df = llm_output_df[REQUIRED_COLUMNS]
        return target_output_df, llm_output_df

def preprocess_data(llm_df, target_df):
    """
    Preprocess the DataFrames by replacing 'unspecified' with NaN,
    converting numeric fields, and normalizing date fields.
    """
    print("Replacing 'unspecified' values with NaN...")
    llm_df.replace('unspecified', np.nan, inplace=True)
    target_df.replace('unspecified', np.nan, inplace=True)

    llm_df, target_df = check_required_columns(llm_df, target_df)

    print("Converting numeric fields...")
    for col in ['class', 'net_weight', 'quantity_per_pallet', 'price']:
        is_int = col in {'class', 'quantity_per_pallet'}
        for df in [llm_df, target_df]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            if is_int:
                df[col] = df[col].astype('Int64')
            else:
                df[col] = df[col].round(2)

    print("Normalizing date fields...")
    for df in [llm_df, target_df]:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['date'] = df['date'].dt.tz_localize(None).dt.normalize()

    return llm_df, target_df

def find_overlap(target_df, llm_df):
    """
    Find overlapping emails between the target and LLM DataFrames.
    """
    print("Finding overlapping emails...")
    emails_ids_target = target_df[['sender', 'date', 'subject']].drop_duplicates()
    emails_ids_llm = llm_df[['sender', 'date', 'subject']].drop_duplicates()

    target_set = set(tuple(x) for x in emails_ids_target.values)
    llm_set = set(tuple(x) for x in emails_ids_llm.values)

    overlap_set = target_set & llm_set
    print(f"Found {len(overlap_set)} overlapping emails.")

    # Filter both DataFrames
    llm_filtered = llm_df[llm_df[['sender', 'date', 'subject']].apply(tuple, axis=1).isin(overlap_set)]
    target_filtered = target_df[target_df[['sender', 'date', 'subject']].apply(tuple, axis=1).isin(overlap_set)]

    print(f"LLM shape after filtering: {llm_filtered.shape}")
    print(f"Target shape after filtering: {target_filtered.shape}")

    return overlap_set, target_filtered, llm_filtered


def row_similarity(target_row, llm_row, columns, weights=None):
    """
    Returns a weighted average per‐column similarity:
     - for numeric columns: 1.0 if exactly equal, else 0
     - for others: fuzzy string similarity (0–100)/100
     - NaNs match only NaNs
    - weights: optional dict of column → weight
    """
    scores = {}
    total_weight = 0
    weighted_sum = 0

    for col in columns:
        target_value = target_row[col]
        llm_value = llm_row[col]

        # Default weight = 1 if not specified
        weight = weights.get(col, 1.0) if weights else 1.0

        # both missing → perfect
        if pd.isna(target_value) and pd.isna(llm_value):
            similarity = 1.0
        # one missing → zero
        elif pd.isna(target_value) or pd.isna(llm_value):
            similarity = 0.0
        # numeric
        elif col in NUMERIC_COLUMNS:
            similarity = 1.0 if target_value == llm_value else 0.0
        # fuzzy string
        else:
            s_target, s_llm = str(target_value), str(llm_value)
            ratio = fuzz.partial_ratio(s_target, s_llm)
            similarity = ratio / 100.0

        scores[col] = similarity
        weighted_sum += weight * similarity
        total_weight += weight

    final_score = weighted_sum / total_weight if total_weight > 0 else 0
    return final_score

def attribute_match(row1, row2, columns):
    """
    Returns a dictionary with 1 for perfect match, 0 for mismatch, and NaN for missing values.
    """
    result = {}
    for col in columns:
        val1 = row1[col]
        val2 = row2[col]
        if pd.isna(val1) and pd.isna(val2):
            result[col] = 1
        elif pd.isna(val1) or pd.isna(val2):
            result[col] = 0
        elif val1 == val2:
            result[col] = 1
        else:
            result[col] = 0
    return result

def match_rows(target_df, llm_df, overlap_set):
    """
    Match rows between the target and LLM DataFrames based on the overlap set.
    """
    all_reports, all_matches, all_mismatches, detailed_field_results_all = [], [], [], []

    for combination in overlap_set:
        sender, date, subject = combination

        # Filter
        llm_filtered = llm_df[(llm_df['sender'] == sender) & 
                              (llm_df['date'] == date) & 
                              (llm_df['subject'] == subject)]

        target_filtered = target_df[(target_df['sender'] == sender) & 
                                    (target_df['date'] == date) & 
                                    (target_df['subject'] == subject)]

        # Sort
        llm_filtered = llm_filtered.sort_values(by=['price', 'type', 'origin_country_code'])
        target_filtered = target_filtered.sort_values(by=['price', 'type', 'origin_country_code'])

        matches = []
        used_llm_indices = set()
        detailed_field_results = []

        for idx_target, target_row in target_filtered.iterrows():
            best_score = -1
            best_idx = None
            best_field_match = None

            for idx_llm, llm_row in llm_filtered.iterrows():
                if idx_llm in used_llm_indices:
                    continue
                score = row_similarity(target_row, llm_row, COMPARED_COLUMNS)
                if score > best_score:
                    best_score = score
                    best_idx = idx_llm
                    best_field_match = attribute_match(target_row, llm_row, COMPARED_COLUMNS)

            if best_idx is not None:
                match_record = {
                    'supplier_name': target_row.get('supplier_name', np.nan),
                    'sender': sender,
                    'date': date,
                    'subject': subject,
                    'idx_target': idx_target,
                    'idx_llm': best_idx,
                    'similarity': best_score
                }
                for col in COMPARED_COLUMNS:
                    match_record[f'{col}_target'] = target_row.get(col, np.nan)
                    match_record[f'{col}_llm'] = llm_filtered.loc[best_idx].get(col, np.nan)
                all_matches.append(match_record)

                # Record mismatches
                for col in COMPARED_COLUMNS:
                    target_val = target_row.get(col, np.nan)
                    llm_val = llm_filtered.loc[best_idx].get(col, np.nan)

                    if (pd.isna(target_val) and pd.isna(llm_val)):
                        continue
                    elif (pd.isna(target_val) or pd.isna(llm_val)) or (target_val != llm_val):
                        mismatch_record = {
                            'supplier_name': target_row.get('supplier_name', np.nan),
                            'sender': sender,
                            'date': date,
                            'subject': subject,
                            'attribute': col,
                            'target_value': target_val,
                            'LLM_value': llm_val
                        }
                        all_mismatches.append(mismatch_record)

                matches.append({'target_idx': idx_target, 'llm_idx': best_idx, 'similarity': best_score})
                used_llm_indices.add(best_idx)
                detailed_field_results.append(best_field_match)

        matches_df = pd.DataFrame(matches)
        detailed_field_df = pd.DataFrame(detailed_field_results)
        detailed_field_results_all.append(detailed_field_df)

        report = {
            'supplier_name': target_row.get('supplier_name', np.nan),
            'sender': sender,
            'date': date,
            'subject': subject,
            'n_offers_target': len(target_filtered),
            'n_offers_llm': len(llm_filtered),
            'average_similarity': matches_df['similarity'].mean(),
            'std_similarity': matches_df['similarity'].std(),
            'percentage_perfect_matches': (matches_df['similarity'] == 1.0).mean() * 100
        }

        for col in COMPARED_COLUMNS:
            if not detailed_field_df.empty:
                report[f'accuracy_{col}'] = detailed_field_df[col].mean()
            else:
                report[f'accuracy_{col}'] = np.nan

        all_reports.append(report)

    return all_reports, all_matches, all_mismatches, pd.concat(detailed_field_results_all, ignore_index=True)

def generate_product_type_similarity_report(matches_df):
    if 'type_target' in matches_df.columns:
        product_match_report = (
            matches_df
            .groupby('type_target')
            .agg(
                n_matches=('similarity', 'count'),
                average_similarity=('similarity', 'mean'),
                std_similarity=('similarity', 'std'),
                n_rows=('similarity', 'count')
            )
            .reset_index()
            .sort_values('average_similarity', ascending=True)
        )
        return product_match_report
    else:
        print("⚠️ Warning: type_target column not found, cannot create product type similarity report.")

def generate_attribute_similarity_report(detailed_field_df, COMPARED_COLUMNS):
    if detailed_field_df.empty:
        print("⚠️ No detailed field comparison data available.")
        return

    report_rows = []
    for col in COMPARED_COLUMNS:
        avg = detailed_field_df[col].mean()
        std = detailed_field_df[col].std()
        report_rows.append({
            'attribute': col,
            'average_similarity': avg,
            'std_similarity': std
        })

    attribute_report_df = pd.DataFrame(report_rows)
    return attribute_report_df

# ---------- Main execution ----------
if __name__ == "__main__":
    # Load both datasets
    llm_output_df = load_data("llm_output.csv")
    target_output_df = load_data("target_output.csv")

    print("Retrieving unique combinations of sender, date, and subject...")
    emails_ids_llm = llm_output_df[['sender', 'date', 'subject']].drop_duplicates()
    print(f"Found {len(emails_ids_llm)} unique combinations of sender, date, and subject within the LLM output:\n")
    print(emails_ids_llm)
    email_ids_target = target_output_df[['sender', 'date', 'subject']].drop_duplicates()
    print(f"Found {len(email_ids_target)} unique combinations of sender, date, and subject within the target output:\n")
    print(email_ids_target)

    # Check if both DataFrames have the required columns
    llm_output_df, target_output_df = check_required_columns(llm_output_df, target_output_df)

    # Preprocess data by replacing 'unspecified' with NaN, converting numeric fields, and normalizing date fields
    llm_output_df, target_output_df = preprocess_data(llm_output_df, target_output_df)

    # Find overlap between the two DataFrames
    overlap_set, target_output_df, llm_output_df = find_overlap(target_output_df, llm_output_df)

    # Match rows and collect reports
    all_reports, all_matches, all_mismatches, all_detailed_field_df = match_rows(target_output_df, llm_output_df, overlap_set)

    # Save outputs
    final_report_df = pd.DataFrame(all_reports)
    final_matches_df = pd.DataFrame(all_matches)
    final_mismatches_df = pd.DataFrame(all_mismatches)
    type_simlairty_report_df = generate_product_type_similarity_report(final_matches_df)
    attribute_similarity_df = generate_attribute_similarity_report(all_detailed_field_df, COMPARED_COLUMNS)
    
    # Now save each with history
    save_with_history(final_report_df,     'report_per_email.csv')
    save_with_history(final_matches_df,    'report_row_matches.csv')
    save_with_history(final_mismatches_df, 'report_value_mismatches.csv')
    save_with_history(type_simlairty_report_df,         'report_per_type.csv')
    save_with_history(attribute_similarity_df,    'report_per_attribute.csv')


    # final_report_df.to_csv('report_per_email.csv', index=False)
    # final_matches_df.to_csv('report_row_matches.csv', index=False)
    # final_mismatches_df.to_csv('report_value_mismatches.csv', index=False)
    # type_simlairty_report_df.to_csv('report_per_type.csv', index=False)
    # attribute_similarity_df.to_csv('report_per_attribute.csv', index=False)

    # print("✅ Validation report saved: report_per_email.csv")
    # print("✅ Row Matches saved: report_row_matches.csv")
    # print("✅ Field-level mismatches saved: report_value_mismatches.csv")
    # print("✅ Product Type Similarity Report saved: report_per_type.csv")
    # print("✅ Attribute Similarity Report saved: report_per_attribute.csv")



    



