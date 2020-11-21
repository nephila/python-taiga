import unittest
from unittest.mock import patch

from taiga.models import Role, Roles
from taiga.requestmaker import RequestMaker


class TestRoles(unittest.TestCase):
    @patch("taiga.models.base.ListResource._new_resource")
    def test_create_role(self, mock_new_resource):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        mock_new_resource.return_value = Role(rm)
        Roles(rm).create(1, "RL 1")
        mock_new_resource.assert_called_with(payload={"project": 1, "name": "RL 1"})
