from taiga.requestmaker import RequestMaker
from taiga.models import WikiPage, WikiPages
import unittest
from mock import patch
import six

if six.PY2:
    import_open = '__builtin__.open'
else:
    import_open = 'builtins.open'

class TestWikiPages(unittest.TestCase):

    @patch('taiga.models.base.ListResource._new_resource')
    def test_create_wikipage(self, mock_new_resource):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        mock_new_resource.return_value = WikiPage(rm)
        wikipage = WikiPages(rm).create(1, 'WikiPage-Slug', 'Some content')
        mock_new_resource.assert_called_with(
            payload={'project': 1, 'slug': 'WikiPage-Slug', 'content': 'Some content'}
        )

    @patch(import_open)
    @patch('taiga.models.base.ListResource._new_resource')
    def test_file_attach(self, mock_new_resource, mock_open):
        fd = open('tests/resources/tasks_list_success.json')
        mock_open.return_value = fd
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        wikipage = WikiPage(rm, id=1, project=1)
        wikipage.attach('tests/resources/tasks_list_success.json')
        mock_new_resource.assert_called_with(
            files={'attached_file': fd},
            payload={'project': 1, 'object_id': 1}
        )