from taiga.requestmaker import RequestMaker, RequestMakerException
from taiga.models.base import InstanceResource, ListResource
from taiga.models import Task
from taiga import TaigaAPI
import taiga.exceptions
import json
import requests
import unittest
from mock import patch
from .tools import create_mock_json
from .tools import MockResponse
import six

if six.PY2:
    import_open = '__builtin__.open'
else:
    import_open = 'builtins.open'

class TestTasks(unittest.TestCase):

    @patch(import_open)
    @patch('taiga.models.base.ListResource._new_resource')
    def test_file_attach(self, mock_new_resource, mock_open):
        fd = open('tests/resources/tasks_list_success.json')
        mock_open.return_value = fd
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        task = Task(rm, id=1, project=1)
        task.attach('tests/resources/tasks_list_success.json')
        mock_new_resource.assert_called_with(
            files={'attached_file': fd},
            payload={'project': 1, 'object_id': 1}
        )