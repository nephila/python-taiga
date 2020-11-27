import unittest
from unittest.mock import patch

from taiga.models import Point, Points
from taiga.requestmaker import RequestMaker


class TestPoints(unittest.TestCase):
    @patch("taiga.models.base.ListResource._new_resource")
    def test_create_point(self, mock_new_resource):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        mock_new_resource.return_value = Point(rm)
        Points(rm).create(1, "Point 1", 4)
        mock_new_resource.assert_called_with(payload={"project": 1, "name": "Point 1", "value": 4})
