import unittest

import mox
import stubout

from py_mstr import Attribute, Metric, MstrClient, MstrClientException, MstrReportException, Prompt, Report, Singleton


class MstrClientTestCase(mox.MoxTestBase):

    def setUp(self):
        mox.MoxTestBase.setUp(self)
        s = stubout.StubOutForTesting()
        s.Set(MstrClient, '_login', lambda self, source, name, username, password: None)
        self.client = MstrClient('url?', 'username', 'pw', 'source', 'name')
        self.client._session = 'session'
        self.mox.StubOutWithMock(self.client, "_request")

    def tearDown(self):
        mox.MoxTestBase.tearDown(self)

    def test_init(self):
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
        self.mox.StubOutWithMock(MstrClient, '_request')
        self.mox.StubOutWithMock(MstrClient, '__del__')
        instance = MstrClient.__new__(MstrClient)
        instance._request(args).AndReturn(result)
        instance.__del__().AndReturn(None)
        instance.__del__().AndReturn(None)

        self.mox.ReplayAll()

        client = MstrClient('url?', 'username', 'pw', 'source', 'name')
        self.assertEqual('session', client._session)
        self.assertEqual('url?', client._base_url)

    def test_folder_contents(self):
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

        self.client._request(args1).AndReturn(result1)
        self.client._request(args2).AndReturn(result2)

        self.mox.ReplayAll()

        base_folders = self.client.get_folder_contents()
        child_folder = self.client.get_folder_contents('parent_folder')

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

    def test_list_elements(self):
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
        self.client._request(args).AndReturn(result)

        self.mox.ReplayAll()

        values = self.client.list_elements('attr_id')
        self.assertEqual(2, len(values))
        self.assertEqual('valid1', values[0])

    def test_get_attribute(self):
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
        self.client._request(args).AndReturn(result)

        self.mox.ReplayAll()

        attr = self.client.get_attribute('attr_id')
        self.assertTrue(isinstance(attr, Attribute))
        self.assertEqual('attr_id', attr.guid)
        self.assertEqual('attr_name', attr.name)


class MstrReportTestCase(mox.MoxTestBase):

    def setUp(self):
        mox.MoxTestBase.setUp(self)
        s = stubout.StubOutForTesting()
        s.Set(MstrClient, '_login', lambda self, source, name, username, password: None)
        self.client = MstrClient('url?', 'username', 'pw', 'source', 'name')
        self.client._session = 'session'
        self.mox.StubOutWithMock(self.client, "_request")
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

    def tearDown(self):
        mox.MoxTestBase.tearDown(self)

    def test_no_prompts_gives_error(self):
        """ Test that if a user tries to retrieve prompts for a report
            and the report has no prompts, that the actual report is returned,
            and subsequently an error is raised.
        """

        args = {'reportID': 'report_id', 'sessionState': 'session', 'taskId': 'reportExecute'}
        self.client._request(args).AndReturn(self.report_response)

        self.mox.ReplayAll()

        self.assertRaises(MstrReportException, self.report.get_prompts)

    def test_valid_prompts(self):
        """ Test a proper use case of retrieving the prompts for a report and
            that the message id is correctly forwarded to retrieve the prompts.
        """

        args1 = {'reportID': 'report_id', 'sessionState': 'session', 'taskId': 'reportExecute'}
        self.client._request(args1).AndReturn("<response><msg><id>msg_id</id></msg></response>")
        args2 = {'taskId': 'getPrompts', 'objectType': '3', 'msgID': 'msg_id', 'sessionState': 'session'}
        result = (
            "<response><rsl><prompts><block><reqd>false</reqd><mn>msg1</mn><junk>junk</junk><orgn><did>"
            "attr1_id</did><t>12</t><n>attr1_name</n><desc/></orgn><loc><did>guid1</did></loc></block>"
            "<block><mn>msg2</mn><reqd>true</reqd><orgn><did>attr2_id</did><t>type2</t><n>attr2_name</n>"
            "<desc/></orgn><loc><did>guid2</did></loc></block></prompts></rsl></response>"
        )
        self.client._request(args2).AndReturn(result)

        self.mox.ReplayAll()

        prompts = self.report.get_prompts()
        self.assertEqual(2, len(prompts))
        self.assertEqual(Prompt, type(prompts[0]))
        self.assertEqual('attr1_name', prompts[0].attribute.name)
        self.assertEqual('attr1_id', prompts[0].attribute.guid)
        self.assertEqual('msg1', prompts[0].prompt_str)

    def test_get_attributes(self):
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
        self.client._request(args).AndReturn(result)

        self.mox.ReplayAll()

        attrs = self.report.get_attributes()
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

    def test_error_execute(self):
        """ Test that when an error is returned by MicroStrategy,
        execute raises an exception
        """
        self.client._request(self.report_args).AndReturn(
            (
                "<taskResponse>"
                "<report_data_list><report_data><error>Object executed is in "
                "prompt status. Please resolve prompts and use the message ID."
                "</error></report_data></report_data_list></taskResponse>"
            )
        )

        self.mox.ReplayAll()

        self.assertRaises(MstrReportException, self.report.execute)
        self.assertRaises(MstrReportException, self.report.get_values)
        self.assertEqual(None, self.report._values)

    def test_basic_execute(self):
        """ Test parsing of a report for a report with no prompts.
        """

        self.client._request(self.report_args).AndReturn(self.report_response)
        self.mox.ReplayAll()

        self.report.execute()

        self.assertEqual(2, len(self.report._headers))
        self.assertEqual(2, len(self.report._values))
        attr1 = Attribute('header1_id', 'header1_name')
        attr2 = Attribute('header2_id', 'header2_name')
        self.assertEqual(attr1, self.report._headers[0])
        self.assertEqual(attr2, self.report._headers[1])
        self.assertEqual([(attr1, 'col1_val1'), (attr2, 'col2_val1')], self.report._values[0])
        self.assertEqual([(attr1, 'col1_val2'), (attr2, 'col2_val2')], self.report._values[1])

    def test_element_prompt_execute(self):
        """ Test element prompt answers are configured correctly before
            executing the report. Prompt answers do not impact the format of
            the returned report
        """

        import copy
        args1 = copy.deepcopy(self.report_args)
        args1['elementsPromptAnswers'] = 'attr1_id;attr1_id:value'
        self.client._request(args1).AndReturn(None)

        args2 = copy.deepcopy(self.report_args)
        args2['elementsPromptAnswers'] = 'attr1_id;attr1_id:val1;attr1_id:val2'
        self.client._request(args2).AndReturn(None)

        self.mox.ReplayAll()

        attr1 = Attribute('attr1_id', 'attr1_name')
        prompt1 = Prompt('p1guid', 'Prompt 1', False, attr1)
        attr2 = Attribute('attr2_id', 'attr2_name')
        prompt2 = Prompt('p2guid', 'Prompt 2', False, attr2)
        self.report.execute(element_prompt_answers={prompt1: ['value']})
        self.report.execute(element_prompt_answers={prompt1: ['val1', 'val2']})
        # test with optional prompt

        # dict iteration is non-deterministic, so test it separately
        result = self.report._format_element_prompts({prompt1: ['value1'], prompt2: ['value2']})
        self.failUnless(
            result['elementsPromptAnswers'] in [
                'attr2_id;attr2_id:value2,attr1_id;attr1_id:value1',
                'attr1_id;attr1_id:value1,attr2_id;attr2_id:value2',
            ]
        )

        result = self.report._format_element_prompts({prompt1: ['val1', 'val2'], prompt2: ['val3']})
        self.failUnless(
            result['elementsPromptAnswers'] in [
                'attr2_id;attr2_id:val3,attr1_id;attr1_id:val1;attr1_id:val2',
                'attr1_id;attr1_id:val1;attr1_id:val2,attr2_id;attr2_id:val3',
            ]
        )

    def test_value_prompt_execute(self):
        """ Test value prompt answers are correctly formated before executing the
            report.
        """

        import copy
        args1 = copy.deepcopy(self.report_args)
        args1['valuePromptAnswers'] = 'prompt1'
        self.client._request(args1).AndReturn(None)

        # multiple prompts
        args2 = copy.deepcopy(self.report_args)
        args2['valuePromptAnswers'] = 'prompt1^prompt2'
        self.client._request(args2).AndReturn(None)

        # optional prompts
        self.report_args.update({'valuePromptAnswers': '^prompt2^^prompt4^'})
        self.client._request(self.report_args).AndReturn(None)

        self.mox.ReplayAll()

        p1 = Prompt('guid1', 'P1', False)
        p2 = Prompt('guid2', 'P2', True)
        p3 = Prompt('guid3', 'P3', False)
        p4 = Prompt('guid4', 'P4', True)
        p5 = Prompt('guid5', 'P5', False)

        self.report.execute(value_prompt_answers=[(p1, 'prompt1')])
        self.report.execute(value_prompt_answers=[(p1, 'prompt1'), (p2, 'prompt2')])
        self.report.execute(value_prompt_answers=[(p1, ''), (p2, 'prompt2'), (p3, ''), (p4, 'prompt4'), (p5, '')])

    def test_value_and_element_prompt_execute(self):
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
        self.client._request(args1).AndReturn(None)

        self.mox.ReplayAll()

        attr1 = Attribute('attr1_id', 'attr1_name')
        prompt1 = Prompt('p1guid', 'Prompt 1', False, attr1)
        prompt2 = Prompt('p2guid', 'Prompt 2', False)
        prompt3 = Prompt('p3guid', 'Prompt 3', False)
        self.report.execute(
            element_prompt_answers={prompt1: ['value']},
            value_prompt_answers=[(prompt2, 'value2'), (prompt3, '')]
        )


class SingletonTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

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


class PromptTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


class AttributeTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


class MetricTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


if __name__ == "__main__":
    unittest.main()
