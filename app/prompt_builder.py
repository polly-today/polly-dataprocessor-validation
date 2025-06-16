import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from utils import (load_csv)
from config import (
    labeled_data_path,
)

# Load database URL from .env file
load_dotenv()
database_url_stg = os.getenv("DATABASE_URL_STG")
if database_url_stg is None:
    raise RuntimeError("DATABASE_URL_STG not found—did you create a .env with that variable?")
database_url_val = os.getenv("DATABASE_URL")
if database_url_val is None:
    raise RuntimeError("DATABASE_URL not found—did you create a .env with that variable?")

# Create a SQLAlchemy engine to run SQL queries
engine_stg = create_engine(database_url_stg)
engine_val = create_engine(database_url_val)


# ### HELPER FUNCTIONS ###
def get_relevant_product_types(input, target_output_df):
    """
    Retrieve the target rows from the labeled data CSV based on the input DataFrame.
    This function will filter the target output DataFrame to match the input metadata.
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
    # Check if supplier_name, date_of_sending, email_adress, phone_number, email_subject are columns in the DataFrame
    if not all(col in target_output_df.columns for col in ["supplier_name", "date_of_sending", "email_address", "phone_number", "email_subject", "product_type"]):
        raise ValueError(f"Missing columns in target_output_df: {set(['supplier_name', 'date_of_sending', 'email_address', 'phone_number', 'email_subject', 'product_type']).difference(target_output_df.columns)}")
    # Ensure date_of_sending is a datetime object in the same time zone
    target_output_df["date_of_sending"] = pd.to_datetime(
        target_output_df["date_of_sending"],
        format="%d-%m-%Y %H:%M:%S",  # or omit format and use dayfirst=True
        errors="coerce"
    )

    # Get rows from target_output where supplier_name, date_of_sending, email_adress, phone_number, email_subject match the input_id
    relevant_target_rows = target_output_df[
        (target_output_df["supplier_name"] == supplier_name) &
        (target_output_df["date_of_sending"] == date_of_sending) &
        (target_output_df["email_address"] == email_adress) &
        #(target_output_df["phone_number"] == phone_number) & TO DO: be able to match phone numbers
        (target_output_df["email_subject"] == email_subject)
    ]

    # Get all product types from the relevant target rows and convert to a set
    if relevant_target_rows.empty:
        raise ValueError(f"No matching rows found in target output for input ID {input_id}.")

    target_output_df = relevant_target_rows.reset_index(drop=True)
    product_types = set(target_output_df["product_type"].dropna().unique())
    #print(f"Relevant product types for input ID {input_id}: {product_types}")
    return product_types


def retrieve_aliases(supplier_id, id_value_dict):
    """
    Retrieve aliases for a given supplier_id and a dictiory of value IDs (e.g. package_type_id to package_type_name.)
    The output is a dictionary where keys are the values from id_value_dict and values are lists of aliases.
    """
    with engine_stg.connect() as conn:
        query = text("""
            SELECT value_id, alias FROM product_attributes_value_aliases 
            WHERE (supplier_id = :supplier_id OR supplier_id IS NULL) AND value_id IN :value_ids;
        """)
        result = conn.execute(query, {"supplier_id": supplier_id, "value_ids": tuple(id_value_dict.keys())})
        id_aliases = {}
        for row in result.fetchall():
            value_id, alias = row[0], row[1]
            if value_id not in id_aliases:
                id_aliases[value_id] = []
            id_aliases[value_id].append(alias)

        # Create a dictionary to hold aliases for each value
        value_aliases = {}
        for value_id, aliases in id_aliases.items():
            if value_id in id_value_dict:
                value_aliases[id_value_dict[value_id]] = aliases
    return value_aliases


def retrieve_product_types(relevant_product_types=None):
    """
    Load product_types table from the database and return as a pandas DataFrame.
    """
    product_types = {}
    toBeAddedProductTypes = []

    for product_type in relevant_product_types:
        query = text("SELECT id, name FROM product_types WHERE name = :product_type;")
        with engine_stg.connect() as conn:
            result = conn.execute(query, {"product_type": product_type})
            row = result.fetchone()
        if row:
            product_types[row[0]] = row[1]
        else:
            toBeAddedProductTypes.append(product_type)

    print(f"The following product types were not found in the database and need to be added: {toBeAddedProductTypes}")
    
    return product_types


def retrieve_supplier_rules(supplier_id):
    with engine_stg.connect() as conn:
        query = text("SELECT rule FROM supplier_rules where supplier_id = :supplier_id;")
        result = conn.execute(query, {"supplier_id": supplier_id})
        supplier_rules = [row[0] for row in result.fetchall()]  # Fetch all rows and extract the first column
        #print(f"Supplier rules retrieved: {supplier_rules}")
        return supplier_rules


def retrieve_package_types(supplier_id):
    with engine_stg.connect() as conn:
        query = text("SELECT id, name FROM package_types;")
        result = conn.execute(query)
        package_types = {row[0]: row[1] for row in result.fetchall()}  # Fetch all rows and extract the first column
        #print(f"Package types retrieved: {package_types.values()}")

    # Retrieve aliases for package types
    aliases = retrieve_aliases(supplier_id=supplier_id, id_value_dict=package_types)
    #print(f"Aliases retrieved for package types: {aliases}")

    # Convert the dictionary to a list of package type names
    package_types = list(package_types.values())
    package_types.sort()
    return package_types, aliases


def retrieve_classes(supplier_id=None):
    with engine_stg.connect() as conn:
        query = text("SELECT id, name FROM classes;")
        result = conn.execute(query)
        classes = {row[0]: row[1] for row in result.fetchall()}  # Fetch all rows and extract the first column
        #print(f"Classes retrieved: {classes.values()}")
    
    # Retrieve aliases for classes
    aliases = retrieve_aliases(supplier_id=supplier_id, id_value_dict=classes)
    #print(f"Aliases retrieved for classes: {aliases}")

    # Convert the dictionary to a list of class names on alphabetical order
    classes = list(classes.values())
    classes.sort()
    return classes, aliases


def retrieve_countries(supplier_id=None):
    with engine_stg.connect() as conn:
        query = text("SELECT id, code, name FROM countries;")
        result = conn.execute(query)
        countries = {row[0]: (str(row[1]) + " - " + row[2]) for row in result.fetchall()}
        #print(f"Countries retrieved: {countries.values()}")
    
    # Retrieve aliases for countries
    aliases = retrieve_aliases(supplier_id=None, id_value_dict=countries)
    #print(f"Aliases retrieved for countries: {aliases}")

    # Convert the dictionary to a list of country names
    countries = list(countries.values())
    countries.sort()
    return countries, aliases


def retrieve_pallets(supplier_id=None):
    with engine_stg.connect() as conn:
        query = text("SELECT id, name FROM pallets;")
        result = conn.execute(query)
        pallets = {row[0]: row[1] for row in result.fetchall()}
        #print(f"Pallets retrieved: {pallets.values()}")
    
    # Retrieve aliases for pallets
    aliases = retrieve_aliases(supplier_id=supplier_id, id_value_dict=pallets)
    #print(f"Aliases retrieved for pallets: {aliases}")

    # Convert the dictionary to a list of pallet names
    pallets = list(pallets.values())
    pallets.sort()
    return pallets, aliases


def retrieve_unit_types(supplier_id=None):
    with engine_stg.connect() as conn:
        query = text("SELECT id, name FROM unit_types;")
        result = conn.execute(query)
        unit_types = {row[0]: row[1] for row in result.fetchall()}  # Fetch all rows and extract the first column
        #print(f"Unit types retrieved: {unit_types.values()}")
    
    # Retrieve aliases for unit types
    aliases = retrieve_aliases(supplier_id=supplier_id, id_value_dict=unit_types)
    #print(f"Aliases retrieved for unit types: {aliases}")

    # Convert the dictionary to a list of unit type names
    unit_types = list(unit_types.values())
    unit_types.sort()
    return unit_types, aliases


def retrieve_unit_trade_types(supplier_id=None):
    with engine_stg.connect() as conn:
        query = text("SELECT id, name FROM unit_trade_types;")
        result = conn.execute(query)
        unit_trade_types = {row[0]: row[1] for row in result.fetchall()}  # Fetch all rows and extract the first column
        #print(f"Unit trade types retrieved: {unit_trade_types.values()}")
    # Retrieve aliases for unit trade types
    aliases = retrieve_aliases(supplier_id=supplier_id, id_value_dict=unit_trade_types)
    #print(f"Aliases retrieved for unit trade types: {aliases}")

    # Convert the dictionary to a list of unit trade type names
    unit_trade_types = list(unit_trade_types.values())
    unit_trade_types.sort()
    return unit_trade_types, aliases


def retrieve_product_info(product_type_id, product_type_name, supplier_id=None):

    product_type_aliases = retrieve_aliases(supplier_id=supplier_id, id_value_dict={product_type_id: product_type_name})
    with engine_stg.connect() as conn:  
        # Retrieve product varieties and subvarieties for the given product_type_id
        query = text("""
            SELECT v.id as variety_id, 
                   v.name as variety_name,
                   sv.id as subvariety_id,
                   sv.name as subvariety_name
            FROM product_varieties as v
            LEFT JOIN product_sub_varieties as sv ON v.id = sv.variety_id
            WHERE v.type_id = :product_type_id;
        """)
        result = conn.execute(query, {"product_type_id": product_type_id})
        rows = result.fetchall()
        varieties = {row[0]: row[1] for row in rows if row[0] is not None}
        #print(f"Varieties retrieved: {varieties.values()}")
        subvarieties = {row[2]: row[3] for row in rows if row[2] is not None}
        #print(f"Sub-varieties retrieved: {subvarieties.values()}")
        # Create a dictionary to hold the relations between varieties and sub-varieties
        variety_subvariety_dict = {}
        for row in rows:
            variety_name = row[1]
            subvariety_name = row[3]
            if variety_name is not None and subvariety_name is not None:
                if variety_name not in variety_subvariety_dict:
                    variety_subvariety_dict[variety_name] = []
                variety_subvariety_dict[variety_name].append(subvariety_name)
        #print(f"Relations between varieties and sub-varieties: {variety_subvariety_dict}")
        variety_aliases = retrieve_aliases(supplier_id=supplier_id, id_value_dict=varieties)
        #print(f"Aliases retrieved for varieties: {variety_aliases}")
        subvariety_aliases = retrieve_aliases(supplier_id=supplier_id, id_value_dict=subvarieties)
        #print(f"Aliases retrieved for sub-varieties: {subvariety_aliases}")
        varieties = list(varieties.values())
        varieties.sort()
        subvarieties = list(subvarieties.values())
        subvarieties.sort()

        # TO DO: Retrieve product sizes for the given product_type_id
        query = text("SELECT id, name FROM sizes")
        result = conn.execute(query)
        sizes = {row[0]: row[1] for row in result.fetchall()}
        #print(f"Sizes retrieved: {sizes.values()}")
        size_aliases = retrieve_aliases(supplier_id=supplier_id, id_value_dict=sizes)
        #print(f"Aliases retrieved for sizes: {size_aliases}")
        sizes = list(sizes.values())
        sizes.sort()

        # TO DO: Retrieve product brands for the given product_type_id
        query = text("SELECT id, name FROM brands")
        result = conn.execute(query)
        brands = {row[0]: row[1] for row in result.fetchall()}
        #print(f"Brands retrieved: {brands.values()}")
        brand_aliases = retrieve_aliases(supplier_id=supplier_id, id_value_dict=brands)
        #print(f"Aliases retrieved for brands: {brand_aliases}")
        brands = list(brands.values())
        brands.sort()

        # TO DO: Retrieve product pieces for the given product_type_id
        query = text("SELECT id, name FROM pieces")
        result = conn.execute(query)
        pieces = {row[0]: row[1] for row in result.fetchall()}
        #print(f"Pieces retrieved: {pieces.values()}")
        piece_aliases = retrieve_aliases(supplier_id=supplier_id, id_value_dict=pieces)
        #print(f"Aliases retrieved for pieces: {piece_aliases}")
        pieces = list(pieces.values())
        pieces.sort()

        # TO DO: Retrieve product_type_rules

        return product_type_aliases, varieties, variety_aliases, subvarieties, subvariety_aliases, variety_subvariety_dict, sizes, size_aliases, brands, brand_aliases, pieces, piece_aliases


def write_prompt(
        relevant_product_types,
        product_type_aliases,
        varieties, variety_aliases,
        subvarieties, subvariety_aliases,
        variety_subvariety_dict,
        sizes, size_aliases,
        brands, brand_aliases,
        pieces, piece_aliases,
        package_types, package_type_aliases,
        pallets, pallet_aliases,
        product_classes, product_class_aliases,
        unit_types, unit_type_aliases,
        unit_trade_types, unit_trade_type_aliases,
        countries, country_aliases,
        supplier_rules):
    """
    Generates a dynamic prompt for extracting structured data from text based on the provided parameters.
    """

    prompt = f"""You are an expert data extractor. Your task is to extract detailed characteristics from the provided text and output them in a structured JSON format.

    Extraction instructions:
    1. Loop over each offer in the input text and produce one object per offer in the JSON output.
    2. Replace any alias with its canonical value.
    3. Detect product_type: 
    \t- Match against a ### Product Type heading or its aliases. 
    \t- If no match is found, use "unspecified" and push the text to the remarks field.
    4. Within that type-specific context, extract the following characteristics:
    \t- variety
    \t- sub_variety
    \t- size (also known as "maat")
    \t- pieces
    \t- brand (also known as "merk")
    5. Extract the following characteristics that are common across all types:
    \t- package_type (also known as "verpakking")
    \t- pallet
    \t- class (also known as "klasse")
    \t- unit_type
    \t- unit_trade_type
    \t- country (also known as "herkomst", "land" or "LvO")
    \t- quantity_per_pallet (also known as "pp" or "cpp")
    \t- net_weight (also known as "gewicht")
    \t- price (also known as "euro")
    \t- remarks
    6. Translate non-English values to English where possible.
    7. If the country value contains multiple codes (e.g. CR/BR, NL/BE/FR), split that single raw offer into separate offers—one per country code—and carry all other fields unchanged.
    8. If the size field contains multiple values (e.g. 8/9 or 5/6/7), split it into separate offers with one value per offer. For example, 8/9 should yield two offers: one with size 8 and one with size 9. Always map each value separately. Do not keep combined size values like 8/9 or 5/6/7.
    9. If a characteristic is not present in the input, set it to "unspecified".
    10. Push any text that does not match the above characteristics to the "remarks" field.
    """

    if supplier_rules != {}:
        prompt += f"11. Supplier-specific rules:\n"
        for rule in supplier_rules:
            prompt += f"- {rule}\n"

    prompt += f"""

    Global definition block with fields that apply to every product type:
    - package_type
    Options: {package_types}
    """
    if package_type_aliases != {}:
        prompt += f"Aliases: {package_type_aliases}\n"

    prompt += f"""
    - pallet
    Options: {pallets}
    """
    if pallet_aliases != {}:
        prompt += f"Aliases: {pallet_aliases}\n"

    prompt += f"""
    - class
    Options: {product_classes}
    """
    if product_class_aliases != {}:
        prompt += f"Aliases: {product_class_aliases}\n"

    prompt += f"""
    - unit_type
    Options: {unit_types}
    """
    if unit_type_aliases != {}:
        prompt += f"Aliases: {unit_type_aliases}\n"

    prompt += f"""
    - unit_trade_type
    Options: {unit_trade_types}
    """
    if unit_trade_type_aliases != {}:
        prompt += f"Aliases: {unit_trade_type_aliases}\n"

    prompt += f"""
    - country
    Options: {countries}
    """
    if country_aliases != {}:
        prompt += f"Aliases: {country_aliases}\n"

    prompt += f"""
    - quantity_per_pallet: A positive integer representing the number of items per pallet. If missing, set to 0.

    - net_weight: Numeric. If in grams, convert to kilograms. If no weight is specified, set to 0.

    - price: Numeric. If no price is specified, set to 0. If the price is specified as "exp", "p.o.r.", "e.x.p.", "o.a.", "POR", "n.a.", "POA", "p.o.a", or "P.O.R.", set to 0.

    - remarks: Free text of anything unmatched.

    """

    for relevant_product_type in relevant_product_types:
        prompt += f"\n### product_type: {relevant_product_type}\n"
        if relevant_product_type in product_type_aliases:
            prompt += f"Aliases: {product_type_aliases[relevant_product_type]}\n"
        # TO DO: Add rules for product types
        prompt += f"\n- Variety options: {varieties}\n"
        if variety_aliases != {}:
            prompt += f"  Variety aliases: {variety_aliases}\n"
        if variety_subvariety_dict != {}:
            prompt += f"\n- Sub-variety options per variety: {variety_subvariety_dict}\n"
        if subvariety_aliases != {}:
            prompt += f"  Sub-variety aliases: {subvariety_aliases}\n"
        prompt += f"\n- Size options: {sizes}\n"
        if size_aliases != {}:
            prompt += f"  Size aliases: {size_aliases}\n"
        prompt += f"\n- Pieces options: {pieces}\n"
        if piece_aliases != {}:
            prompt += f"  Pieces aliases: {piece_aliases}\n"
        prompt += f"\n- Brand options: {brands}\n"
        if brand_aliases != {}:
            prompt += f"  Brand aliases: {brand_aliases}\n\n"

    return prompt



def build_prompt(input):
    supplier_id = input["supplier_id"].values[0]
    # Load the target output from the labeled data CSV
    if not os.path.exists(labeled_data_path):
        raise FileNotFoundError(f"Labeled data file not found: {labeled_data_path}")
    target_output_df = load_csv(labeled_data_path)
    supplier_id = '41420926-6295-4ac8-8640-e6d29f54185b'
    
    relevant_product_types = get_relevant_product_types(input, target_output_df)
    supplier_rules = retrieve_supplier_rules(supplier_id)
    package_types, package_type_aliases = retrieve_package_types(supplier_id)
    classes, class_aliases = retrieve_classes()
    countries, country_aliases = retrieve_countries()
    pallets, pallet_aliases = retrieve_pallets()
    unit_types, unit_type_aliases = retrieve_unit_types()
    unit_trade_types, unit_trade_type_aliases = retrieve_unit_trade_types()
    product_type_ids =  retrieve_product_types(relevant_product_types=relevant_product_types)
    for product_type_id, product_type_name in product_type_ids.items():
        product_type_aliases, varieties, variety_aliases, subvarieties, subvariety_aliases, variety_subvariety_dict, sizes, size_aliases, brands, brand_aliases, pieces, piece_aliases = retrieve_product_info(product_type_id, product_type_name, product_type_id)


    prompt = write_prompt(
        relevant_product_types=relevant_product_types,
        product_type_aliases=product_type_aliases,
        varieties=varieties, variety_aliases=variety_aliases,
        subvarieties=subvarieties, subvariety_aliases=subvariety_aliases,
        variety_subvariety_dict=variety_subvariety_dict,
        sizes=sizes, size_aliases=size_aliases,
        brands=brands, brand_aliases=brand_aliases,
        pieces=pieces, piece_aliases=piece_aliases,
        package_types=package_types, package_type_aliases=package_type_aliases,
        pallets=pallets, pallet_aliases=pallet_aliases,
        product_classes=classes, product_class_aliases=class_aliases,
        unit_types=unit_types, unit_type_aliases=unit_type_aliases,
        unit_trade_types=unit_trade_types, unit_trade_type_aliases=unit_trade_type_aliases,
        countries=countries, country_aliases=country_aliases,
        supplier_rules=supplier_rules
    )
    
    return prompt







