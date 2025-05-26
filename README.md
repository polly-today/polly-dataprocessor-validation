# polly-dataprocessor-validation
Validates the output of the dataprocessor compared to a labaled set of 

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
docker compose up 
```

**TODO: database setup**

## Initial Run
**Use jupyter notebook to run**

You can open the validation notebook directly:
[Open Validation Notebook](validation.ipynb)

use local py venv 

## Batch Run

TODO: add instructions for batch run
