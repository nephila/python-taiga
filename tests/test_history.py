from taiga.requestmaker import RequestMaker
from taiga.models import History
import unittest
from mock import patch
import six
from taiga import TaigaAPI
from .tools import create_mock_json
from .tools import MockResponse

if six.PY2:
    import_open = '__builtin__.open'
else:
    import_open = 'builtins.open'

class TestHistory(unittest.TestCase):

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_issue(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(200,
            create_mock_json('tests/resources/history_success.json'))
        api = TaigaAPI(token='f4k3')
        res_id = 1
        issue = api.history.issue.get(res_id)
        mock_requestmaker_get.assert_called_with(
            '/{endpoint}/{entity}/{id}',
            endpoint='history', entity='issue', id=res_id
        )

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_task(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(200,
            create_mock_json('tests/resources/history_success.json'))
        api = TaigaAPI(token='f4k3')
        res_id = 1
        task = api.history.task.get(res_id)
        mock_requestmaker_get.assert_called_with(
            '/{endpoint}/{entity}/{id}',
            endpoint='history', entity='task', id=res_id
        )

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_userstory(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(200,
            create_mock_json('tests/resources/history_success.json'))
        api = TaigaAPI(token='f4k3')
        res_id = 1
        userstory = api.history.user_story.get(res_id)
        mock_requestmaker_get.assert_called_with(
            '/{endpoint}/{entity}/{id}',
            endpoint='history', entity='userstory', id=res_id
        )

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_wiki(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(200,
            create_mock_json('tests/resources/history_success.json'))
        api = TaigaAPI(token='f4k3')
        res_id = 1
        wiki = api.history.wiki.get(res_id)
        mock_requestmaker_get.assert_called_with(
            '/{endpoint}/{entity}/{id}',
            endpoint='history', entity='wiki', id=res_id
        )

    @patch('taiga.requestmaker.RequestMaker.post')
    def test_task_delete_comment(self, mock_requestmaker_post):
        mock_requestmaker_post.return_value = MockResponse(204, '')
        api = TaigaAPI(token='f4k3')
        res_id = 1
        ent_id = '9660411e-6fea-11e4-a5b3-b499ba565108'
        task = api.history.task.delete_comment(res_id, ent_id)
        mock_requestmaker_post.assert_called_with(
            '/{endpoint}/{entity}/{id}/delete_comment?id={ent_id}',
            endpoint='history', entity='task', id=res_id, ent_id=ent_id
        )

    @patch('taiga.requestmaker.RequestMaker.post')
    def test_userstory_undelete_comment(self, mock_requestmaker_post):
        mock_requestmaker_post.return_value = MockResponse(204, '')
        api = TaigaAPI(token='f4k3')
        res_id = 1
        ent_id = '9660411e-6fea-11e4-a5b3-b499ba565108'
        task = api.history.user_story.undelete_comment(res_id, ent_id)
        mock_requestmaker_post.assert_called_with(
            '/{endpoint}/{entity}/{id}/undelete_comment?id={ent_id}',
            endpoint='history', entity='userstory', id=res_id, ent_id=ent_id
        )
