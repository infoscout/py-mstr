import logging
import six.moves.urllib.request
import six.moves.urllib.parse
import six.moves.urllib.error

from pyquery import PyQuery as pq
import requests
import six


""" This API only supports xml format, as it relies on the format for parsing
    the data into python data structures
"""
BASE_PARAMS = {'taskEnv': 'xml', 'taskContentType': 'xml'}
BASE_URL = 'http://hostname/MicroStrategy/asp/TaskProc.aspx?'
logger = logging.getLogger(__name__)


class MstrClient(object):
    """Class encapsulating base logic for the MicroStrategy Task Proc API
    """

    def __init__(self, base_url, username, password, project_source, project_name):
        """Initialize the MstrClient by logging in and retrieving a session.

        Args:
            base_url (str): base url of form http://hostname/MicroStrategy/asp/TaskProc.aspx?
            username (str): username for project
            password (str): password for project
            project_source (str): project source of form ip-####
            project_name (str): name of project
        """
        self._base_url = base_url
        self._session = self._login(project_source, project_name, username, password)

    def __del__(self):
        """Logs the user out of the session.
        """
        self._logout()

    def __str__(self):
        return 'MstrClient session: %s' % self._session

    def _login(self, project_source, project_name, username, password):
        arguments = {
            'taskId': 'login',
            'server': project_source,
            'project': project_name,
            'userid': username,
            'password': password
        }
        logger.info("logging in.")
        response = self._request(arguments)
        d = pq(response)
        return d[0][0].find('sessionState').text

    def get_report(self, report_id):
        """Returns a report object.

        Args:
            report_id (str): report guid for the report
        """
        return Report(self, report_id)

    def get_folder_contents(self, folder_id=None):
        """Returns a dictionary with folder name, GUID, and description.

        Args:
            folder_id (str): guid of folder to list contents. If not supplied,
                returns contents of root folder

        Returns:
            list: list of dictionaries with keys id, name, description, and type as keys
        """

        arguments = {'sessionState': self._session, 'taskID': 'folderBrowse'}
        if folder_id:
            arguments.update({'folderID': folder_id})
        response = self._request(arguments)
        return self._parse_folder_contents(response)

    def _parse_folder_contents(self, response):
        d = pq(response)
        result = []
        for folder in d('folders').find('obj'):
            result.append({
                'name': folder.find('n').text,
                'description': folder.find('d').text,
                'id': folder.find('id').text,
                'type': folder.find('t').text
            })
        return result

    def list_elements(self, attribute_id):
        """Returns the elements associated with the given attribute id.

        Note that if the call fails (i.e. MicroStrategy returns an
        out of memory stack trace) the returned list is empty

        Args:
            attribute_id (str): the attribute guid

        Returns:
            list: a list of strings containing the names for attribute values
        """

        arguments = {'taskId': 'browseElements', 'attributeID': attribute_id, 'sessionState': self._session}
        response = self._request(arguments)
        return self._parse_elements(response)

    def _parse_elements(self, response):
        d = pq(response)
        result = []
        for attr in d('block'):
            if attr.find('n').text:
                result.append(attr.find('n').text)
        return result

    def get_attribute(self, attribute_id):
        """ Returns the attribute object for the given attribute id.

        Args:
            attribute_id (str): the attribute guid

        Returns:
            Attribute: Attribute object for this guid

        Raises:
            MstrClientException: if no attribute id is supplied
        """

        if not attribute_id:
            raise MstrClientException("You must provide an attribute id")
        arguments = {'taskId': 'getAttributeForms', 'attributeID': attribute_id, 'sessionState': self._session}
        response = self._request(arguments)
        d = pq(response)
        return Attribute(d('dssid')[0].text, d('n')[0].text)

    def _logout(self):
        arguments = {'sessionState': self._session}
        arguments.update(BASE_PARAMS)
        result = self._request(arguments)
        logging.info("logging out returned %s" % result)

    def _request(self, arguments, timeout=None):
        """Assembles the url and performs a get request to
        the MicroStrategy Task Service API

        Args:
            arguments (dict): Maps get key parameters to values

        Returns:
            str: the xml text response
        """

        arguments.update(BASE_PARAMS)
        request = self._base_url + six.moves.urllib.parse.urlencode(arguments)
        logger.info("submitting request %s" % request)

        try:
            response = requests.get(request, timeout=timeout)
        except requests.exceptions.Timeout as e:
            raise MstrClientException(str(e))

        if not response.ok:
            raise MstrClientException(response.text)

        logger.info("received response %s" % response.text)
        return response.text


class Singleton(type):
    """Singleton parent class to preserve memory.

    Objects are considered to be the same, and thus a new object
    does not need to be instantiated, if an object with that guid
    already exists.
    """

    def __call__(cls, *args, **kwargs):
        """Called when a new Singleton object is created.

        Singleton class checks to see if there is already a copy
        of the object in the class instances, and if so returns
        that object. Otherwise, it creates a new object of that
        subclass type.
        """
        # see if guid is in instances
        if args[0] not in cls._instances:
            cls._instances[args[0]] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[args[0]]


class Attribute(six.with_metaclass(Singleton, object)):
    """ Object encapsulating an attribute on MicroStrategy

    An attribute can take many values, all of which are elements
    of that attribute. An attribute is defined by its name and
    its guid. Its __metaclass__ is Singleton.

    Args:
        guid (str): guid for this attribute
        name (str): the name of this attribute

    Attributes:
        guid (str): attribute guid
        name (str): attribute name
    """
    _instances = {}

    def __init__(self, guid, name):
        self.guid = guid
        self.name = name

    def __repr__(self):
        return "<Attribute: guid:%s name:%s>" % (self.guid, self.name)

    def __str__(self):
        return "Attribute: %s - %s" % (self.guid, self.name)


class Metric(six.with_metaclass(Singleton, object)):
    """ Object encapsulating a metric on MicroStrategy

    A metric represents computation on attributes. A metric
    is defined by its name and its guid. Its __metaclass__ is Singleton.

    Args:
        guid (str): guid for this metric
        name (str): the name of this metric

    Attributes:
        guid (str): guid for this metric
        name (str): the name of this metric
    """
    _instances = {}

    def __init__(self, guid, name):
        self.guid = guid
        self.name = name

    def __repr__(self):
        return "<Metric: guid:%s name:%s>" % (self.guid, self.name)

    def __str__(self):
        return "Metric: %s - %s" % (self.guid, self.name)


class Prompt(object):
    """ Object encapsulating a prompt on MicroStrategy

    A prompt object has a guid and string and is or is not
    required. A prompt also potentially has an Attribute
    associated with it if it is an element prompt.

    Args:
        guid (str): guid for the prompt
        prompt_str (str): string for the prompt that is displayed
            when the user uses the web interface
        required (bool): indicates whether or not the prompt is required
        attribute (Attribute): Attribute object associated with the
            prompt if it is an element prompt

    Attributes:
        guid (str): guid for the prompt
        prompt_str (str): string for the prompt that is displayed
            when the user uses the web interface
        required (bool): indicates whether or not the prompt is required
        attribute (Attribute): Attribute object associated with the
            prompt if it is an element prompt
    """

    def __init__(self, guid, prompt_str, required, attribute=None):
        self.guid = guid
        self.prompt_str = prompt_str
        self.attribute = attribute
        self.required = required

    def __repr__(self):
        return "<Prompt: guid:%s string:%s>" % (self.guid, self.prompt_str)

    def __str__(self):
        return "Prompt: %s - %s" % (self.guid, self.prompt_str)


class Report(object):
    """Encapsulates a report in MicroStrategy

    The most common use case will be to execute a report.

    Args:
        mstr_client (MstrClient): client to be used to
            make requests
        report_id (str): report guid
    """

    def __init__(self, mstr_client, report_id):
        self._mstr_client = mstr_client
        self._id = report_id
        self._args = {'reportID': self._id, 'sessionState': mstr_client._session}
        self._attributes = []
        self._metrics = []
        self._headers = []
        self._values = None

    def __str__(self):
        return 'Report with id %s' % self._id

    def get_prompts(self):
        """ Returns the prompts associated with this report. If there are
            no prompts, this method raises an error.

        Returns:
            list: a list of Prompt objects

        Raises:
            MstrReportException: if a msgID could not be retrieved
                likely implying there are no prompts for this report.
        """

        arguments = {'taskId': 'reportExecute'}
        arguments.update(self._args)
        response = self._mstr_client._request(arguments)
        message = pq(response)('msg')('id')
        if not message:
            logger.debug("failed retrieval of msgID in response %s" % response)
            raise MstrReportException(
                "Error retrieving msgID for report. Most likely the report does not have any prompts."
            )
            return
        message_id = message[0].text
        arguments = {
            'taskId': 'getPrompts',
            'objectType': '3',
            'msgID': message_id,
            'sessionState': self._mstr_client._session
        }
        response = self._mstr_client._request(arguments)
        return self._parse_prompts(response)

    def _parse_prompts(self, response):
        """ There are many ways that prompts can be returned. This api
        currently supports a prompt that uses precreated prompt objects.
        """
        prompts = []
        d = pq(response)[0][0]
        for prompt in d.find('prompts').iterchildren():
            data = prompt.find('orgn')
            attr = None
            if data is not None:
                attr = Attribute(data.find('did').text, data.find('n').text)
            s = prompt.find('mn').text
            required = prompt.find('reqd').text
            guid = prompt.find('loc').find('did').text
            prompts.append(Prompt(guid, s, required, attribute=attr))

        return prompts

    def get_headers(self):
        """ Returns the column headers for the report. A report must have
        been executed before calling this method

        Returns:
            list: a list of Attribute/Metric objects
        """

        if self._headers:
            return self._headers
        logger.debug("Attempted to retrieve the headers for a report without prior successful execution.")
        raise MstrReportException("Execute a report before viewing the headers")

    def get_attributes(self):
        """Returns the attribute objects for the columns of this report.

        If a report has not been executed, there exists an api call
        to retrieve just the attribute objects in a Report.

        Returns:
            list: list of Attribute objects
        """
        if self._attributes:
            logger.info("Attributes have already been retrieved. Returning saved objects.")
            return self._attributes
        arguments = {'taskId': 'browseAttributeForms', 'contentType': 3}
        arguments.update(self._args)
        response = self._mstr_client._request(arguments)
        self._parse_attributes(response)
        return self._attributes

    def _parse_attributes(self, response):
        d = pq(response)
        self._attributes = [Attribute(attr.find('did').text, attr.find('n').text) for attr in d('a')]

    def get_values(self):
        """ Returns the rows for a prompt that has been executed.

        A report must have been executed for this method to run.

        Returns:
            list: list of lists containing tuples of the (Attribute/Metric, value)
            pair, where the Attribute/Metric is the object for the column header,
            and the value is that cell's value

        Raises:
            MstrReportException: if execute has not been called on this report
        """
        if self._values is not None:
            return self._values
        raise MstrReportException("Execute a report before viewing the rows")

    def get_metrics(self):
        """Returns the metric objects for the columns of this report.

        A report must have already been executed for this method to run.

        Returns:
            list: list of Attribute objects

        Raises:
            MstrReportException: if execute has not been called on this report
        """
        if self._metrics:
            return self._metrics
        logger.debug("Attempted to retrieve the metrics for a report without prior successful execution.")
        raise MstrReportException("Execute a report before viewing the metrics")

    def execute(self, start_row=0, start_col=0, max_rows=100000, max_cols=255,
                value_prompt_answers=None, element_prompt_answers=None, timeout=None):
        """Execute a report.

        Executes a report with the specified parameters. Default values
        are chosen so that most likely all rows and columns will be
        retrieved in one call. However, a client could use pagination
        by cycling through calls of execute and changing the min and max
        rows. Pagination is usefull when there is a risk of the amount of
        data causing the MicroStrategy API to run out of memory. The report
        supports any combination of optional/required value prompt answers
        and element prompt answers.

        Args:
            start_row (int): first row number to be returned
            start_col (int): first column number to be returned
            max_rows (int): maximum number of rows to return
            max_cols (int): maximum number of columns to return
            value_prompt_answers (list): list of (Prompts, strings) in order. If
                a value is to be left blank, the second argument in the tuple
                should be the empty string
            element_prompt_answers: (dict) element prompt answers represented as a
                dictionary of Prompt objects (with attr field specified)
                mapping to a list of attribute values to pass
            timeout (int): Number of seconds client will wait for server to send response

        Raises:
            MstrReportException: if there was an error executing the report.
        """

        arguments = {
            'taskId': 'reportExecute',
            'startRow': start_row,
            'startCol': start_col,
            'maxRows': max_rows,
            'maxCols': max_cols,
            'styleName': 'ReportDataVisualizationXMLStyle',
            'resultFlags': '393216'  # prevent columns from merging
        }
        if value_prompt_answers and element_prompt_answers:
            arguments.update(self._format_xml_prompts(value_prompt_answers, element_prompt_answers))
        elif value_prompt_answers:
            arguments.update(self._format_value_prompts(value_prompt_answers))
        elif element_prompt_answers:
            arguments.update(self._format_element_prompts(element_prompt_answers))
        arguments.update(self._args)
        response = self._mstr_client._request(arguments, timeout)
        self._values = self._parse_report(response)

    def _format_xml_prompts(self, v_prompts, e_prompts):
        result = "<rsl>"
        for p, s in v_prompts:
            result = result + "<pa pt='5' pin='0' did='" + p.guid + \
                "' tp='10'>" + s + "</pa>"
        result += "</rsl>"
        d = self._format_element_prompts(e_prompts)
        d['promptsAnswerXML'] = result
        return d

    def _format_value_prompts(self, prompts):
        result = ''
        for i, (prompt, s) in enumerate(prompts):
            if i > 0:
                result += '^'
            if s:
                result += s
            elif not (s == '' and type(prompt) == Prompt):
                raise MstrReportException("Invalid syntax for value prompt answers. Must pass (Prompt, string) tuples")
        return {'valuePromptAnswers': result}

    def _format_element_prompts(self, prompts):
        result = ''
        for prompt, values in six.iteritems(prompts):
            if result:
                result += ","
            if values:
                prefix = ";" + prompt.attribute.guid + ":"
                result = result + prompt.attribute.guid + ";" + prompt.attribute.guid + ":" + \
                    prefix.join(values)
            else:
                result += prompt.attribute.guid + ";"
        return {'elementsPromptAnswers': result}

    def _parse_report(self, response):
        d = pq(response)
        if self._report_errors(d):
            return None
        if not self._headers:
            self._get_headers(d)
        # iterate through the columns while iterating through the rows
        # and create a list of tuples with the attribute and value for that
        # column for each row
        return [[(self._headers[index], val.text) for index, val in enumerate(row.iterchildren())] for row in d('r')]

    def _report_errors(self, d):
        """ Performs error checking on the result from the execute
        call.

        Specifically, this method is looking for the <error> tag
        returned by MicroStrategy.

        Args:
            d (pyquery): a pyquery object

        Returns:
            bool: indicates whether or not there was an error.
            If there was an error, an exception should be raised.

        Raises:
            MstrReportException: if there was an error executing
            the report.
        """
        error = d('error')
        if error:
            raise MstrReportException(
                "There was an error running the report. Microstrategy error message: " + error[0].text
            )
            return True
        return False

    def _get_headers(self, d):
        obj = d('objects')
        headers = d('headers')
        for col in headers.children():
            elem = obj("[rfd='" + col.attrib['rfd'] + "']")
            if elem('attribute'):
                attr = Attribute(elem.attr('id'), elem.attr('name'))
                self._attributes.append(attr)
                self._headers.append(attr)
            else:
                metric = Metric(elem.attr('id'), elem.attr('name'))
                self._metrics.append(metric)
                self._headers.append(metric)


class MstrClientException(Exception):
    """Class used to raise errors in the MstrClient class
    """

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class MstrReportException(Exception):
    """Class used to raise errors in the MstrReport class
    """

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg
