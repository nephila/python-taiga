import unittest
from unittest.mock import patch

from taiga import TaigaAPI
from taiga.models import Epic, Issue, Task, UserStory, WikiPage

from .tools import MockResponse, create_mock_json


class TestSearch(unittest.TestCase):
    @patch("taiga.requestmaker.RequestMaker.get")
    def test_single_user_parsing(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(200, create_mock_json("tests/resources/search_success.json"))
        api = TaigaAPI(token="f4k3")
        search_result = api.search(1, "NEW")
        self.assertEqual(search_result.count, 3)
        self.assertEqual(len(search_result.tasks), 1)
        self.assertEqual(len(search_result.user_stories), 1)
        self.assertEqual(len(search_result.issues), 1)
        self.assertEqual(len(search_result.wikipages), 1)
        self.assertEqual(len(search_result.epics), 2)

        self.assertTrue(isinstance(search_result.count, int))
        self.assertTrue(isinstance(search_result.tasks[0], Task))
        self.assertTrue(isinstance(search_result.issues[0], Issue))
        self.assertTrue(isinstance(search_result.user_stories[0], UserStory))
        self.assertTrue(isinstance(search_result.wikipages[0], WikiPage))
        self.assertTrue(isinstance(search_result.epics[0], Epic))
