from taiga.requestmaker import RequestMaker
from taiga.models import TaskStatus, TaskStatuses
import unittest
from mock import patch


class TestTaskStatuses(unittest.TestCase):

    @patch('taiga.models.base.ListResource._new_resource')
    def test_create_task_status(self, mock_new_resource):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        mock_new_resource.return_value = TaskStatus(rm)
        ts = TaskStatuses(rm).create(1, 'TS 1')
        mock_new_resource.assert_called_with(
            payload={'project': 1, 'name': 'TS 1'}
        )

