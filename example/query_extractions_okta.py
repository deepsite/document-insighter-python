# -*- coding: utf-8 -*-
"""
Query Document Insighter extractions by dates and types
"""
import argparse
from datetime import datetime

from document_insighter.api_client import OktaApplicationClient
from document_insighter.model import Env, Extraction
import pandas as pd
from typing import List, Optional, Generator


def get_insighter_client() -> OktaApplicationClient:
    """
    Get the API client which is authenticated with Okta.
    """
    document_insighter = OktaApplicationClient(Env.PRODUCTION)
    document_insighter.fetch_token()
    return document_insighter


def query_extractions_pages(
        document_type: str,
        start_date: datetime,
        end_date: datetime,
        page_size: int = 50,
        tags: Optional[List[str]] = None
) -> Generator[Extraction, None, None]:
    """
    Query extractions by dates, types and tags and return a list of Extraction objects.
    """
    document_insighter = get_insighter_client()
    pages_generator = document_insighter.query_extractions_pages(
        document_type,
        start_date,
        end_date,
        page_size=page_size,
        tags=tags or []
    )
    return (Extraction.from_dict(x) for page in pages_generator for x in page)


def print_extraction(extraction: Extraction):
    """
    Print the extraction information.
    """
    print("Extraction Link", f"https://document-insighter.godeepsite.com/extractions/{extraction.id}/review")
    # print status 
    print("Status:", extraction.status)
    header_section = next(
        (section for section in extraction.data.sections if section.category == 'coa_header'),
        None
    )
    print("Tags:", extraction.tags)
    if header_section is not None:
        print("Order #:", next(x for x in header_section.fields if x.name == 'order_number').value)

    batch_sections = [x for x in extraction.data.sections if x.category == 'coa_batch']
    for section in batch_sections:
        batch_number_field = next(
            (x for x in section.fields if x.name == 'batch_number'),
            None
        )
        if batch_number_field is not None:
            print("Batch #:", batch_number_field.value)

        coa_attributes_table = next(
            (x for x in section.tables if x.name == 'test_parameters'),
            None
        )
        if coa_attributes_table is not None:
            df = pd.DataFrame(
                {col: col_obj.values for col, col_obj in coa_attributes_table.columns.items()}
            )
            print(df)


if __name__ == "__main__":
    """
    Example command:
    python example/query_extractions_okta.py --category NB_COA --start_date 2024-05-01 --end_date 2024-07-10 --page_size 50 --tags HB_Ops tag1 tag2
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", required=True, help="Document Category")
    parser.add_argument("--start_date", required=True, help="Start Date (YYYY-MM-DD)")
    parser.add_argument("--end_date", required=True, help="End Date (YYYY-MM-DD)")
    parser.add_argument("--page_size", default=50, type=int, help="Page Size")
    parser.add_argument("--tags", default=[], nargs="*", help="Tags")
    args = parser.parse_args()

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

    extractions = query_extractions_pages(
        args.category,
        start_date,
        end_date,
        page_size=args.page_size,
        tags=args.tags
    )

    n = 0
    for extraction in extractions:
        print_extraction(extraction)
        n += 1
    print(f"Total extractions: {n}")

