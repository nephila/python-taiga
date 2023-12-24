import json

try:
    import requests
    from requests.exceptions import RequestException
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
except ImportError:  # pragma: no cover
    pass

from . import exceptions, utils
from .models import (
    Epics,
    History,
    IssueAttachments,
    IssueAttributes,
    Issues,
    IssueStatuses,
    IssueTypes,
    Milestones,
    Points,
    Priorities,
    Projects,
    Roles,
    Severities,
    SwimLanes,
    TaskAttachments,
    TaskAttributes,
    Tasks,
    TaskStatuses,
    Users,
    UserStories,
    UserStoryAttachments,
    UserStoryAttributes,
    UserStoryStatuses,
    Webhooks,
    WikiLinks,
    WikiPages,
)
from .requestmaker import RequestMaker


class SearchResult:
    count = 0
    tasks = []
    issues = []
    user_stories = []
    wikipages = []
    epics = []


class TaigaAPI:
    """
    TaigaAPI class

    :param host: the host of your Taiga.io instance
    :param token: the token you may provide
    :param token_type: the token type
    :param tls_verify: verify server certificate
    :param auth_type: authentication type identifier
    """

    def __init__(
        self, host="https://api.taiga.io", token=None, token_type="Bearer", tls_verify=True, auth_type="normal"
    ):
        self.host = host
        self.token = token
        self.token_refresh = None
        self.token_type = token_type
        self.tls_verify = tls_verify
        self.auth_type = auth_type
        if not self.tls_verify:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        if token:
            self.raw_request = RequestMaker("/api/v1", self.host, self.token, self.token_type, self.tls_verify)
            self._init_resources()

    def _init_resources(self):
        self.projects = Projects(self.raw_request)
        self.user_stories = UserStories(self.raw_request)
        self.user_story_attachments = UserStoryAttachments(self.raw_request)
        self.users = Users(self.raw_request)
        self.swimlanes = SwimLanes(self.raw_request)
        self.issues = Issues(self.raw_request)
        self.issue_attachments = IssueAttachments(self.raw_request)
        self.tasks = Tasks(self.raw_request)
        self.task_attachments = TaskAttachments(self.raw_request)
        self.milestones = Milestones(self.raw_request)
        self.severities = Severities(self.raw_request)
        self.roles = Roles(self.raw_request)
        self.points = Points(self.raw_request)
        self.issue_statuses = IssueStatuses(self.raw_request)
        self.issue_types = IssueTypes(self.raw_request)
        self.issue_attributes = IssueAttributes(self.raw_request)
        self.task_attributes = TaskAttributes(self.raw_request)
        self.user_story_attributes = UserStoryAttributes(self.raw_request)
        self.task_statuses = TaskStatuses(self.raw_request)
        self.priorities = Priorities(self.raw_request)
        self.user_story_statuses = UserStoryStatuses(self.raw_request)
        self.wikipages = WikiPages(self.raw_request)
        self.wikilinks = WikiLinks(self.raw_request)
        self.history = History(self.raw_request)
        self.webhooks = Webhooks(self.raw_request)
        self.epics = Epics(self.raw_request)

    def me(self):
        """
        Get a :class:`taiga.models.models.User` representing me
        """
        return self.users.get("me")

    def search(self, project, text=""):
        """
        Search in your Taiga.io instance

        :param project: the project id
        :param text: the query of your search
        """
        result = self.raw_request.get("search", query={"project": project, "text": text})
        result = result.json()
        search_result = SearchResult()
        search_result.count = result["count"]
        search_result.tasks = self.tasks.parse_list(result["tasks"])
        search_result.issues = self.issues.parse_list(result["issues"])
        search_result.user_stories = self.user_stories.parse_list(result["userstories"])
        search_result.wikipages = self.wikipages.parse_list(result["wikipages"])
        search_result.epics = self.epics.parse_list(result["epics"])
        return search_result

    def auth(self, username, password):
        """
        Authenticate you

        :param username: your username
        :param password: your password
        """
        headers = {"Content-type": "application/json"}
        payload = {"type": self.auth_type, "username": username, "password": password}
        try:
            full_url = utils.urljoin(self.host, "/api/v1/auth")
            response = requests.post(full_url, data=json.dumps(payload), headers=headers, verify=self.tls_verify)
        except RequestException:
            raise exceptions.TaigaRestException(full_url, 400, "NETWORK ERROR", "POST")
        if response.status_code != 200:
            raise exceptions.TaigaRestException(full_url, response.status_code, response.text, "POST")
        self.token = response.json()["auth_token"]
        self.token_refresh = response.json()["refresh"]
        self.raw_request = RequestMaker("/api/v1", self.host, self.token, "Bearer", self.tls_verify)
        self._init_resources()

    def auth_app(self, app_id, app_secret, auth_code, state=""):
        """
        Authenticate an app

        :param app_id: the app id
        :param app_secret: the app secret
        :param auth_code: the app auth code
        """
        headers = {"Content-type": "application/json"}
        payload = {"application": app_id, "auth_code": auth_code, "state": state}
        try:
            full_url = utils.urljoin(self.host, "/api/v1/application-tokens/validate")
            response = requests.post(full_url, data=json.dumps(payload), headers=headers, verify=self.tls_verify)
        except RequestException:
            raise exceptions.TaigaRestException(full_url, 400, "NETWORK ERROR", "POST")
        if response.status_code != 200:
            raise exceptions.TaigaRestException(full_url, response.status_code, response.text, "POST")
        cyphered_token = response.json().get("cyphered_token", "")
        if cyphered_token:
            from jwkest.jwe import JWE
            from jwkest.jwk import SYMKey

            sym_key = SYMKey(key=app_secret, alg="A128KW")
            data, success = JWE().decrypt(cyphered_token, keys=[sym_key]), True
            if isinstance(data, tuple):
                data, success = data
            try:
                self.token = json.loads(data.decode("utf-8")).get("token", None)
            except ValueError:  # pragma: no cover
                self.token = None
            if not success:
                self.token = None
        else:
            self.token = None

        if self.token is None:
            raise exceptions.TaigaRestException(full_url, 400, "INVALID TOKEN", "POST")

        self.raw_request = RequestMaker("/api/v1", self.host, self.token, "Application", self.tls_verify)
        self._init_resources()

    def refresh_token(self, token_refresh=""):
        """
        Refresh auth token.

        Passing a token_refresh will use passed token, otherwise it will try to use self.token_refresh.

        :param token_refresh: the refresh token to be used to refresh api token
        """
        if not token_refresh:
            if self.token_refresh:
                token_refresh = self.token_refresh
            else:
                raise ValueError("Refresh token not set")
        headers = {"Content-type": "application/json"}
        payload = {"refresh": token_refresh}
        try:
            full_url = utils.urljoin(self.host, "/api/v1/auth/refresh")
            response = requests.post(full_url, data=json.dumps(payload), headers=headers, verify=self.tls_verify)
        except RequestException:
            raise exceptions.TaigaRestException(full_url, 400, "NETWORK ERROR", "POST")
        if response.status_code != 200:
            raise exceptions.TaigaRestException(full_url, response.status_code, response.text, "POST")
        self.token = response.json()["auth_token"]
        self.token_refresh = response.json()["refresh"]
        self.raw_request = RequestMaker("/api/v1", self.host, self.token, "Bearer", self.tls_verify)
        self._init_resources()
