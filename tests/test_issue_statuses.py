import unittest
from unittest.mock import patch

from taiga.models import IssueStatus, IssueStatuses
from taiga.requestmaker import RequestMaker

from .tools import MockResponse


class TestIssueStatuses(unittest.TestCase):
    @patch("taiga.models.base.ListResource._new_resource")
    def test_create_issue_status(self, mock_new_resource):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        mock_new_resource.return_value = IssueStatus(rm)
        IssueStatuses(rm).create(1, "IST 1")
        mock_new_resource.assert_called_with(payload={"project": 1, "name": "IST 1"})

    @patch("taiga.requestmaker.requests.delete")
    def test_delete_issue_statuses(self, requests_delete):
        rm = RequestMaker(api_path="/api/v1", host="host", token="f4k3")
        requests_delete.return_value = MockResponse(204, "")
        IssueStatuses(rm).delete(1, 2)
        requests_delete.assert_called_with(
            "host/api/v1/issue-statuses/1",
            headers={"Content-type": "application/json", "Authorization": "Bearer f4k3", "x-lazy-pagination": "True"},
            params={"moveTo": 2},
            verify=True,
        )

    @patch("taiga.requestmaker.requests.delete")
    def test_delete_issue_status(self, requests_delete):
        rm = RequestMaker(api_path="/api/v1", host="host", token="f4k3")
        requests_delete.return_value = MockResponse(204, "")
        IssueStatus(rm, id=1).delete(2)
        requests_delete.assert_called_with(
            "host/api/v1/issue-statuses/1",
            headers={"Content-type": "application/json", "Authorization": "Bearer f4k3", "x-lazy-pagination": "True"},
            params={"moveTo": 2},
            verify=True,
        )
