from document_insighter.api_client import DocumentInsighter
from document_insighter.model import Env, Extraction
from datetime import datetime


def test_fetch_token_with_token_json():
    document_insighter = DocumentInsighter(Env.STAGING)
    document_insighter.fetch_token()


def test_query_extractions_pages():
    document_insighter = DocumentInsighter(Env.STAGING)
    document_insighter.fetch_token()
    pages_generator = document_insighter.query_extractions_pages(
        "NB_COA", datetime(2022, 3, 1), datetime(2022, 5, 17), page_size=50
    )

    extraction_dicts = [x for page in pages_generator for x in page]
    extractions = [Extraction.from_dict(x) for x in extraction_dicts]
    print(extractions[0])
