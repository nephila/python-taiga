import unittest
from unittest.mock import patch

from taiga.models import Priorities, Priority
from taiga.requestmaker import RequestMaker

from .tools import MockResponse


class TestPriorities(unittest.TestCase):
    @patch("taiga.models.base.ListResource._new_resource")
    def test_create_priority(self, mock_new_resource):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        mock_new_resource.return_value = Priority(rm)
        Priorities(rm).create(1, "Priority 1")
        mock_new_resource.assert_called_with(payload={"project": 1, "name": "Priority 1"})

    @patch("taiga.requestmaker.requests.delete")
    def test_delete_priorities(self, requests_delete):
        rm = RequestMaker(api_path="/api/v1", host="host", token="f4k3")
        requests_delete.return_value = MockResponse(204, "")
        Priorities(rm).delete(1, 2)
        requests_delete.assert_called_with(
            "host/api/v1/priorities/1",
            headers={"Content-type": "application/json", "Authorization": "Bearer f4k3", "x-lazy-pagination": "True"},
            params={"moveTo": 2},
            verify=True,
        )

    @patch("taiga.requestmaker.requests.delete")
    def test_delete_priority(self, requests_delete):
        rm = RequestMaker(api_path="/api/v1", host="host", token="f4k3")
        requests_delete.return_value = MockResponse(204, "")
        Priority(rm, id=1).delete(2)
        requests_delete.assert_called_with(
            "host/api/v1/priorities/1",
            headers={"Content-type": "application/json", "Authorization": "Bearer f4k3", "x-lazy-pagination": "True"},
            params={"moveTo": 2},
            verify=True,
        )
