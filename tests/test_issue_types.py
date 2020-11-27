import unittest
from unittest.mock import patch

from taiga.models.models import IssueType, IssueTypes
from taiga.requestmaker import RequestMaker


class TestIssueTypes(unittest.TestCase):
    @patch("taiga.models.base.ListResource._new_resource")
    def test_create_issue_type(self, mock_new_resource):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        mock_new_resource.return_value = IssueType(rm)
        IssueTypes(rm).create(1, "IT 1")
        mock_new_resource.assert_called_with(payload={"project": 1, "name": "IT 1"})
