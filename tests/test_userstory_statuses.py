import unittest
from unittest.mock import patch

from taiga.models import UserStoryStatus, UserStoryStatuses
from taiga.requestmaker import RequestMaker

from .tools import MockResponse


class TestPriorities(unittest.TestCase):
    @patch("taiga.models.base.ListResource._new_resource")
    def test_create_user_story_status(self, mock_new_resource):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        mock_new_resource.return_value = UserStoryStatus(rm)
        UserStoryStatuses(rm).create(1, "USS 1")
        mock_new_resource.assert_called_with(payload={"project": 1, "name": "USS 1"})

    @patch("taiga.requestmaker.requests.delete")
    def test_delete_user_story_statuses(self, requests_delete):
        rm = RequestMaker(api_path="/api/v1", host="host", token="f4k3")
        requests_delete.return_value = MockResponse(204, "")
        UserStoryStatuses(rm).delete(1, 2)
        requests_delete.assert_called_with(
            "host/api/v1/userstory-statuses/1",
            headers={"Content-type": "application/json", "Authorization": "Bearer f4k3", "x-lazy-pagination": "True"},
            params={"moveTo": 2},
            verify=True,
        )

    @patch("taiga.requestmaker.requests.delete")
    def test_delete_user_story_status(self, requests_delete):
        rm = RequestMaker(api_path="/api/v1", host="host", token="f4k3")
        requests_delete.return_value = MockResponse(204, "")
        UserStoryStatus(rm, id=1).delete(2)
        requests_delete.assert_called_with(
            "host/api/v1/userstory-statuses/1",
            headers={"Content-type": "application/json", "Authorization": "Bearer f4k3", "x-lazy-pagination": "True"},
            params={"moveTo": 2},
            verify=True,
        )
