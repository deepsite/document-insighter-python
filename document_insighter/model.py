from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase
from typing import Dict, Optional, List
from datetime import datetime


@dataclass
class EnvType:
    host: str
    service_account_token_url: str


class Env:
    PRODUCTION = EnvType("https://document-insighter.godeepsite.com", "https://prod-document-insighter-id.auth.us-east-1.amazoncognito.com/oauth2/token")
    STAGING = EnvType("https://document-insighter-staging.godeepsite.com", "https://staging-document-insighter-id.auth.us-east-1.amazoncognito.com/oauth2/token")
    DEV = EnvType("https://65-181-89-178.ap.ngrok.io", "https://dev-document-insighter-id.auth.us-east-1.amazoncognito.com/oauth2/token")


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Field:
    name: str
    value: Optional[str]
    standard_value: Optional[str] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Column:
    values: List[str]
    standard_values: List[Optional[str]] = field(default_factory=lambda: [])


@dataclass_json
@dataclass
class Table:
    name: str
    columns: Dict[str, Column]


@dataclass_json
@dataclass
class Section:
    category: str
    fields: Optional[List[Field]] = field(default_factory=lambda: [])
    tables: Optional[List[Table]] = field(default_factory=lambda: [])


@dataclass_json
@dataclass
class Data:
    sections: Optional[List[Section]] = field(default_factory=lambda: [])


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Extraction:
    id: str
    category: str
    category_key: str
    receive_date: str
    receive_from: str
    data: Data
