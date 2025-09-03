import unittest
from unittest.mock import patch

import requests

import taiga.exceptions
from taiga import TaigaAPI

from .tools import MockResponse, create_mock_json


class TestAuthApp(unittest.TestCase):
    @patch("taiga.client.requests")
    def test_auth_success(self, requests):
        requests.post.return_value = MockResponse(200, create_mock_json("tests/resources/auth_app_success.json"))
        api = TaigaAPI(host="host")
        token = api.auth_app("valid-app-id", "valid-auth-code", "valid-state")
        self.assertEqual(token, "eyJhcHBfdG9rZW5faWQiOjN9:1utpZt:fXS-ifJ6TGWQEy7IkkxemDPGM5jXTOYYn7heGf8MFWU")

    @patch("taiga.client.requests")
    def test_auth_not_success(self, requests):
        requests.post.return_value = MockResponse(401, "Not allowed")
        api = TaigaAPI(host="host")
        self.assertRaises(
            taiga.exceptions.TaigaRestException,
            api.auth_app,
            "valid-app-id",
            "valid-auth-code",
            "valid-state",
        )

    @patch("taiga.client.requests.post")
    def test_auth_connection_error(self, requests_post):
        requests_post.side_effect = requests.RequestException()
        api = TaigaAPI(host="host")
        self.assertRaises(
            taiga.exceptions.TaigaRestException,
            api.auth_app,
            "valid-app-id",
            "valid-auth-code",
            "valid-state",
        )
