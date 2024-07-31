# Document Insighter Client

Document Insighter Client is a Python library for interacting with the Document Insighter API. It allows you to query
document extractions and process the data for various document types.

## Getting Started

### Prerequisites

- Python 3.7+

### Installation

1. Install the required dependencies using the provided `requirements.txt`:

    ```bash
    pip install -U document-insighter
    ```

### Getting Started

The following steps demonstrate how to use the Document Insighter Client in your Python project:

#### Okta Based Authentication

- Include the necessary environment variables in your project or by setting them in your environment. The required
  environment variables are:
    - `INSIGHTER_CLIENT_IDP`
    - `INSIGHTER_CLIENT_ID`
    - `INSIGHTER_CLIENT_SECRET`
    - `INSIGHTER_CLIENT_TOKEN_PATH`
    - `INSIGHTER_TENANT`

- Now, let's proceed to the next step. Install the required packages for the example script.
  ```bash
    pip install pandas==2.2.2
  ```

- Once the packages are installed, you can run the example to fetch and print out document extractions:
  ```bash
    python example/query_extractions_okta.py --category NB_COA --start_date 2024-05-01 --end_date 2024-07-10 --page_size 50 --tags HB_Ops tag1 tag2
  ```
  Options:

  | Option       | Required | Description                                                                                      |
  |--------------|----------|--------------------------------------------------------------------------------------------------|
  | `category`   | Yes      | The category of the document extractions to fetch, e.g. "COA", "NB_COA"                          |
  | `start_date` | Yes      | The start date of the document extractions to fetch, in the format `YYYY-MM-DD`.                 |
  | `end_date`   | Yes      | The end date of the document extractions to fetch, in the format `YYYY-MM-DD`.                   |
  | `page_size`  | No       | The number of document extractions to fetch per page.                                            |
  | `tags`       | No       | The tags to filter the document extractions by. Use quotes for tags with spaces, e.g. "NB Stade" |

  You can specify multiple tags to filter extractions that include any of the specified tags.
