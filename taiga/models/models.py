import datetime
import warnings
from io import IOBase

from .. import exceptions
from .base import InstanceResource, ListResource


class MoveOnDestroyMixinList:
    """
    Mixin that define a delete method with moveTo parameter
    """

    def delete(self, resource_id, move_to_id):
        return super().delete(resource_id=resource_id, query={"moveTo": move_to_id})


class MoveOnDestroyMixinObject:
    """
    Mixin that define a delete method with moveTo parameter
    """

    def delete(self, move_to_id):
        return super().delete(query={"moveTo": move_to_id})


class CommentableResource(InstanceResource):
    """
    CommentableResource base class
    """

    def add_comment(self, comment):
        """
        Add a comment to the current element

        :param comment: the comment you want to insert
        """
        return self.update(comment=comment)


class CustomAttributeResource(InstanceResource):
    """
    CustomAttributeResource base class
    """

    def set_attribute(self, id, value, version=1):  # noqa: A002
        """
        Set attribute to a specific value

        :param id: id of the attribute
        :param value: value of the attribute
        :param version: version of the attribute (default = 1)
        """
        attributes = self._get_attributes(cache=True)
        formatted_id = "{}".format(id)
        attributes["attributes_values"][formatted_id] = value
        response = self.requester.patch(
            "/{endpoint}/custom-attributes-values/{id}",
            endpoint=self.endpoint,
            id=self.id,
            payload={"attributes_values": attributes["attributes_values"], "version": version},
        )
        cache_key = self.requester.get_full_url(
            "/{endpoint}/custom-attributes-values/{id}", endpoint=self.endpoint, id=self.id
        )
        self.requester.cache.put(cache_key, response)
        return response.json()

    def _get_attributes(self, cache=False):
        response = self.requester.get(
            "/{endpoint}/custom-attributes-values/{id}", endpoint=self.endpoint, id=self.id, cache=cache
        )
        return response.json()

    def get_attributes(self):
        """
        Get all the attributes of the current object
        """
        return self._get_attributes()


class CustomAttribute(InstanceResource):
    """
    CustomAttribute base class

    :param requester: :class:`Requester` instance
    :param name: name of the custom attribute
    :param description: id of the current object
    :param order: order of the custom attribute
    :param project: :class:`Project` id
    """

    repr_attribute = "name"

    allowed_params = ["name", "description", "order", "project"]


class CustomAttributes(ListResource):
    """
    CustomAttributes factory base class
    """

    def create(self, project, name, **attrs):
        """
        Create a new :class:`CustomAttribute`.

        :param project: :class:`Project` id
        :param name: name of the custom attribute
        :param attrs: optional attributes of the custom attributes
        """
        attrs.update({"project": project, "name": name})
        return self._new_resource(payload=attrs)


class User(InstanceResource):
    """
    User model
    """

    endpoint = "users"

    repr_attribute = "full_name"

    def starred_projects(self):
        """
        Get a list of starred :class:`Project`.
        """
        response = self.requester.get("/{endpoint}/{id}/starred", endpoint=self.endpoint, id=self.id)
        return Projects.parse(self.requester, response.json())


class Users(ListResource):
    """
    Users factory class
    """

    instance = User


class Membership(InstanceResource):
    """
    Membership model

    :param email: email of :class:`Membership`
    :param role: role of :class:`Membership`
    :param project: project of :class:`Membership`
    """

    endpoint = "memberships"

    allowed_params = ["email", "role", "project"]

    repr_attribute = "email"


class Memberships(ListResource):
    """
    Memberships factory class
    """

    instance = Membership

    def create(self, project, email, role, **attrs):
        """
        Create a new :class:`Membership`.

        :param project: :class:`Project` id
        :param email: email of :class:`Membership`
        :param role: role of :class:`Membership`
        :param attrs: optional attributes of :class:`Membership`
        """
        attrs.update({"project": project, "email": email, "role": role})
        return self._new_resource(payload=attrs)


class Priority(MoveOnDestroyMixinObject, InstanceResource):
    """
    Priority model

    :param name: name of :class:`Priority`
    :param color: color of the class:`Priority`
    :param order: order of the class:`Priority`
    :param project: project of the class:`Priority`
    """

    endpoint = "priorities"

    allowed_params = ["name", "color", "order", "project"]

    repr_attribute = "name"


class Priorities(MoveOnDestroyMixinList, ListResource):
    """
    Priorities factory class
    """

    instance = Priority

    def create(self, project, name, **attrs):
        """
        Create a new :class:`Priority`.

        :param project: :class:`Project` id
        :param name: email of the priority
        :param attrs: optional attributes of the priority
        """
        attrs.update({"project": project, "name": name})
        return self._new_resource(payload=attrs)


class Attachment(InstanceResource):
    """
    Attachment base class

    :param object_id: object_id of :class:`Attachment`
    :param project: project of :class:`Attachment`
    :param attached_file: attached_file of :class:`Attachment`
    :param description: description of :class:`Attachment`
    :param is_deprecated: is_deprecated of :class:`Attachment`
    """

    repr_attribute = "subject"

    allowed_params = ["object_id", "project", "attached_file", "description", "is_deprecated", "size", "name", "url"]


class Attachments(ListResource):
    """
    Attachments factory base class
    """

    def create(self, project, object_id, attached_file, **attrs):
        """
        Create a new :class:`Attachment`.

        :param project: :class:`Project` id
        :param object_id: id of the current object
        :param ref: :class:`Task` reference
        :param attached_file: file path that you want to upload
        :param attrs: optional attributes for the :class:`Attachment`
        """
        attrs.update({"project": project, "object_id": object_id})

        if isinstance(attached_file, IOBase):
            attachment = attached_file
        elif isinstance(attached_file, str):
            try:
                attachment = open(attached_file, "rb")
            except OSError:
                raise exceptions.TaigaException("Attachment must be a IOBase or a path to an existing file")
        else:
            raise exceptions.TaigaException("Attachment must be a IOBase or a path to an existing file")

        return self._new_resource(files={"attached_file": attachment}, payload=attrs)


class UserStoryAttachment(Attachment):
    """
    UserStoryAttachment class
    """

    endpoint = "userstories/attachments"


class UserStoryAttachments(Attachments):
    """
    UserStoryAttachments factory class
    """

    instance = UserStoryAttachment


class EpicAttachment(Attachment):
    """
    EpicAttachment class
    """

    endpoint = "epics/attachments"


class EpicAttachments(Attachments):
    """
    EpicAttachments factory class
    """

    instance = EpicAttachment


class Epic(CustomAttributeResource, CommentableResource):
    """
    Epic model

    :param assigned_to: assigned to property of :class:`Epic`
    :param blocked_note: blocked note of :class:`Epic`
    :param description: description of :class:`Epic` (not available in the :py:meth:`Epics.list` response)
    :param is_blocked: is blocked property of :class:`Epic`
    :param is_closed: is closed property of :class:`Epic`
    :param color: the color of :class:`Epic`
    :param project: the project of :class:`TaskStatus`
    :param subject: subject of :class:`TaskStatus`
    :param tags: tags of :class:`TaskStatus`
    :param watchers: watchers of :class:`TaskStatus`
    :param version: version of :class:`Epic`
    """

    endpoint = "epics"

    repr_attribute = "subject"

    allowed_params = [
        "assigned_to",
        "blocked_note",
        "description",
        "is_blocked",
        "is_closed",
        "color",
        "project",
        "subject",
        "tags",
        "watchers",
        "version",
    ]

    def list_user_stories(self, **queryparams):
        """
        Returns the :class:`UserStory` list of the project.
        """
        return UserStories(self.requester).list(epic=self.id, **queryparams)

    def list_attachments(self):
        """
        Get a list of :class:`EpicAttachment`.
        """
        return EpicAttachments(self.requester).list(object_id=self.id)

    def attach(self, attached_file, **attrs):
        """
        Attach a file to the :class:`Epic`

        :param attached_file: file path to attach
        :param attrs: optional attributes for the attached file
        """
        return EpicAttachments(self.requester).create(self.project, self.id, attached_file, **attrs)


class Epics(ListResource):
    """
    Epics factory class
    """

    instance = Epic

    def create(self, project, subject, **attrs):
        """
        Create a new :class:`Epic`.

        :param project: :class:`Project` id
        :param subject: subject of :class:`Epic`
        :param attrs: optional attributes of :class:`Epic`
        """
        attrs.update({"project": project, "subject": subject})
        return self._new_resource(payload=attrs)


class EpicStatus(MoveOnDestroyMixinObject, InstanceResource):
    """
    Taiga Epic Status model

    :param color: the color of :class:`EpicStatus`
    :param is_closed: closed property of :class:`EpicStatus`
    :param name: The name of :class:`EpicStatus`
    :param order: order of :class:`EpicStatus`
    :param project: the Taiga project of :class:`EpicStatus`
    :param slug: the slug of :class:`EpicStatus`
    """

    repr_attribute = "subject"

    endpoint = "epic-statuses"

    allowed_params = ["color", "is_closed", "name", "order", "project", "slug`"]


class EpicStatuses(MoveOnDestroyMixinList, ListResource):
    instance = EpicStatus

    def create(self, project, name, **attrs):
        """
        Create a new :class:`EpicStatus`.

        :param project: :class:`Project` id
        :param name: name of :class:`EpicStatus`
        :param attrs: optional attributes of :class:`EpicStatus`
        """
        attrs.update({"project": project, "name": name})
        return self._new_resource(payload=attrs)


class UserStory(CustomAttributeResource, CommentableResource):
    """
    User Story model

    :param assigned_to: assigned to of :class:`UserStory`
    :param assigned_users: additional users assigned to of :class:`UserStory`
    :param backlog_order: backlog order of :class:`UserStory`
    :param blocked_note: blocked note of :class:`UserStory`
    :param version: version of :class:`UserStory`
    :param client_requirement: client requirement of :class:`UserStory`
    :param description: description of :class:`UserStory` (not available in the :py:meth:`UserStories.list` response)
    :param is_blocked: is blocked of :class:`UserStory`
    :param kanban_order: kanban order of :class:`UserStory`
    :param milestone: milestone of :class:`UserStory`
    :param points: points of :class:`UserStory`
    :param project: project of :class:`UserStory`
    :param sprint_order: sprint order of :class:`UserStory`
    :param status: status of :class:`UserStory`
    :param subject: subject of :class:`UserStory`
    :param tags: tags of :class:`UserStory`
    :param team_requirement: team requirement of :class:`UserStory`
    :param watchers: watchers of :class:`UserStory`
    :param due_date: :class:`UserStory` due date
    :param generated_from_issue: :class:`UserStory` parent issue
    :param generated_from_task: :class:`UserStory` parent task
    """

    endpoint = "userstories"

    repr_attribute = "subject"
    element_type = "User Story"
    element_shortcut = "us"

    allowed_params = [
        "assigned_to",
        "assigned_users",
        "backlog_order",
        "blocked_note",
        "version",
        "client_requirement",
        "description",
        "is_blocked",
        "is_closed",
        "kanban_order",
        "milestone",
        "points",
        "project",
        "sprint_order",
        "status",
        "subject",
        "tags",
        "team_requirement",
        "watchers",
        "due_date",
        "generated_from_issue",
        "generated_from_task",
        "swimlane",
    ]

    def add_task(self, subject, status, **attrs):
        """
        Add a :class:`Task` to the current :class:`UserStory` and return it.
        :param subject: subject of :class:`Task`
        :param status: status of :class:`Task`
        :param attrs: optional attributes for :class:`Task`

        """
        return Tasks(self.requester).create(self.project, subject, status, user_story=self.id, **attrs)

    def list_tasks(self):
        """
        Get a list of :class:`Task` in the current :class:`UserStory`.
        """
        return Tasks(self.requester).list(user_story=self.id)

    def list_attachments(self):
        """
        Get a list of :class:`UserStoryAttachment`.
        """
        return UserStoryAttachments(self.requester).list(object_id=self.id)

    def attach(self, attached_file, **attrs):
        """
        Attach a file to the :class:`UserStory`

        :param attached_file: file path to attach
        :param attrs: optional attributes for the attached file
        """
        return UserStoryAttachments(self.requester).create(self.project, self.id, attached_file, **attrs)


class UserStories(ListResource):
    """
    UserStories factory class
    """

    instance = UserStory

    def create(self, project, subject, **attrs):
        """
        Create a new :class:`UserStory`.

        :param project: :class:`Project` id
        :param subject: subject of :class:`UserStory`
        :param attrs: optional attributes of :class:`UserStory`
        """
        attrs.update({"project": project, "subject": subject})
        return self._new_resource(payload=attrs)

    def import_(self, project, subject, status, **attrs):
        attrs.update({"project": project, "subject": subject, "status": status})
        response = self.requester.post(
            "/{endpoint}/{id}/{type}", endpoint="importer", id=project, type="us", payload=attrs
        )
        return self.instance.parse(self.requester, response.json())


class UserStoryStatus(MoveOnDestroyMixinObject, InstanceResource):
    """
    Taiga User Story Status model

    :param color: the color of :class:`UserStoryStatus`
    :param is_closed: closed property of :class:`UserStoryStatus`
    :param name: The name of :class:`UserStoryStatus`
    :param order: order of :class:`UserStoryStatus`
    :param project: the Taiga project of :class:`UserStoryStatus`
    :param wip_limit: wip limit of :class:`UserStoryStatus`
    """

    repr_attribute = "subject"

    endpoint = "userstory-statuses"

    allowed_params = ["color", "is_closed", "name", "order", "project", "wip_limit"]


class UserStoryStatuses(MoveOnDestroyMixinList, ListResource):
    instance = UserStoryStatus

    def create(self, project, name, **attrs):
        """
        Create a new :class:`UserStoryStatus`.

        :param project: :class:`Project` id
        :param name: name of :class:`UserStoryStatus`
        :param attrs: optional attributes of :class:`UserStoryStatus`
        """
        attrs.update({"project": project, "name": name})
        return self._new_resource(payload=attrs)


class SwimLane(MoveOnDestroyMixinObject, InstanceResource):
    """
    Taiga Swimlane model

    :param name: The name of :class:`SwimLane`
    :param order: the order of :class:`SwimLane`
    :param project: the project of :class:`SwimLane`
    :param statuses: the statuses of :class:`SwimLane`
    """

    repr_attribute = "name"

    endpoint = "swimlanes"

    allowed_params = ["name", "order", "project", "statuses"]

    parser = {
        "statuses": UserStoryStatuses,
    }


class SwimLanes(MoveOnDestroyMixinList, ListResource):
    instance = SwimLane

    def create(self, project, name, **attrs):
        """
        Create a new :class:`SwimLane`.

        :param project: :class:`Project` id
        :param name: name of :class:`SwimLane`
        :param attrs: optional attributes of :class:`SwimLane`
        """
        attrs.update({"project": project, "name": name})
        return self._new_resource(payload=attrs)


class Point(MoveOnDestroyMixinObject, InstanceResource):
    """
    Taiga Point model

    :param color: the color of :class:`Point`
    :param value: value of :class:`Point`
    :param name: name of :class:`Point`
    :param order: the order of :class:`Point`
    :param project: the Taiga project of :class:`Point`
    """

    endpoint = "points"

    repr_attribute = "subject"

    allowed_params = ["color", "value", "name", "order", "project"]


class Points(MoveOnDestroyMixinList, ListResource):
    """
    Points factory
    """

    instance = Point

    def create(self, project, name, value, **attrs):
        """
        Create a new :class:`UserStoryStatus`.

        :param project: :class:`Project` id
        :param name: name of :class:`Point`
        :param value: value of :class:`Point`
        :param attrs: optional attributes of :class:`Point`
        """
        attrs.update({"project": project, "name": name, "value": value})
        return self._new_resource(payload=attrs)


class Milestone(InstanceResource):
    """
    Milestone model

    :param name: the name of :class:`Milestone`
    :param project: the Taiga project  of :class:`Milestone`
    :param estimated_start: the estimated start of :class:`Milestone`
    :param estimated_finish: the estimated finish  of :class:`Milestone`
    :param disponibility: the disponibility  of :class:`Milestone`
    """

    endpoint = "milestones"

    allowed_params = [
        "name",
        "project",
        "estimated_start",
        "estimated_finish",
        "disponibility",
        "slug",
        "order",
        "watchers",
    ]

    parser = {
        "user_stories": UserStories,
    }

    def stats(self):
        """
        Get the stats for the current :class:`Milestone`
        """
        response = self.requester.get("/{endpoint}/{id}/stats", endpoint=self.endpoint, id=self.id)
        return response.json()


class Milestones(ListResource):
    """
    Milestones factory
    """

    instance = Milestone

    def create(self, project, name, estimated_start, estimated_finish, **attrs):
        """
        Create a new :class:`Milestone`.

        :param project: :class:`Project` id
        :param name: name of :class:`Milestone`
        :param estimated_start: est. start time of :class:`Milestone`
        :param estimated_finish: est. finish time of :class:`Milestone`
        :param attrs: optional attributes of :class:`Milestone`
        """
        if isinstance(estimated_start, datetime.datetime):
            estimated_start = estimated_start.strftime("%Y-%m-%d")
        if isinstance(estimated_finish, datetime.datetime):
            estimated_finish = estimated_finish.strftime("%Y-%m-%d")
        attrs.update(
            {
                "project": project,
                "name": name,
                "estimated_start": estimated_start,
                "estimated_finish": estimated_finish,
            }
        )
        return self._new_resource(payload=attrs)

    def import_(self, project, name, estimated_start, estimated_finish, **attrs):
        if isinstance(estimated_start, datetime.datetime):
            estimated_start = estimated_start.strftime("%Y-%m-%d")
        if isinstance(estimated_finish, datetime.datetime):
            estimated_finish = estimated_finish.strftime("%Y-%m-%d")
        attrs.update(
            {
                "project": project,
                "name": name,
                "estimated_start": estimated_start,
                "estimated_finish": estimated_finish,
            }
        )
        response = self.requester.post(
            "/{endpoint}/{id}/{type}", endpoint="importer", id=project, type="milestone", payload=attrs
        )
        return self.instance.parse(self.requester, response.json())


class TaskStatus(MoveOnDestroyMixinObject, InstanceResource):
    """
    Task Status model

    :param name: the name of :class:`TaskStatus`
    :param color: the color of :class:`TaskStatus`
    :param order: the order of :class:`TaskStatus`
    :param project: the project  of :class:`TaskStatus`
    :param is_closed: the is closed property of :class:`TaskStatus`
    """

    endpoint = "task-statuses"

    allowed_params = ["name", "color", "order", "project", "is_closed"]


class TaskStatuses(MoveOnDestroyMixinList, ListResource):
    instance = TaskStatus

    def create(self, project, name, **attrs):
        """
        Create a new :class:`TaskStatus`.

        :param project: :class:`Project` id
        :param name: name of :class:`TaskStatus`
        :param attrs: optional attributes of :class:`TaskStatus`
        """
        attrs.update({"project": project, "name": name})
        return self._new_resource(payload=attrs)


class TaskAttachment(Attachment):
    """
    TaskAttachment model
    """

    endpoint = "tasks/attachments"


class TaskAttachments(Attachments):
    """
    TaskAttachments factory
    """

    instance = TaskAttachment


class Task(CustomAttributeResource, CommentableResource):
    """
    Task model

    :param assigned_to: assigned to property of :class:`TaskStatus`
    :param blocked_note: blocked note of :class:`TaskStatus`
    :param description: description of of :class:`TaskStatus` (not available in the :py:meth:`Tasks.list` response)
    :param version: version of :class:`TaskStatus`
    :param is_blocked: is blocked property of :class:`TaskStatus`
    :param milestone: milestone property of :class:`TaskStatus`
    :param project: the project of :class:`TaskStatus`
    :param user_story: the user story of :class:`TaskStatus`
    :param status: status of :class:`TaskStatus`
    :param subject: subject of :class:`TaskStatus`
    :param tags: tags of :class:`TaskStatus`
    :param us_order: the use order of :class:`TaskStatus`
    :param taskboard_order: the taskboard order of :class:`TaskStatus`
    :param is_iocaine: the is iocaine of :class:`TaskStatus`
    :param external_reference: external reference of :class:`TaskStatus`
    :param watchers: watchers of :class:`TaskStatus`
    :param due_date: :class:`Task` due date
    """

    endpoint = "tasks"

    repr_attribute = "subject"
    element_type = "Task"
    element_shortcut = "task"

    allowed_params = [
        "assigned_to",
        "blocked_note",
        "description",
        "version",
        "is_blocked",
        "is_closed",
        "milestone",
        "project",
        "user_story",
        "status",
        "subject",
        "tags",
        "us_order",
        "taskboard_order",
        "is_iocaine",
        "external_reference",
        "watchers",
    ]

    def list_attachments(self):
        """
        Get a list of :class:`TaskAttachment`.
        """
        return TaskAttachments(self.requester).list(object_id=self.id)

    def attach(self, attached_file, **attrs):
        """
        Attach a file to the :class:`Task`

        :param attached_file: file path to attach
        :param attrs: optional attributes for the attached file
        """
        return TaskAttachments(self.requester).create(self.project, self.id, attached_file, **attrs)


class Tasks(ListResource):
    """
    Tasks factory
    """

    instance = Task

    def create(self, project, subject, status, **attrs):
        """
        Create a new :class:`Task`.

        :param project: :class:`Project` id
        :param subject: subject of :class:`Task`
        :param status: status of :class:`Task`
        :param attrs: optional attributes of :class:`Task`
        """
        attrs.update({"project": project, "subject": subject, "status": status})
        return self._new_resource(payload=attrs)

    def import_(self, project, subject, status, **attrs):
        attrs.update({"project": project, "subject": subject, "status": status})
        response = self.requester.post(
            "/{endpoint}/{id}/{type}", endpoint="importer", id=project, type="task", payload=attrs
        )
        return self.instance.parse(self.requester, response.json())


class IssueType(MoveOnDestroyMixinObject, InstanceResource):
    """
    IssueType model

    :param name: name of :class:`IssueType`
    :param color: color of :class:`IssueType`
    :param order: order of :class:`IssueType`
    :param project: the taiga project of :class:`IssueType`
    """

    endpoint = "issue-types"

    allowed_params = ["name", "color", "order", "project"]


class IssueTypes(MoveOnDestroyMixinList, ListResource):
    """
    IssueTypes factory
    """

    instance = IssueType

    def create(self, project, name, **attrs):
        attrs.update({"project": project, "name": name})
        return self._new_resource(payload=attrs)


class IssueStatus(MoveOnDestroyMixinObject, InstanceResource):
    """
    Issue Status model

    :param name: name of :class:`IssueStatus`
    :param color: color of :class:`IssueStatus`
    :param order: order of :class:`IssueStatus`
    :param project: the taiga project of :class:`IssueStatus`
    :param is_closed: is closed property of :class:`IssueStatus`
    """

    endpoint = "issue-statuses"

    allowed_params = ["name", "color", "order", "project", "is_closed"]


class IssueStatuses(MoveOnDestroyMixinList, ListResource):
    """
    IssueStatuses factory
    """

    instance = IssueStatus

    def create(self, project, name, **attrs):
        attrs.update({"project": project, "name": name})
        return self._new_resource(payload=attrs)


class IssueAttachment(Attachment):
    """
    IssueAttachment model
    """

    endpoint = "issues/attachments"


class IssueAttachments(Attachments):
    """
    IssueAttachments factory
    """

    instance = IssueAttachment


class Issue(CustomAttributeResource, CommentableResource):
    """Issue model

    :param requester: :class:`Requester` instance
    :param assigned_to: :class:`User` id this issue is assigned to
    :param description: description of the issue (not available in the :py:meth:`Issues.list` response)
    :param is_blocked: set if this issue is blocked or not
    :param milestone: :class:`Milestone` id
    :param project: :class:`Project` id
    :param status: :class:`Status` id
    :param severity: class:`Severity` id
    :param priority: class:`Priority` id
    :param type: class:`Type` id
    :param subject: subject of the issue
    :param tags: array of tags
    :param watchers: array of watchers id
    :param due_date: :class:`Issue` due date
    """

    endpoint = "issues"

    repr_attribute = "subject"
    element_type = "Issue"
    element_shortcut = "issue"

    allowed_params = [
        "assigned_to",
        "blocked_note",
        "description",
        "version",
        "is_blocked",
        "is_closed",
        "milestone",
        "project",
        "status",
        "severity",
        "priority",
        "type",
        "subject",
        "tags",
        "watchers",
    ]

    def list_attachments(self):
        """
        Get a list of :class:`IssueAttachment`.
        """
        return IssueAttachments(self.requester).list(object_id=self.id)

    def upvote(self):
        """
        Upvote :class:`Issue`.
        """
        self.requester.post("/{endpoint}/{id}/upvote", endpoint=self.endpoint, id=self.id)
        return self

    def downvote(self):
        """
        Downvote :class:`Issue`.
        """
        self.requester.post("/{endpoint}/{id}/downvote", endpoint=self.endpoint, id=self.id)
        return self

    def attach(self, attached_file, **attrs):
        """
        Attach a file to the :class:`Issue`

        :param attached_file: file path to attach
        :param attrs: optional attributes for the attached file
        """
        return IssueAttachments(self.requester).create(self.project, self.id, attached_file, **attrs)


class Issues(ListResource):
    instance = Issue

    def create(self, project, subject, priority, status, issue_type, severity, **attrs):
        """
        Create a new :class:`Task`.

        :param project: :class:`Project` id
        :param subject: subject of :class:`Issue`
        :param priority: priority of :class:`Issue`
        :param status: status of :class:`Issue`
        :param issue_type: Issue type of :class:`Issue`
        :param severity: severity of :class:`Issue`
        :param attrs: optional attributes of :class:`Task`
        """
        attrs.update(
            {
                "project": project,
                "subject": subject,
                "priority": priority,
                "status": status,
                "type": issue_type,
                "severity": severity,
            }
        )
        return self._new_resource(payload=attrs)

    def import_(self, project, subject, priority, status, issue_type, severity, **attrs):
        attrs.update(
            {
                "project": project,
                "subject": subject,
                "priority": priority,
                "status": status,
                "type": issue_type,
                "severity": severity,
            }
        )
        response = self.requester.post(
            "/{endpoint}/{id}/{type}", endpoint="importer", id=project, type="issue", payload=attrs
        )
        return self.instance.parse(self.requester, response.json())


class IssueAttribute(CustomAttribute):
    """
    IssueAttribute model
    """

    endpoint = "issue-custom-attributes"


class IssueAttributes(CustomAttributes):
    """
    IssueAttributes factory
    """

    instance = IssueAttribute


class TaskAttribute(CustomAttribute):
    """
    TaskAttribute model
    """

    endpoint = "task-custom-attributes"


class TaskAttributes(CustomAttributes):
    """
    TaskAttributes factory
    """

    instance = TaskAttribute


class UserStoryAttribute(CustomAttribute):
    """
    UserStoryAttribute model
    """

    endpoint = "userstory-custom-attributes"


class UserStoryAttributes(CustomAttributes):
    """
    UserStoryAttributes factory
    """

    instance = UserStoryAttribute


class EpicAttribute(CustomAttribute):
    """
    EpicAttribute model
    """

    endpoint = "epic-custom-attributes"


class EpicAttributes(CustomAttributes):
    """
    EpicAttributes factory
    """

    instance = EpicAttribute


class Severity(MoveOnDestroyMixinObject, InstanceResource):
    """
    Severity model

    :param requester: :class:`Requester` instance
    :param name: name of :class:`Severity`
    :param order: order of :class:`Severity`
    :param project: :class:`Project` id
    """

    endpoint = "severities"

    allowed_params = ["name", "color", "order", "project"]


class Severities(MoveOnDestroyMixinList, ListResource):
    """
    Severities factory
    """

    instance = Severity

    def create(self, project, name, **attrs):
        """
        Create a new :class:`Severity`

        :param project: :class:`Project` id
        :param name: name of :class:`Severity`
        :param attrs: optional attributes for :class:`Role`
        """
        attrs.update({"project": project, "name": name})
        return self._new_resource(payload=attrs)


class Role(InstanceResource):
    """
    Role model

    :param requester: :class:`Requester` instance
    :param name: name of :class:`Role`
    :param slug: slug of :class:`Role`
    :param order: order of :class:`Role`
    :param computable: choose if :class:`Role` is computable or not

    """

    endpoint = "roles"

    allowed_params = ["name", "slug", "order", "computable"]


class Roles(ListResource):
    """
    Roles factory
    """

    instance = Role

    def create(self, project, name, **attrs):
        """
        Create a new :class:`Role`

        :param project: :class:`Project` id
        :param name: name of :class:`Role`
        :param attrs: optional attributes for :class:`Role`
        """
        attrs.update({"project": project, "name": name})
        return self._new_resource(payload=attrs)


class Project(InstanceResource):
    """Taiga project model

    :param requester: :class:`Requester` instance
    :param name: name of the project
    :param description: description of the project (not available in the :py:meth:`Projects.list` response)
    :param creation_template: base template for the project
    :param is_backlog_activated: name of the project
    :param is_issues_activated: name of the project
    :param is_kanban_activated: name of the project
    :param is_wiki_activated: determines if the project is private or not
    :param is_private: determines if the project is private or not
    :param videoconferences: appear-in or talky
    :param videoconferences_salt: for videoconference chat url generation
    :param total_milestones: missing
    :param total_story_points: missing

    """

    endpoint = "projects"

    allowed_params = [
        "name",
        "description",
        "default_swimlane",
        "creation_template",
        "is_backlog_activated",
        "is_issues_activated",
        "is_kanban_activated",
        "is_private",
        "is_wiki_activated",
        "videoconferences",
        "videoconferences_salt",
        "total_milestones",
        "total_story_points",
    ]

    parser = {
        "members": Users,
        "priorities": Priorities,
        "issue_statuses": IssueStatuses,
        "issue_types": IssueTypes,
        "task_statuses": TaskStatuses,
        "severities": Severities,
        "roles": Roles,
        "points": Points,
        "us_statuses": UserStoryStatuses,
        "milestones": Milestones,
        "swimlanes": SwimLanes,
    }

    def get_item_by_ref(self, ref):
        response = self.requester.get(
            "/resolver?project={project_id}&ref={task_ref}", task_ref=ref, project_id=self.slug
        )
        response_json = response.json()

        if response_json and "task" in response_json:
            return self.get_task_by_ref(ref)
        elif response_json and "us" in response_json:
            return self.get_userstory_by_ref(ref)
        elif response_json and "issue" in response_json:
            return self.get_issue_by_ref(ref)
        else:
            return None

    def get_task_by_ref(self, ref):
        """
        Get a :class:`Task` by ref.

        :param ref: :class:`Task` reference
        """
        response = self.requester.get(
            "/{endpoint}/by_ref?ref={task_ref}&project={project_id}",
            endpoint=Task.endpoint,
            task_ref=ref,
            project_id=self.id,
        )
        return Task.parse(self.requester, response.json())

    def get_epic_by_ref(self, ref):
        """
        Get a :class:`Epic` by ref.

        :param ref: :class:`Epic` reference
        """
        response = self.requester.get(
            "/{endpoint}/by_ref?ref={ep_ref}&project={project_id}",
            endpoint=Epic.endpoint,
            ep_ref=ref,
            project_id=self.id,
        )
        return Epic.parse(self.requester, response.json())

    def get_userstory_by_ref(self, ref):
        """
        Get a :class:`UserStory` by ref.

        :param ref: :class:`UserStory` reference
        """
        response = self.requester.get(
            "/{endpoint}/by_ref?ref={us_ref}&project={project_id}",
            endpoint=UserStory.endpoint,
            us_ref=ref,
            project_id=self.id,
        )
        return UserStory.parse(self.requester, response.json())

    def get_issue_by_ref(self, ref):
        """
        Get a :class:`Issue` by ref.

        :param ref: :class:`Issue` reference
        """
        response = self.requester.get(
            "/{endpoint}/by_ref?ref={us_ref}&project={project_id}",
            endpoint=Issue.endpoint,
            us_ref=ref,
            project_id=self.id,
        )
        return Issue.parse(self.requester, response.json())

    def stats(self):
        """
        Get the stats of the project
        """
        response = self.requester.get("/{endpoint}/{id}/stats", endpoint=self.endpoint, id=self.id)
        return response.json()

    def issues_stats(self):
        """
        Get stats for issues of the project
        """
        response = self.requester.get("/{endpoint}/{id}/issues_stats", endpoint=self.endpoint, id=self.id)
        return response.json()

    def like(self):
        """
        Like the project
        """
        self.requester.post("/{endpoint}/{id}/like", endpoint=self.endpoint, id=self.id)
        return self

    def unlike(self):
        """
        Unlike the project
        """
        self.requester.post("/{endpoint}/{id}/unlike", endpoint=self.endpoint, id=self.id)
        return self

    def star(self):
        """
        Stars the project

        .. deprecated:: 0.8.5

            Update Taiga and use like instead
        """
        warnings.warn("Deprecated! Update Taiga and use .like() instead", DeprecationWarning)
        self.requester.post("/{endpoint}/{id}/star", endpoint=self.endpoint, id=self.id)
        return self

    def unstar(self):
        """
        Unstars the project

        .. deprecated:: 0.8.5

            Update Taiga and use unlike instead
        """
        warnings.warn("Deprecated! Update Taiga and use .unlike() instead", DeprecationWarning)
        self.requester.post("/{endpoint}/{id}/unstar", endpoint=self.endpoint, id=self.id)
        return self

    def add_membership(self, email, role, **attrs):
        """
        Add a Membership to the project and returns a
        :class:`Membership` resource.

        :param email: email for :class:`Membership`
        :param role: role for :class:`Membership`
        :param attrs: role for :class:`Membership`
        :param attrs: optional :class:`Membership` attributes
        """
        return Memberships(self.requester).create(self.id, email, role, **attrs)

    def list_memberships(self):
        """
        Get the list of :class:`Membership` resources for the project.
        """
        return Memberships(self.requester).list(project=self.id)

    def add_user_story(self, subject, **attrs):
        """
        Adds a :class:`UserStory` and returns a :class:`UserStory` resource.

        :param subject: subject of :class:`UserStory`
        :param attrs: other :class:`UserStory` attributes
        """
        return UserStories(self.requester).create(self.id, subject, **attrs)

    def import_user_story(self, subject, status, **attrs):
        """
        Import an user story and returns a :class:`UserStory` resource.

        :param subject: subject of :class:`UserStory`
        :param status: status of :class:`UserStory`
        :param attrs: optional :class:`UserStory` attributes
        """
        return UserStories(self.requester).import_(self.id, subject, status, **attrs)

    def list_user_stories(self, **queryparams):
        """
        Returns the :class:`UserStory` list of the project.
        """
        return UserStories(self.requester).list(project=self.id, **queryparams)

    def add_swimlane(self, name, **attrs):
        """
        Adds a :class:`SwimLane` and returns a :class:`SwimLane` resource.

        :param name: name of :class:`SwimLane`
        :param attrs: other :class:`SwimLane` attributes
        """
        return SwimLanes(self.requester).create(self.id, name, **attrs)

    def list_swimlanes(self, **queryparams):
        """
        Returns the :class:`SwimLane` list of the project.
        """
        return SwimLanes(self.requester).list(project=self.id, **queryparams)

    def add_issue(self, subject, priority, status, issue_type, severity, **attrs):
        """
        Adds a Issue and returns a :class:`Issue` resource.

        :param subject: subject of :class:`Issue`
        :param priority: priority of :class:`Issue`
        :param priority: status of :class:`Issue`
        :param issue_type: type of :class:`Issue`
        :param severity: severity of :class:`Issue`
        :param attrs: other :class:`Issue` attributes
        """
        return Issues(self.requester).create(self.id, subject, priority, status, issue_type, severity, **attrs)

    def import_issue(self, subject, priority, status, issue_type, severity, **attrs):
        """
        Import and issue and returns a :class:`Issue` resource.

        :param subject: subject of :class:`Issue`
        :param priority: priority of :class:`Issue`
        :param status: status of :class:`Issue`
        :param issue_type: issue type of :class:`Issue`
        :param severity: severity of :class:`Issue`
        :param attrs: optional :class:`Issue` attributes
        """
        return Issues(self.requester).import_(self.id, subject, priority, status, issue_type, severity, **attrs)

    def list_issues(self):
        """
        Returns the :class:`Issue` list of the project.
        """
        return Issues(self.requester).list(project=self.id)

    def add_milestone(self, name, estimated_start, estimated_finish, **attrs):
        """
        Add a Milestone to the project and returns a :class:`Milestone` object.

        :param name: name of :class:`Milestone`
        :param estimated_start: estimated start time of the
                                :class:`Milestone`
        :param estimated_finish: estimated finish time of the
                                 :class:`Milestone`
        :param attrs: optional attributes for :class:`Milestone`
        """
        return Milestones(self.requester).create(self.id, name, estimated_start, estimated_finish, **attrs)

    def import_milestone(self, name, estimated_start, estimated_finish, **attrs):
        """
        Import a Milestone and returns a :class:`Milestone` object.

        :param name: name of :class:`Milestone`
        :param estimated_start: estimated start time of the
                                :class:`Milestone`
        :param estimated_finish: estimated finish time of the
                                 :class:`Milestone`
        :param attrs: optional attributes for :class:`Milestone`
        """
        return Milestones(self.requester).import_(self.id, name, estimated_start, estimated_finish, **attrs)

    def list_milestones(self, **queryparams):
        """
        Get the list of :class:`Milestone` resources for the project.
        """
        return Milestones(self.requester).list(project=self.id, **queryparams)

    def add_point(self, name, value, **attrs):
        """
        Add a Point to the project and returns a :class:`Point` object.

        :param name: name of :class:`Point`
        :param value: value of :class:`Point`
        :param attrs: optional attributes for :class:`Point`
        """
        return Points(self.requester).create(self.id, name, value, **attrs)

    def list_points(self):
        """
        Get the list of :class:`Point` resources for the project.
        """
        return Points(self.requester).list(project=self.id)

    def add_epic(self, subject, **attrs):
        """
        Adds a :class:`UserStory` and returns a :class:`UserStory` resource.

        :param subject: subject of :class:`UserStory`
        :param attrs: other :class:`UserStory` attributes
        """
        return Epics(self.requester).create(self.id, subject, **attrs)

    def list_epics(self):
        """
        Get the list of :class:`Epic` resources for the project.
        """
        return Epics(self.requester).list(project=self.id)

    def add_task_status(self, name, **attrs):
        """
        Add a Task status to the project and returns a
        :class:`TaskStatus` object.

        :param name: name of :class:`TaskStatus`
        :param attrs: optional attributes for :class:`TaskStatus`
        """
        return TaskStatuses(self.requester).create(self.id, name, **attrs)

    def list_task_statuses(self):
        """
        Get the list of :class:`Task` resources for the project.
        """
        return TaskStatuses(self.requester).list(project=self.id)

    def import_task(self, subject, status, **attrs):
        """
        Import a Task and return a :class:`Task` object.

        :param subject: subject of :class:`Task`
        :param status: status of :class:`Task`
        :param attrs: optional attributes for :class:`Task`
        """
        return Tasks(self.requester).import_(self.id, subject, status, **attrs)

    def add_user_story_status(self, name, **attrs):
        """
        Add a UserStory status to the project and returns a
        :class:`UserStoryStatus` object.

        :param name: name of :class:`UserStoryStatus`
        :param attrs: optional attributes for :class:`UserStoryStatus`
        """
        return UserStoryStatuses(self.requester).create(self.id, name, **attrs)

    def list_user_story_statuses(self):
        """
        Get the list of :class:`UserStoryStatus` resources for the project.
        """
        return UserStoryStatuses(self.requester).list(project=self.id)

    def add_issue_type(self, name, **attrs):
        """
        Add a Issue type to the project and returns a
        :class:`IssueType` object.

        :param name: name of :class:`IssueType`
        :param attrs: optional attributes for :class:`IssueType`
        """
        return IssueTypes(self.requester).create(self.id, name, **attrs)

    def list_issue_types(self):
        """
        Get the list of :class:`IssueType` resources for the project.
        """
        return IssueTypes(self.requester).list(project=self.id)

    def add_severity(self, name, **attrs):
        """
        Add a Severity to the project and returns a :class:`Severity` object.

        :param name: name of :class:`Severity`
        :param attrs: optional attributes for :class:`Severity`
        """
        return Severities(self.requester).create(self.id, name, **attrs)

    def list_severities(self):
        """
        Get the list of :class:`Severity` resources for the project.
        """
        return Severities(self.requester).list(project=self.id)

    def add_role(self, name, **attrs):
        """
        Add a Role to the project and returns a :class:`Role` object.

        :param name: name of :class:`Role`
        :param attrs: optional attributes for :class:`Role`
        """
        return Roles(self.requester).create(self.id, name, **attrs)

    def list_roles(self):
        """
        Get the list of :class:`Role` resources for the project.
        """
        return Roles(self.requester).list(project=self.id)

    def add_priority(self, name, **attrs):
        """
        Add a Priority to the project and returns a :class:`Priority` object.

        :param name: name of :class:`Priority`
        :param attrs: optional attributes for :class:`Priority`
        """
        return Priorities(self.requester).create(self.id, name, **attrs)

    def list_priorities(self):
        """
        Get the list of :class:`Priority` resources for the project.
        """
        return Priorities(self.requester).list(project=self.id)

    def add_issue_status(self, name, **attrs):
        """
        Add a Issue status to the project and returns a
        :class:`IssueStatus` object.

        :param name: name of :class:`IssueStatus`
        :param attrs: optional attributes for :class:`IssueStatus`
        """
        return IssueStatuses(self.requester).create(self.id, name, **attrs)

    def list_issue_statuses(self):
        """
        Get the list of :class:`IssueStatus` resources for the project.
        """
        return IssueStatuses(self.requester).list(project=self.id)

    def add_wikipage(self, slug, content, **attrs):
        """
        Add a Wiki page to the project and returns a :class:`WikiPage` object.

        :param name: name of :class:`WikiPage`
        :param attrs: optional attributes for :class:`WikiPage`
        """
        return WikiPages(self.requester).create(self.id, slug, content, **attrs)

    def import_wikipage(self, slug, content, **attrs):
        """
        Import a Wiki page and return a :class:`WikiPage` object.

        :param slug: slug of :class:`WikiPage`
        :param content: content of :class:`WikiPage`
        :param attrs: optional attributes for :class:`Task`
        """
        return WikiPages(self.requester).import_(self.id, slug, content, **attrs)

    def list_wikipages(self):
        """
        Get the list of :class:`WikiPage` resources for the project.
        """
        return WikiPages(self.requester).list(project=self.id)

    def add_wikilink(self, title, href, **attrs):
        """
        Add a Wiki link to the project and returns a :class:`WikiLink` object.

        :param title: title of :class:`WikiLink`
        :param href: href of :class:`WikiLink`
        :param attrs: optional attributes for :class:`WikiLink`
        """
        return WikiLinks(self.requester).create(self.id, title, href, **attrs)

    def import_wikilink(self, title, href, **attrs):
        """
        Import a Wiki link and return a :class:`WikiLink` object.

        :param title: title of :class:`WikiLink`
        :param href: href of :class:`WikiLink`
        :param attrs: optional attributes for :class:`WikiLink`
        """
        return WikiLinks(self.requester).import_(self.id, title, href, **attrs)

    def list_wikilinks(self):
        """
        Get the list of :class:`WikiLink` resources for the project.
        """
        return WikiLinks(self.requester).list(project=self.id)

    def add_issue_attribute(self, name, **attrs):
        """
        Add a new Issue attribute and return a :class:`IssueAttribute` object.

        :param name: name of :class:`IssueAttribute`
        :param attrs: optional attributes for :class:`IssueAttribute`
        """
        return IssueAttributes(self.requester).create(self.id, name, **attrs)

    def list_issue_attributes(self):
        """
        Get the list of :class:`IssueAttribute` resources for the project.
        """
        return IssueAttributes(self.requester).list(project=self.id)

    def add_task_attribute(self, name, **attrs):
        """
        Add a new Task attribute and return a :class:`TaskAttribute` object.

        :param name: name of :class:`TaskAttribute`
        :param attrs: optional attributes for :class:`TaskAttribute`
        """
        return TaskAttributes(self.requester).create(self.id, name, **attrs)

    def list_task_attributes(self):
        """
        Get the list of :class:`TaskAttribute` resources for the project.
        """
        return TaskAttributes(self.requester).list(project=self.id)

    def add_user_story_attribute(self, name, **attrs):
        """
        Add a new User Story attribute and return a
        :class:`UserStoryAttribute` object.

        :param name: name of :class:`UserStoryAttribute`
        :param attrs: optional attributes for :class:`UserStoryAttribute`
        """
        return UserStoryAttributes(self.requester).create(self.id, name, **attrs)

    def list_user_story_attributes(self):
        """
        Get the list of :class:`UserStoryAttribute` resources for the project.
        """
        return UserStoryAttributes(self.requester).list(project=self.id)

    def list_epic_attributes(self):
        """
        Get the list of :class:`EpicAttribute` resources for the project.
        """
        return EpicAttributes(self.requester).list(project=self.id)

    def add_webhook(self, name, url, key, **attrs):
        """
        Add a new Webhook and return a :class:`Webhook` object.

        :param name: name of :class:`Webhook`
        :param url: payload url of :class:`Webhook`
        :param key: secret key of :class:`Webhook`
        :param attrs: optional attributes for :class:`Webhook`
        """
        return Webhooks(self.requester).create(self.id, name, url, key, **attrs)

    def list_webhooks(self):
        """
        Get the list of :class:`Webhook` resources for the project.
        """
        return Webhooks(self.requester).list(project=self.id)

    def add_tag(self, tag, color=None):
        """
        Add a new tag and return a response object.

        :param tag: name of the tag
        :param color: optional color of the tag
        """
        attrs = {"tag": tag}
        if color:
            attrs["color"] = color
        response = self.requester.post("/{}/{}/create_tag".format(self.endpoint, self.id), payload=attrs)
        return response

    def list_tags(self):
        """
        Get the list of tags for the project.
        """
        response = self.requester.get("/{}/{}/tags_colors".format(self.endpoint, self.id))
        return response.json()

    def duplicate(self, name, description, is_private=False, users=[], **attrs):
        """
        Duplicate a :class:`Project`

        :param name: name of new :class:`Project`
        :param description: description of new :class:`Project`
        :param is_private: determines if the project is private or not
        :param users: users of the new :class:`Project`
        :param attrs: optional attributes for the new :class:`Project`
        """
        attrs.update({"name": name, "description": description, "is_private": is_private, "users": users})
        response = self.requester.post("/{endpoint}/{id}/duplicate", payload=attrs, endpoint=self.endpoint, id=self.id)
        return self.parse(self.requester, response.json())


class Projects(ListResource):
    """
    Projects factory
    """

    instance = Project

    def create(self, name, description, **attrs):
        """
        Create a new :class:`Project`

        :param name: name of :class:`Project`
        :param description: description of :class:`Project`
        :param attrs: optional attributes for :class:`Project`
        """
        attrs.update({"name": name, "description": description})
        return self._new_resource(payload=attrs)

    def import_(self, name, description, roles, **attrs):
        attrs.update({"name": name, "description": description, "roles": roles})
        response = self.requester.post("/{endpoint}", endpoint="importer", payload=attrs)
        return self.instance.parse(self.requester, response.json())

    def get_by_slug(self, slug):
        """
        Get a :class:`Project` by slug

        :param slug: the slug of :class:`Project`
        """
        response = self.requester.get("/{endpoint}/by_slug?slug={slug}", endpoint=self.instance.endpoint, slug=slug)
        return self.instance.parse(self.requester, response.json())


class WikiAttachment(Attachment):
    """
    WikiAttachment model
    """

    endpoint = "wiki/attachments"


class WikiAttachments(Attachments):
    """
    WikiAttachments factory
    """

    instance = WikiAttachment


class WikiPage(InstanceResource):
    """
    WikiPage model

    :param project: :class:`Project` id
    :param slug: slug of the wiki page
    :param content: content of the wiki page
    :param watchers: list of watchers id
    """

    endpoint = "wiki"

    repr_attribute = "slug"

    allowed_params = ["project", "slug", "content", "watchers", "version"]

    def attach(self, attached_file, **attrs):
        """
        Attach a file to the :class:`WikiPage`

        :param attached_file: file path to attach
        :param attrs: optional attributes for the attached file
        """
        return WikiAttachments(self.requester).create(self.project, self.id, attached_file, **attrs)

    def list_attachments(self):
        """
        Get a list of :class:`WikiAttachment`.
        """
        return WikiAttachments(self.requester).list(object_id=self.id, project=self.project)


class WikiPages(ListResource):
    """
    WikiPages factory
    """

    instance = WikiPage

    def create(self, project, slug, content, **attrs):
        """
        create a new :class:`WikiPage`

        :param project: :class:`Project` id
        :param slug: slug of the wiki page
        :param content: content of the wiki page
        :param attrs: optional attributes for the :class:`WikiPage`
        """
        attrs.update({"project": project, "slug": slug, "content": content})
        return self._new_resource(payload=attrs)

    def import_(self, project, slug, content, **attrs):
        attrs.update({"project": project, "slug": slug, "content": content})
        response = self.requester.post(
            "/{endpoint}/{id}/{type}", endpoint="importer", id=project, type="wiki_page", payload=attrs
        )
        return self.instance.parse(self.requester, response.json())


class WikiLink(InstanceResource):
    """
    WikiLink model

    :param project: :class:`Project` id
    :param title: title of the wiki link
    :param href: href for the wiki link
    :param order: order of the wiki link
    """

    endpoint = "wiki-links"

    repr_attribute = "title"

    allowed_params = ["project", "title", "href", "order"]


class WikiLinks(ListResource):
    """
    WikiLinks factory
    """

    instance = WikiLink

    def create(self, project, title, href, **attrs):
        """
        Create a new :class:`WikiLink`

        :param project: :class:`Project` id
        :param title: title of the wiki link
        :param href: href for the wiki link
        :param attrs: optional attributes for the :class:`WikiLink`
        """
        attrs.update({"project": project, "title": title, "href": href})
        return self._new_resource(payload=attrs)

    def import_(self, project, title, href, **attrs):
        attrs.update({"project": project, "title": title, "href": href})
        response = self.requester.post(
            "/{endpoint}/{id}/{type}", endpoint="importer", id=project, type="wiki_link", payload=attrs
        )
        return self.instance.parse(self.requester, response.json())


class History(InstanceResource):
    """
    History model
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.issue = HistoryIssue(self.requester)
        self.task = HistoryTask(self.requester)
        self.user_story = HistoryUserStory(self.requester)
        self.wiki = HistoryWiki(self.requester)
        self.epic = HistoryEpic(self.requester)


class HistoryEntity:
    """
    HistoryEntity model
    """

    endpoint = "history"

    def __init__(self, requester):
        self.requester = requester

    def get(self, resource_id):
        """
        Get a history element

        :param resource_id: id of the resource object (resource type is defined by the HistoryEntity subclass used)
        """
        response = self.requester.get(
            "/{endpoint}/{entity}/{id}", endpoint=self.endpoint, entity=self.entity, id=resource_id, paginate=False
        )
        return response.json()

    def delete_comment(self, resource_id, comment_id):
        """
        Delete a comment

        :param resource_id: id of the resource object (resource type is defined by the HistoryEntity subclass used)
        :param comment_id: id of the comment to delete
        """
        self.requester.post(
            "/{endpoint}/{entity}/{id}/delete_comment?id={comment_id}",
            endpoint=self.endpoint,
            entity=self.entity,
            id=resource_id,
            comment_id=comment_id,
        )

    def undelete_comment(self, resource_id, comment_id):
        """
        Undelete a comment

        :param resource_id: id of the resource object (resource type is defined by the HistoryEntity subclass used)
        :param comment_id: id of the comment to undelete
        """
        self.requester.post(
            "/{endpoint}/{entity}/{id}/undelete_comment?id={comment_id}",
            endpoint=self.endpoint,
            entity=self.entity,
            id=resource_id,
            comment_id=comment_id,
        )


class HistoryIssue(HistoryEntity):
    """
    HistoryIssue model
    """

    def __init__(self, *args, **kwargs):
        super(type(self), self).__init__(*args, **kwargs)
        self.entity = "issue"


class HistoryEpic(HistoryEntity):
    """
    HistoryEpic model
    """

    def __init__(self, *args, **kwargs):
        super(type(self), self).__init__(*args, **kwargs)
        self.entity = "epic"


class HistoryTask(HistoryEntity):
    """
    HistoryTask model
    """

    def __init__(self, *args, **kwargs):
        super(type(self), self).__init__(*args, **kwargs)
        self.entity = "task"


class HistoryUserStory(HistoryEntity):
    """
    HistoryUserStory model
    """

    def __init__(self, *args, **kwargs):
        super(type(self), self).__init__(*args, **kwargs)
        self.entity = "userstory"


class HistoryWiki(HistoryEntity):
    """
    HistoryWiki model
    """

    def __init__(self, *args, **kwargs):
        super(type(self), self).__init__(*args, **kwargs)
        self.entity = "wiki"


class Webhook(InstanceResource):
    """
    Webhook model

    :param requester: :class:`Requester` instance
    :param name: name of :class:`Webhook`
    :param url: payload url of :class:`Webhook`
    :param key: secret key of :class:`Webhook`

    """

    endpoint = "webhooks"

    allowed_params = ["name", "url", "key"]


class Webhooks(ListResource):
    """
    Webhooks factory
    """

    instance = Webhook

    def create(self, project, name, url, key, **attrs):
        """
        Create a new :class:`Webhook`

        :param project: :class:`Project` id
        :param name: name of :class:`Webhook`
        :param url: payload url of :class:`Webhook`
        :param key: secret key of :class:`Webhook`
        :param attrs: optional attributes for :class:`Webhook`
        """
        attrs.update({"project": project, "name": name, "url": url, "key": key})
        return self._new_resource(payload=attrs)
