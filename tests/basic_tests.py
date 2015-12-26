
import sys
import os
import json
import unittest
import cStringIO
import re
from functools import wraps, partial

from flask import url_for

sys.path.insert(0, os.path.abspath(os.path.normpath(
		os.path.join(os.path.dirname(__file__), '..'))))

from app import create_app
import db.model as m

question_file = cStringIO.StringIO('this is a fake file')
data_file = cStringIO.StringIO('this is a sample data file')

def check_result(testcase, spec, result):
	if spec is None:
		return
	elif isinstance(spec, type):
		testcase.assertIsInstance(result, spec,
			'expecting {0}, got {1}'.format(spec.__name__, type(result)))
	elif isinstance(spec, dict):
		testcase.assertIsInstance(result, dict,
			'expecting a dict, got {0}'.format(repr(result)))
		for key, child_spec in spec.iteritems():
			testcase.assertIn(key, result,
				'key {0} not found in {1}'.format(key, result))
			value = result[key]
			check_result(testcase, child_spec, value)
	elif isinstance(spec, set):
		testcase.assertIsInstance(result, dict,
			'expecting a dict, got {0}'.format(repr(result)))
		for key in spec:
			if isinstance(key, basestring):
				testcase.assertIn(key, result,
					'key {0} not found in {1}'.format(key, result))
			elif isinstance(key, tuple):
				key, child_spec = key
				testcase.assertIn(key, result,
					'key {0} not found in {1}'.format(key, result))
				value = result[key]
				check_result(testcase, child_spec, value)
	elif isinstance(spec, tuple):
		testcase.assertIsInstance(result, list,
			'expecting a list, got {0}'.format(repr(result)))
		length = len(result)
		length_expression, member_spec = spec
		match = re.match('(?P<op><|<=|==|>|>=)(?P<value>\d+)$', length_expression)
		if not match:
			testcase.fail('unable to verify result list length: {0}'.format(length_expression))
		op = match.group('op')
		v = int(match.group('value'))
		if op == '<':
			testcase.assertLess(length, v)
		elif op == '<=':
			testcase.assertLessEqual(length, v)
		elif op == '==':
			testcase.assertEqual(length, v)
		elif op == '>':
			testcase.assertGreater(length, v)
		else:
			testcase.assertGreaterEqual(length, v)
		if length:
			first = result[0]
			check_result(testcase, member_spec, first)


def run_test(method='GET', headers=None, data=None,
	content_type='application/json',
	expected_mimetype='application/json',
	expected_status_code=200,
	expected_result=None,
	environ_overrides={},
	endpoint_prefix='', **values):
	if method not in ('GET', 'PATCH', 'POST', 'HEAD', 'PUT',
			'DELETE', 'OPTIONS', 'TRACE'):
		raise ValueError, 'invalid method'
	request_data = json.dumps(data) if content_type == 'application/json' else data
	def testcase_injection_decorator(fn):
		@wraps(fn)
		def testcase_injected(*args, **kwargs):
			testcase = self = args[0]
			try:
				# return value is ignored
				fn(*args, **kwargs)
			except NotImplementedError, e:
				# implemented now
				pass

			with self.app.test_request_context():
				url = url_for(endpoint_prefix + fn.__name__[5:], **values)
			rv = self.client.open(url, method=method,
				environ_overrides=environ_overrides,
				content_type=content_type, data=request_data)
			testcase.assertEqual(rv.mimetype, expected_mimetype,
				'expected mimetype {0}, got {1}'.format(expected_mimetype, rv.mimetype))
			testcase.assertEqual(rv.status_code, expected_status_code,
				'expected status code {0}, got {1}\n{2}'.format(expected_status_code, rv.status_code, rv.get_data()))
			if expected_result is None:
				return
			if expected_mimetype == 'application/json':
				data = json.loads(rv.get_data())
				testcase.assertIsInstance(data, dict)
				# check result recursively
				check_result(self, expected_result, data)
		return testcase_injected
	return testcase_injection_decorator


for _ in ('put', 'post', 'delete', 'get'):
	locals()[_] = partial(run_test, method=_.upper(),
		endpoint_prefix='api_1_0.')



class MyTestCase(unittest.TestCase):

	def setUp(self):
		# set up stuff
		self.app = app = create_app('testing')
		self.client = app.test_client()

	def tearDown(self):
		# reverse all the changes here
		pass

	@put(
		data={'severity': 0.5},
		expected_result={
			'taskErrorType': {'taskId', 'errorTypeId', 'severity',
				'disabled', 'errorType', 'defaultSeverity',
				'errorClassId', 'errorClass'},
			'message': unicode,
		},
		taskId=999999, errorTypeId=1)
	def test_configure_task_error_type(self):
		# /tasks/<int:taskId>/errortypes/<int:errorTypeId>
		raise NotImplementedError

	def test_create_error_class(self):
		# /errorclasses/
		rv = self.client.post('/api/1.0/errorclasses/',
			content_type='application/json',
			data=json.dumps({'name': 'SomethingNew'}))
		assert rv.mimetype == 'application/json'
		data = json.loads(rv.get_data())
		assert 'errorClass' in data
		assert 'errorClassId' in data['errorClass']
		assert 'name' in data['errorClass']
		assert data['errorClass']['name'] == 'SomethingNew'
		rv = self.client.post('/api/1.0/errorclasses/',
			content_type='application/json',
			data=json.dumps({'nameX': 'SomethingNew'}))
		assert rv.mimetype == 'application/json'
		data = json.loads(rv.get_data())
		assert 'error' in data
		assert data['error'] == 'name: mandatory parameter missing'

	@post(data={'name':'deleteme','errorClassId':1,'defaultSeverity':0.5},
		expected_result={'errorType': {'errorTypeId', 'name', 'errorClassId',
		'errorClass', 'defaultSeverity'}})
	def test_create_error_type(self):
		# /errortypes/
		raise NotImplementedError

	@post(data={'name': 'deleteme', 'extract': 'deleteme'},
		expected_result={'label': {'labelId'}}, labelSetId=1)
	def test_create_label(self):
		# /labelsets/<int:labelSetId>/labels/
		raise NotImplementedError

	@post(data={'name': 'deleteme'}, expected_result={
		'labelGroup': {'labelGroupId', 'name', 'labelSetId',
		'isMandatory', 'dropDownDisplay'}}, labelSetId=1)
	def test_create_label_group(self):
		# /labelsets/<int:labelSetId>/labelgroups/
		raise NotImplementedError

	@post(expected_result={'message': unicode}, subTaskId=1668)
	def test_create_new_batches(self):
		# /subtasks/<int:subTaskId>/batches/
		raise NotImplementedError

	@post(data={'name': 'newpooltobedeleted', 'taskTypeId': 1,
		'autoScoring': True, 'dataFile': question_file},
		content_type='multipart/form-data',
		expected_result={'pool': {'poolId', 'name', 'meta',
		'taskTypeId', 'taskType', 'questions'}})
	def test_create_pool(self):
		# /pools/
		raise NotImplementedError

	@post(
		data={'name': 'mygreat', 'workTypeId': 1, 'modeId': 1},
		expected_result={'subTask': {'subTaskId', 'name'}},
		taskId=999999)
	def test_create_sub_task(self):
		# /tasks/<int:taskId>/subtasks/
		raise NotImplementedError

	@post(data={'rateId': 1, 'multiplier': 2.0}, expected_result={
		'subTaskRate': {'subTaskRateId', 'rateId', 'subTaskId',
		'multiplier'}}, subTaskId=1668)
	def test_create_sub_task_rate_record(self):
		# /subtasks/<int:subTaskId>/rates/
		raise NotImplementedError

	@post(data={'name': 'deleteme', 'tagType':'Event',
		'extractStart': '<deleteme>', 'surround':False, 'split': False,
		'extend': False, 'previewId': 8},
		expected_result={'message': unicode, 'tag': {'tagId', 'name',
		'tagType', 'extractStart', 'extractEnd', 'shortcutKey'}}, tagSetId=1)
	def test_create_tag(self):
		# /tagsets/<int:tagSetId>/tags/
		raise NotImplementedError

	@post(data={'options': {}, 'dataFile': data_file},
		content_type='multipart/form-data',
		expected_result={'message': unicode, 'load': {'loadId', 'taskId',
		'createdAt', 'createdBy'}}, taskId=999991)
	def test_create_task_load(self):
		# /tasks/<int:taskId>/loads/
		raise NotImplementedError

	def test_create_task_utterrance_selection(self):
		# /tasks/<int:taskId>/selections/
		raise NotImplementedError

	def test_create_test(self):
		# /tests/
		raise NotImplementedError

	def test_delete_custom_utterance_group(self):
		# /tasks/<int:taskId>/uttgroups/<int:groupId>
		raise NotImplementedError

	@delete(expected_result={'message': unicode},
		labelSetId=1, labelGroupId=1)
	def test_delete_label_group(self):
		# /labelsets/<int:labelSetId>/labelgroups/<int:labelGroupId>
		raise NotImplementedError

	def test_delete_task_utterrance_selection(self):
		# /tasks/<int:taskId>/selections/<int:selectionId>
		raise NotImplementedError

	def test_disable_task_error_type(self):
		# /tasks/<int:taskId>/errortypes/<int:errorTypeId>
		with self.app.test_request_context():
			url = url_for('api_1_0.disable_task_error_type', taskId=999999, errorTypeId=1)
		rv = self.client.delete(url)
		assert rv.content_type == 'application/json'
		data = json.loads(rv.get_data())
		assert 'message' in data
		assert 'taskErrorType' in data
		assert data['taskErrorType']['taskId'] == 999999
		assert data['taskErrorType']['errorTypeId'] == 1
		assert data['taskErrorType']['disabled'] == True

	@delete(expected_result={'message': unicode}, environ_overrides={
		'REMOTE_ADDR': '123.123.78.90'}, subTaskId=1668)
	def test_dismiss_all_batches(self):
		# /subtasks/<int:subTaskId>/batches/
		raise NotImplementedError

	def test_get_task_extract(self):
		# /tasks/<int:taskId>/extract_<timestamp>.txt
		raise NotImplementedError

	@get(expected_result={'batch': {'batchId', 'taskId', 'subTaskId',
		'priority', 'onHold', 'checkedOut', 'userId', 'userName',
		'leaseExpires', 'leaseGranted', 'pages'}}, batchId=334382)
	def test_get_batch(self):
		# /batches/<int:batchId>
		raise NotImplementedError

	@get(expected_result={'stat': {'itemCount', 'pageCount', 'unitCount'}},
		batchId=334382)
	def test_get_batch_stats(self):
		# /batches/<int:batchId>/stat
		raise NotImplementedError

	@get(expected_result={'errorClasses': ('>0', {'errorClassId', 'name'})})
	def test_get_error_classes(self):
		# /errorclasses/
		raise NotImplementedError

	@get(expected_result={'errorTypes': ('>0', {'errorTypeId', 'name',
		'errorClassId', 'errorClass', 'defaultSeverity', 'isStandard'})})
	def test_get_error_types(self):
		# /errortypes/
		raise NotImplementedError

	@get(expected_result={'fileHandlers': ('>0', {'handlerId', 'name',
		'description', ('options', list)})})
	def test_get_file_handlers(self):
		# /filehandlers/
		raise NotImplementedError

	@get(expected_result={'error': unicode}, expected_status_code=404,
		labelSetId=3)
	@get(expected_result={'labelSet': {'labelSetId', 'created',
		'labelGroups', 'ungroupedLabels'}}, labelSetId=1)
	def test_get_label_set(self):
		# /labelsets/<int:labelSetId>
		raise NotImplementedError

	@get(expected_result={'labelSets': ('>0', {'labelSetId', 'created'})})
	def test_get_label_sets(self):
		# /labelsets/
		raise NotImplementedError

	def test_get_pool(self):
		# /pools/<int:poolId>
		rv = self.client.get('/api/1.0/pools/1')
		assert rv.mimetype == 'application/json'
		data = json.loads(rv.get_data())
		assert 'pool' in data
		assert isinstance(data['pool'], dict)
		assert 'name' in data['pool']
		assert 'poolId' in data['pool']
		assert 'meta' in data['pool']
		assert 'autoScoring' in data['pool']
		assert 'questions' in data['pool']
		assert 'taskTypeId' in data['pool']
		assert 'taskType' in data['pool']
		assert isinstance(data['pool']['meta'], dict)
		assert isinstance(data['pool']['questions'], list)
		assert data['pool']['name'] == 'My Fake Test Pool'
		rv = self.client.get('/api/1.0/pools/125')
		assert rv.mimetype == 'application/json'
		assert rv.status_code == 404
		data = json.loads(rv.get_data())
		assert 'error' in data
		assert data['error'] == 'pool 125 not found'

	@get(expected_result={'pools': ('>0', {'poolId', 'name', 'autoScoring',
		'meta', 'taskTypeId', 'taskType', 'questions'})})
	def test_get_pools(self):
		# /pools/
		raise NotImplementedError

	def test_get_project(self):
		# /projects/<int:projectId>
		rv = self.client.get('/api/1.0/projects/10000')
		assert rv.mimetype == 'application/json'
		data = json.loads(rv.get_data())
		assert 'project' in data
		assert 'projectId' in data['project']
		assert 'name' in data['project']
		assert 'description' in data['project']
		assert 'created' in data['project']
		assert 'migratedBy' in data['project']
		rv = self.client.get('/api/1.0/projects/000')
		assert rv.mimetype == 'application/json'
		assert rv.status_code == 404
		data = json.loads(rv.get_data())
		assert 'error' in data

	@get(expected_result={'projects': ('>0', {'projectId', 'name',
		'description', 'migratedBy', 'created'})})
	def test_get_projects(self):
		# /projects/
		# rv = self.client.get('/api/1.0/projects')
		# assert rv.status_code == 301
		# rv = self.client.get('/api/1.0/projects/')
		# assert rv.mimetype == 'application/json'
		# data = json.loads(rv.get_data())
		# assert 'projects' in data
		# assert isinstance(data['projects'], list)
		# assert len(data['projects']) > 0
		rv = self.client.get('/api/1.0/projects/?t=candidate')
		assert rv.mimetype == 'application/json'
		data = json.loads(rv.get_data())
		assert 'projects' in data
		assert len(data['projects']) > 0

	def test_get_rate(self):
		# /rates/<int:rateId>
		rv = self.client.get('/api/1.0/rates/1')
		assert rv.mimetype == 'application/json'
		data = json.loads(rv.get_data())
		assert 'rate' in data
		assert isinstance(data['rate'], dict)
		assert 'name' in data['rate']
		assert data['rate']['name'] == 'Standard Curve'
		rv = self.client.get('/api/1.0/rates/313')
		assert rv.mimetype == 'application/json'
		assert rv.status_code == 404
		data = json.loads(rv.get_data())
		assert 'error' in data
		assert data['error'] == 'rate 313 not found'

	@get(expected_result={'rates': ('>0', {'rateId', 'name',
		'standardValue', 'targetAccuracy', 'maxValue', 'details'})})
	def test_get_rates(self):
		# /rates/
		raise NotImplementedError

	@put(
		data={'handlerId': 1},
		expected_result={('message', unicode)},
		taskId=999999)
	def test_configure_task_file_handler(self):
		# /tasks/<int:taskId>/filehandlers/
		raise NotImplementedError

	def test_get_sheet(self):
		rv = self.client.get('/api/1.0/sheets/6')
		assert rv.mimetype == 'application/json'
		data = json.loads(rv.get_data())
		assert 'sheet' in data
		assert isinstance(data['sheet'], dict)
		assert 'sheetId' in data['sheet']
		assert 'testId' in data['sheet']
		assert 'user' in data['sheet']
		assert 'nTimes' in data['sheet']
		assert 'moreAttempts' in data['sheet']
		# TODO: check if sheet content contains answers
		rv = self.client.get('/api/1.0/sheets/1')
		assert rv.mimetype == 'application/json'
		assert rv.status_code == 404
		data = json.loads(rv.get_data())
		assert 'error' in data
		assert data['error'] == 'sheet 1 not found'

	@get(expected_result={'sheet': {
			'comment': None, 'tStartedAt': None, 'tExpiresBy': None,
			'tExpiredAt': None, 'tFinishedAt': None,
			'entries': ('>0', {
				'index': int,
				'question': {'respondentData', 'scorerData'},
				'sheetEntryId': int,
				'sheetId': int
			})
		}}, sheetId=6)
	def test_get_sheet_with_markings(self):
		# /sheets/<int:sheetId>/markings/
		raise NotImplementedError

	@get(expected_result={'subTask': {'subTaskId', 'name', 'taskId',
		'workTypeId', 'workType'}}, subTaskId=2084)
	def test_get_sub_task(self):
		# /subtasks/<int:subTaskId>
		raise NotImplementedError

	@get(expected_result={'batches': ('>0', {'batchId', })},
		subTaskId=1664)
	def test_get_sub_task_batches(self):
		# /subtasks/<int:subTaskId>/batches/
		raise NotImplementedError

	@get(expected_result={'subtotals': ('>0', {'totalId', 'date',
		'subTaskId', 'userId', 'userName', 'items', 'units'})},
		subTaskId=1802)
	def test_get_sub_task_daily_subtotals(self):
		# /subtasks/<int:subTaskId>/dailysubtotals/
		raise NotImplementedError

	@get(expected_result={'subTaskRates': ('>0', {'subTaskRateId',
		'subTaskId', 'rateId', 'rateName', 'multiplier', 'updatedAt',
		'updatedBy', 'validFrom'})}, subTaskId=1802)
	def test_get_sub_task_rate_records(self):
		# /subtasks/<int:subTaskId>/rates/
		raise NotImplementedError

	@get(expected_result={'events': ('>0', {'subTaskId', 'selectionId',
		'amount', 'populating', 'tProcessedAt', 'operator'})},
		subTaskId=2728)
	def test_get_sub_task_rework_load_records(self):
		# /subtasks/<int:subTaskId>/loads/
		raise NotImplementedError

	@get(expected_result={'batchCount'}, subTaskId=2148)
	def test_get_sub_task_statistics(self):
		# /subtasks/<int:subTaskId>/stats/
		raise NotImplementedError

	def test_get_sub_task_warnings(self):
		# /subtasks/<int:subTaskId>/warnings/
		raise NotImplementedError

	@get(expected_result={'intervals': ('>0', {'workIntervalId',
		'taskId', 'subTaskId', 'startTime', 'endTime', 'status'})},
		subTaskId=1802)
	def test_get_sub_task_work_intervals(self):
		# /subtasks/<int:subTaskId>/intervals/
		raise NotImplementedError

	@get(expected_result={'metrics': ('>0', {'metricId', 'userId',
		'subTaskId', 'workIntervalId', 'userId', 'accuracy', 'amount',
		'lastUpdated', 'words', 'workRate'})}, subTaskId=179)
	def test_get_sub_task_work_metrics(self):
		# /subtasks/<int:subTaskId>/metrics/
		raise NotImplementedError

	@get(expected_result={'workers': ('>0', {'userId', 'userName', 'removed',
		'lastWorked', 'overall', 'recent'})}, subTaskId=179)
	def test_get_sub_task_worker_performance_records(self):
		# /subtasks/<int:subTaskId>/performance/
		raise NotImplementedError

	@get(expected_result={'workers': ('>0', {'userId', 'userName', 'removed',
		'taskId', 'subTaskId', 'paymentFactor', 'isNew',
		'hasReadInstructions'})}, subTaskId=179)
	def test_get_sub_task_workers(self):
		# /subtasks/<int:subTaskId>/workers/
		raise NotImplementedError

	@get(expected_result={'tagSet': {'tagSetId': int,
		'lastUpdated': None, 'created': None,
		'tags': ('>0', {'tagId', 'tagType', 'tagSetId', 'extractStart'})}},
		tagSetId=1)
	def test_get_tag_set(self):
		# /tagsets/<int:tagSetId>
		raise NotImplementedError

	@get(expected_result={'tagSets': ('>0', {'tagSetId', 'created',
		'lastUpdated', ('tags', list)})})
	def test_get_tag_sets(self):
		# /tagsets/
		raise NotImplementedError

	@get(expected_result={'task': {'taskId', 'name', 'projectId',
		'status', 'srcDir', 'migratedBy'}}, taskId=999999)
	@get(expected_result={'error': unicode},
		expected_status_code=404, taskId=382)
	def test_get_task(self):
		# /tasks/<int:taskId>
		raise NotImplementedError

	@get(expected_result={'utteranceGroups': ('>0', {'groupId', 'name',
		'created', 'rawPieces'})}, taskId=999999)
	def test_get_task_custom_utterance_groups(self):
		# /tasks/<int:taskId>/uttgroups/
		raise NotImplementedError

	@get(expected_result={'subtotals': ('>0', {'totalId', 'date',
		'subTaskId', 'userId', 'userName', 'items', 'units'})},
		taskId=999999)
	def test_get_task_daily_subtotals(self):
		# /tasks/<int:taskId>/dailysubtotals/
		raise NotImplementedError

	@get(expected_result={'errorClasses': ('>0', {'errorClassId', 'name'})},
		taskId=999999)
	def test_get_task_error_classes(self):
		# /tasks/<int:taskId>/errorclasses/
		raise NotImplementedError

	@get(expected_result={'taskErrorTypes': ('>0', {'taskId', 'errorTypeId',
		'errorType', 'errorClassId', 'errorClass', 'severity',
		'defaultSeverity', 'disabled'})}, taskId=999999)
	def test_get_task_error_types(self):
		# /tasks/<int:taskId>/errortypes/
		raise NotImplementedError

	@get(expected_result={'instructions': ('>0', {'basename', 'path'})},
		taskId=999999)
	def test_get_task_instruction_files(self):
		# /tasks/<int:taskId>/instructions/
		raise NotImplementedError

	@get(expected_result={'loads': ('>0', {'loadId', 'taskId', 'createdAt',
		('createdBy', dict)})}, taskId=999999)
	def test_get_task_loads(self):
		# /tasks/<int:taskId>/loads/
		raise NotImplementedError

	def test_get_task_payment_statistics(self):
		# /tasks/<int:taskId>/paystats/
		raise NotImplementedError

	@get(expected_result={'payments': ('==0', {'calculatedPaymentId',
		'payrollId', 'taskId', 'subTaskId', 'workIntervalId', 'userId',
		'userName', 'amount', 'originalAmount', 'updated', 'receipt',
		'items', 'units', 'qaedItems', 'qaedUnits', 'accuracy'})},
		taskId=300464)
	def test_get_task_payments(self):
		# /tasks/<int:taskId>/payments/
		raise NotImplementedError

	@get(expected_result={'rawPieces': ('>0', {'rawPieceId', 'rawText',
		'allocationContext', 'assemblyContext', 'words', 'hypothesis'})},
		taskId=999999)
	def test_get_task_raw_pieces(self):
		# /tasks/<int:taskId>/rawpieces/
		raise NotImplementedError

	@get(expected_result={'subTasks': ('>0', {'subTaskId', 'name', 'modeId',
		'taskId', 'taskTypeId', 'taskType', 'workTypeId', 'workType',
		'maxPageSize', 'defaultLeaseLife'})}, taskId=999999)
	def test_get_task_sub_tasks(self):
		# /tasks/<int:taskId>/subtasks/
		raise NotImplementedError

	def test_get_task_summary(self):
		# /tasks/<int:taskId>/summary/
		raise NotImplementedError

	@get(expected_result={'supervisors': ('>0', {'taskId', 'userId',
		'userName', 'receivesFeedback', 'informLoads'})}, taskId=999999)
	def test_get_task_supervisors(self):
		# /tasks/<int:taskId>/supervisors/
		raise NotImplementedError

	@get(expected_result={'selections': ('>0', {'selectionId', 'name',
		'taskId', 'userId', 'userName', 'random', ('filters', list)})},
		taskId=300735)
	def test_get_task_utterrance_selections(self):
		# /tasks/<int:taskId>/selections/
		raise NotImplementedError

	def test_get_task_warnings(self):
		# /tasks/<int:taskId>/warnings/
		raise NotImplementedError

	@get(expected_result={'workers': ('>0', {'userId', 'userName',
		'taskId', 'subTaskId', 'removed', 'isNew', 'paymentFactor',
		'hasReadInstructions'})}, taskId=999999)
	def test_get_task_workers(self):
		# /tasks/<int:taskId>/workers/
		raise NotImplementedError

	@get(expected_result={'tasks': ('>0', {'taskId', 'name', 'projectId',
		'status', 'taskTypeId', 'taskType', 'migrated', 'migratedBy'})})
	def test_get_tasks(self):
		# /tasks/
		raise NotImplementedError

	def test_get_test(self):
		# /tests/<int:testId>
		rv = self.client.get('/api/1.0/tests/1')
		assert rv.mimetype == 'application/json'
		data = json.loads(rv.get_data())
		assert 'test' in data
		assert isinstance(data['test'], dict)
		assert 'testId' in data['test']
		assert 'name' in data['test']
		assert 'description' in data['test']
		assert 'testType' in data['test']
		assert 'requirement' in data['test']
		assert 'timeLimit' in data['test']
		assert 'passingScore' in data['test']
		assert 'isEnabled' in data['test']
		assert 'instructionPage' in data['test']
		assert isinstance(data['test']['requirement'], dict)
		assert data['test']['testType'] in ('static', 'dynamic')
		if data['test']['testType'] == 'dynamic':
			assert 'size' in data['test']
		assert data['test']['name'] == 'My Fake Test'
		rv = self.client.get('/api/1.0/tests/125')
		assert rv.mimetype == 'application/json'
		assert rv.status_code == 404
		data = json.loads(rv.get_data())
		assert 'error' in data
		assert data['error'] == 'test 125 not found'

	@get(expected_result={'sheets': ('>0', {'sheetId', 'testId', 'nTimes',
		'user', 'tStartedAt', 'tExpiresBy', 'tExpiredAt', 'tFinishedAt',
		'score', 'comment', 'moreAttempts', ('entries', list)})}, testId=1)
	def test_get_test_sheets(self):
		# /tests/<int:testId>/sheets/
		raise NotImplementedError

	@get(expected_result={'tests': ('>0', {'testId', 'name', 'poolId',
		'taskTypeId', 'taskType', 'requirement', 'passingScore',
		'timeLimit', 'testType'})})
	def test_get_tests(self):
		# /tests/
		raise NotImplementedError

	@get(expected_result={'words': int}, taskId=999999, groupId=814)
	def test_get_utterance_group_word_count(self):
		# /tasks/<int:taskId>/uttgroups/<int:groupId>/words
		raise NotImplementedError

	@put(expected_result={
			'project': {'projectId', 'name'},
		}, projectId=60112)
	def test_migrate_project(self):
		# /projects/<int:projectId>
		raise NotImplementedError

	@put(data={'taskTypeId':1},
		expected_result={
			'task': {'taskId', 'name', 'migrated', 'migratedBy',
				'taskTypeId', 'taskType'}},
		taskId=1500)
	def test_migrate_task(self):
		# /tasks/<int:taskId>
		raise NotImplementedError

	def test_populate_task_utterrance_selection(self):
		# /tasks/<int:taskId>/selections/<int:selectionId>
		raise NotImplementedError

	@delete(expected_result={'message', unicode}, taskId=999999, userId=658)
	def test_remove_task_supervisor(self):
		# /tasks/<int:taskId>/supervisors/<int:userId>
		raise NotImplementedError

	@post(data={'sheetEntryId': 25, 'answer': 'whatever'},
		expected_result={'message': unicode, 'answer': {'answerId',
		'answer', 'sheetEntryId', 'tCreatedAt'}}, sheetId=6)
	def test_submit_answer(self):
		# /sheets/<int:sheetId>/answers/
		raise NotImplementedError

	@post(data={'moreAttempts': True, 'comment': 'great job',
		'markings': [{'score':10}, {'score':10}, {'score':5},
		{'score':0}, {'score':0}]},
		expected_result={'message', 'sheet'}, sheetId=6)
	def test_submit_marking(self):
		# /sheets/<int:sheetId>/markings/
		raise NotImplementedError

	@delete(expected_result={'message': unicode}, sheetId=6)
	def test_submit_sheet(self):
		# /sheets/<int:sheetId>
		raise NotImplementedError

	@delete(expected_result={'message': unicode}, taskId=999999)
	def test_unassign_all_task_workers(self):
		# /tasks/<int:taskId>/workers/
		raise NotImplementedError

	@put(expected_result={'error': unicode}, expected_status_code=400,
		batchId=334382, userId=1920)
	@put(expected_result={'message': unicode}, batchId=334382, userId=699)
	def test_assign_batch_to_user(self):
		# /batches/<int:batchId>/users/<int:userId>
		raise NotImplementedError

	@delete(expected_result={'message', unicode}, batchId=334382)
	def test_unassign_batch(self):
		# /batches/<int:batchId>/users/
		raise NotImplementedError

	@put(data={'priority': '+3', 'batchIds': [304793, 304794]},
		expected_result={'message'}, subTaskId=1802)
	def test_update_batches(self):
		# /subtasks/<int:subTaskId>/batches/
		raise NotImplementedError

	@put(data={'name': 'it cant be this', 'description': 'good',
		'labelGroupId': None},
		expected_result={'label': {'labelId', 'name', 'labelGroupId'},
		'message': unicode, 'updatedFields': list},
		labelSetId=1, labelId=3)
	def test_update_label(self):
		# /labelsets/<int:labelSetId>/labels/<int:labelId>
		raise NotImplementedError

	@put(data={'dropDownDisplay': True}, expected_result={'message':
		unicode, 'labelGroup': {'labelGroupId'}, 'updatedFields': list},
		labelSetId=1, labelGroupId=16)
	def test_update_label_group(self):
		# /labelsets/<int:labelSetId>/labelgroups/<int:labelGroupId>
		raise NotImplementedError

	@put(data={'name': 'somethingdifferent'},
		expected_result={'message': unicode, 'updatedFields': list},
		subTaskId=1664)
	def test_update_sub_task(self):
		# /subtasks/<int:subTaskId>
		raise NotImplementedError

	@get(expected_result={'qaConfig': {'workSubTaskId', 'qaSubTaskId',
		'defaultExpectedAccuracy', 'samplingError', 'confidenceInterval',
		'populateRework', 'accuracyThreshold', 'reworkSubTaskId'}},
		subTaskId=179)
	def test_get_sub_task_qa_settings(self):
		# /subtasks/<int:subTaskId>/qasettings/
		raise NotImplementedError

	@delete(expected_result={'message': unicode}, subTaskId=1685)
	def test_delete_sub_task_qa_settings(self):
		# /subtasks/<int:subTaskId>/qasettings/
		raise NotImplementedError

	@put(data={'confidenceInterval': 0.9, 'samplingError': 0.04,
		'defaultExpectedAccuracy': 0.9, 'qaSubTaskId': 1958},
		expected_result={'message', 'qaConfig', 'updatedFields'},
		subTaskId=1685)
	@put(data={'confidenceInterval': 0.95, 'samplingError': 0.02,
		'defaultExpectedAccuracy': 0.85, 'qaSubTaskId': 1958},
		expected_result={'message', 'qaConfig', 'updatedFields'},
		subTaskId=1685)
	def test_update_sub_task_qa_settings(self):
		# /subtasks/<int:subTaskId>/qasettings/
		raise NotImplementedError

	@put(data={'name': 'KEYWORD', 'extractStart': '<KKKEEEYYY>',
		'surround': True, 'split': True, 'extend': True},
		expected_result={'message': unicode, 'tag': {'tagId', 'name',
		'tagType', 'extractStart', 'extractEnd', 'shortcutKey'}},
		tagSetId=1, tagId=4)
	@put(data={'name': 'Key word', 'extractStart': '<Keyword>',
		'surround': False, 'split': False, 'extend': False},
		expected_result={'message': unicode, 'tag': {'tagId', 'name',
		'tagType', 'extractStart', 'extractEnd', 'shortcutKey'}},
		tagSetId=1, tagId=4)
	def test_update_tag(self):
		# /tagsets<int:tagSetId>/tags/<int:tagId>
		raise NotImplementedError

	def test_update_task_error_types(self):
		# /tasks/<int:taskId>/errortypes/
		raise NotImplementedError

	@put(
		data={'status': m.Task.STATUS_CLOSED},
		expected_result={'message': unicode},
		taskId=999999)
	def test_update_task_status(self):
		# /tasks/<int:taskId>/status
		raise NotImplementedError

	@put(
		data={'informLoads': True},
		expected_result={
			'supervisor',
		},
		taskId=999999, userId=699)
	def test_update_task_supervisor_settings(self):
		# /tasks/<int:taskId>/supervisors/<int:userId>
		raise NotImplementedError

	def test_upload_task_instruction_file(self):
		# /tasks/<int:taskId>/instructions/
		raise NotImplementedError

	def test_index(self):
		# /
		raise NotImplementedError

	def test_static(self):
		# /static/<path:filename>
		raise NotImplementedError

	def test_webservices_apply_user_search_action(self):
		# /webservices/apply_user_search_action
		raise NotImplementedError

	def test_webservices_apply_user_search_filters(self):
		# /webservices/apply_user_search_filters
		raise NotImplementedError

	def test_webservices_get_available_qualification_tests(self):
		# /webservices/available_qualifications
		raise NotImplementedError

	def test_webservices_get_available_work_entries(self):
		# /webservices/available_work
		raise NotImplementedError

	def test_webservices_get_recent_work_entries(self):
		# /webservices/recent_work
		raise NotImplementedError

	def test_webservices_get_user_details(self):
		# /webservices/user_details
		raise NotImplementedError

	def test_webservices_get_user_details_css(self):
		# /webservices/get_user_details_css
		raise NotImplementedError

	def test_webservices_get_user_details_js(self):
		# /webservices/get_user_details_js
		raise NotImplementedError

	def test_webservices_get_user_search_actions(self):
		# /webservices/get_user_search_actions
		raise NotImplementedError

	def test_webservices_get_user_search_filters(self):
		# /webservices/get_user_search_filters
		raise NotImplementedError

	def test_webservices_update_payments(self):
		# /webservices/update_payments
		raise NotImplementedError

if __name__ == '__main__':
	unittest.main()
