from taiga.requestmaker import RequestMaker, RequestMakerException
from taiga.models.base import InstanceResource, ListResource
from taiga.models import UserStoryStatus, UserStoryStatuses
from taiga import TaigaAPI
import taiga.exceptions
import json
import requests
import unittest
from mock import patch
from .tools import create_mock_json
from .tools import MockResponse


class TestPriorities(unittest.TestCase):

    @patch('taiga.models.base.ListResource._new_resource')
    def test_create_user_story_status(self, mock_new_resource):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        mock_new_resource.return_value = UserStoryStatus(rm)
        userstory_status = UserStoryStatuses(rm).create(1, 'USS 1')
        mock_new_resource.assert_called_with(
            payload={'project': 1, 'name': 'USS 1'}
        )

