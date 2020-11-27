import unittest
from unittest.mock import patch

from taiga.models import IssueStatus, IssueStatuses
from taiga.requestmaker import RequestMaker


class TestIssueStatuses(unittest.TestCase):
    @patch("taiga.models.base.ListResource._new_resource")
    def test_create_issue_status(self, mock_new_resource):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        mock_new_resource.return_value = IssueStatus(rm)
        IssueStatuses(rm).create(1, "IST 1")
        mock_new_resource.assert_called_with(payload={"project": 1, "name": "IST 1"})
