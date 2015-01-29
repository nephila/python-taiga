# -*- coding: utf-8 -*-

from taiga import TaigaAPI

api = TaigaAPI()

api.auth(
    username='yourusername',
    password='yourpassword'
)

new_project = api.projects.create('TEST PROJECT', 'TESTING API')

new_project.name = 'TEST PROJECT 2'
new_project.update()

jan_feb_milestone = new_project.add_milestone(
    'New milestone jan feb', '2015-01-26', '2015-02-26'
)

userstory = new_project.add_user_story(
    'New Story', description='Blablablabla',
    milestone=jan_feb_milestone.id
)
userstory.attach('Read the README in User Story', 'README.md')

userstory.add_task('New Task 2',
    new_project.task_statuses[0].id
).attach('Read the README in Task', 'README.md')

print (userstory.list_tasks())

newissue = new_project.add_issue(
    'New Issue',
    new_project.priorities.get(name='High').id,
    new_project.issue_statuses.get(name='New').id,
    new_project.issue_types.get(name='Bug').id,
    new_project.severities.get(name='Minor').id,
    description='Bug #5'
).attach('Read the README in Issue', 'README.md')

projects = api.projects.list()
print (projects)

for user in projects[0].users:
    print (user)

stories = api.user_stories.list()
print (stories)

projects[0].star()

api.milestones.list()

print api.search(projects[0].id, 'New').user_stories[0].subject
