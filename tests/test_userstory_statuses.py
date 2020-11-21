import unittest
from unittest.mock import patch

from taiga.models import UserStoryStatus, UserStoryStatuses
from taiga.requestmaker import RequestMaker


class TestPriorities(unittest.TestCase):
    @patch("taiga.models.base.ListResource._new_resource")
    def test_create_user_story_status(self, mock_new_resource):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        mock_new_resource.return_value = UserStoryStatus(rm)
        UserStoryStatuses(rm).create(1, "USS 1")
        mock_new_resource.assert_called_with(payload={"project": 1, "name": "USS 1"})
