import os
import time

from document_insighter.api_client import ServiceAccountClient
from document_insighter.model import Env

document_insighter = ServiceAccountClient(Env.STAGING)


def test_upload():
    start = time.time()
    extractions = document_insighter.upload_and_poll("BR", 'tests/data/br_document.pdf')
    print(extractions)
    print(f"Costs {time.time() - start}")



