import unittest
from unittest.mock import patch

from taiga import TaigaAPI
from taiga.exceptions import TaigaException
from taiga.models import Epic, Epics, UserStory
from taiga.requestmaker import RequestMaker

from .tools import MockResponse, create_mock_json

import_open = "builtins.open"


class TestEpics(unittest.TestCase):
    @patch("taiga.requestmaker.RequestMaker.get")
    def test_list_attachments(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/epics_list_success.json")
        )
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        Epic(rm, id=1).list_attachments()
        mock_requestmaker_get.assert_called_with("epics/attachments", query={"object_id": 1}, paginate=True)

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_single_epic_parsing(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/epic_details_success.json")
        )
        api = TaigaAPI(token="f4k3")
        epic = api.epics.get(1)
        self.assertEqual(epic.description, "Description of the epic")

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_list_epics_parsing(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/epics_list_success.json")
        )
        api = TaigaAPI(token="f4k3")
        epics = api.epics.list()
        print(epics)
        # TODO: check this:
        # self.assertEqual(epics[0].description, 'Description of the Epic')
        self.assertEqual(len(epics), 1)

    @patch(import_open)
    @patch("taiga.models.base.ListResource._new_resource")
    def test_file_attach(self, mock_new_resource, mock_open):
        fd = open("tests/resources/tasks_list_success.json")
        mock_open.return_value = fd
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        epic = Epic(rm, id=1, project=1)
        epic.attach("tests/resources/tasks_list_success.json")
        mock_new_resource.assert_called_with(files={"attached_file": fd}, payload={"project": 1, "object_id": 1})

    @patch("taiga.models.base.ListResource._new_resource")
    def test_open_file_attach(self, mock_new_resource):
        fd = open("tests/resources/tasks_list_success.json")
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        epic = Epic(rm, id=1, project=1)
        epic.attach(fd)
        mock_new_resource.assert_called_with(files={"attached_file": fd}, payload={"project": 1, "object_id": 1})

    def test_not_existing_file_attach(self):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        epic = Epic(rm, id=1, project=1)
        self.assertRaises(TaigaException, epic.attach, "not-existing-file")

    def test_not_valid_type_file_attach(self):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        epic = Epic(rm, id=1, project=1)
        self.assertRaises(TaigaException, epic.attach, 4)

    @patch("taiga.models.base.ListResource._new_resource")
    def test_create_epic(self, mock_new_resource):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        mock_new_resource.return_value = Epic(rm)
        Epics(rm).create(1, "Epic 1")
        mock_new_resource.assert_called_with(payload={"project": 1, "subject": "Epic 1"})

    @patch("taiga.models.base.InstanceResource.update")
    def test_add_comment(self, mock_update):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        epic = Epic(rm, id=1)
        epic.add_comment("hola")
        mock_update.assert_called_with(comment="hola")

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_list_related_user_stories(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/epic_related_userstories_success.json")
        )
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        relations = Epic(rm, id=1, project=1).list_related_user_stories()
        self.assertEqual([relation["user_story"] for relation in relations], [7, 8])
        mock_requestmaker_get.assert_called_with(
            "/{endpoint}/{id}/related_userstories", endpoint=Epic.endpoint, id=1, query={}
        )

    @patch("taiga.requestmaker.RequestMaker.post")
    def test_add_user_story(self, mock_requestmaker_post):
        mock_requestmaker_post.return_value = MockResponse(
            200, create_mock_json("tests/resources/epic_related_userstory_success.json")
        )
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        relation = Epic(rm, id=1, project=1).add_user_story(7)
        self.assertEqual(relation["user_story"], 7)
        mock_requestmaker_post.assert_called_with(
            "/{endpoint}/{id}/related_userstories",
            endpoint=Epic.endpoint,
            id=1,
            payload={"epic": 1, "user_story": 7},
        )

    @patch("taiga.requestmaker.RequestMaker.post")
    def test_add_user_story_instance(self, mock_requestmaker_post):
        mock_requestmaker_post.return_value = MockResponse(
            200, create_mock_json("tests/resources/epic_related_userstory_success.json")
        )
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        Epic(rm, id=1, project=1).add_user_story(UserStory(rm, id=7), order=3)
        mock_requestmaker_post.assert_called_with(
            "/{endpoint}/{id}/related_userstories",
            endpoint=Epic.endpoint,
            id=1,
            payload={"order": 3, "epic": 1, "user_story": 7},
        )

    @patch("taiga.requestmaker.RequestMaker.delete")
    def test_remove_user_story(self, mock_requestmaker_delete):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        Epic(rm, id=1, project=1).remove_user_story(7)
        mock_requestmaker_delete.assert_called_with(
            "/{endpoint}/{id}/related_userstories/{user_story}",
            endpoint=Epic.endpoint,
            id=1,
            user_story=7,
        )
