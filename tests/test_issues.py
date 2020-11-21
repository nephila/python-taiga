import unittest
from unittest.mock import patch

from taiga.exceptions import TaigaException
from taiga.models import Issue, Issues
from taiga.requestmaker import RequestMaker

from .tools import MockResponse, create_mock_json

import_open = "builtins.open"


class TestIssues(unittest.TestCase):
    @patch("taiga.requestmaker.RequestMaker.get")
    def test_list_attachments(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/issues_list_success.json")
        )
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        Issue(rm, id=1).list_attachments()
        mock_requestmaker_get.assert_called_with("issues/attachments", query={"object_id": 1}, paginate=True)

    @patch("taiga.requestmaker.RequestMaker.post")
    def test_upvote(self, mock_requestmaker_post):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        issue = Issue(rm, id=1)
        self.assertEqual(issue.upvote().id, 1)
        mock_requestmaker_post.assert_called_with("/{endpoint}/{id}/upvote", endpoint="issues", id=1)

    @patch("taiga.requestmaker.RequestMaker.post")
    def test_downvote(self, mock_requestmaker_post):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        issue = Issue(rm, id=1)
        self.assertEqual(issue.downvote().id, 1)
        mock_requestmaker_post.assert_called_with("/{endpoint}/{id}/downvote", endpoint="issues", id=1)

    @patch("taiga.requestmaker.RequestMaker.post")
    def test_issue_creation(self, mock_requestmaker_post):
        mock_requestmaker_post.return_value = MockResponse(
            200, create_mock_json("tests/resources/issue_details_success.json")
        )
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        issue = Issues(rm).create(1, 2, 3, 4, 5, 6)
        self.assertTrue(isinstance(issue, Issue))

    @patch("taiga.requestmaker.RequestMaker.post")
    def test_issue_import(self, mock_requestmaker_post):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        Issues(rm).import_(1, "subject", "Normal", "Closed", "Normal", "Wishlist")
        mock_requestmaker_post.assert_called_with(
            "/{endpoint}/{id}/{type}",
            type="issue",
            payload={
                "type": "Normal",
                "project": 1,
                "subject": "subject",
                "priority": "Normal",
                "status": "Closed",
                "severity": "Wishlist",
            },
            endpoint="importer",
            id=1,
        )

    @patch(import_open)
    @patch("taiga.models.base.ListResource._new_resource")
    def test_file_attach(self, mock_new_resource, mock_open):
        fd = open("tests/resources/tasks_list_success.json")
        mock_open.return_value = fd
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        issue = Issue(rm, id=1, project=1)
        issue.attach("tests/resources/tasks_list_success.json")
        mock_new_resource.assert_called_with(files={"attached_file": fd}, payload={"project": 1, "object_id": 1})

    @patch("taiga.models.base.ListResource._new_resource")
    def test_open_file_attach(self, mock_new_resource):
        fd = open("tests/resources/tasks_list_success.json")
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        issue = Issue(rm, id=1, project=1)
        issue.attach(fd)
        mock_new_resource.assert_called_with(files={"attached_file": fd}, payload={"project": 1, "object_id": 1})

    def test_not_existing_file_attach(self):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        issue = Issue(rm, id=1, project=1)
        self.assertRaises(TaigaException, issue.attach, "not-existing-file")

    def test_not_valid_type_file_attach(self):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        issue = Issue(rm, id=1, project=1)
        self.assertRaises(TaigaException, issue.attach, 4)

    @patch("taiga.models.base.InstanceResource.update")
    def test_add_comment(self, mock_update):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        issue = Issue(rm, id=1)
        issue.add_comment("hola")
        mock_update.assert_called_with(comment="hola")
