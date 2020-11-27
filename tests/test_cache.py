import unittest
from unittest.mock import patch

from taiga.requestmaker import RequestCache, RequestCacheInvalidException, RequestCacheMissingException, RequestMaker

from .tools import MockResponse


class TestRequestCache(unittest.TestCase):
    def test_cache_put_get(self):
        cache = RequestCache()
        cache.put("http://ciao", "value")
        self.assertEqual(cache.get("http://ciao"), "value")
        self.assertRaises(RequestCacheMissingException, cache.get, "http://hola")

    def test_cache_remove(self):
        cache = RequestCache()
        cache.put("http://ciao", "value")
        self.assertEqual(cache.get("http://ciao"), "value")
        cache.remove("http://ciao")
        self.assertRaises(RequestCacheMissingException, cache.get, "http://ciao")

    @patch("time.time")
    def test_cache_valid_time(self, mock_time):
        mock_time.return_value = 0
        cache = RequestCache(valid_time=100)
        cache.put("http://ciao", "value")
        self.assertEqual(cache.get("http://ciao"), "value")
        mock_time.return_value = 101
        self.assertRaises(RequestCacheInvalidException, cache.get, "http://ciao")

    @patch("taiga.requestmaker.requests.get")
    @patch("time.time")
    def test_call_requests_get_with_cache(self, mock_time, requests_get):
        mock_time.return_value = 0
        rm = RequestMaker(api_path="/", host="host", token="f4k3")
        requests_get.return_value = MockResponse(200, "")
        rm.get("/nowhere", cache=True)
        self.assertEqual(requests_get.call_count, 1)
        rm.get("/nowhere", cache=True)
        self.assertEqual(requests_get.call_count, 1)
        rm.get("/nowhere", cache=False)
        self.assertEqual(requests_get.call_count, 2)
        rm.get("/nowhere", cache=True)
        self.assertEqual(requests_get.call_count, 2)
        mock_time.return_value = 61
        rm.get("/nowhere", cache=True)
        self.assertEqual(requests_get.call_count, 3)
