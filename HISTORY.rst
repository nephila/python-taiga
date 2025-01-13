.. :changelog:

*********
History
*********

.. towncrier release notes start

1.3.1 (2025-01-13)
==================

Bugfixes
--------

- Fix parser when entries is None (#169)
- Add missing swimlane to user story allowed_params (#185)
- Use pytest for tests (#190)


1.3.0 (2024-01-02)
==================

Features
--------

- Switch to bump-my-version (#140)
- Switch to Coveralls Github action (#155)
- Add a duplicate() method to Project. (#161)
- Adds SwimLane/SwimLanes models and support to add/list in Project. (#162)
- Adds the ability to read/write the default_swimlane attribute in Project. (#166)


Bugfixes
--------

- Add the version parameter to the alloed parameter so the requester can acess it. (#149)


1.2.0 (2023-08-23)
==================

Features
--------

- Add list_attachments on WikiPage (#100)
- Add refresh_token API call (#131)


Bugfixes
--------

- Add count to SearchResult object, fix wikipages attribute name in SearchResult object (#111)
- Add moveTo parameter in delete methods when needed by Taiga API (#130)
- Fix ruff linting error (#134)


1.1.0 (2023-04-23)
==================

Features
--------

- Update tooling, drop Python 2 (#59)
- Implement list_epic_attributes() (#103)
- Update packaging - python versions (#124)


Bugfixes
--------

- Update HistoryItem methods signatures (#97)
- Improve models documentation (#105)
- Add refresh token support to tests/resources/auth_users_success.json (#114)
- Fix pagination (#116)
- Update linting tools and fix code style (#117)


Improved Documentation
----------------------

- Improve documentation (#58)


1.0.0 (2019-08-08)
==================

* Add support for python 3.7
* Add support for epics
* Add support for additional attributes from Taiga 3.2/3.3
* Improve models
* Improve pagination support
* Fix and enforce code style

0.9.0 (2018-01-31)
==================

* Add support for multiple authentication backends
* Add support for self-signed and not verified SSL certificates
* Add support for webhooks
* Add pagination support for lists
* Add debian packaging
* Avoid installing tests as a separate module
* Move documentation to readthedocs
* Add support for Python 3.5/3.6

0.8.6 (2016-08-26)
==================

* Fix header values to be strings instead of boolean
* Fix requests compatibility issues
