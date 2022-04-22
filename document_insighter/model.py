from dataclasses import dataclass


@dataclass
class EnvType:
    host: str


class Env:
    PRODUCTION = EnvType("https://document-insighter.godeepsite.com")
    STAGING = EnvType("https://document-insighter-staging.godeepsite.com")
