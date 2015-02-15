from taiga import TaigaAPI
import taiga.exceptions
import requests
import unittest
from mock import patch
from .tools import create_mock_json
from .tools import MockResponse

class TestAuth(unittest.TestCase):

    @patch('taiga.client.TaigaAPI._init_resources')
    def test_call_init_if_token_provided(self, init):
        api = TaigaAPI(token='f4k3')
        init.assert_called_once_with()

    @patch('taiga.client.TaigaAPI._init_resources')
    def test_not_call_init_if_no_token_provided(self, init):
        api = TaigaAPI(host='host')
        self.assertFalse(init.called)

    @patch('taiga.client.requests')
    def test_auth_success(self, requests):
        requests.post.return_value = MockResponse(200, create_mock_json('tests/resources/auth_user_success.json'))
        api = TaigaAPI(host='host')
        api.auth('valid_user', 'valid_password')
        self.assertEqual(api.token, 'f4k3')

    @patch('taiga.client.requests')
    def test_auth_not_success(self, requests):
        requests.post.return_value = MockResponse(401, 'Not allowed')
        api = TaigaAPI(host='host')
        self.assertRaises(taiga.exceptions.TaigaRestException, api.auth, 'valid_user', 'valid_password')

    @patch('taiga.client.requests.post')
    def test_auth_connection_error(self, requests_post):
        requests_post.side_effect = requests.RequestException()
        api = TaigaAPI(host='host')
        self.assertRaises(taiga.exceptions.TaigaRestException, api.auth, 'valid_user', 'valid_password')
