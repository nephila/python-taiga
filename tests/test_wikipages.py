from taiga.requestmaker import RequestMaker, RequestMakerException
from taiga.models.base import InstanceResource, ListResource
from taiga.models import WikiPage, WikiPages
from taiga import TaigaAPI
import taiga.exceptions
import json
import requests
import unittest
from mock import patch
from .tools import create_mock_json
from .tools import MockResponse


class TestWikiPages(unittest.TestCase):

    @patch('taiga.models.base.ListResource._new_resource')
    def test_create_wikipage(self, mock_new_resource):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        mock_new_resource.return_value = WikiPage(rm)
        wikipage = WikiPages(rm).create(1, 'WikiPage-Slug', 'Some content')
        mock_new_resource.assert_called_with(
            payload={'project': 1, 'slug': 'WikiPage-Slug', 'content': 'Some content'}
        )
