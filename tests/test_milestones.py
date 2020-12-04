import datetime
import unittest
from unittest.mock import patch

from taiga import TaigaAPI
from taiga.models import Milestones, UserStory
from taiga.requestmaker import RequestMaker

from .tools import MockResponse, create_mock_json


class TestMilestones(unittest.TestCase):
    @patch("taiga.requestmaker.RequestMaker.get")
    def test_single_milestone_parsing(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/milestone_details_success.json")
        )
        api = TaigaAPI(token="f4k3")
        milestone = api.milestones.get(1)
        self.assertEqual(milestone.name, "MILESTONE 1")
        self.assertTrue(isinstance(milestone.user_stories[0], UserStory))

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_list_milestones_parsing(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/milestones_list_success.json")
        )
        api = TaigaAPI(token="f4k3")
        milestones = api.milestones.list()
        self.assertEqual(milestones[0].name, "MILESTONE 1")
        self.assertTrue(isinstance(milestones[0].user_stories[0], UserStory))

    @patch("taiga.requestmaker.RequestMaker.post")
    def test_milestone_create(self, mock_requestmaker_post):
        api = TaigaAPI(token="f4k3")
        start_time = datetime.datetime(2015, 1, 16, 0, 0)
        finish_time = datetime.datetime(2015, 2, 16, 0, 0)
        api.milestones.create(1, "Sprint Jan", start_time, finish_time)
        mock_requestmaker_post.assert_called_with(
            "milestones",
            payload={
                "project": 1,
                "estimated_finish": "2015-02-16",
                "estimated_start": "2015-01-16",
                "name": "Sprint Jan",
            },
        )

    @patch("taiga.requestmaker.RequestMaker.post")
    def test_milestone_import(self, mock_requestmaker_post):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        start_time = datetime.datetime(2015, 1, 16, 0, 0)
        finish_time = datetime.datetime(2015, 2, 16, 0, 0)
        Milestones(rm).import_(1, "Sprint Jan", start_time, finish_time)
        mock_requestmaker_post.assert_called_with(
            "/{endpoint}/{id}/{type}",
            endpoint="importer",
            payload={
                "project": 1,
                "name": "Sprint Jan",
                "estimated_start": "2015-01-16",
                "estimated_finish": "2015-02-16",
            },
            id=1,
            type="milestone",
        )

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_stats(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/milestone_details_success.json")
        )
        api = TaigaAPI(token="f4k3")
        milestone = api.milestones.get(1)
        milestone.stats()
        mock_requestmaker_get.assert_called_with("/{endpoint}/{id}/stats", endpoint="milestones", id=milestone.id)
