from document_insighter.api_client import DocumentInsighter
from document_insighter.model import Env
from datetime import datetime


def test_fetch_token_with_token_json():
    document_insighter = DocumentInsighter(Env.STAGING)
    document_insighter.fetch_token()


def test_query_extractions_pages():
    document_insighter = DocumentInsighter(Env.STAGING)
    document_insighter.fetch_token()
    pages_generator = document_insighter.query_extractions_pages(
        datetime(2022, 4, 13), datetime(2022, 5, 17), page_size=50
    )
    assert len([1 for x in pages_generator]) >= 0


if __name__ == "__main__":
    test_fetch_token_with_token_json()
