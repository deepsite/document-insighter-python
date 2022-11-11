# Document Insighter Python Client

`document-insighter` is a set of tools that enables developers to interactive with Document Insighter API, like query extraction results.

# Installation

`pip install document-insighter`

# Getting Started

## Authentication 
### OKTA Base Applications

#### Configure ENV variables

```bash
# Client application credentials
INSIGHTER_CLIENT_IDP=xxxx
INSIGHTER_CLIENT_ID=xxxx
INSIGHTER_CLIENT_SECRET=xxxx

# Client access token file path, no need to create it
INSIGHTER_CLIENT_TOKEN_PATH=insighter_token.json

```

#### Fetch Token

```python
from document_insighter.api_client import OktaApplicationClient
from document_insighter.model import Env, Extraction

# Change to Env.PRODUCTION for production
document_insighter = OktaApplicationClient(Env.STAGING)
document_insighter.fetch_token()
```

### Service Account Base Applications
#### Configure ENV variables
```bash
# Client application credentials
INSIGHTER_SA_CLIENT_ID=xxxx
INSIGHTER_SA_CLIENT_SECRET=xxxx

# Path of service account access token, which download from settings page
INSIGHTER_SA_CLIENT_TOKEN_PATH=service-account-token.json
```
#### Create Client

```python
from document_insighter.api_client import ServiceAccountClient
from document_insighter.model import Env

document_insighter = ServiceAccountClient(Env.STAGING)
```
## Query Extractions

```python
from datetime import datetime

pages_generator = document_insighter.query_extractions_pages(datetime(2022, 4, 13), datetime(2022, 4, 14), page_size=50)
extraction_dicts = [x for page in pages_generator for x in page]

# read first extraction
sections = extraction_dicts[0].get('data').get('sections')
batch_sections = list(filter(lambda x:x.get('category') == 'coa_batch', sections))
aggregation_sections = list(filter(lambda x:x.get('category') == 'coa_aggregation', sections))
```

```python
# load json to models
from typing import List
extractions: List[Extraction] = [Extraction.from_dict(x) for x in extraction_dicts]
```

## Upload and Poll Extractions
```python
extractions = document_insighter.upload_and_poll("BR", 'tests/data/br_document.pdf')
```
# License

MIT
