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

    @patch('taiga.requestmaker.RequestMaker.post')
    def test_import_wikilink(self, mock_requestmaker_post):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        wikilink = WikiLinks(rm).import_(1, 'Title', 'home')
        mock_requestmaker_post.assert_called_with(
            '/{endpoint}/{id}/{type}', endpoint='importer', payload={'project': 1,
                                                                     'href': 'home',
                                                                     'title': 'Title'},
            id=1, type='wiki_link'
        )
