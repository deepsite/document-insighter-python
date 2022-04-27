# Document Insighter Python Client

`document-insighter` is a set of tools that enables developers to interactive with Document Insighter API, like query extraction results.

# Installation

`pip install document-insighter`

# Getting Started

## Configure ENV variables

```bash
# Client application credentials
INSIGHTER_CLIENT_IDP=xxxx
INSIGHTER_CLIENT_ID=xxxx
INSIGHTER_CLIENT_SECRET=xxxx

# Client access token file path
INSIGHTER_CLIENT_TOKEN_PATH=insighter_token.json

```

## Fetch Token

```python
from document_insighter.api_client import DocumentInsighter
from document_insighter.model import Env, Extraction

# Change to Env.PRODUCTION for production
document_insighter = DocumentInsighter(Env.STAGING)
document_insighter.fetch_token()
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

# License

MIT
