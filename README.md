# polly-dataprocessor-validation

validation.py is a Python utility that automatically compares two CSV files:
* LLM_output.csv – the data extracted from our database
* target_output.csv – the “ground-truth” download from the following Google Sheet: https://docs.google.com/spreadsheets/d/1otbn32kXfS3nqHbBOKcnDB94zenEbiRR4QNXTewk4Gg/edit?gid=0#gid=0

It produces five distinct reports:

* Per-attribute similarity summary
* Per-email similarity summary
* Per-type similarity summarys
* Row-level match assignments
* Value-level mismatch details

Each report is written twice on every run:
* latest_<report>.csv – a fresh snapshot, overwritten each time
* all_<report>.csv – an append-only history of every run

Both versions include a leading timestamp_of_validation column so you always know when each row was generated.

---

## Requirements

- Python **3.8+**  
- A virtual environment (recommended)  
- Dependencies listed in `requirements.txt`


**Usage**
```bash
python validation.py
```
After it finishes, you’ll see files like:
latest_report_per_email.csv, all_report_per_email.csv, latest_report_per_attribute.csv, all_report_per_attribute.csv, etc.

# TODOs

- add instructions on how to run all examples at once
- separate each scenario into different folder 
- add python script to read from these new folders and perform the batch run
- add masterdata into local db
- add prompt builder service code to generate the prompt locally and send request to ai-svc to mimic data processor worker
- provide each run a UUID and a timestamp
- add SQL script for 1st database run - schema creation

# How to use locally

## initial setup 

### Installation
**virtual environment:**

```bash
python3 -m venv venv
```

OR 
```bash
py -m venv venv
```

**activate the virtual environment**

Linux/MAC
```bash
source venv/bin/activate
```

Windows 
```bash
venv\Scripts\activate
```

**install dependencies:**

```bash
pip install -r requirements.txt
```

or 1 by 1 at once

```bash
pip install numpy pandas rapidfuzz
```

list all installed dependencies and check versions

```bash
pip list
```


**docker compose for local database:**

```bash
docker compose up -d
```

**TODO: database setup**


