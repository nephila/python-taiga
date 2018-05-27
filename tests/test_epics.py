from taiga.requestmaker import RequestMaker
from taiga.models import Epic, Epics
from taiga.exceptions import TaigaException
import unittest
from mock import patch
import six
from taiga import TaigaAPI
from .tools import create_mock_json
from .tools import MockResponse

if six.PY2:
    import_open = '__builtin__.open'
else:
    import_open = 'builtins.open'


class TestEpics(unittest.TestCase):

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_list_attachments(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(200,
            create_mock_json('tests/resources/epics_list_success.json'))
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        Epic(rm, id=1).list_attachments()
        mock_requestmaker_get.assert_called_with(
            'epics/attachments',
            query={"object_id": 1},
            paginate=True
        )

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_single_epic_parsing(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(200,
            create_mock_json('tests/resources/epic_details_success.json'))
        api = TaigaAPI(token='f4k3')
        epic = api.epics.get(1)
        self.assertEqual(epic.description, 'Description of the epic')

    @patch('taiga.requestmaker.RequestMaker.get')
    def test_list_epics_parsing(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(200,
            create_mock_json('tests/resources/epics_list_success.json'))
        api = TaigaAPI(token='f4k3')
        epics = api.epics.list()
        print(epics)
        self.assertEqual(epics[0].description, 'Description of the Epic')
        self.assertEqual(len(epics), 1)

    @patch(import_open)
    @patch('taiga.models.base.ListResource._new_resource')
    def test_file_attach(self, mock_new_resource, mock_open):
        fd = open('tests/resources/tasks_list_success.json')
        mock_open.return_value = fd
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        epic = Epic(rm, id=1, project=1)
        epic.attach('tests/resources/tasks_list_success.json')
        mock_new_resource.assert_called_with(
            files={'attached_file': fd},
            payload={'project': 1, 'object_id': 1}
        )

    @patch('taiga.models.base.ListResource._new_resource')
    def test_open_file_attach(self, mock_new_resource):
        fd = open('tests/resources/tasks_list_success.json')
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        epic = Epic(rm, id=1, project=1)
        epic.attach(fd)
        mock_new_resource.assert_called_with(
            files={'attached_file': fd},
            payload={'project': 1, 'object_id': 1}
        )

    def test_not_existing_file_attach(self):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        epic = Epic(rm, id=1, project=1)
        self.assertRaises(TaigaException, epic.attach, 'not-existing-file')

    def test_not_valid_type_file_attach(self):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        epic = Epic(rm, id=1, project=1)
        self.assertRaises(TaigaException, epic.attach, 4)

    @patch('taiga.models.base.ListResource._new_resource')
    def test_create_epic(self, mock_new_resource):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        mock_new_resource.return_value = Epic(rm)
        epic = Epics(rm).create(1, 'Epic 1')
        mock_new_resource.assert_called_with(
            payload={'project': 1, 'subject': 'Epic 1'}
        )

    @patch('taiga.requestmaker.RequestMaker.post')
    def test_import_epic(self, mock_requestmaker_post):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        epic = Epics(rm).import_(1, 'Epic 1', 'New')
        mock_requestmaker_post.assert_called_with(
            '/{endpoint}/{id}/{type}', payload={'status': 'New', 'project': 1,
                                                'subject': 'Epic 1'},
            endpoint='importer', type='ep', id=1
        )

    @patch('taiga.models.base.InstanceResource.update')
    def test_add_comment(self, mock_update):
        rm = RequestMaker('/api/v1', 'fakehost', 'faketoken')
        epic = Epic(rm, id=1)
        epic.add_comment('hola')
        mock_update.assert_called_with(
            comment='hola'
        )
