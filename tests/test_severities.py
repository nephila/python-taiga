from taiga.requestmaker import RequestMaker
from taiga.models import Severity, Severities
import unittest
from mock import patch


class TestSeverities(unittest.TestCase):

    @patch('taiga.models.base.ListResource._new_resource')
    def test_create_severity(self, mock_new_resource):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        mock_new_resource.return_value = Severity(rm)
        sv = Severities(rm).create(1, 'SV 1')
        mock_new_resource.assert_called_with(
            payload={'project': 1, 'name': 'SV 1'}
        )
