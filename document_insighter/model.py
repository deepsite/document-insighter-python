from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase
from typing import Dict, Optional, List
from datetime import datetime


@dataclass
class EnvType:
    """
    EnvType model, contains the host and service account token url

    The service account token url is used for AWS Cognito based authentication.
    """
    host: str
    service_account_token_url: str


class Env:
    PRODUCTION = EnvType("https://document-insighter.godeepsite.com", "https://prod-document-insighter-id.auth.us-east-1.amazoncognito.com/oauth2/token")
    STAGING = EnvType("https://document-insighter-staging.godeepsite.com", "https://staging-document-insighter-id.auth.us-east-1.amazoncognito.com/oauth2/token")
    DEV = EnvType("https://65-181-89-178.ap.ngrok.io", "https://dev-document-insighter-id.auth.us-east-1.amazoncognito.com/oauth2/token")


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Field:
    """
    Field model, contains the name, value and standard value of the field
    """
    name: str
    value: Optional[str]
    standard_value: Optional[str] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Column:
    """
    Column model, contains the name and values of the column in the table
    """
    values: List[str]
    standard_values: List[Optional[str]] = field(default_factory=lambda: [])


@dataclass_json
@dataclass
class Table:
    """
    Table model, contains the name and columns of the table
    """
    name: str
    columns: Dict[str, Column]


@dataclass_json
@dataclass
class Section:
    """
    Section model, contains the name, fields and tables of the section. The fields and tables are optional.
    """
    category: str
    fields: Optional[List[Field]] = field(default_factory=lambda: [])
    tables: Optional[List[Table]] = field(default_factory=lambda: [])


@dataclass_json
@dataclass
class Data:
    """
    Data model, contains the sections of the data
    """
    sections: Optional[List[Section]] = field(default_factory=lambda: [])


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Extraction:
    """
    Extraction model, contains the id, category, category_key, receive_date, receive_from and data of the extraction.
    the id is the uuid of the extraction.
    the category is the category of the extraction, like COA, NB_COA, INVOICE, PACKING_LIST, etc.
    the category_key is the key of the category, like purchase order number, invoice number, etc.
    the receive_date is the date when the extraction was received.
    the receive_from is the name of the person who uploaded the document and the mailbox which the document was sent to.
    the data is the data of the extraction, which contains all the sections of the extraction.
    """
    id: str
    category: str
    category_key: str
    receive_date: str
    receive_from: str
    data: Data
    status: Optional[str] = field(default_factory=lambda: None)
    tags: Optional[List[str]] = field(default_factory=lambda: [])