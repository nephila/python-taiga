import unittest
from unittest.mock import patch

from taiga import TaigaAPI
from taiga.models import Project, User
from taiga.requestmaker import RequestMaker

from .tools import MockResponse, create_mock_json


class TestUsers(unittest.TestCase):
    @patch("taiga.requestmaker.RequestMaker.get")
    def test_starred_projects(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/starred_projects.json")
        )
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        user = User(rm, id=1)
        projects = user.starred_projects()
        self.assertEqual(len(projects), 2)
        self.assertTrue(isinstance(projects[0], Project))
        self.assertTrue(isinstance(projects[1], Project))

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_list_all_users(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/projects_list_success.json")
        )
        api = TaigaAPI(token="f4k3")
        users = api.users.list()
        self.assertEqual(len(users), 1)
        self.assertTrue(isinstance(users[0], User))

    @patch("taiga.models.Users.get")
    def test_me(self, mock_user_get):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        mock_user_get.return_value = User(rm, full_name="Andrea")
        api = TaigaAPI(token="f4k3")
        user = api.me()
        self.assertEqual(user.full_name, "Andrea")
