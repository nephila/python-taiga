from taiga.requestmaker import RequestMaker, RequestMakerException
from taiga.models.base import InstanceResource, ListResource
from taiga.models import Point, Points
from taiga import TaigaAPI
import taiga.exceptions
import json
import requests
import unittest
from mock import patch
from .tools import create_mock_json
from .tools import MockResponse


class TestPoints(unittest.TestCase):

    @patch('taiga.models.base.ListResource._new_resource')
    def test_create_point(self, mock_new_resource):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        mock_new_resource.return_value = Point(rm)
        point = Points(rm).create(1, 'Point 1', 4)
        mock_new_resource.assert_called_with(
            payload={'project': 1, 'name': 'Point 1', 'value': 4}
        )

