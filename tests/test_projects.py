import unittest
from datetime import datetime
from unittest.mock import patch

from taiga import TaigaAPI
from taiga.models import Point, Project, Projects, Severity, SwimLane, User, UserStoryStatus
from taiga.requestmaker import RequestMaker

from .tools import MockResponse, create_mock_json


class TestProjects(unittest.TestCase):
    @patch("taiga.requestmaker.RequestMaker.get")
    def test_single_project_parsing(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/project_details_success.json")
        )
        api = TaigaAPI(token="f4k3")
        project = api.projects.get(1)
        self.assertEqual(project.description, "Project example 0 description")
        self.assertEqual(len(project.members), 11)
        self.assertTrue(isinstance(project.members[0], User))
        self.assertTrue(isinstance(project.points[0], Point))
        self.assertTrue(isinstance(project.swimlanes[0], SwimLane))
        self.assertTrue(isinstance(project.us_statuses[0], UserStoryStatus))
        self.assertTrue(isinstance(project.severities[0], Severity))

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_list_projects_parsing(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/projects_list_success.json")
        )
        api = TaigaAPI(token="f4k3")
        projects = api.projects.list()
        self.assertEqual(projects[0].description, "Project example 0 description")
        self.assertEqual(len(projects), 1)

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_get_project_by_slug(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/project_details_success.json")
        )
        api = TaigaAPI(token="f4k3")
        project = api.projects.get_by_slug("my_slug")
        self.assertTrue(isinstance(project, Project))
        self.assertEqual(project.name, "Project Example 0")
        mock_requestmaker_get.assert_called_with(
            "/{endpoint}/by_slug?slug={slug}", endpoint="projects", slug="my_slug"
        )

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_get_project_by_slug_no_swimlanes(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/project_details_success_no_swimlanes.json")
        )
        api = TaigaAPI(token="f4k3")
        project = api.projects.get_by_slug("my_slug")
        self.assertTrue(isinstance(project, Project))
        self.assertEqual(project.name, "Project Example 0")
        mock_requestmaker_get.assert_called_with(
            "/{endpoint}/by_slug?slug={slug}", endpoint="projects", slug="my_slug"
        )

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_get_item_by_ref(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/project_details_success.json")
        )
        api = TaigaAPI(token="f4k3")
        project = api.projects.get_by_slug("my_slug")
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/projects_resolve_us.json")
        )
        with patch.object(project, "get_userstory_by_ref") as mock_get_userstory_by_ref:
            mock_get_userstory_by_ref.return_value = MockResponse(
                200, create_mock_json("tests/resources/userstory_details_success.json")
            )
            project.get_item_by_ref(1)
            mock_get_userstory_by_ref.assert_called_with(1)

        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/projects_resolve_issue.json")
        )
        with patch.object(project, "get_issue_by_ref") as mock_get_issue_by_ref:
            mock_get_issue_by_ref.return_value = MockResponse(
                200, create_mock_json("tests/resources/issue_details_success.json")
            )
            project.get_item_by_ref(1)
            mock_get_issue_by_ref.assert_called_with(1)

        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/projects_resolve_task.json")
        )
        with patch.object(project, "get_task_by_ref") as mock_get_task_by_ref:
            mock_get_task_by_ref.return_value = MockResponse(
                200, create_mock_json("tests/resources/task_details_success.json")
            )
            project.get_item_by_ref(1)
            mock_get_task_by_ref.assert_called_with(1)

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_get_userstories_by_ref(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/userstory_details_success.json")
        )
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        TaigaAPI(token="f4k3")
        us = project.get_userstory_by_ref(1)
        self.assertEqual(us.description, "Description of the story")

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_get_tasks_by_ref(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/task_details_success.json")
        )
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        TaigaAPI(token="f4k3")
        task = project.get_task_by_ref(1)
        self.assertEqual(task.description, "Implement API CALL")

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_get_issues_by_ref(self, mock_requestmaker_get):
        mock_requestmaker_get.return_value = MockResponse(
            200, create_mock_json("tests/resources/issue_details_success.json")
        )
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        TaigaAPI(token="f4k3")
        issue = project.get_issue_by_ref(31)
        self.assertEqual(issue.description, "Implement API CALL")

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_stats(self, mock_requestmaker_get):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.stats()
        mock_requestmaker_get.assert_called_with("/{endpoint}/{id}/stats", endpoint="projects", id=1)

    @patch("taiga.requestmaker.RequestMaker.get")
    def test_issues_stats(self, mock_requestmaker_get):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.issues_stats()
        mock_requestmaker_get.assert_called_with("/{endpoint}/{id}/issues_stats", endpoint="projects", id=1)

    @patch("taiga.requestmaker.RequestMaker.post")
    def test_like(self, mock_requestmaker_post):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        self.assertEqual(project.like().id, 1)
        mock_requestmaker_post.assert_called_with("/{endpoint}/{id}/like", endpoint="projects", id=1)

    @patch("taiga.requestmaker.RequestMaker.post")
    def test_unlike(self, mock_requestmaker_post):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        self.assertEqual(project.unlike().id, 1)
        mock_requestmaker_post.assert_called_with("/{endpoint}/{id}/unlike", endpoint="projects", id=1)

    @patch("taiga.requestmaker.RequestMaker.post")
    def test_star(self, mock_requestmaker_post):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        self.assertEqual(project.star().id, 1)
        mock_requestmaker_post.assert_called_with("/{endpoint}/{id}/star", endpoint="projects", id=1)

    @patch("taiga.requestmaker.RequestMaker.post")
    def test_unstar(self, mock_requestmaker_post):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        self.assertEqual(project.unstar().id, 1)
        mock_requestmaker_post.assert_called_with("/{endpoint}/{id}/unstar", endpoint="projects", id=1)

    @patch("taiga.models.base.ListResource._new_resource")
    def test_create_project(self, mock_new_resource):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        mock_new_resource.return_value = Project(rm)
        Projects(rm).create("PR 1", "PR desc 1")
        mock_new_resource.assert_called_with(payload={"name": "PR 1", "description": "PR desc 1"})

    @patch("taiga.requestmaker.RequestMaker.post")
    def test_import_project(self, mock_requestmaker_post):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        roles = [{"name": "Role 1"}]
        Projects(rm).import_("PR 1 1", "PR 1 desc 1", roles)
        mock_requestmaker_post.assert_called_with(
            "/{endpoint}",
            payload={"description": "PR 1 desc 1", "name": "PR 1 1", "roles": [{"name": "Role 1"}]},
            endpoint="importer",
        )

    @patch("taiga.requestmaker.RequestMaker.post")
    def test_duplicate_project(self, mock_requestmaker_post):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.duplicate("PR 1 1", "PR 1 desc 1")
        mock_requestmaker_post.assert_called_with(
            "/{endpoint}/{id}/duplicate",
            payload={"name": "PR 1 1", "description": "PR 1 desc 1", "is_private": False, "users": []},
            endpoint="projects",
            id=project.id,
        )

    @patch("taiga.models.IssueStatuses.create")
    def test_add_issue_status(self, mock_new_issue_status):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_issue_status("Issue 1")
        mock_new_issue_status.assert_called_with(1, "Issue 1")

    @patch("taiga.models.IssueStatuses.list")
    def test_list_issue_statuses(self, mock_list_issue_statuses):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_issue_statuses()
        mock_list_issue_statuses.assert_called_with(project=1)

    @patch("taiga.models.Priorities.create")
    def test_add_priority(self, mock_new_priority):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_priority("Priority 1")
        mock_new_priority.assert_called_with(1, "Priority 1")

    @patch("taiga.models.Priorities.list")
    def test_list_priorities(self, mock_list_priorities):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_priorities()
        mock_list_priorities.assert_called_with(project=1)

    @patch("taiga.models.Severities.create")
    def test_add_severity(self, mock_new_severity):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_severity("Severity 1")
        mock_new_severity.assert_called_with(1, "Severity 1")

    @patch("taiga.models.Severities.list")
    def test_list_severities(self, mock_list_severities):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_severities()
        mock_list_severities.assert_called_with(project=1)

    @patch("taiga.models.Roles.create")
    def test_add_role(self, mock_new_role):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_role("Role 1")
        mock_new_role.assert_called_with(1, "Role 1")

    @patch("taiga.models.Roles.list")
    def test_list_roles(self, mock_list_roles):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_roles()
        mock_list_roles.assert_called_with(project=1)

    @patch("taiga.models.models.IssueTypes.create")
    def test_add_issue_type(self, mock_new_issue_type):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_issue_type("Severity 1")
        mock_new_issue_type.assert_called_with(1, "Severity 1")

    @patch("taiga.models.models.IssueTypes.list")
    def test_list_issue_types(self, mock_list_issue_types):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_issue_types()
        mock_list_issue_types.assert_called_with(project=1)

    @patch("taiga.models.UserStoryStatuses.create")
    def test_add_us_status(self, mock_new_us_status):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_user_story_status("US status 1")
        mock_new_us_status.assert_called_with(1, "US status 1")

    @patch("taiga.models.UserStoryStatuses.list")
    def test_list_us_statuses(self, mock_list_us_statuses):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_user_story_statuses()
        mock_list_us_statuses.assert_called_with(project=1)

    @patch("taiga.models.TaskStatuses.create")
    def test_add_task_status(self, mock_new_task_status):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_task_status("Task status 1")
        mock_new_task_status.assert_called_with(1, "Task status 1")

    @patch("taiga.models.TaskStatuses.list")
    def test_list_task_statuses(self, mock_list_task_statuses):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_task_statuses()
        mock_list_task_statuses.assert_called_with(project=1)

    @patch("taiga.models.SwimLanes.create")
    def test_add_swimlane(self, mock_new_swimlane):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_swimlane("SwimLane 1")
        mock_new_swimlane.assert_called_with(1, "SwimLane 1")

    @patch("taiga.models.SwimLanes.list")
    def test_list_swimlanes(self, mock_list_swimlanes):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_swimlanes()
        mock_list_swimlanes.assert_called_with(project=1)

    @patch("taiga.models.Points.create")
    def test_add_point(self, mock_new_point):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_point("Point 1", 1.5)
        mock_new_point.assert_called_with(1, "Point 1", 1.5)

    @patch("taiga.models.Points.list")
    def test_list_points(self, mock_list_points):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_points()
        mock_list_points.assert_called_with(project=1)

    @patch("taiga.models.Milestones.create")
    def test_add_milestone(self, mock_new_milestone):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        time1 = datetime.now()
        time2 = datetime.now()
        project.add_milestone("Milestone 1", time1, time2)
        mock_new_milestone.assert_called_with(1, "Milestone 1", time1, time2)

    @patch("taiga.models.Milestones.import_")
    def test_import_milestone(self, mock_import_milestone):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        time1 = datetime.now()
        time2 = datetime.now()
        project.import_milestone("Milestone 1", time1, time2)
        mock_import_milestone.assert_called_with(1, "Milestone 1", time1, time2)

    @patch("taiga.models.Milestones.list")
    def test_list_milestones(self, mock_list_milestones):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_milestones(subject="foo")
        mock_list_milestones.assert_called_with(project=1, subject="foo")

    @patch("taiga.models.Issues.create")
    def test_add_issue(self, mock_new_issue):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_issue("Issue 1", 1, 2, 3, 4)
        mock_new_issue.assert_called_with(1, "Issue 1", 1, 2, 3, 4)

    @patch("taiga.models.Issues.import_")
    def test_import_issue(self, mock_import_issue):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.import_issue("Issue 1", 1, 2, 3, 4)
        mock_import_issue.assert_called_with(1, "Issue 1", 1, 2, 3, 4)

    @patch("taiga.models.Issues.list")
    def test_list_issues(self, mock_list_issues):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_issues()
        mock_list_issues.assert_called_with(project=1)

    @patch("taiga.models.UserStories.create")
    def test_add_userstory(self, mock_new_userstory):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_user_story("US 1")
        mock_new_userstory.assert_called_with(1, "US 1")

    @patch("taiga.models.UserStories.import_")
    def test_import_userstory(self, mock_import_userstory):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.import_user_story("US 1", "Closed")
        mock_import_userstory.assert_called_with(1, "US 1", "Closed")

    @patch("taiga.models.UserStories.list")
    def test_list_userstories(self, mock_list_userstories):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_user_stories()
        mock_list_userstories.assert_called_with(project=1)

    @patch("taiga.models.WikiPages.create")
    def test_add_wikipage(self, mock_new_wikipage):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_wikipage("WP 1", "Content")
        mock_new_wikipage.assert_called_with(1, "WP 1", "Content")

    @patch("taiga.models.WikiPages.import_")
    def test_import_wikipage(self, mock_import_wikipage):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.import_wikipage("Slug 1", "Content")
        mock_import_wikipage.assert_called_with(1, "Slug 1", "Content")

    @patch("taiga.models.WikiPages.list")
    def test_list_wikipages(self, mock_list_wikipages):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_wikipages()
        mock_list_wikipages.assert_called_with(project=1)

    @patch("taiga.models.WikiLinks.create")
    def test_add_wikilink(self, mock_new_wikilink):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_wikilink("WL 1", "href")
        mock_new_wikilink.assert_called_with(1, "WL 1", "href")

    @patch("taiga.models.WikiLinks.import_")
    def test_import_wikilink(self, mock_import_wikilink):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.import_wikilink("WL 1", "href")
        mock_import_wikilink.assert_called_with(1, "WL 1", "href")

    @patch("taiga.models.WikiLinks.list")
    def test_list_wikilinks(self, mock_list_wikilinks):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_wikilinks()
        mock_list_wikilinks.assert_called_with(project=1)

    @patch("taiga.models.IssueAttributes.create")
    def test_add_issue_attribute(self, mock_new_issue_attr):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_issue_attribute("New Attribute")
        mock_new_issue_attr.assert_called_with(1, "New Attribute")

    @patch("taiga.models.IssueAttributes.list")
    def test_list_issue_attributes(self, mock_list_issues_attr):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_issue_attributes()
        mock_list_issues_attr.assert_called_with(project=1)

    @patch("taiga.models.TaskAttributes.create")
    def test_add_task_attribute(self, mock_new_task_attr):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_task_attribute("New Attribute")
        mock_new_task_attr.assert_called_with(1, "New Attribute")

    @patch("taiga.models.TaskAttributes.list")
    def test_list_task_attributes(self, mock_list_issues_attr):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_task_attributes()
        mock_list_issues_attr.assert_called_with(project=1)

    @patch("taiga.models.Tasks.import_")
    def test_import_task(self, mock_import_task):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.import_task("Task 1", "New")
        mock_import_task.assert_called_with(1, "Task 1", "New")

    @patch("taiga.models.UserStoryAttributes.create")
    def test_add_user_story_attribute(self, mock_new_us_attr):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_user_story_attribute("New Attribute")
        mock_new_us_attr.assert_called_with(1, "New Attribute")

    @patch("taiga.models.UserStoryAttributes.list")
    def test_list_user_story_attributes(self, mock_list_us_attr):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_user_story_attributes()
        mock_list_us_attr.assert_called_with(project=1)

    @patch("taiga.models.EpicAttributes.list")
    def test_list_epic_attributes(self, mock_list_epic_attr):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_epic_attributes()
        mock_list_epic_attr.assert_called_with(project=1)

    @patch("taiga.models.Memberships.create")
    def test_add_membership(self, mock_new_membership):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_membership("test@example.com", 1)
        mock_new_membership.assert_called_with(1, "test@example.com", 1)

    @patch("taiga.models.Memberships.list")
    def test_list_membership(self, mock_list_memberships):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_memberships()
        mock_list_memberships.assert_called_with(project=1)

    @patch("taiga.models.Webhooks.create")
    def test_add_webhook(self, mock_new_webhook):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_webhook("New Webhook", "webhook-url", "webhook-key")
        mock_new_webhook.assert_called_with(1, "New Webhook", "webhook-url", "webhook-key")

    @patch("taiga.models.Webhooks.list")
    def test_list_webhooks(self, mock_list_webhooks):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_webhooks()
        mock_list_webhooks.assert_called_with(project=1)

    @patch("taiga.models.Epics.create")
    def test_add_epic(self, mock_new_epic):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.add_epic("Epic 1")
        mock_new_epic.assert_called_with(1, "Epic 1")

    @patch("taiga.models.Epics.list")
    def test_list_epics(self, mock_list_epics):
        rm = RequestMaker("/api/v1", "fakehost", "faketoken")
        project = Project(rm, id=1)
        project.list_epics()
        mock_list_epics.assert_called_with(project=1)
