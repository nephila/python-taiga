from taiga.requestmaker import RequestMaker
from taiga.models import UserStory, UserStories, Task
import unittest
from mock import patch
import six
from taiga import TaigaAPI
from .tools import create_mock_json
from .tools import MockResponse

if six.PY2:
    import_open = '__builtin__.open'
else:
    import_open = 'builtins.open'

class TestUserStories(unittest.TestCase):

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_single_userstory_parsing(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(200,
            create_mock_json('tests/resources/userstory_details_success.json'))
        api = TaigaAPI(token='f4k3')
        userstory = api.user_stories.get(1)
        self.assertEqual(userstory.description, 'Description of the story')

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_list_userstories_parsing(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(200,
            create_mock_json('tests/resources/userstories_list_success.json'))
        api = TaigaAPI(token='f4k3')
        userstories = api.user_stories.list()
        self.assertEqual(userstories[0].description, 'Description of the story')
        self.assertEqual(len(userstories), 1)

    @patch('taiga.requestmaker.RequestMaker.post')
    def test_add_task(self, mock_requestmaker_post):
        mock_requestmaker_post.return_value = MockResponse(200,
            create_mock_json('tests/resources/task_details_success.json'))
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        userstory = UserStory(rm, id=1, project=1)
        task = userstory.add_task('', '')
        self.assertTrue(isinstance(task, Task))

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_list_tasks(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(200,
            create_mock_json('tests/resources/tasks_list_success.json'))
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        userstory = UserStory(rm, id=1, project=1)
        tasks = userstory.list_tasks()
        self.assertEqual(len(tasks), 2)

    @patch(import_open)
    @patch('taiga.models.base.ListResource._new_resource')
    def test_file_attach(self, mock_new_resource, mock_open):
        fd = open('tests/resources/tasks_list_success.json')
        mock_open.return_value = fd
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        userstory = UserStory(rm, id=1, project=1)
        userstory.attach('tests/resources/tasks_list_success.json')
        mock_new_resource.assert_called_with(
            files={'attached_file': fd},
            payload={'project': 1, 'object_id': 1}
        )

    @patch('taiga.models.base.ListResource._new_resource')
    def test_create_user_story(self, mock_new_resource):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        mock_new_resource.return_value = UserStory(rm)
        user_story = UserStories(rm).create(1, 'UserStory 1')
        mock_new_resource.assert_called_with(
            payload={'project': 1, 'subject': 'UserStory 1'}
        )

