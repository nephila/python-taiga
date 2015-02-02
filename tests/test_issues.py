from taiga.requestmaker import RequestMaker, RequestMakerException
from taiga.models.base import InstanceResource, ListResource
from taiga.models import Issue, Issues
from taiga import TaigaAPI
import taiga.exceptions
import json
import requests
import unittest
from mock import patch
from .tools import create_mock_json
from .tools import MockResponse


class TestIssues(unittest.TestCase):

    @patch('taiga.requestmaker.RequestMaker.post')
    def test_upvote(self, mock_requestmaker_post):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        issue = Issue(rm, id=1)
        self.assertEqual(issue.upvote().id, 1)
        mock_requestmaker_post.assert_called_with(
            '/{endpoint}/{id}/upvote',
            endpoint='issues', id=1
        )

    @patch('taiga.requestmaker.RequestMaker.post')
    def test_downvote(self, mock_requestmaker_post):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        issue = Issue(rm, id=1)
        self.assertEqual(issue.downvote().id, 1)
        mock_requestmaker_post.assert_called_with(
            '/{endpoint}/{id}/downvote',
            endpoint='issues', id=1
        )

    @patch('taiga.requestmaker.RequestMaker.post')
    def test_issue_creation(self, mock_requestmaker_post):
        mock_requestmaker_post.return_value = MockResponse(200,
            create_mock_json('tests/resources/issue_details_success.json'))
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        issue = Issues(rm).create(1, 2, 3, 4, 5, 6)
        self.assertTrue(isinstance(issue, Issue))
