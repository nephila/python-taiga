from taiga import TaigaAPI
import unittest
from mock import patch
from .tools import create_mock_json
from .tools import MockResponse
from taiga.models import Task, UserStory, Issue, WikiPage


class TestSearch(unittest.TestCase):

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_single_user_parsing(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(200,
            create_mock_json('tests/resources/search_success.json'))
        api = TaigaAPI(token='f4k3')
        search_result = api.search(1, 'NEW')
        self.assertEqual(len(search_result.tasks), 1)
        self.assertEqual(len(search_result.user_stories), 1)
        self.assertEqual(len(search_result.issues), 1)
        self.assertEqual(len(search_result.wikipages), 1)

        self.assertTrue(isinstance(search_result.tasks[0], Task))
        self.assertTrue(isinstance(search_result.issues[0], Issue))
        self.assertTrue(isinstance(search_result.user_stories[0], UserStory))
        self.assertTrue(isinstance(search_result.wikipages[0], WikiPage))
