# Configuration file for the application

# Path to the labeled data CSV file
labeled_data_path = "../data/labeled_data.csv"
# Path to the manual prompt text file
manual_prompt_path = "../prompts/manual_prompt.txt"
# Path to the default prompt text file
default_prompt_path = "../prompts/default_prompt.txt"
# Path to the response schema JSON file
response_schema_path = "../data/response_schema.json"

### VALIDATION.py ###
# Required columns for the target_output (labeled data)
REQUIRED_COLUMNS_TARGET = [
    "date_of_sending", "supplier_name", "email_address", "email_subject", "phone_number",
    "product_type", "variety", "sub_variety", "size", "piece", "brand", "package_type",
    "product_class", "country", "net_weight", "qty_per_pallet", "price"
]

# Required columns for comparison of the LLM output & to the target output
REQUIRED_COLUMNS_COMPARISON = [
    "product_type", "variety", "sub_variety", "size", "piece",
    "brand", "package_type", "product_class", "country",
    "net_weight", "qty_per_pallet", "price"
]

# Numerical columns for comparison
NUMERIC_COLUMNS = {"net_weight", "qty_per_pallet", "price"}

# Text columns for comparison
TEXT_COLUMNS = {
    "product_type", "variety", "sub_variety", "size", "piece",
    "brand", "package_type", "product_class", "country"
}

# Weights for similarity: override “default = 1.0” logic per‐column
SIMILARITY_WEIGHTS = {
    "product_type": 2.0,
    "price": 2.0,
}