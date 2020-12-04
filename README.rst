==============
python-taiga
==============

|Gitter| |PyPiVersion| |PyVersion| |Status| |TestCoverage| |CodeClimate| |License|

A python wrapper for the `Taiga REST API <http://taigaio.github.io/taiga-doc/dist/api.html>`_.

Documentation: https://python-taiga.readthedocs.io/

Usage: : https://python-taiga.readthedocs.io/usage.html


.. warning:: Version 1.1 change the signature of HistoryItem methods.
             Check the `documentation <https://python-taiga.readthedocs.io/>`_ and update your code if it uses kwargs for
             ``HistoryEntity.delete_comment`` / ``HistoryEntity.undelete_comment``.

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
