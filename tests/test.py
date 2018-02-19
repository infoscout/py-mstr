import unittest

import mock

from py_mstr import Attribute, Metric, MstrClient, MstrReportException, Prompt, Report


class MstrTestCase(unittest.TestCase):

    def setUp(self):
        with mock.patch.object(MstrClient, '_login'):
            self.client = MstrClient('url?', 'username', 'pw', 'source', 'name')
        self.client._session = 'session'

    def tearDown(self):
        # We cannot use mock here, since __del__ is called AFTER the patch is stopped
        self.client._logout = lambda: None


class MstrClientTestCase(MstrTestCase):

    @mock.patch.object(MstrClient, '_request')
    def test_init(self, mock_mstr_client_request):
        """ Test the format of retrieving the session when logging in.
            Requires creating a separate client object in order to test _login
        """
        args = {
            'taskId': 'login',
            'server': 'source',
            'project': 'name',
            'userid': 'username',
            'password': 'pw'
        }
        result = "<response><root><sessionState>session</sessionState><name>" +\
            "</name></root></response>"
        mock_mstr_client_request.return_value = result

        client = MstrClient('url?', 'username', 'pw', 'source', 'name')
        mock_mstr_client_request.assert_called_with(args)
        self.assertEqual('session', client._session)
        self.assertEqual('url?', client._base_url)

    @mock.patch.object(MstrClient, '_request')
    def test_folder_contents(self, mock_mstr_client_request):
        """ Test folder contents are correctly parsed when either a parent
            folder is supplied or is not
        """
        args1 = {
            'sessionState': 'session',
            'taskID': 'folderBrowse',
        }
        args2 = {
            'sessionState': 'session',
            'taskID': 'folderBrowse',
            'folderID': 'parent_folder'
        }
        result1 = "<response><folders><obj><n>folder 1</n><d>description 1</d>" + \
            "description 1</d><id>id 1</id><t>type 1</t></obj><obj><n>folder 2" +\
            "</n><d>description 2</d><id>id 2</id><t>type 2</t></obj></folders>" +\
            "</response>"
        result2 = "<response><folders name='name' id='folder_id'><path>" +\
            "parent_folder</path><obj><n>child folder</n><d>description</d>" +\
            "<id>child id</id><t>8</t><st>2048</st></obj></folders></response>"
        mock_mstr_client_request.side_effect = [result1, result2]

        base_folders = self.client.get_folder_contents()
        mock_mstr_client_request.assert_called_with(args1)
        child_folder = self.client.get_folder_contents('parent_folder')
        mock_mstr_client_request.assert_called_with(args2)

        self.assertEqual(2, len(base_folders))
        self.assertEqual(
            {'name': 'folder 1', 'description': 'description 1', 'id': 'id 1', 'type': 'type 1'},
            base_folders[0]
        )
        self.assertEqual(
            {'name': 'folder 2', 'description': 'description 2', 'id': 'id 2', 'type': 'type 2'},
            base_folders[1]
        )
        self.assertEqual(1, len(child_folder))
        self.assertEqual(
            {'name': 'child folder', 'description': 'description', 'id': 'child id', 'type': '8'},
            child_folder[0]
        )

    @mock.patch.object(MstrClient, '_request')
    def test_list_elements(self, mock_mstr_client_request):
        """ Test correct values are retrieved when retrieving all the values that
            an attribute can take.
        """
        args = {
            'taskId': 'browseElements',
            'attributeID': 'attr_id',
            'sessionState': 'session'
        }
        result = (
            "<response><root><rmc></rmc><items><block><dssid>attr_id:junk"
            "</dssid><n/></block><block><dssid>attr_id:valid1</dssid><n>valid1"
            "</n></block><block><dssid>attr_id:valid2</dssid><n>valid2</n>"
            "</block></items><valueForm>dssid</valueForm><totalSize>3</totalSize>"
        )
        mock_mstr_client_request.return_value = result

        values = self.client.list_elements('attr_id')
        mock_mstr_client_request.assert_called_with(args)
        self.assertEqual(2, len(values))
        self.assertEqual('valid1', values[0])

    @mock.patch.object(MstrClient, '_request')
    def test_get_attribute(self, mock_mstr_client_request):
        """ Test retrieving information about an attribute returns a proper
            Attribute object.
        """
        args = {
            'taskId': 'getAttributeForms',
            'attributeID': 'attr_id',
            'sessionState': 'session'
        }
        result = (
            "<response><root><container><dssid>attr_id</dssid><n>"
            "attr_name</n><desc/><dssforms><block><dssid>form_guid</dssid>"
            "<n>form_name</n><desc/></block></dssforms></container></root>"
            "</response>"
        )
        mock_mstr_client_request.return_value = result

        attr = self.client.get_attribute('attr_id')
        mock_mstr_client_request.assert_called_with(args)
        self.assertTrue(isinstance(attr, Attribute))
        self.assertEqual('attr_id', attr.guid)
        self.assertEqual('attr_name', attr.name)


class MstrReportTestCase(MstrTestCase):

    def setUp(self):
        super(MstrReportTestCase, self).setUp()
        self.report = Report(self.client, 'report_id')
        self.report_response = (
            "<response><report_data_list><report_data>"
            "<prs></prs><objects><attribute rfd='0' id='header1_id' "
            "name='header1_name' type='header1_type'><form rfd='1' id='frm1_id'"
            " base_form_type='frm1_basetype' name='frm1_name' id_form='1' "
            "type='frm1_type'/></attribute><attribute rfd='2' id='header2_id' "
            "name='header2_name' type='header2_type'><form/></attribute>"
            "</objects><template></template><raw_data><headers><oi rfd='0'/>"
            "<oi rfd='2'/></headers><rows cn='100000'><r fr='1'>"
            "<v id='BB:header1_id:1:1:0:2:col1_val1'>col1_val1</v>"
            "<v id='BB:header2_id:1:1:0:3:col2_val1'>col2_val1</v></r>"
            "<r><v id='BB:header1_id:1:1:0:2:col1_val2'>col1_val2</v>"
            "<v id='BB:header2_id:1:1:0:3:col2_val2'>col2_val2</v></r></rows>"
            "</raw_data></report_data></report_data_list></response>"
        )
        self.report_args = {
            'taskId': 'reportExecute',
            'startRow': 0,
            'startCol': 0,
            'maxRows': 100000,
            'maxCols': 255,
            'styleName': 'ReportDataVisualizationXMLStyle',
            'resultFlags': '393216',
            'reportID': 'report_id',
            'sessionState': 'session'
        }

    @mock.patch.object(MstrClient, '_request')
    def test_no_prompts_gives_error(self, mock_mstr_client_request):
        """ Test that if a user tries to retrieve prompts for a report
            and the report has no prompts, that the actual report is returned,
            and subsequently an error is raised.
        """
        args = {'reportID': 'report_id', 'sessionState': 'session', 'taskId': 'reportExecute'}
        mock_mstr_client_request.return_value = self.report_response

        self.assertRaises(MstrReportException, self.report.get_prompts)
        mock_mstr_client_request.assert_called_with(args)

    @mock.patch.object(MstrClient, '_request')
    def test_valid_prompts(self, mock_mstr_client_request):
        """ Test a proper use case of retrieving the prompts for a report and
            that the message id is correctly forwarded to retrieve the prompts.
        """
        args1 = {'reportID': 'report_id', 'sessionState': 'session', 'taskId': 'reportExecute'}
        args2 = {'taskId': 'getPrompts', 'objectType': '3', 'msgID': 'msg_id', 'sessionState': 'session'}
        result = (
            "<response><rsl><prompts><block><reqd>false</reqd><mn>msg1</mn><junk>junk</junk><orgn><did>"
            "attr1_id</did><t>12</t><n>attr1_name</n><desc/></orgn><loc><did>guid1</did></loc></block>"
            "<block><mn>msg2</mn><reqd>true</reqd><orgn><did>attr2_id</did><t>type2</t><n>attr2_name</n>"
            "<desc/></orgn><loc><did>guid2</did></loc></block></prompts></rsl></response>"
        )
        mock_mstr_client_request.side_effect = ["<response><msg><id>msg_id</id></msg></response>", result]

        prompts = self.report.get_prompts()
        mock_mstr_client_request.assert_has_calls([mock.call(args1), mock.call(args2)])
        self.assertEqual(2, len(prompts))
        self.assertEqual(Prompt, type(prompts[0]))
        self.assertEqual('attr1_name', prompts[0].attribute.name)
        self.assertEqual('attr1_id', prompts[0].attribute.guid)
        self.assertEqual('msg1', prompts[0].prompt_str)

    @mock.patch.object(MstrClient, '_request')
    def test_get_attributes(self, mock_mstr_client_request):
        """ Test getting the attributes (or headers) for a report returns
            valid Attribute/Metric objects. Also test that headers are saved
            once a report has been executed or headers have been requested.
        """
        args = {'taskId': 'browseAttributeForms', 'contentType': 3, 'sessionState': 'session', 'reportID': 'report_id'}
        result = (
            "<response><forms><attrs><a><did>attr1_id</did><n>attr1_name"
            "</n><fms><block><did>form1_id</did><n>DESC</n></block></fms></a>"
            "<a><did>attr2_id</did><n>attr2_name</n><fms></fms></a></attrs>"
            "</forms></response>"
        )
        mock_mstr_client_request.return_value = result

        attrs = self.report.get_attributes()
        mock_mstr_client_request.assert_called_with(args)
        self.assertEqual(2, len(attrs))
        self.assertEqual('attr1_id', attrs[0].guid)
        self.assertEqual('attr1_name', attrs[0].name)
        self.assertEqual('attr2_id', attrs[1].guid)
        self.assertEqual('attr2_name', attrs[1].name)

        # when called a second time, should immediately
        # return same list without issuing a request
        attrs2 = self.report.get_attributes()
        self.assertEqual(attrs, attrs2)

    def test_get_headers_without_execution(self):
        self.assertRaises(MstrReportException, self.report.get_headers)

    def test_get_headers_with_execution(self):
        self.report._headers = ['h1', 'h2']
        self.assertEquals(self.report._headers, self.report.get_headers())

    def test_get_values_without_execution(self):
        self.assertRaises(MstrReportException, self.report.get_values)

    def test_get_values_with_execution(self):
        self.report._values = ['v1', 'v2']
        self.assertEquals(self.report._values, self.report.get_values())

    @mock.patch.object(MstrClient, '_request')
    def test_error_execute(self, mock_mstr_client_request):
        """ Test that when an error is returned by MicroStrategy,
        execute raises an exception
        """
        mock_mstr_client_request.return_value = (
            "<taskResponse>"
            "<report_data_list><report_data><error>Object executed is in "
            "prompt status. Please resolve prompts and use the message ID."
            "</error></report_data></report_data_list></taskResponse>"
        )

        self.assertRaises(MstrReportException, self.report.execute)
        mock_mstr_client_request.assert_called_with(self.report_args)
        self.assertRaises(MstrReportException, self.report.get_values)
        mock_mstr_client_request.assert_called_with(self.report_args)
        self.assertEqual(None, self.report._values)

    @mock.patch.object(MstrClient, '_request')
    def test_basic_execute(self, mock_mstr_client_request):
        """ Test parsing of a report for a report with no prompts.
        """
        mock_mstr_client_request.return_value = self.report_response

        self.report.execute()
        mock_mstr_client_request.assert_called_with(self.report_args)

        self.assertEqual(2, len(self.report._headers))
        self.assertEqual(2, len(self.report._values))
        attr1 = Attribute('header1_id', 'header1_name')
        attr2 = Attribute('header2_id', 'header2_name')
        self.assertEqual(attr1, self.report._headers[0])
        self.assertEqual(attr2, self.report._headers[1])
        self.assertEqual([(attr1, 'col1_val1'), (attr2, 'col2_val1')], self.report._values[0])
        self.assertEqual([(attr1, 'col1_val2'), (attr2, 'col2_val2')], self.report._values[1])

    @mock.patch.object(MstrClient, '_request')
    def test_element_prompt_execute(self, mock_mstr_client_request):
        """ Test element prompt answers are configured correctly before
            executing the report. Prompt answers do not impact the format of
            the returned report
        """
        import copy
        args1 = copy.deepcopy(self.report_args)
        args1['elementsPromptAnswers'] = 'attr1_id;attr1_id:value'

        args2 = copy.deepcopy(self.report_args)
        args2['elementsPromptAnswers'] = 'attr1_id;attr1_id:val1;attr1_id:val2'

        attr1 = Attribute('attr1_id', 'attr1_name')
        prompt1 = Prompt('p1guid', 'Prompt 1', False, attr1)
        attr2 = Attribute('attr2_id', 'attr2_name')
        prompt2 = Prompt('p2guid', 'Prompt 2', False, attr2)
        self.report.execute(element_prompt_answers={prompt1: ['value']})
        mock_mstr_client_request.assert_called_with(args1)
        self.report.execute(element_prompt_answers={prompt1: ['val1', 'val2']})
        mock_mstr_client_request.assert_called_with(args2)
        # test with optional prompt

        # dict iteration is non-deterministic, so test it separately
        result = self.report._format_element_prompts({prompt1: ['value1'], prompt2: ['value2']})
        mock_mstr_client_request.assert_called_with(args2)
        self.failUnless(
            result['elementsPromptAnswers'] in [
                'attr2_id;attr2_id:value2,attr1_id;attr1_id:value1',
                'attr1_id;attr1_id:value1,attr2_id;attr2_id:value2',
            ]
        )

        result = self.report._format_element_prompts({prompt1: ['val1', 'val2'], prompt2: ['val3']})
        mock_mstr_client_request.assert_called_with(args2)
        self.failUnless(
            result['elementsPromptAnswers'] in [
                'attr2_id;attr2_id:val3,attr1_id;attr1_id:val1;attr1_id:val2',
                'attr1_id;attr1_id:val1;attr1_id:val2,attr2_id;attr2_id:val3',
            ]
        )

    @mock.patch.object(MstrClient, '_request')
    def test_value_prompt_execute(self, mock_mstr_client_request):
        """ Test value prompt answers are correctly formated before executing the
            report.
        """
        import copy
        args1 = copy.deepcopy(self.report_args)
        args1['valuePromptAnswers'] = 'prompt1'

        # multiple prompts
        args2 = copy.deepcopy(self.report_args)
        args2['valuePromptAnswers'] = 'prompt1^prompt2'

        # optional prompts
        self.report_args.update({'valuePromptAnswers': '^prompt2^^prompt4^'})

        p1 = Prompt('guid1', 'P1', False)
        p2 = Prompt('guid2', 'P2', True)
        p3 = Prompt('guid3', 'P3', False)
        p4 = Prompt('guid4', 'P4', True)
        p5 = Prompt('guid5', 'P5', False)

        self.report.execute(value_prompt_answers=[(p1, 'prompt1')])
        mock_mstr_client_request.assert_called_with(args1)
        self.report.execute(value_prompt_answers=[(p1, 'prompt1'), (p2, 'prompt2')])
        mock_mstr_client_request.assert_called_with(args2)
        self.report.execute(value_prompt_answers=[(p1, ''), (p2, 'prompt2'), (p3, ''), (p4, 'prompt4'), (p5, '')])
        mock_mstr_client_request.assert_called_with(self.report_args)

    @mock.patch.object(MstrClient, '_request')
    def test_value_and_element_prompt_execute(self, mock_mstr_client_request):
        """ Test that when both value prompt answers and element prompt
        answers are included, the data is correctly formatted.
        """
        import copy
        args1 = copy.deepcopy(self.report_args)
        args1['elementsPromptAnswers'] = 'attr1_id;attr1_id:value'
        args1['promptsAnswerXML'] = (
            "<rsl><pa pt='5' pin='0' did='p2guid' "
            "tp='10'>value2</pa><pa pt='5' pin='0' did='p3guid' tp='10'></pa></rsl>"
        )

        attr1 = Attribute('attr1_id', 'attr1_name')
        prompt1 = Prompt('p1guid', 'Prompt 1', False, attr1)
        prompt2 = Prompt('p2guid', 'Prompt 2', False)
        prompt3 = Prompt('p3guid', 'Prompt 3', False)
        self.report.execute(
            element_prompt_answers={prompt1: ['value']},
            value_prompt_answers=[(prompt2, 'value2'), (prompt3, '')]
        )
        mock_mstr_client_request.assert_called_with(args1)


class SingletonTestCase(unittest.TestCase):

    def test_two_identical_guids_are_same_object(self):
        s1 = Attribute('guid1', 'value1')
        s2 = Attribute('guid1', 'value2')
        self.assertEqual(s1, s2)

        s2 = Attribute('guid1', 'value1')
        self.assertEqual(s1, s2)

    def test_two_dif_guids_are_different_objects(self):
        s1 = Attribute('guid1', 'value1')
        s2 = Attribute('guid2', 'value1')
        self.assertNotEqual(s1, s2)

    def test_values_are_not_singleton(self):
        s1 = Attribute('guid1', 'value1')
        s2 = Attribute('guid2', 'value1')
        self.assertNotEqual(s1, s2)

    def test_dif_classes_are_not_singleton(self):
        s1 = Attribute('guid1', 'value1')
        s2 = Metric('guid1', 'value2')
        self.assertNotEqual(s1, s2)
