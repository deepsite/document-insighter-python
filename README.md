
# Document Insighter Client

Document Insighter Client is a Python library for interacting with the Document Insighter API. It allows you to query document extractions and process the data for various document types.

## Getting Started

### Prerequisites

- Python 3.7+

### Installation

1. Install the required dependencies using the provided `requirements.txt`:

    ```bash
    pip install -r requirements.txt
    ```

### Configuration

1. Add the necessary environment variables in the provided .env to your project.
```
INSIGHTER_CLIENT_IDP=xxxxxx
INSIGHTER_CLIENT_ID=xxxxxx  
INSIGHTER_CLIENT_SECRET=xxxxxx
INSIGHTER_CLIENT_TOKEN_PATH=insighter_token.json  
INSIGHTER_TENANT=xxx
```

### Getting Started

1. **Import Libraries**:
Imports necessary libraries and modules
    ```python
   from document_insighter.api_client import OktaApplicationClient
   from document_insighter.model import Env, Extraction
   import pandas as pd
   from datetime import datetime
   ```

2. **Get Document Insighter Client**:
   - Defines a function to create an instance of the `OktaApplicationClient` configured for the production environment.
   - Fetches the API token for authentication and returns the client instance.
    ```python
   def get_insighter_client():
       document_insighter = OktaApplicationClient(Env.PRODUCTION)
       document_insighter.fetch_token()
       return document_insighter
   ```
3. **Query Extractions**:
   - Defines a function to query extractions from the Document Insighter API.
   - Uses `get_insighter_client` to get the API client.
   - Queries extraction pages based on the document type, start date, end date, and page size.
   - Converts each page of results into `Extraction` objects and returns a list of extractions.
   ```python
   def query_extractions_pages(document_type, start_date, end_date, page_size=50):
       document_insighter = get_insighter_client()
       pages_generator = document_insighter.query_extractions_pages(document_type, start_date, end_date,
                                                                    page_size=page_size)
       extractions = [Extraction.from_dict(x) for page in pages_generator for x in page]
       return extractions
   ```

4. **Run the Query**:
Queries extractions for documents of type 'XXXXXX' between July 1, 2024, and July 10, 2024.
   ```python
   extractions = query_extractions_pages('XXXXXX', datetime(2024, 7, 1), datetime(2024, 7, 10))
   ```
   

5. **Print Total Extractions**:
Prints the total number of extractions retrieved.
   ```python
   print("Total extractions:", len(extractions))
   ```

6. **Access and Print First Extraction**:
   - Accesses the first extraction in the list.
   - Prints a link to review the extraction.
   - Finds and prints the order number from the 'coa_header' section.
   ```python
   first_extraction = extractions[0]
   
   print("Extraction Link", f"https://document-insighter.godeepsite.com/extractions/{first_extraction.id}/review")
   header_section = next(x for x in first_extraction.data.sections if x.category == 'coa_header')
   print("Order #:", next(x for x in header_section.fields if x.name == 'order_number').value)
   ```


7. **Access and Print Batch Sections**:
   - Finds and prints batch numbers from 'coa_batch' sections.
   - Converts 'test_parameters' table into a pandas DataFrame and prints it for each batch section.
   ```python
   batch_sections = [x for x in first_extraction.data.sections if x.category == 'coa_batch']
   for section in batch_sections:
       print("Batch #:", next(x for x in section.fields if x.name == 'batch_number').value)

       coa_attributes_table = next(x for x in section.tables if x.name == 'test_parameters')
       df = pd.DataFrame({col: col_obj.values for col, col_obj in coa_attributes_table.columns.items()})
       print(df)
   ```