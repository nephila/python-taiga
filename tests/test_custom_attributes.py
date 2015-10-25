from taiga.requestmaker import RequestMaker
from taiga.models import Issue, Issues, IssueAttributes, IssueAttribute
from taiga.exceptions import TaigaException
import unittest
from mock import patch
from .tools import create_mock_json
from .tools import MockResponse
import six

if six.PY2:
    import_open = '__builtin__.open'
else:
    import_open = 'builtins.open'

class TestCustomAttributes(unittest.TestCase):

    @patch('taiga.requestmaker.RequestMaker.get')
    @patch('taiga.requestmaker.RequestMaker.patch')
    def test_edit_issue_custom_attribute(self, mock_requestmaker_patch, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(200,
            create_mock_json('tests/resources/issue_customattr_success.json'))
        mock_requestmaker_patch.return_value = MockResponse(200,
            create_mock_json('tests/resources/issue_customattr_success.json'))
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        issue = Issue(rm, id=1, project=1)
        new_attribute = issue.set_attribute(1, 13)
        self.assertTrue('attributes_values' in new_attribute)
        mock_requestmaker_patch.assert_called_with(
            '/{endpoint}/custom-attributes-values/{id}',
            endpoint=Issue.endpoint, id=issue.id,
            payload={
                'attributes_values': {u'1': 13},
                'version': 1
            }
        )

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_get_issue_custom_attributes(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(200,
            create_mock_json('tests/resources/issue_customattr_success.json'))
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        issue = Issue(rm, id=1, project=1)
        my_attributes = issue.get_attributes()
        self.assertTrue('attributes_values' in my_attributes)
        mock_requestmaker_get.assert_called_with(
            '/{endpoint}/custom-attributes-values/{id}',
            endpoint=Issue.endpoint, id=issue.id, cache=False
        )

    @patch('taiga.requestmaker.RequestMaker.post')
    def test_issue_attribute_creation(self, mock_requestmaker_post):
        mock_requestmaker_post.return_value = MockResponse(200,
            create_mock_json('tests/resources/issue_details_success.json'))
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        issue_attribute = IssueAttributes(rm).create(1, 'new attribute')
        self.assertTrue(isinstance(issue_attribute, IssueAttribute))
