import unittest

from mock import patch

from taiga import TaigaAPI

from .tools import MockResponse, create_mock_json


class TestHistory(unittest.TestCase):

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_issue(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200,
            create_mock_json('tests/resources/history_success.json')
        )
        api = TaigaAPI(token='f4k3')
        res_id = 1
        api.history.issue.get(res_id)
        mock_requestmaker_get.assert_called_with(
            '/{endpoint}/{entity}/{id}',
            endpoint='history', entity='issue', id=res_id
        )

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_task(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200,
            create_mock_json('tests/resources/history_success.json')
        )
        api = TaigaAPI(token='f4k3')
        res_id = 1
        api.history.task.get(res_id)
        mock_requestmaker_get.assert_called_with(
            '/{endpoint}/{entity}/{id}',
            endpoint='history', entity='task', id=res_id
        )

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_userstory(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200,
            create_mock_json('tests/resources/history_success.json')
        )
        api = TaigaAPI(token='f4k3')
        res_id = 1
        api.history.user_story.get(res_id)
        mock_requestmaker_get.assert_called_with(
            '/{endpoint}/{entity}/{id}',
            endpoint='history', entity='userstory', id=res_id
        )

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_wiki(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200,
            create_mock_json('tests/resources/history_success.json')
        )
        api = TaigaAPI(token='f4k3')
        res_id = 1
        api.history.wiki.get(res_id)
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
        api.history.task.delete_comment(res_id, ent_id)
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
        api.history.user_story.undelete_comment(res_id, ent_id)
        mock_requestmaker_post.assert_called_with(
            '/{endpoint}/{entity}/{id}/undelete_comment?id={ent_id}',
            endpoint='history', entity='userstory', id=res_id, ent_id=ent_id
        )
