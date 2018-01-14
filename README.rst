python-taiga
============

|Gitter| |PyPiVersion| |PyVersion| |Status| |TestCoverage| |CodeClimate| |License|

A module for using the `Taiga REST
API <http://taigaio.github.io/taiga-doc/dist/api.html>`__.
Documentation: https://python-taiga.readthedocs.io/

Install
-------

::

    pip install python-taiga

Contribute to python-taiga
--------------------------

-  If you want to contribute to python-taiga with small fixes or updates
   please open a PR on Github

-  If you want to start working on a big feature please let's discuss it
   together, opening a new issue

-  If you want to contribute to python-taiga's documentation use the
   ``generate_docs.sh`` script to build the official documentation and
   send a PR (We use sphinx http://sphinx-doc.org/)

Getting Started
---------------

Getting started with the Taiga API couldn't be easier. Create a
``TaigaAPI`` and you're ready to go.

API Credentials
~~~~~~~~~~~~~~~

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

Get projects, user stories, task and issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can get projects, user stories, tasks and issues using the primary
key or using slug/ref

.. code:: python

    new_project = api.projects.get_by_slug('nephila')
    print (new_project.get_issue_by_ref(1036))
    print (new_project.get_userstory_by_ref(1111))
    print (new_project.get_task_by_ref(1112))

Create a project
~~~~~~~~~~~~~~~~

.. code:: python

    new_project = api.projects.create('TEST PROJECT', 'TESTING API')

Create a new user story
~~~~~~~~~~~~~~~~~~~~~~~

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

Create an issue
~~~~~~~~~~~~~~~

.. code:: python

    newissue = new_project.add_issue(
        'New Issue',
        new_project.priorities.get(name='High').id,
        new_project.issue_statuses.get(name='New').id,
        new_project.issue_types.get(name='Bug').id,
        new_project.severities.get(name='Minor').id,
        description='Bug #5'
    )

Create a custom attribute
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    new_project.add_issue_attribute(
        'Device', description='(iPad, iPod, iPhone, Desktop, etc.)'
    )
    newissue.set_attribute('1', 'Desktop')

List elements
~~~~~~~~~~~~~

.. code:: python

    projects = api.projects.list()
    stories = api.user_stories.list()

You can also specify filters

.. code:: python

    tasks = api.tasks.list(project=1)

Attach a file
~~~~~~~~~~~~~

You can attach files to issues, user stories and tasks

.. code:: python

    newissue.attach('README.md', description='Read the README in Issue')

Play with instances
~~~~~~~~~~~~~~~~~~~

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

Search
~~~~~~

Search function returns a SearchResult object, containing tasks, user
stories and issues:

.. code:: python

    projects = api.projects.list()
    search_result = api.search(projects[0].id, 'NEW')
    for user_story in search_result.user_stories:
        print (user_story)

History
~~~~~~~

You can access the history of issues, tasks, userstories and wiki pages:

.. code:: python

    history = api.history.user_story.get(user_story.id)

You can find a complete example in demo.py.


.. |Gitter| image:: https://img.shields.io/badge/GITTER-join%20chat-brightgreen.svg?style=flat-square
    :target: https://gitter.im/nephila/applications
    :alt: Join the Gitter chat

.. |PyPiVersion| image:: https://img.shields.io/pypi/v/python-taiga.svg?style=flat-square
    :target: https://pypi.python.org/pypi/python-taiga
    :alt: Latest PyPI version

.. |PyVersion| image:: https://img.shields.io/pypi/pyversions/python-taiga.svg?style=flat-square
    :target: https://pypi.python.org/pypi/python-taiga
    :alt: Python versions

.. |Status| image:: https://img.shields.io/travis/nephila/python-taiga.svg?style=flat-square
    :target: https://travis-ci.org/nephila/python-taiga
    :alt: Latest Travis CI build status

.. |TestCoverage| image:: https://img.shields.io/coveralls/nephila/python-taiga/master.svg?style=flat-square
    :target: https://coveralls.io/r/nephila/python-taiga?branch=master
    :alt: Test coverage

.. |License| image:: https://img.shields.io/github/license/nephila/python-taiga.svg?style=flat-square
   :target: https://pypi.python.org/pypi/python-taiga/
    :alt: License

.. |CodeClimate| image:: https://codeclimate.com/github/nephila/python-taiga/badges/gpa.svg?style=flat-square
   :target: https://codeclimate.com/github/nephila/python-taiga
   :alt: Code Climate
