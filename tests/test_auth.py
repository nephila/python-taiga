import unittest
from unittest.mock import patch

import requests

import taiga.exceptions
from taiga import TaigaAPI

from .tools import MockResponse, create_mock_json


class TestAuth(unittest.TestCase):
    @patch("taiga.client.TaigaAPI._init_resources")
    def test_call_init_if_token_provided(self, init):
        TaigaAPI(token="f4k3")
        init.assert_called_once_with()

    @patch("taiga.client.TaigaAPI._init_resources")
    def test_not_call_init_if_no_token_provided(self, init):
        TaigaAPI(host="host")
        self.assertFalse(init.called)

    @patch("taiga.client.requests")
    def test_auth_success(self, requests):
        requests.post.return_value = MockResponse(200, create_mock_json("tests/resources/auth_user_success.json"))
        api = TaigaAPI(host="host")
        api.auth("valid_user", "valid_password")
        self.assertEqual(api.token, "f4k3")

    @patch("taiga.client.requests")
    def test_auth_not_success(self, requests):
        requests.post.return_value = MockResponse(401, "Not allowed")
        api = TaigaAPI(host="host")
        self.assertRaises(taiga.exceptions.TaigaRestException, api.auth, "valid_user", "valid_password")

    @patch("taiga.client.requests.post")
    def test_auth_connection_error(self, requests_post):
        requests_post.side_effect = requests.RequestException()
        api = TaigaAPI(host="host")
        self.assertRaises(taiga.exceptions.TaigaRestException, api.auth, "valid_user", "valid_password")

    @patch("taiga.client.requests")
    def test_refresh_token_not_success(self, requests):
        requests.post.return_value = MockResponse(401, "Not allowed")
        api = TaigaAPI(host="host")
        self.assertRaises(taiga.exceptions.TaigaRestException, api.refresh_token, "testToken")

    @patch("taiga.client.requests.post")
    def test_refresh_token_connection_error(self, requests_post):
        requests_post.side_effect = requests.RequestException()
        api = TaigaAPI(host="host")
        self.assertRaises(taiga.exceptions.TaigaRestException, api.refresh_token, "testToken")

    def test_refresh_token_without_auth(self):
        api = TaigaAPI(host="host")
        self.assertRaises(ValueError, api.refresh_token)

    @patch("taiga.client.requests.post")
    def test_refresh_token_passed_token(self, requests_post):
        requests_post.return_value = MockResponse(
            200, create_mock_json("tests/resources/auth_refresh_token_success.json")
        )
        api = TaigaAPI(host="host")
        api.refresh_token("testToken")
        requests_post.assert_called_with(
            "host/api/v1/auth/refresh",
            data='{"refresh": "testToken"}',
            headers={"Content-type": "application/json"},
            verify=True,
        )

    @patch("taiga.client.requests.post")
    def test_refresh_token_with_auth(self, requests_post):
        requests_post.return_value = MockResponse(200, create_mock_json("tests/resources/auth_user_success.json"))
        api = TaigaAPI(host="host")
        api.auth("valid_user", "valid_password")
        self.assertEqual(api.token, "f4k3")
        self.assertEqual(api.token_refresh, "j5l4")
        requests_post.reset_mock()
        requests_post.return_value = MockResponse(
            200, create_mock_json("tests/resources/auth_refresh_token_success.json")
        )
        api.refresh_token()
        self.assertEqual(api.token, "newToken")
        self.assertEqual(api.token_refresh, "newRefreshToken")
