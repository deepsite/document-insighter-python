import json
import logging
import os
from datetime import datetime
from typing import Generator
from requests_oauthlib import OAuth2Session
from document_insighter.model import EnvType
import polling2

SEARCH_DATE_FORMAT = "%Y-%m-%d"
logger = logging.getLogger(__name__)

class DocumentInsighter:
    def __init__(
            self,
            env: EnvType,
            client_id,
            client_secret,
            token_filename,
            token_json
    ):
        """
        The APIClient for communication with Document Insighter API.

        :param env used for swtich production and staging env
        :param client_id client_id of the okta api client application.
            env variable: INSIGHTER_CLIENT_ID
        :param token_filename name of file which used to store token json.
            env variable: INSIGHTER_CLIENT_TOKEN_PATH. init token can be passed
            with env variable INSIGHTER_CLIENT_TOKEN_JSON
        """
        self.env = env
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_filename = token_filename
        self.token_json = token_json

    def _token_saver(self, token):
        if token:
            id_token = token['id_token']
            token['access_token'] = id_token
            self.oauth.access_token = id_token
            if self.token_filename:
                os.makedirs(os.path.abspath(os.path.dirname(self.token_filename)), exist_ok=True)
                with open(self.token_filename, "w") as fp:
                    json.dump(token, fp)

    def _load_token(self):
        token = None
        if self.token_filename and os.path.exists(self.token_filename):
            with open(self.token_filename, "r") as fp:
                token = json.load(fp)
        elif self.token_json:
            token = json.loads(self.token_json)

        if token:
            token['access_token'] = token['id_token']
        return token

    def upload_document(self, category, file_path):
        params = {"category": category}
        files = {
            'fields': (None, json.dumps([{}]), 'application/json'),
            'files': (os.path.basename(file_path), open(file_path, 'rb'), 'application/octet-stream')
        }

        res = self.oauth.post(
            f"{self.env.host}/api/documents/common/upload", files=files, params=params,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        logger.info("Ends upload document.")
        res.raise_for_status()
        logs = res.json()
        return logs[0] if logs else None

    def upload_and_poll(self, category: str, file_path: str, timeout=600):
        log = self.upload_document(category, file_path)
        log_id = log.get("id")
        logger.info("Starts polling extractions.")
        polling2.poll(target=lambda: self.get_channel_log_status(log_id).get("status") in ['COMPLETED', 'FAILED'],
                      step=1,
                      timeout=timeout)
        extractions = self.get_channel_extractions_exporting(log_id)
        logger.info("Ends polling extractions.")
        return extractions

    def get_channel_log_status(self, id):
        res = self.oauth.get(
            f"{self.env.host}/api/document-channel-logs/{id}/status",
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        res.raise_for_status()
        return res.json()

    def get_channel_extractions_exporting(self, id):
        res = self.oauth.get(
            f"{self.env.host}/api/extraction-exporting/document-channel-logs/{id}/extractions",
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        res.raise_for_status()
        return res.json()

    def query_extractions_pages(
            self,
            category: str,
            start_date: datetime,
            end_date: datetime,
            page_size: int = 50,
    ) -> Generator:
        """Query extraction pages by dates
        :param category extraction category, like NB_COA
        :param start_date filter extraction processed after this date,
            start date is inclusive.
        :prarm end_date filter extraction processed after this date, exclusive
        :page_size number of extraction in each page

        :returns pages in generator. each page is a list of extraction
        """
        params = {
            "category": category,
            "startDate": start_date.strftime(SEARCH_DATE_FORMAT),
            "endDate": end_date.strftime(SEARCH_DATE_FORMAT),
            "page": 0,
            "size": page_size,
        }
        res = self.oauth.get(
            f"{self.env.host}/api/extraction-exporting/extractions",
            params=params,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        res.raise_for_status()
        yield res.json()

        while res.links.get("next") is not None:
            res = self.oauth.get(
                res.links.get("next").get("url").replace("http://", "https://"),
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
            res.raise_for_status()
            yield res.json()


class ServiceAccountClient(DocumentInsighter):

    def __init__(
            self,
            env: EnvType,
            client_id=os.getenv("INSIGHTER_SA_CLIENT_ID"),
            client_secret=os.getenv("INSIGHTER_SA_CLIENT_SECRET"),
            token_filename=os.getenv("INSIGHTER_SA_CLIENT_TOKEN_PATH"),
            token_json=os.getenv("INSIGHTER_SA_CLIENT_TOKEN_JSON")
    ):
        """
        The APIClient for communication with Document Insighter API.

        :param env used for swtich production and staging env
        :param client_id client_id of the okta api client application.
            env variable: INSIGHTER_CLIENT_ID
        :param token_filename name of file which used to store token json.
            env variable: INSIGHTER_CLIENT_TOKEN_PATH. init token can be passed
            with env variable INSIGHTER_CLIENT_TOKEN_JSON
        """
        super().__init__(env, client_id, client_secret, token_filename, token_json)

        self.oauth = OAuth2Session(
            self.client_id,
            token=self._load_token(),
            # scope=["openid", "profile", "offline_access"],
            scope=["profile", "offline_access"],
            auto_refresh_url=self.env.service_account_token_url,
            token_updater=self._token_saver,
        )

    def fetch_token(self, force_fetch: bool = False):
        if not self.oauth.token:
            raise ValueError("Please download service account json and config token file.")


class OktaApplicationClient(DocumentInsighter):
    REDIRECT_URI = "https://localhost/callback"
    TOKEN_URL = "https://id.godeepsite.com/oauth2/default/v1/token"
    AUTHORIZATION_URL_FORMAT = (
        "https://id.godeepsite.com/oauth2/default/v1/authorize?idp=%s"
    )

    def __init__(
            self,
            env: EnvType,
            idp_id=os.getenv("INSIGHTER_CLIENT_IDP"),
            client_id=os.getenv("INSIGHTER_CLIENT_ID"),
            client_secret=os.getenv("INSIGHTER_CLIENT_SECRET"),
            token_filename=os.getenv("INSIGHTER_CLIENT_TOKEN_PATH"),
            token_json=os.getenv("INSIGHTER_CLIENT_TOKEN_JSON")
    ):
        """
        The APIClient for communication with Document Insighter API.

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
        super().__init__(env, client_id, client_secret, token_filename, token_json)
        self.idp_id = idp_id
        self.oauth = OAuth2Session(
            self.client_id,
            token=self._load_token(),
            scope=["openid", "profile", "offline_access"],
            redirect_uri=self.REDIRECT_URI,
            auto_refresh_url=self.TOKEN_URL,
            token_updater=self._token_saver,
        )

    def fetch_token(self, force_fetch: bool = False):
        if not self.oauth.token or force_fetch:
            authorization_url, state = self.oauth.authorization_url(
                self.AUTHORIZATION_URL_FORMAT % self.idp_id
            )
            print(authorization_url)
            redirect_response = input("Paste the full redirect URL here:")
            token = self.oauth.fetch_token(
                self.TOKEN_URL,
                client_secret=self.client_secret,
                authorization_response=redirect_response,
            )
            self._token_saver(token)
