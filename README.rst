=======
py-mstr
=======

.. image:: https://circleci.com/gh/infoscout/py-mstr.svg?style=svg
    :target: https://circleci.com/gh/infoscout/py-mstr

.. image:: https://codecov.io/gh/infoscout/py-mstr/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/infoscout/py-mstr

py-mstr is a python package to connect and interact with MicroStrategy intelligence server. The code interacts with a MicroStrategy Webservices Task Processing API. Endpoint is generally ``http://hostname/MicroStrategy/asp/TaskProc.aspx?``.

Its features include:

- View folder contents
- List the elements of an ``Attribute``
- Get an ``Attribute`` based on an ``attribute_id``

On a ``Report``:

- Execute a ``Report`` with or without ``Prompts``
- Get the ``Prompt`` objects
- Get the ``Attribute`` and ``Metric`` objects that comprise the headers
- Get the ``Attribute`` objects for the columns of the ``Report``
- Get the ``Metric`` objects for the columns of the ``Report``
- Get the values for the rows of the ``Report``

Installation
============

.. code-block:: python

    pip install py-mstr

Implementation
==============

Establish connection
--------------------

First institiate the mstr_client object and establish connection:

.. code-block:: python

    from py_mstr import MstrClient

    BASE_URL = 'http://insights.infoscout.co/MicroStrategy/asp/TaskProc.aspx?"'
    USERNAME = 'johndoe'
    PASSWORD = 'passhere'
    PROJECT_SOURCE = 'ip-0AB4D138'
    PROJECT_NAME = 'MicroStrategy Tutorial Project'

    # Establish connection
    try:
        mstr_client = MstrClient(base_url=BASE_URL, username=MSTR_USERNAME, password=MSTR_PASSWORD, project_source=MSTR_PROJECT_SOURCE, project_name=MSTR_PROJECT_NAME)
    except MstrClientException, e:
        print e


Execute report
--------------

To execute a report, get a report object from mstr_client, and execute with optional prompt answers:

.. code-block:: python

    # Get report object
    report = mstr_client.get_report('481EC98441A518210472CB95B7B1734D')

    # Populate prompt objects
    attribute_state = mstr_client.get_attribute('A92CD58C4FAC38EF2672EE86B4A0E53D')

    # Execute report with Element Prompt Answers
    prompts = report.get_prompts()
    answers = {}
    for prompt in prompts:
        answers[prompt] = ['value']

    try:
        report.execute(elements_prompt_answers=answers)

        # Print out all headers.  (note returns list of Attribute or Metric objects)
        headers = report.get_headers()
        for header in headers:
            print header

        # Get values
        rows = report.get_values()
        for row in rows:
            print row # row will be a list of tuples of form (header, value)
    except MstrReportException, e:
        print e


See folder contents
-------------------

refer to this `post <http://www.scribd.com/doc/82137944/List-of-Object-Type>`_ for type number meaning
common number types: 3 - executable folder, 8 - folder, 10 - prompt

.. code-block:: python

    contents = mstr_client.get_folder_contents('parent_folder_guid')
    for content in contents:
        print 'guid: %s name: %s, type: %s, description: %s' % (content['guid'], content['name'],
            content['type'], content['description'])


Documentation
==========================

Refer to `ReadTheDocs <http://py-mstr.readthedocs.org>`_ for in depth documentation

If you want to build the docs from within a virtualenv, and Sphinx is installed globally, use::

    make html


Contributing
============

#. Check for `open issues <https://github.com/infoscout/py-mstr/issues>`_ or open a fresh issue to start a discussion around a feature idea or a bug.
#. Fork the `py-mstr <https://github.com/infoscout/py-mstr>`_ repository on Github to make your changes.
#. Write tests to show the changes work as expected.
#. Send a pull request to the maintainer. Add yourself to ``CONTRIBUTORS.txt``.
