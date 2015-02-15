from taiga.requestmaker import RequestMaker
from taiga.models import Point, Points
import unittest
from mock import patch


class TestPoints(unittest.TestCase):

    @patch('taiga.models.base.ListResource._new_resource')
    def test_create_point(self, mock_new_resource):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        mock_new_resource.return_value = Point(rm)
        point = Points(rm).create(1, 'Point 1', 4)
        mock_new_resource.assert_called_with(
            payload={'project': 1, 'name': 'Point 1', 'value': 4}
        )

