# TODOs

- add masterdata into local db
- add prompt builder service code to generate the prompt locally and send request to ai-svc to mimic data processor worker
- explanation of data base setup below
- process excel files within validation environment


# How to use locally

## Initial setup 

### Installation
**Create virtual environment:**

```bash
python3 -m venv venv
```

OR 
```bash
py -m venv venv
```

**Activate the virtual environment:**

Linux/MAC
```bash
source venv/bin/activate
```

Windows 
```bash
venv\Scripts\activate
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```
**TODO: Database setup**

Port in use: 5433 

**Docker compose for local database:**

```bash
docker compose up -d
```

**Populate your .env file with:**

```bash
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=your_database_connection_url_here
```

**Run validation:**
```bash
# Show help (lists all available inputs for validation and exits)
python main.py
# Process all available inputs with the built-in prompt
python main.py -p default
# Process inputs 1 and 3 with the built-in prompt
python main.py -p default -i 1 3
# Process all inputs with a custom (manual) prompt from prompt.txt
python main.py -p manual
# Process inputs 5, 8, 10 with a custom prompt
python main.py --prompt manual --inputs 5 8 10
```


## What happens inside the script
**Argument parsing**

If you run with no flags at all (i.e. python main.py and no -p or -i), the parser will detect that sys.argv has length 1 and will immediately print the help message (including a formatted list of all valid IDs) and exit.

**Loading and filtering inputs**

After parsing, args.inputs is converted to a set(...) of IDs.
If you passed -i, only those IDs will be processed; otherwise, it defaults to every ID from your inputs table.

**Batch & run creation**

A new batch_id is generated using the current timestamp (e.g. 20250605142317).

For each input_id in args.inputs, the script:
* Generates a fresh UUID as run_id.
* Calls insert_run(run_id, input_id, system_prompt, batch_id) to record that run in your database (public.runs) with status "pending".

**Per-input processing**

The script loops over each input_id again. For each:
* Marks that run_id as "running" in the database (public.runs)
* Fetches value (price list of supplier) and value_type (pdf, img, txt, xslx) from the inputs DataFrame.
* Sends the input value to the LLM along with the JSON schema defined in 'data/response_schema.json', ensuring the LLM’s response conforms to the expected format.
* If the LLM call succeeds, updates run.status = "completed" with llm_output. If it fails, updates run.status = "failed", capturing the error.

**Comparison & saving results**

Once the LLM returns a structured response, the script calls compare_llm_to_target_output(...).
The comparison metrics (attribute, target_value, llm_value, similarity_score) is written into the database (public.results)

## Interpreting results

In order to gain insights from the results table, different queries are written:
* **value_mismatches.sql**: Lists all rows where the target_value doesn’t match the llm_value for a given run and attribute.
* **run_offer_count_discrepancy.sql**: Shows, for each run, how many offers the LLM found versus how many were in the target, and gives the difference.
* **run_similarity.sql**: For each run, reports the total number of offers and the average ± STD of their similarity scores.
* **run_similarity_per_offer.sql**: For each offer, shows its average similarity score across all attributes.
* **batch_similarity.sql**: For each batch, shows how many runs and offers it has, plus the average ± STD of run-level similarity scores.
* **batch_similarity_per_value_type.sql**: For each batch and each value type (e.g. “pdf,” “img,” “xlsx”), shows how many runs and offers there were, plus the average ± STD of their similarity scores.
* **batch_similarity_per_attribute.sql**: For each batch and each attribute (e.g. “brand,” “price,” “variety”), shows how many runs and offers used that attribute, plus the average ± STD of their similarity scores.
* **batch_similarity_per_product_type.sql**: For each batch and each product type (e.g. “Cherry Tomato,” “Plum Tomato”), shows how many runs and offers included that product, plus the average ± STD of their similarity scores.

## Using the validation environment
* If you want to experiment with the overal structure of the prompt, you can adjust the prompt in prompts/manual_prompt.txt and run python main.py -p manual.
* If you want to experiment with possible adjustments in the prompt (e.g. different varieties for a product type), you can adjust the values within the prompt in prompts/manual_prompt.txt and run python main.py -p manual.
* Everytime you have made an adjustment within the target output (Google Sheet: https://docs.google.com/spreadsheets/d/1otbn32kXfS3nqHbBOKcnDB94zenEbiRR4QNXTewk4Gg/edit?gid=0#gid=0), download the sheet and store it as 'labeled_data.csv' within the 'data'-folder. 
