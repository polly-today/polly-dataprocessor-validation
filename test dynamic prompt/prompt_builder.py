package_types = []
package_type_aliases = {}
pallets = []
pallet_aliases = {}
product_classes = []
product_class_aliases = {}
unit_types = [] 
unit_trade_types = []
countries = []
country_aliases = {}

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

Global definition block with fields that apply to every product type:
- package_type
  Options: {package_types}
  Aliases: {package_type_aliases}

- pallet
  Options: {pallets}

- class
  Options: {product_classes}
  Aliases: {product_class_aliases}

- unit_type
  Options: {unit_types}

- unit_trade_type
  Options: {unit_trade_types}

- country
  Options: {countries}
  Aliases: {country_aliases}

- quantity_per_pallet: A positive integer representing the number of items per pallet. If missing, set to 0.

- net_weight: Numeric. If in grams, convert to kilograms. If no weight is specified, set to 0.

- price: Numeric. If no price is specified, set to 0. If the price is specified as "exp", "p.o.r.", "e.x.p.", "o.a.", "POR", "n.a.", "POA", "p.o.a", or "P.O.R.", set to 0.

- remarks: Free text of anything unmatched.

"""


relevant_product_types = ['Cucumber', 'Green Cabbage']
product_type_info = {
    'Cucumber': {
        'aliases': ['Komkommer', 'Cucumis sativus'],
        'varieties': ['Filmed', 'Industry', 'Naked', 'Mini'],
        'variety_aliases': {
            'Filmed': ['Foly'],
            'Industry': ['Krom', 'Pickling Cucumber']
        },
        'sub_varieties': ['unspecified'],
        'sizes': ['25+', '25-30'],
        'pieces': ['10stk', '12stk', '14stk'],
        'brands': ['Cuckies', 'Jackpot'],
        'rules': [
            "Cucumbers are Naked by default unless specified otherwise.",
        ]
    },
    'Green Cabbage': {
        'aliases': ['Groene Kool', 'Brassica oleracea'],
        'varieties': ['Savoy', 'Pointed', 'White'],
        'sub_varieties': ['Winter', 'Summer'],
        'sizes': ['Small', 'Medium', 'Large'],
        'pieces': ['1 piece', '2 pieces', '3 pieces'],
        'brands': ['Brand X', 'Brand Y', 'Brand Z'],
        'rules': None
    },
    'Capsicum': {
        'aliases': ['Bell Pepper', 'Capsicum annuum'],
        'varieties': ['Red', 'Green', 'Yellow', 'Orange'],
        'sub_varieties': ['Sweet', 'Hot'],
        'sizes': ['Small', 'Medium', 'Large'],
        'pieces': ['1 piece', '2 pieces', '3 pieces'],
        'brands': ['Brand D', 'Brand E', 'Brand F'],
        'rules': None
    }
}

for relevant_product_type in relevant_product_types:
    info = product_type_info.get(relevant_product_type, {})
    prompt += f"\n### product_type: {relevant_product_type}\n"
    if info.get('aliases'):
        prompt += f"- product_type aliases: {info['aliases']}\n"
    if info.get('rules'):
        prompt += f"\n- product_type specific extraction rules: {info['rules']}\n"
    prompt += f"\n- Variety options: {info.get('varieties', [])}\n"
    if info.get('variety_aliases'):
        prompt += f"  Variety aliases: {info['variety_aliases']}\n"
    prompt += f"\n- Sub-variety options: {info.get('sub_varieties', [])}\n"
    if info.get('sub_variety_aliases'):
        prompt += f"  Sub-variety aliases: {info['sub_variety_aliases']}\n"
    prompt += f"\n- Size options: {info.get('sizes', [])}\n"
    if info.get('size_aliases'):
        prompt += f"  Size aliases: {info['size_aliases']}\n"
    prompt += f"\n- Pieces options: {info.get('pieces', [])}\n"
    if info.get('piece_aliases'):
        prompt += f"  Pieces aliases: {info['piece_aliases']}\n"
    prompt += f"\n- Brand options: {info.get('brands', [])}\n"
    if info.get('brand_aliases'):
        prompt += f"  Brand aliases: {info['brand_aliases']}\n\n"



print(prompt)



# #masterdata_product_types = await database.fetch_masterdata_product_types()
# #masterdata_varieties = await database.fetch_masterdata_varieties()

# existent_product_types_system_prompt = _get_existent_product_types_system_prompt(masterdata_product_types, masterdata_varieties)
# list_of_product_types = ai_service.get_existent_product_types(existent_product_types_system_prompt, processing_type.value, dataprocessor_sqs_message_id, text, encoded_file)
# list_of_product_type_ids:List[UUID] = await database.fetch_product_type_ids_by_name_similarity(list_of_product_types.get('product_types', None)) 

# masterdata = await database.fetch_masterdata(list_of_product_type_ids)
# masterdata_varieties = await database.fetch_masterdata_varieties(list_of_product_type_ids)
# masterdata_sub_varieties = await database.fetch_masterdata_sub_varieties(list_of_product_type_ids)
# attr_name_aliases = await database.fetch_attr_name_aliases(supplier_id=supplier_id)
# value_aliases = await database.fetch_value_aliases(supplier_id=supplier_id, list_of_product_type_ids=list_of_product_type_ids)
# supplier_rules = await database.fetch_supplier_rules(supplier_id=supplier_id)
# zero_price_aliases = ["exp", "p.o.r.", "e.x.p.", "o.a.", "POR", "n.a.", "POA", "p.o.a", "P.O.R."]
# product_type_rules = await database.fetch_product_type_rules(list_of_product_type_ids)

# prompt = 'You are the best data extractor in the world. Your task is to extract specific characteristics from the following text as a table with a row with the characteristics for each offer. \n'

# for attribute, attribute_name_aliases, value_alternatives, val_aliases in [
#     ('type', attr_name_aliases.get('type', []), masterdata['product_types'], value_aliases.get('type', [])),
#     ('variety', attr_name_aliases.get('variety', []), masterdata_varieties, value_aliases.get('variety', [])),
#     ('sub_variety', attr_name_aliases.get('sub_variety', []), masterdata_sub_varieties, value_aliases.get('sub_variety', [])),
#     ('size', attr_name_aliases.get('size', []), masterdata['sizes'], value_aliases.get('size', [])),
#     ('piece', attr_name_aliases.get('pieces', []), masterdata['pieces'], value_aliases.get('pieces', [])),
#     ('brand', attr_name_aliases.get('brand', []), masterdata['brands'], value_aliases.get('brand', [])),
#     ('package_type', attr_name_aliases.get('package_type', []), masterdata['package_types'], value_aliases.get('package_type', [])),
#     ('pallet', attr_name_aliases.get('pallet', []), masterdata['pallets'], value_aliases.get('pallet', [])),
#     ('class', attr_name_aliases.get('class', []), masterdata['classes'], value_aliases.get('class', [])),
#     ('unit_type', attr_name_aliases.get('unit_type', []), masterdata['unit_types'], value_aliases.get('unit_type', [])),
#     ('unit_trade_type', attr_name_aliases.get('unit_trade_type', []), masterdata['unit_trade_types'], value_aliases.get('unit_trade_type', [])),
#     ('country', attr_name_aliases.get('origin', []), masterdata['countries'], value_aliases.get('origin', [])),
#     ('net_weight', attr_name_aliases.get('net_weight', []), [], []),
#     ('quantity_per_pallet', attr_name_aliases.get('quantity_per_pallet', []), [], []),
# ]:
#     match attribute:
#         case 'variety': 
#             prompt += f"\n\n- For each 'type' characteristic, identify the characteristic 'variety'"
#         case 'sub_variety':
#             if value_alternatives and len(value_alternatives) > 0:
#                 prompt += f"\n\n- For each 'variety' characteristic of each 'type', identify the characteristic 'sub_variety'"
#         case _:
#             prompt += f"\n\n- Identify the characteristic '{attribute}'"

#     # NAME ALIASES
#     if value_alternatives and len(value_alternatives) > 0:
#         if attribute_name_aliases:
#             prompt += f" also known as {" or ".join(f"'{str(value)}'" for value in attribute_name_aliases)} "
#         else:
#             prompt += ". "
    
#     # VALUES
#     if value_alternatives and len(value_alternatives) > 0:
#         prompt += "The possible options are: "
#         match attribute:
#             case 'variety': 
#                 prompt += '; '.join(f"{str(value['varieties'])} for type '{value['type']}'" for value in value_alternatives)
#             case 'sub_variety':
#                 prompt += '; '.join(f"{str(value['sub_varieties'])} for variety '{value['variety']}' of type '{value['type']}'" for value in value_alternatives)
#             case _:
#                 prompt += ', '.join(f"'{str(value)}'" for value in value_alternatives)
#         prompt += ". "

#         # PRODUCT TYPE RULES
#         if attribute == 'type' and product_type_rules and len(product_type_rules) > 0:
#             prompt += "Apply the following rules for 'types': "
#             for product_type_rule in product_type_rules:
#                 prompt += f"\n- {product_type_rule}"
#             prompt += ". "

#     # ALIASES
#     if val_aliases:
#         prompt += "Consider the following alias for mapping purposes: "
#         for i, val_alias in enumerate(val_aliases):
#             if i > 0:  # Add comma before all items except the first
#                 prompt += ", "
#             prompt += f"'{val_alias['alias']}' is an alias for '{val_alias['aliasof']}'"
#         prompt += ". "

#     # NOTES
#     match attribute:
#         case 'net_weight':
#             prompt += " ** Note: Any numeric value followed by 'kg' or 'gr' should be extracted as net_weight. Do not consider 'kg' as part of the size characteristic ** "
#             prompt += " ** Note: Extract as 'kg' and not as 'gr', do convertion as needed ** "
#         case 'size':
#             prompt += " ** Note: If 'kg' or 'gr' is mentioned, it should be extracted as net_weight and not as size ** "
#         case 'country':
#             prompt += " ** Note: origin country can be the full name or ISO code ** "

#     prompt += "; "

# price_aliases = attr_name_aliases.get('price', [])
# prompt += '\n\n- Identify the Price'
# if price_aliases:
#     prompt += f" also known as {" or ".join(f"'{str(value)}'" for value in price_aliases)}. "
# else:
#     prompt += ". "
# prompt += f'Do not confuse the price with other parameters. The price can be specified as {", ".join(zero_price_aliases)}. If you see any of the following values, define the price as 0. It also means that this column contains price information;'
# prompt += 'In case multiple prices are present for the same offer/product, extract the price per colli/box;'

# prompt += '\n\nNOTES:'
# prompt += '\n- Size is NOT net weight, don`t mix them.'
# prompt += '\n- Do not add Kg or similar units to size. Only net_weight should have this type of data.'
# prompt += '\n- Extract all offers lines even if there is no price.'
# prompt += '\n- Anything not able to extract, add it to remarks property.'
# prompt += '\n If the data is not in English, the response should translate it into English.'
# prompt += '\n- For characteristics ["variety", "sub_variety"], the value "unspecified" is also possible. But you can choose it if the data you have does not match the data in the message or if the message does not contain such information.'

# if supplier_rules:
#     prompt += '\n\nRules for this supplier:'
#     for supplier_rule in supplier_rules:
#         prompt += f'\n- {supplier_rule}'
