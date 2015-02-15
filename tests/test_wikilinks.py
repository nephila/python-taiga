from taiga.requestmaker import RequestMaker
from taiga.models import WikiLink, WikiLinks
import unittest
from mock import patch


class TestWikiLinks(unittest.TestCase):

    @patch('taiga.models.base.ListResource._new_resource')
    def test_create_wikilink(self, mock_new_resource):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        mock_new_resource.return_value = WikiLink(rm)
        wikilink = WikiLinks(rm).create(1, 'Title', 'home')
        mock_new_resource.assert_called_with(
            payload={'project': 1, 'title': 'Title', 'href': 'home'}
        )
