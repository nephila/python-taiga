import unittest
from unittest.mock import patch

from taiga.exceptions import TaigaException
from taiga.models import Task, Tasks
from taiga.requestmaker import RequestMaker
from tests.tools import MockResponse, create_mock_json

import_open = "builtins.open"


class TestTasks(unittest.TestCase):
    @patch("taiga.requestmaker.RequestMaker.get")
    def test_list_attachments(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/tasks_list_success.json")
        )
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        Task(rm, id=1).list_attachments()
        mock_requestmaker_get.assert_called_with("tasks/attachments", query={"object_id": 1}, paginate=True)

    @patch(import_open)
    @patch("taiga.models.base.ListResource._new_resource")
    def test_file_attach(self, mock_new_resource, mock_open):
        fd = open("tests/resources/tasks_list_success.json")
        mock_open.return_value = fd
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        task = Task(rm, id=1, project=1)
        task.attach("tests/resources/tasks_list_success.json")
        mock_new_resource.assert_called_with(files={"attached_file": fd}, payload={"project": 1, "object_id": 1})

    @patch("taiga.models.base.ListResource._new_resource")
    def test_open_file_attach(self, mock_new_resource):
        fd = open("tests/resources/tasks_list_success.json")
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        task = Task(rm, id=1, project=1)
        task.attach(fd)
        mock_new_resource.assert_called_with(files={"attached_file": fd}, payload={"project": 1, "object_id": 1})

    def test_not_existing_file_attach(self):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        task = Task(rm, id=1, project=1)
        self.assertRaises(TaigaException, task.attach, "not-existing-file")

    def test_not_valid_type_file_attach(self):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        task = Task(rm, id=1, project=1)
        self.assertRaises(TaigaException, task.attach, 4)

    @patch("taiga.requestmaker.RequestMaker.post")
    def test_import_task(self, mock_requestmaker_post):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        Tasks(rm).import_(1, "Subject", "New")
        mock_requestmaker_post.assert_called_with(
            "/{endpoint}/{id}/{type}",
            endpoint="importer",
            payload={"project": 1, "subject": "Subject", "status": "New"},
            id=1,
            type="task",
        )

    @patch("taiga.models.base.InstanceResource.update")
    def test_add_comment(self, mock_update):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        task = Task(rm, id=1)
        task.add_comment("hola")
        mock_update.assert_called_with(comment="hola")
