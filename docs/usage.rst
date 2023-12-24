.. :usage:

=======
Install
=======

::

    pip install python-taiga


=====================
Getting Started
=====================

Getting started with the Taiga API couldn't be easier: create a ``TaigaAPI`` and you're ready to go.

.. note:: python-taiga is a python wrapper for the `Taiga REST API <http://taigaio.github.io/taiga-doc/dist/api.html>`_.
          Any data structure, argument and response matches exactly the Taiga REST API, so refer to it for any usage.


*********************
API Credentials
*********************

The ``TaigaAPI`` needs your Taiga credentials. You can pass these
directly to the auth method (see the code below).

.. code:: python

    from taiga import TaigaAPI

    api = TaigaAPI()

    api.auth(
        username='user',
        password='psw'
    )

Alternately, you can pass a token to the constructor ``TaigaAPI``
constructor.

.. code:: python

    from taiga import TaigaAPI

    api = TaigaAPI(token='mytoken')

You can also specify a different host if you use Taiga somewhere else

.. code:: python

    from taiga import TaigaAPI

    api = TaigaAPI(
        host='http://taiga.my.host.org'
    )

To use LDAP or other authentication backends, use ``auth_type`` argument

.. code:: python

    from taiga import TaigaAPI

    api = TaigaAPI(
        host='http://taiga.my.host.org',
        auth_type='ldap'
    )

To ignore SSL certificate verification (use at your own risk!) use ``tls_verify`` argument

.. code:: python

    from taiga import TaigaAPI

    api = TaigaAPI(
        host='http://taiga.my.host.org',
        tls_verify=False
    )

******************************************************
Get projects, user stories, task and issues
******************************************************

You can get projects, user stories, tasks and issues using the primary
key or using slug/ref

.. code:: python

    new_project = api.projects.get_by_slug('nephila')
    print (new_project.get_issue_by_ref(1036))
    print (new_project.get_userstory_by_ref(1111))
    print (new_project.get_task_by_ref(1112))

******************************************************
Create a project
******************************************************

.. code:: python

    new_project = api.projects.create('TEST PROJECT', 'TESTING API')

******************************************************
Create a new user story
******************************************************

.. code:: python

    userstory = new_project.add_user_story(
        'New Story', description='Blablablabla'
    )

You can also create a milestone and pass it to a story

.. code:: python

    jan_feb_milestone = new_project.add_milestone(
        'MILESTONE 1', '2015-01-26', '2015-02-26'
    )

    userstory = new_project.add_user_story(
        'New Story', description='Blablablabla',
        milestone=jan_feb_milestone.id
    )

To add a task to your user story just run

.. code:: python

    userstory.add_task(
        'New Task 2',
        new_project.task_statuses[0].id
    )

******************************************************
Create a swimlane
******************************************************

.. code:: python

    newlane = new_project.add_swimlane('New Swimlane')

******************************************************
Create an issue
******************************************************

.. code:: python

    newissue = new_project.add_issue(
        'New Issue',
        new_project.priorities.get(name='High').id,
        new_project.issue_statuses.get(name='New').id,
        new_project.issue_types.get(name='Bug').id,
        new_project.severities.get(name='Minor').id,
        description='Bug #5'
    )

******************************************************
Create a custom attribute
******************************************************

.. code:: python

    new_project.add_issue_attribute(
        'Device', description='(iPad, iPod, iPhone, Desktop, etc.)'
    )
    newissue.set_attribute('1', 'Desktop')

******************************************************
List elements
******************************************************

.. code:: python

    projects = api.projects.list()
    stories = api.user_stories.list()

You can also specify filters

.. code:: python

    tasks = api.tasks.list(project=1)

By default list returns all objects, eventually getting the
paginated results behind the scenes.

Pagination
===========

Pagination is controlled by three parameters as explained below:

+--------------------+------------------------------+---------------+--------------------------------------------------------+
|``pagination``      | ``page_size`` (default: 100) | ``page``      | Output                                                 |
+====================+==============================+===============+========================================================+
| ``True`` (default) | ``<integer>``                | ``None``      | All results retrieved by using paginated results and   |
|                    |                              |               | loading them behind the scenes, using given page       |
|                    |                              |               | size (higher page size could yield better performances)|
+--------------------+------------------------------+---------------+--------------------------------------------------------+
| ``True`` (default) | ``<integer>``                | ``<integer>`` | Only results for the given page of the given size      |
|                    |                              |               | are retrieved                                          |
+--------------------+------------------------------+---------------+--------------------------------------------------------+
| ``False``          | ``unused``                   | ``unused``    | Current behavior: all results, ignoring pagination     |
+--------------------+------------------------------+---------------+--------------------------------------------------------+


.. note:: non numerical or false `page_size` values is casted to the default value

Examples
===========

**No pagination**

.. code:: python

   tasks = api.tasks.list(paginate=False)

.. warning:: be aware that the unpaginated results may exceed
             the data the parser can handle and may result in an error.

**Retrieve a single page**

.. code:: python

   tasks_page_1 = api.tasks.list(page=1)  # Will only return page 1

**Specify the page size**

.. code:: python

   tasks_page_1 = api.tasks.list(page=1, page_size=200)  # Will 200 results from page 1


******************************************************
Attach a file
******************************************************

You can attach files to issues, user stories and tasks

.. code:: python

    newissue.attach('README.md', description='Read the README in Issue')

******************************************************
Play with instances
******************************************************

Instances can have actions, for example you can star a project just
calling

.. code:: python

    new_project = api.projects.create('TEST PROJECT', 'TESTING API')
    new_project.star()

Any instance can be updated and deleted

.. code:: python

    new_project.name = 'New name for my project'
    new_project.update()
    new_project.delete()

******************************************************
Search
******************************************************

Search function returns a SearchResult object, containing tasks, user
stories and issues:

.. code:: python

    projects = api.projects.list()
    search_result = api.search(projects[0].id, 'NEW')
    for user_story in search_result.user_stories:
        print (user_story)

******************************************************
History
******************************************************

You can access the history of issues, tasks, userstories and wiki pages:

.. code:: python

    history = api.history.user_story.get(user_story.id)
