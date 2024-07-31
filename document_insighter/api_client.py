import json
import logging
import os
from datetime import datetime
from typing import Generator, List, Optional

from requests.sessions import merge_setting
from requests.structures import CaseInsensitiveDict
from requests_oauthlib import OAuth2Session

from document_insighter.exceptions import ChannelLogExistsError
from document_insighter.model import EnvType
import polling2

from document_insighter.helpers import md5_checksum

SEARCH_DATE_FORMAT = "%Y-%m-%d"
logger = logging.getLogger(__name__)


class DocumentInsighter:
    def __init__(self, env: EnvType, client_id, client_secret, token_filename, token_json, tenant: str):
        """
        The APIClient for communication with Document Insighter API.

        :param tenant: tenant name
        :param env used for switch production and staging env
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
        self.tenant = tenant
        self.oauth = None
        self.default_headers = CaseInsensitiveDict({
            "X-CURRENT-TENANT": tenant,
        }) if tenant else {}

    def _append_default_headers(self):
        if self.oauth:
            self.oauth.headers = merge_setting(self.oauth.headers, self.default_headers, dict_class=CaseInsensitiveDict)

    def _token_saver(self, token):
        if token:
            id_token = token['id_token']
            if 'access_token' not in token:
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

        if token and 'access_token' not in token:
            token['access_token'] = token['id_token']
        return token

    def upload_document(self, category, file_path, metadata=None, ignore_duplicate=False):
        """
        Upload document to Document Insighter.

        :param category: category of the document
        :param file_path: path of the file
        :param metadata: metadata of the document
        :param ignore_duplicate: ignore duplicate check
        """
        params = {"category": category, 'extracts[]': ['true']}
        files = {
            'fields': (None, json.dumps([metadata or {}]), 'application/json'),
            'files': (os.path.basename(file_path), open(file_path, 'rb'), 'application/octet-stream')
        }

        if not ignore_duplicate:
            md5 = md5_checksum(file_path)
            existing_channel_log_uuids = self.oauth.get(
                f"{self.env.host}/api/document-channel-logs/md5-checksum/{md5}/uuids",
                client_id=self.client_id,
                client_secret=self.client_secret,
            ).json()
            if existing_channel_log_uuids:
                # TODO: name should be changed to File has been already uploaded
                raise ChannelLogExistsError(md5, existing_channel_log_uuids)

        res = self.oauth.post(
            f"{self.env.host}/api/documents/common/upload", files=files, params=params,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        logger.info("Ends upload document.")
        res.raise_for_status()
        logs = res.json()
        return logs[0] if logs else None

    def upload_and_poll(self, category: str, file_path: str, metadata: dict = None, timeout=600):
        """
        Upload a document and poll the extractions until it is completed or failed.

        :param category: extraction category
        :param file_path: local file path
        :param metadata: file metadata and channel log metadata
        :param timeout: request timeout
        :return: extraction list
        """
        log = self.upload_document(category, file_path, metadata)
        log_id = log.get("id")
        logger.info("Starts polling extractions.")
        polling2.poll(target=lambda: self.get_channel_log_status(log_id).get("status") in ['COMPLETED', 'FAILED'],
                      step=1,
                      timeout=timeout)
        extractions = self.get_channel_extractions_exporting(log_id)
        logger.info("Ends polling extractions.")
        return extractions

    def get_channel_log_status(self, channel_log_id):
        """
        Get channel log status. the status can be UPLOADING, PROCESSING, COMPLETED, FAILED

        :param channel_log_id: channel log id
        :return: status
        """
        res = self.oauth.get(
            f"{self.env.host}/api/document-channel-logs/{channel_log_id}/status",
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        res.raise_for_status()
        return res.json()

    def get_channel_extractions_exporting(self, channel_log_id):
        """
        Get channel extractions, one document may have multiple extractions

        :param channel_log_id: channel log id
        :return: extractions
        """
        res = self.oauth.get(
            f"{self.env.host}/api/extraction-exporting/document-channel-logs/{channel_log_id}/extractions",
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
            tags: List[str] = None
    ) -> Generator:
        """Query extraction pages by dates

        :param category: extraction category, like NB_COA
        :param start_date: filter extraction processed after this date,
            start date is inclusive.
        :param end_date: filter extraction processed after this date, exclusive
        :param page_size: number of extraction in each page
        :returns pages in generator. each page is a list of extraction
        """
        params = {
            "category": category,
            "startDate": start_date.strftime(SEARCH_DATE_FORMAT),
            "endDate": end_date.strftime(SEARCH_DATE_FORMAT),
            "page": 0,
            "size": page_size,
        }

        if tags:
            params["tags"] = tags or []

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
    """
    The APIClient for communication with Document Insighter API through AWS Congito service account, instead of a user account.
    which designs to be used in computer to computer communication.
    """

    def _load_token(self):
        if self.token_json:
            return self.token_json
        if self.token_filename:
            with open(self.token_filename) as f:
                return json.load(f)

    def __init__(
            self,
            env: EnvType,
            client_id: Optional[str] = None,
            client_secret: Optional[str] = None,
            token_filename: Optional[str] = None,
            token_json: Optional[str] = None,
            tenant: Optional[str] = None,
    ):
        """
        The APIClient for communication with Document Insighter API.

        :param env used for swtitch production and staging env
        :param client_id client_id of the okta api client application.
            env variable: INSIGHTER_CLIENT_ID
        :param token_filename name of file which used to store token json.
            env variable: INSIGHTER_CLIENT_TOKEN_PATH. init token can be passed
            with env variable INSIGHTER_CLIENT_TOKEN_JSON
        """
        client_id = client_id or os.getenv("INSIGHTER_SA_CLIENT_ID")
        client_secret = client_secret or os.getenv("INSIGHTER_SA_CLIENT_SECRET")
        token_filename = token_filename or os.getenv("INSIGHTER_SA_CLIENT_TOKEN_PATH")
        token_json = token_json or os.getenv("INSIGHTER_SA_CLIENT_TOKEN_JSON")
        tenant = tenant or os.getenv("INSIGHTER_TENANT")

        super().__init__(env, client_id, client_secret, token_filename, token_json, tenant)

        self.oauth = OAuth2Session(
            self.client_id,
            token=self._load_token(),
            # scope=["openid", "profile", "offline_access"],
            scope=["profile", "offline_access"],
            auto_refresh_url=self.env.service_account_token_url,
            token_updater=self._token_saver,
        )
        self._append_default_headers()

    def fetch_token(self, force_fetch: bool = False):
        """
        Fetch token from token file or token json, if token file does not exist, download token json from the system settings pages.

        :param force_fetch: force fetch token
        """
        if not self.oauth.token:
            raise ValueError("Please download service account json and config token file.")


class OktaApplicationClient(DocumentInsighter):
    """
    The APIClient for communication with Document Insighter API on behalf of user through okta. This is designed to be used for user data analysis.
    """

    REDIRECT_URI = "https://localhost/callback"
    TOKEN_URL = "https://id.godeepsite.com/oauth2/default/v1/token"
    AUTHORIZATION_URL_FORMAT = (
        "https://id.godeepsite.com/oauth2/default/v1/authorize?idp=%s"
    )

    def __init__(
            self,
            env: EnvType,
            idp_id: Optional[str] = None,
            client_id: Optional[str] = None,
            client_secret: Optional[str] = None,
            token_filename: Optional[str] = None,
            token_json: Optional[str] = None,
            tenant: Optional[str] = None,
    ):
        """
        The APIClient for communication with Document Insighter API.

        :param env used for switch production and staging env
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
        idp_id = idp_id or os.getenv("INSIGHTER_CLIENT_IDP")
        client_id = client_id or os.getenv("INSIGHTER_CLIENT_ID")
        client_secret = client_secret or os.getenv("INSIGHTER_CLIENT_SECRET")
        token_filename = token_filename or os.getenv("INSIGHTER_CLIENT_TOKEN_PATH")
        token_json = token_json or os.getenv("INSIGHTER_CLIENT_TOKEN_JSON")
        tenant = tenant or os.getenv("INSIGHTER_TENANT")
        super().__init__(env, client_id, client_secret, token_filename, token_json, tenant)
        self.idp_id = idp_id
        self.oauth = OAuth2Session(
            self.client_id,
            token=self._load_token(),
            scope=["openid", "profile", "offline_access"],
            redirect_uri=self.REDIRECT_URI,
            auto_refresh_url=self.TOKEN_URL,
            token_updater=self._token_saver,
        )
        self._append_default_headers()

    def fetch_token(self, force_fetch: bool = False):
        """
        Fetch token from okta, if token is expired, it will be refreshed with refresh token if it exists and valid. 
        If not authenticated, it will output an authorization url and prompt user to visit it.
        After authorization, please paste the full redirect URL to complete authentication.
        """

        if not self.oauth.token or force_fetch:
            authorization_url, state = self.oauth.authorization_url(
                self.AUTHORIZATION_URL_FORMAT % self.idp_id
            )
            print("Please visit the following URL in your browser and copy the full redirect URL:")
            print(authorization_url)
            redirect_response = input("Paste the full redirect URL here:")
            token = self.oauth.fetch_token(
                self.TOKEN_URL,
                client_secret=self.client_secret,
                authorization_response=redirect_response,
            )
            self._token_saver(token)
