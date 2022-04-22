import json
import os
from datetime import datetime
from typing import Generator
from requests_oauthlib import OAuth2Session
from document_insighter.model import EnvType

REDIRECT_URI = "https://localhost/callback"
TOKEN_URL = "https://id.godeepsite.com/oauth2/default/v1/token"
AUTHORIZATION_URL_FORMAT = (
    "https://id.godeepsite.com/oauth2/default/v1/authorize?idp=%s"
)
SEARCH_DATE_FORMAT = "%Y-%m-%d"


class DocumentInsighter:
    def __init__(
        self,
        env: EnvType,
        idp_id=os.getenv("INSIGHTER_CLIENT_IDP"),
        client_id=os.getenv("INSIGHTER_CLIENT_ID"),
        client_secret=os.getenv("INSIGHTER_CLIENT_SECRET"),
        token_filename=os.getenv("INSIGHTER_CLIENT_TOKEN_PATH"),
    ):
        """
        The APIClient for communication with Rossum API.

        :param env used for swtich production and staging env
        :param idp_id the identify provider id in DEEPSITE okta,
            based on customer okta integration.
            env variable: INSIGHTER_CLIENT_IDP
        :param client_id client_id of the okta api client application.
            env variable: INSIGHTER_CLIENT_ID
        :param client_secret client_id of the okta api client application.
            env variable: INSIGHTER_CLIENT_SECRET
        :param token_filename name of file which used to store token json.
            env variable: INSIGHTER_CLIENT_TOKEN_PATH. init token can be passed
            with env variable INSIGHTER_CLIENT_TOKEN_JSON
        """
        self.env = env
        self.idp_id = idp_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_filename = token_filename
        self.oauth = OAuth2Session(
            self.client_id,
            token=self._load_token(),
            scope=["openid", "profile", "offline_access"],
            redirect_uri=REDIRECT_URI,
            auto_refresh_url=TOKEN_URL,
            token_updater=self._token_saver,
        )

    def _token_saver(self, token):
        if token:
            with open(self.token_filename, "w") as fp:
                json.dump(token, fp)

    def _load_token(self):
        if self.token_filename and os.path.exists(self.token_filename):
            with open(self.token_filename, "r") as fp:
                return json.load(fp)
        elif os.getenv("INSIGHTER_CLIENT_TOKEN_JSON"):
            return json.loads(os.getenv("INSIGHTER_CLIENT_TOKEN_JSON"))

    def fetch_token(self, force_fetch: bool = False):
        if not self.oauth.token or force_fetch:
            authorization_url, state = self.oauth.authorization_url(
                AUTHORIZATION_URL_FORMAT % self.idp_id
            )
            print(authorization_url)
            redirect_response = input("Paste the full redirect URL here:")
            token = self.oauth.fetch_token(
                TOKEN_URL,
                client_secret=self.client_secret,
                authorization_response=redirect_response,
            )
            self._token_saver(token)

    def query_extractions_pages(
        self, start_date: datetime, end_date: datetime, page_size=50
    ) -> Generator:
        """Query extraction pages by dates

        :param start_date filter extraction processed after this date,
            start date is inclusive.
        :prarm end_date filter extraction processed after this date, exclusive
        :page_size number of extraction in each page

        :returns pages in generator. each page is a list of extraction
        """
        params = {
            "startDate": start_date.strftime(SEARCH_DATE_FORMAT),
            "endDate": end_date.strftime(SEARCH_DATE_FORMAT),
            "page": 0,
            "size": page_size,
        }
        res = self.oauth.get(
            f"{self.env.host}/api/extraction-exporting/nb_coa/extractions",
            params=params,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        res.raise_for_status()
        yield res.json()

        while res.links.get("next") is not None:
            res = self.oauth.get(
                res.links.get("next").get("url").replace("http", "https"),
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
            res.raise_for_status()
            yield res.json()
