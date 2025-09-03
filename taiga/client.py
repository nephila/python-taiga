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
    :param proxies: a dictionary of proxies to use for requests
    """

    def __init__(
        self,
        host="https://api.taiga.io",
        token=None,
        token_type="Bearer",
        tls_verify=True,
        auth_type="normal",
        proxies=None,
    ):
        self.host = host
        self.token = token
        self.token_refresh = None
        self.token_type = token_type
        self.tls_verify = tls_verify
        self.auth_type = auth_type
        self.proxies = proxies
        if not self.tls_verify:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        if token:
            self.raw_request = RequestMaker(
                "/api/v1", self.host, self.token, self.token_type, self.tls_verify, proxies=proxies
            )
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
            response = requests.post(
                full_url, data=json.dumps(payload), headers=headers, verify=self.tls_verify, proxies=self.proxies
            )
        except RequestException:
            raise exceptions.TaigaRestException(full_url, 400, "NETWORK ERROR", "POST")
        if response.status_code != 200:
            raise exceptions.TaigaRestException(full_url, response.status_code, response.text, "POST")
        self.token = response.json()["auth_token"]
        self.token_refresh = response.json()["refresh"]
        self.raw_request = RequestMaker(
            "/api/v1", self.host, self.token, "Bearer", self.tls_verify, proxies=self.proxies
        )
        self._init_resources()

    def auth_app(self, app_id, auth_code, state):
        """
        Retrieve an application token.
        This only works once per token; in order to reset it, the auth code needs
        to be set again in the Taiga admin UI.

        In order to use the token, initialize TaigaAPI with token_type="Application"
        and token="token from this function".

        :param app_id: the app id
        :param auth_code: app auth code as specified in Taiga
        :param state: state as specified in Taiga (any string; must not be empty)
        :return: token string
        """
        headers = {"Content-type": "application/json"}
        payload = {"application": app_id, "auth_code": auth_code, "state": state}
        try:
            full_url = utils.urljoin(self.host, "/api/v1/application-tokens/validate")
            response = requests.post(
                full_url, data=json.dumps(payload), headers=headers, verify=self.tls_verify, proxies=self.proxies
            )
        except RequestException:
            raise exceptions.TaigaRestException(full_url, 400, "NETWORK ERROR", "POST")
        if response.status_code != 200:
            raise exceptions.TaigaRestException(full_url, response.status_code, response.text, "POST")
        token = response.json().get("token", None)

        if token is None:
            raise exceptions.TaigaRestException(full_url, 400, "INVALID TOKEN", "POST")

        return token

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
            response = requests.post(
                full_url, data=json.dumps(payload), headers=headers, verify=self.tls_verify, proxies=self.proxies
            )
        except RequestException:
            raise exceptions.TaigaRestException(full_url, 400, "NETWORK ERROR", "POST")
        if response.status_code != 200:
            raise exceptions.TaigaRestException(full_url, response.status_code, response.text, "POST")
        self.token = response.json()["auth_token"]
        self.token_refresh = response.json()["refresh"]
        self.raw_request = RequestMaker(
            "/api/v1", self.host, self.token, "Bearer", self.tls_verify, proxies=self.proxies
        )
        self._init_resources()
