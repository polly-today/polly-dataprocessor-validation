REQUIRED_COLUMNS_TARGET = [
    "date_of_sending", "supplier_name", "email_address", "email_subject", "phone_number",
    "product_type", "variety", "sub_variety", "size", "piece", "brand", "package_type",
    "product_class", "country", "net_weight", "qty_per_pallet", "price"
]

REQUIRED_COLUMNS_COMPARISON = [
    "product_type", "variety", "sub_variety", "size", "piece",
    "brand", "package_type", "product_class", "country",
    "net_weight", "qty_per_pallet", "price"
]

NUMERIC_COLUMNS = {"net_weight", "qty_per_pallet", "price", "piece"}

# Weights for similarity: override “default = 1.0” logic per‐column
SIMILARITY_WEIGHTS = {
    "product_type": 2.0,
    "price": 2.0,
}