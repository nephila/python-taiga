import json
import requests
from .models import Users
from .models import Projects
from .models import UserStories
from .models import Tasks
from .models import Issues
from .models import Milestones
from .models import Points
from .models import UserStoryStatuses
from .models import Severities
from .models import Roles
from .models import Priorities
from .models import IssueStatuses
from .models import IssueAttributes
from .models import TaskAttributes
from .models import UserStoryAttributes
from .models import TaskStatuses
from .models import WikiPages
from .models import WikiLinks
from .requestmaker import RequestMaker
from requests.exceptions import RequestException
from . import exceptions


class SearchResult(object):

    count = 0
    tasks = []
    issues = []
    user_stories = []
    wiki_pages = []


class TaigaAPI:

    def __init__(self, host='https://api.taiga.io', token=None):
        self.host = host
        self.token = token
        if token:
            self.raw_request = RequestMaker('/api/v1', self.host, self.token)
            self._init_resources()

    def _init_resources(self):
        self.projects = Projects(self.raw_request)
        self.user_stories = UserStories(self.raw_request)
        self.users = Users(self.raw_request)
        self.issues = Issues(self.raw_request)
        self.tasks = Tasks(self.raw_request)
        self.milestones = Milestones(self.raw_request)
        self.severities = Severities(self.raw_request)
        self.roles = Roles(self.raw_request)
        self.points = Points(self.raw_request)
        self.issue_statuses = IssueStatuses(self.raw_request)
        self.issue_attributes = IssueAttributes(self.raw_request)
        self.task_attributes = TaskAttributes(self.raw_request)
        self.user_story_attributes = UserStoryAttributes(self.raw_request)
        self.task_statuses = TaskStatuses(self.raw_request)
        self.priorities = Priorities(self.raw_request)
        self.user_story_statuses = UserStoryStatuses(self.raw_request)
        self.wikipages = WikiPages(self.raw_request)
        self.wikilinks = WikiLinks(self.raw_request)

    def me(self):
        return self.users.get('me')

    def search(self, project, text=''):
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
        headers = {
            'Content-type': 'application/json'
        }
        payload = {
            'type': 'normal',
            'username': username,
            'password': password
        }
        try:
            full_url = self.host + '/api/v1/auth'
            response = requests.post(
                full_url,
                data=json.dumps(payload),
                headers=headers
            )
        except RequestException:
            raise exceptions.TaigaRestException(
                full_url, 400,
                'NETWORK ERROR', 'GET'
            )
        if response.status_code != 200:
            raise exceptions.TaigaRestException(
                full_url,
                response.status_code,
                response.text,
                'GET'
            )
        self.token = response.json()['auth_token']
        self.raw_request = RequestMaker('/api/v1', self.host, self.token)
        self._init_resources()
