from taiga.requestmaker import RequestMaker
from taiga.models import WikiPage, WikiPages
import unittest
from mock import patch


class TestWikiPages(unittest.TestCase):

    @patch('taiga.models.base.ListResource._new_resource')
    def test_create_wikipage(self, mock_new_resource):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        mock_new_resource.return_value = WikiPage(rm)
        wikipage = WikiPages(rm).create(1, 'WikiPage-Slug', 'Some content')
        mock_new_resource.assert_called_with(
            payload={'project': 1, 'slug': 'WikiPage-Slug', 'content': 'Some content'}
        )
