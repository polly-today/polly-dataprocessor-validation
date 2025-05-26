## validation.py
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

## Requirements

- Python **3.8+**  
- A virtual environment (recommended)  
- Dependencies listed in `requirements.txt`


---

## Installation

1. **Clone the repo**  
```bash 
git clone https://github.com/polly-today/polly-dataprocessor-validation.git
cd polly-dataprocessor-validation
```

2. **Install dependencies**
```bash
python3 -m venv .venv
source .venv/bin/activate
```
3. **Usage**
```bash
python validation.py
```
After it finishes, you’ll see files like:
latest_report_per_email.csv, all_report_per_email.csv, latest_report_per_attribute.csv, all_report_per_attribute.csv, etc.

