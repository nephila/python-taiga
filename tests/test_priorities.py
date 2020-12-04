import unittest
from unittest.mock import patch

from taiga.models import Priorities, Priority
from taiga.requestmaker import RequestMaker


class TestPriorities(unittest.TestCase):
    @patch("taiga.models.base.ListResource._new_resource")
    def test_create_priority(self, mock_new_resource):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        mock_new_resource.return_value = Priority(rm)
        Priorities(rm).create(1, "Priority 1")
        mock_new_resource.assert_called_with(payload={"project": 1, "name": "Priority 1"})
