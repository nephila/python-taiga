from taiga.requestmaker import RequestMaker, RequestMakerException
from taiga.models.base import InstanceResource, ListResource
from taiga.models import User, Point, UserStoryStatus, Severity, Project
from taiga import TaigaAPI
import taiga.exceptions
import json
import requests
import unittest
from mock import patch
from .tools import create_mock_json
from .tools import MockResponse


class TestUsers(unittest.TestCase):

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_starred_projects(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(200,
            create_mock_json('tests/resources/starred_projects.json'))
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        user = User(rm, id=1)
        projects = user.starred_projects()
        self.assertEqual(len(projects), 2)
        self.assertTrue(isinstance(projects[0], Project))
        self.assertTrue(isinstance(projects[1], Project))