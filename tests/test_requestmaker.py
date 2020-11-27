import unittest
from unittest.mock import patch

import requests

import taiga.exceptions
from taiga.requestmaker import RequestMaker

from .tools import MockResponse


class TestRequestMaker(unittest.TestCase):
    @patch("taiga.requestmaker.requests.get")
    def test_call_requests_get(self, requests_get):
        rm = RequestMaker(api_path="/", host="host", token="f4k3")
        requests_get.return_value = MockResponse(200, "")
        rm.get("/nowhere")
        self.assertTrue(requests_get.called)

    @patch("taiga.requestmaker.requests.post")
    def test_call_requests_post(self, requests_post):
        rm = RequestMaker(api_path="/", host="host", token="f4k3")
        requests_post.return_value = MockResponse(200, "")
        rm.post("/nowhere")
        self.assertTrue(requests_post.called)

    @patch("taiga.requestmaker.requests.post")
    def test_call_requests_post_with_files(self, requests_post):
        rm = RequestMaker(api_path="/v1/", host="http://host", token="f4k3")
        requests_post.return_value = MockResponse(200, "")
        file_desc = open("tests/resources/fake_objects.json")
        rm.post("nowhere", files={"sample": file_desc})
        requests_post.assert_called_once_with(
            "http://host/v1/nowhere",
            files={"sample": file_desc},
            verify=True,
            data=None,
            params={},
            headers={"Authorization": "Bearer f4k3", "x-disable-pagination": "True"},
        )

    @patch("taiga.requestmaker.requests.put")
    def test_call_requests_put(self, requests_put):
        rm = RequestMaker(api_path="/", host="host", token="f4k3")
        requests_put.return_value = MockResponse(200, "")
        rm.put("/nowhere")
        self.assertTrue(requests_put.called)

    @patch("taiga.requestmaker.requests.patch")
    def test_call_requests_patch(self, requests_patch):
        rm = RequestMaker(api_path="/", host="host", token="f4k3")
        requests_patch.return_value = MockResponse(200, "")
        rm.patch("/nowhere")
        self.assertTrue(requests_patch.called)

    @patch("taiga.requestmaker.requests.delete")
    def test_call_requests_delete(self, requests_delete):
        rm = RequestMaker(api_path="/", host="host", token="f4k3")
        requests_delete.return_value = MockResponse(200, "")
        rm.delete("/nowhere")
        self.assertTrue(requests_delete.called)

    @patch("taiga.requestmaker.requests.get")
    def test_call_requests_get_raise_exception_on_bad_response(self, requests_get):
        rm = RequestMaker(api_path="/", host="host", token="f4k3")
        requests_get.return_value = MockResponse(400, "")
        self.assertRaises(taiga.exceptions.TaigaRestException, rm.get, "/nowhere")

    @patch("taiga.requestmaker.requests.post")
    def test_call_requests_post_raise_exception_on_bad_response(self, requests_post):
        rm = RequestMaker(api_path="/", host="host", token="f4k3")
        requests_post.return_value = MockResponse(400, "")
        self.assertRaises(taiga.exceptions.TaigaRestException, rm.post, "/nowhere")

    @patch("taiga.requestmaker.requests.put")
    def test_call_requests_put_raise_exception_on_bad_response(self, requests_put):
        rm = RequestMaker(api_path="/", host="host", token="f4k3")
        requests_put.return_value = MockResponse(400, "")
        self.assertRaises(taiga.exceptions.TaigaRestException, rm.put, "/nowhere")

    @patch("taiga.requestmaker.requests.patch")
    def test_call_requests_patch_raise_exception_on_bad_response(self, requests_patch):
        rm = RequestMaker(api_path="/", host="host", token="f4k3")
        requests_patch.return_value = MockResponse(400, "")
        self.assertRaises(taiga.exceptions.TaigaRestException, rm.patch, "/nowhere")

    @patch("taiga.requestmaker.requests.delete")
    def test_call_requests_delete_raise_exception_on_bad_response(self, requests_delete):
        rm = RequestMaker(api_path="/", host="host", token="f4k3")
        requests_delete.return_value = MockResponse(400, "")
        self.assertRaises(taiga.exceptions.TaigaRestException, rm.delete, "/nowhere")

    @patch("taiga.requestmaker.requests.get")
    def test_call_requests_get_raise_exception_on_requests_error(self, requests_get):
        rm = RequestMaker(api_path="/", host="host", token="f4k3")
        requests_get.side_effect = requests.RequestException()
        self.assertRaises(taiga.exceptions.TaigaRestException, rm.get, "/nowhere")

    @patch("taiga.requestmaker.requests.post")
    def test_call_requests_post_raise_exception_on_requests_error(self, requests_post):
        rm = RequestMaker(api_path="/", host="host", token="f4k3")
        requests_post.side_effect = requests.RequestException()
        self.assertRaises(taiga.exceptions.TaigaRestException, rm.post, "/nowhere")

    @patch("taiga.requestmaker.requests.put")
    def test_call_requests_put_raise_exception_on_requests_error(self, requests_put):
        rm = RequestMaker(api_path="/", host="host", token="f4k3")
        requests_put.side_effect = requests.RequestException()
        self.assertRaises(taiga.exceptions.TaigaRestException, rm.put, "/nowhere")

    @patch("taiga.requestmaker.requests.patch")
    def test_call_requests_patch_raise_exception_on_requests_error(self, requests_patch):
        rm = RequestMaker(api_path="/", host="host", token="f4k3")
        requests_patch.side_effect = requests.RequestException()
        self.assertRaises(taiga.exceptions.TaigaRestException, rm.patch, "/nowhere")

    @patch("taiga.requestmaker.requests.delete")
    def test_call_requests_delete_raise_exception_on_requests_error(self, requests_delete):
        rm = RequestMaker(api_path="/", host="host", token="f4k3")
        requests_delete.side_effect = requests.RequestException()
        self.assertRaises(taiga.exceptions.TaigaRestException, rm.delete, "/nowhere")
