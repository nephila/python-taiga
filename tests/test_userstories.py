from taiga.requestmaker import RequestMaker, RequestMakerException
from taiga.models.base import InstanceResource, ListResource
from taiga import TaigaAPI
import taiga.exceptions
import json
import requests
import unittest
from mock import patch
from .tools import create_mock_json
from .tools import MockResponse

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

