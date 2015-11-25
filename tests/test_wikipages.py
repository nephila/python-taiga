from taiga.requestmaker import RequestMaker
from taiga.models import WikiPage, WikiPages
from taiga.exceptions import TaigaException
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

    @patch('taiga.requestmaker.RequestMaker.post')
    def test_import_wikipage(self, mock_requestmaker_post):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        wikipage = WikiPages(rm).import_(1, 'WikiPage-Slug', 'Some content')
        mock_requestmaker_post.assert_called_with(
            '/{endpoint}/{id}/{type}', endpoint='importer', payload={'project': 1,
                                                                     'content': 'Some content',
                                                                     'slug': 'WikiPage-Slug'},
            id=1, type='wiki_page'
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

    @patch('taiga.models.base.ListResource._new_resource')
    def test_open_file_attach(self, mock_new_resource):
        fd = open('tests/resources/tasks_list_success.json')
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        wikipage = WikiPage(rm, id=1, project=1)
        wikipage.attach(fd)
        mock_new_resource.assert_called_with(
            files={'attached_file': fd},
            payload={'project': 1, 'object_id': 1}
        )

    def test_not_existing_file_attach(self):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        wikipage = WikiPage(rm, id=1, project=1)
        self.assertRaises(TaigaException, wikipage.attach, 'not-existing-file')

    def test_not_valid_type_file_attach(self):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        wikipage = WikiPage(rm, id=1, project=1)
        self.assertRaises(TaigaException, wikipage.attach, 4)
