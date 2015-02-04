from taiga.requestmaker import RequestMaker, RequestMakerException
from taiga.models.base import InstanceResource, ListResource
from taiga.models.models import IssueType, IssueTypes
from taiga import TaigaAPI
import taiga.exceptions
import json
import requests
import unittest
from mock import patch
from .tools import create_mock_json
from .tools import MockResponse


class TestIssueTypes(unittest.TestCase):

    @patch('taiga.models.base.ListResource._new_resource')
    def test_create_issue_type(self, mock_new_resource):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        mock_new_resource.return_value = IssueType(rm)
        it = IssueTypes(rm).create(1, 'IT 1')
        mock_new_resource.assert_called_with(
            payload={'project': 1, 'name': 'IT 1'}
        )

