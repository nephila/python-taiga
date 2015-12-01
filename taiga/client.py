import json
import requests
from .models import Users
from .models import Projects
from .models import UserStories
from .models import UserStoryAttachments
from .models import Tasks
from .models import TaskAttachments
from .models import Issues
from .models import IssueAttachments
from .models import Milestones
from .models import Points
from .models import UserStoryStatuses
from .models import Severities
from .models import Roles
from .models import Priorities
from .models import IssueStatuses
from .models import IssueAttributes
from .models import IssueTypes
from .models import TaskAttributes
from .models import UserStoryAttributes
from .models import TaskStatuses
from .models import WikiPages
from .models import WikiLinks
from .models import History
from .requestmaker import RequestMaker
from requests.exceptions import RequestException
from . import exceptions
from . import utils


class SearchResult(object):

    count = 0
    tasks = []
    issues = []
    user_stories = []
    wiki_pages = []


class TaigaAPI:
    """
    TaigaAPI class

    :param host: the host of your Taiga.io instance
    :param token: the token you may provide
    :param token_type: the token type
    """
    def __init__(self, host='https://api.taiga.io', token=None,
                 token_type='Bearer'):
        self.host = host
        self.token = token
        self.token_type = token_type
        if token:
            self.raw_request = RequestMaker('/api/v1', self.host, self.token,
                                            self.token_type)
            self._init_resources()

    def _init_resources(self):
        self.projects = Projects(self.raw_request)
        self.user_stories = UserStories(self.raw_request)
        self.user_story_attachments = UserStoryAttachments(self.raw_request)
        self.users = Users(self.raw_request)
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

    def me(self):
        """
        Get a :class:`taiga.models.models.User` representing me
        """
        return self.users.get('me')

    def search(self, project, text=''):
        """
        Search in your Taiga.io instance

        :param project: the project id
        :param text: the query of your search
        """
        result = self.raw_request.get(
            'search', query={'project': project, 'text': text}
        )
        result = result.json()
        search_result = SearchResult()
        search_result.tasks = self.tasks.parse_list(result['tasks'])
        search_result.issues = self.issues.parse_list(result['issues'])
        search_result.user_stories = self.user_stories.parse_list(
            result['userstories']
        )
        search_result.wikipages = self.wikipages.parse_list(
            result['wikipages']
        )
        return search_result

    def auth(self, username, password):
        """
        Authenticate you

        :param username: your username
        :param password: your password
        """
        headers = {
            'Content-type': 'application/json'
        }
        payload = {
            'type': 'normal',
            'username': username,
            'password': password
        }
        try:
            full_url = utils.urljoin(self.host, '/api/v1/auth')
            response = requests.post(
                full_url,
                data=json.dumps(payload),
                headers=headers
            )
        except RequestException:
            raise exceptions.TaigaRestException(
                full_url, 400,
                'NETWORK ERROR', 'POST'
            )
        if response.status_code != 200:
            raise exceptions.TaigaRestException(
                full_url,
                response.status_code,
                response.text,
                'POST'
            )
        self.token = response.json()['auth_token']
        self.raw_request = RequestMaker('/api/v1', self.host, self.token,
                                        'Bearer')
        self._init_resources()

    def auth_app(self, app_id, app_secret, auth_code, state=''):
        """
        Authenticate an app

        :param app_id: the app id
        :param app_secret: the app secret
        :param auth_code: the app auth code
        """
        headers = {
            'Content-type': 'application/json'
        }
        payload = {
            'application': app_id,
            'auth_code': auth_code,
            'state': state
        }
        try:
            full_url = utils.urljoin(
                self.host,
                '/api/v1/application-tokens/validate'
            )
            response = requests.post(
                full_url,
                data=json.dumps(payload),
                headers=headers
            )
        except RequestException:
            raise exceptions.TaigaRestException(
                full_url, 400,
                'NETWORK ERROR', 'POST'
            )
        if response.status_code != 200:
            raise exceptions.TaigaRestException(
                full_url,
                response.status_code,
                response.text,
                'POST'
            )
        cyphered_token = response.json().get('cyphered_token', '')
        if cyphered_token:
            from jwkest.jwk import SYMKey
            from jwkest.jwe import JWE

            sym_key = SYMKey(key=app_secret, alg='A128KW')
            (data, success) = JWE().decrypt(cyphered_token, keys=[sym_key])
            if success:
                self.token = json.loads(data.decode('utf-8')).get('token',
                                                                  None)
            else:
                self.token = None
        else:
            self.token = None

        if self.token is None:
            raise exceptions.TaigaRestException(
                full_url, 400,
                'INVALID TOKEN', 'POST'
            )

        self.raw_request = RequestMaker('/api/v1', self.host, self.token,
                                        'Application')
        self._init_resources()
