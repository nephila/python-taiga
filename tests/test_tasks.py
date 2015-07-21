from taiga.requestmaker import RequestMaker
from taiga.models import Task, Tasks
import unittest
from mock import patch
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

    @patch('taiga.requestmaker.RequestMaker.post')
    def test_import_task(self, mock_requestmaker_post):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        task = Tasks(rm).import_(1, 'Subject', 'New')
        mock_requestmaker_post.assert_called_with(
            '/{endpoint}/{id}/{type}', endpoint='importer', payload={'project': 1,
                                                                     'subject': 'Subject',
                                                                     'status': 'New'},
            id=1, type='task'
        )
