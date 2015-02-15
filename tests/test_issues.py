from taiga.requestmaker import RequestMaker
from taiga.models import Issue, Issues
import unittest
from mock import patch
from .tools import create_mock_json
from .tools import MockResponse
import six

if six.PY2:
    import_open = '__builtin__.open'
else:
    import_open = 'builtins.open'

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

    @patch(import_open)
    @patch('taiga.models.base.ListResource._new_resource')
    def test_file_attach(self, mock_new_resource, mock_open):
        fd = open('tests/resources/tasks_list_success.json')
        mock_open.return_value = fd
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        issue = Issue(rm, id=1, project=1)
        issue.attach('tests/resources/tasks_list_success.json')
        mock_new_resource.assert_called_with(
            files={'attached_file': fd},
            payload={'project': 1, 'object_id': 1}
        )
