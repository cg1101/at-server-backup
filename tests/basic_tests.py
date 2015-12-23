
import sys
import os
import json
import unittest
import re
from functools import wraps, partial

from flask import url_for

sys.path.insert(0, os.path.abspath(os.path.normpath(
		os.path.join(os.path.dirname(__file__), '..'))))

from app import create_app
import db.model as m


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
	endpoint_prefix='', **values):
	if method not in ('GET', 'PATCH', 'POST', 'HEAD', 'PUT',
			'DELETE', 'OPTIONS', 'TRACE'):
		raise ValueError, 'invalid method'
	request_data = json.dumps(data) if content_type == 'application/json' else data
	def testcase_injection_decorator(fn):
		@wraps(fn)
		def testcase_injected(*args, **kwargs):
			testcase = self = args[0]
			with self.app.test_request_context():
				url = url_for(endpoint_prefix + fn.__name__[5:], **values)
			rv = self.client.open(url, method=method,
				content_type=content_type, data=request_data)
			testcase.assertEqual(rv.mimetype, expected_mimetype,
				'expected mimetype {0}, got {1}'.format(expected_mimetype, rv.mimetype))
			testcase.assertEqual(rv.status_code, expected_status_code,
				'expected status code {0}, got {1}'.format(expected_status_code, rv.status_code))
			if expected_result is None:
				return fn(*args, **kwargs)
			if expected_mimetype == 'application/json':
				data = json.loads(rv.get_data())
				testcase.assertIsInstance(data, dict)
				# check result recursively
				check_result(self, expected_result, data)
			return fn(*args, **kwargs)
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
		pass

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


	def test_create_error_type(self):
		# /errortypes/
		pass

	def test_create_label(self):
		# /labelsets/<int:labelSetId>/labels/
		pass

	def test_create_label_group(self):
		# /labelsets/<int:labelSetId>/labelgroups/
		pass

	def test_create_new_batches(self):
		# /subtasks/<int:subTaskId>/batches/
		pass

	def test_create_pool(self):
		# /pools/
		pass

	@post(
		data={'name': 'mygreat', 'workTypeId': 1, 'modeId': 1},
		expected_result={'subTask': {'subTaskId', 'name'}},
		taskId=999999)
	def test_create_sub_task(self):
		# /tasks/<int:taskId>/subtasks/
		pass

	def test_create_sub_task_rate_record(self):
		# /subtasks/<int:subTaskId>/rates/
		pass

	def test_create_tag(self):
		# /tagsets/<int:tagSetId>/tags/
		pass

	def test_create_task_load(self):
		# /tasks/<int:taskId>/loads/
		pass

	def test_create_task_utterrance_selection(self):
		# /tasks/<int:taskId>/selections/
		pass

	def test_create_test(self):
		# /tests/
		pass

	def test_delete_custom_utterance_group(self):
		# /tasks/<int:taskId>/uttgroups/<int:groupId>
		pass

	def test_delete_label_group(self):
		# /labelsets/<int:labelSetId>/labelgroups/<int:labelGroupId>
		pass

	def test_delete_sub_task_qa_settings(self):
		# /subtasks/<int:subTaskId>/qasettings/
		pass

	def test_delete_task_utterrance_selection(self):
		# /tasks/<int:taskId>/selections/<int:selectionId>
		pass

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

	def test_dismiss_all_batches(self):
		# /subtasks/<int:subTaskId>/batches/
		pass

	def test_get_task_extract(self):
		# /tasks/<int:taskId>/extract_<timestamp>.txt
		pass

	def test_get_batch(self):
		# /batches/<int:batchId>
		pass

	def test_get_batch_stats(self):
		# /batches/<int:batchId>/stat
		pass

	@get(expected_result={'errorClasses': ('>0', {'errorClassId', 'name'})})
	def test_get_error_classes(self):
		# /errorclasses/
		pass

	@get(expected_result={'errorTypes': ('>0', {'errorTypeId', 'name',
		'errorClassId', 'errorClass', 'defaultSeverity', 'isStandard'})})
	def test_get_error_types(self):
		# /errortypes/
		pass

	@get(expected_result={'fileHandlers': ('>0', {'handlerId', 'name',
		'description', ('options', list)})})
	def test_get_file_handlers(self):
		# /filehandlers/
		pass

	def test_get_label_set(self):
		# /labelsets/<int:labelSetId>
		pass

	@get(expected_result={'labelSets': ('>0', {'labelSetId', 'created'})})
	def test_get_label_sets(self):
		# /labelsets/
		pass

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
		pass

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
		pass

	@put(
		data={'handlerId': 1},
		expected_result={('message', unicode)},
		taskId=999999)
	def test_configure_task_file_handler(self):
		# /tasks/<int:taskId>/filehandlers/
		pass

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

	def test_get_sheet_with_markings(self):
		# /sheets/<int:sheetId>/markings/
		pass

	def test_get_sub_task(self):
		# /subtasks/<int:subTaskId>
		pass

	@get(expected_result={'batches': ('>0', {'batchId', })},
		subTaskId=1664)
	def test_get_sub_task_batches(self):
		# /subtasks/<int:subTaskId>/batches/
		pass

	@get(expected_result={'subtotals': ('>0', {'totalId', 'date',
		'subTaskId', 'userId', 'userName', 'items', 'units'})},
		subTaskId=1802)
	def test_get_sub_task_daily_subtotals(self):
		# /subtasks/<int:subTaskId>/dailysubtotals/
		pass

	def test_get_sub_task_qa_settings(self):
		# /subtasks/<int:subTaskId>/qasettings/
		pass

	@get(expected_result={'subTaskRates': ('>0', {'subTaskRateId',
		'subTaskId', 'rateId', 'rateName', 'multiplier', 'updatedAt',
		'updatedBy', 'validFrom'})}, subTaskId=1802)
	def test_get_sub_task_rate_records(self):
		# /subtasks/<int:subTaskId>/rates/
		pass

	@get(expected_result={'events': ('>0', {'subTaskId', 'selectionId',
		'amount', 'populating', 'tProcessedAt', 'operator'})},
		subTaskId=2728)
	def test_get_sub_task_rework_load_records(self):
		# /subtasks/<int:subTaskId>/loads/
		pass

	@get(expected_result={'batchCount'}, subTaskId=2148)
	def test_get_sub_task_statistics(self):
		# /subtasks/<int:subTaskId>/stats/
		pass

	def test_get_sub_task_warnings(self):
		# /subtasks/<int:subTaskId>/warnings/
		pass

	@get(expected_result={'intervals': ('>0', {'workIntervalId',
		'taskId', 'subTaskId', 'startTime', 'endTime', 'status'})},
		subTaskId=1802)
	def test_get_sub_task_work_intervals(self):
		# /subtasks/<int:subTaskId>/intervals/
		pass

	def test_get_sub_task_work_metrics(self):
		# /subtasks/<int:subTaskId>/metrics/
		pass

	def test_get_sub_task_worker_performance_records(self):
		# /subtasks/<int:subTaskId>/performance/
		pass

	def test_get_sub_task_workers(self):
		# /subtasks/<int:subTaskId>/workers/
		pass

	def test_get_tag_set(self):
		# /tagsets/<int:tagSetId>
		pass

	@get(expected_result={'tagSets': ('>0', {'tagSetId', 'created',
		'lastUpdated', ('tags', list)})})
	def test_get_tag_sets(self):
		# /tagsets/
		pass

	@get(expected_result={'task': {'taskId', 'name', 'projectId',
		'status', 'srcDir', 'migratedBy'}}, taskId=999999)
	@get(expected_result={'error': unicode},
		expected_status_code=404, taskId=382)
	def test_get_task(self):
		# /tasks/<int:taskId>
		pass

	@get(expected_result={'utteranceGroups': ('>0', {'groupId', 'name',
		'created', 'rawPieces'})}, taskId=999999)
	def test_get_task_custom_utterance_groups(self):
		# /tasks/<int:taskId>/uttgroups/
		pass

	@get(expected_result={'subtotals': ('>0', {'totalId', 'date',
		'subTaskId', 'userId', 'userName', 'items', 'units'})},
		taskId=999999)
	def test_get_task_daily_subtotals(self):
		# /tasks/<int:taskId>/dailysubtotals/
		pass

	@get(expected_result={'errorClasses': ('>0', {'errorClassId', 'name'})},
		taskId=999999)
	def test_get_task_error_classes(self):
		# /tasks/<int:taskId>/errorclasses/
		pass

	@get(expected_result={'taskErrorTypes': ('>0', {'taskId', 'errorTypeId',
		'errorType', 'errorClassId', 'errorClass', 'severity',
		'defaultSeverity', 'disabled'})}, taskId=999999)
	def test_get_task_error_types(self):
		# /tasks/<int:taskId>/errortypes/
		pass

	@get(expected_result={'instructions': ('>0', {'basename', 'path'})},
		taskId=999999)
	def test_get_task_instruction_files(self):
		# /tasks/<int:taskId>/instructions/
		pass

	@get(expected_result={'loads': ('>0', {'loadId', 'taskId', 'createdAt',
		('createdBy', dict)})}, taskId=999999)
	def test_get_task_loads(self):
		# /tasks/<int:taskId>/loads/
		pass

	def test_get_task_payment_statistics(self):
		# /tasks/<int:taskId>/paystats/
		pass

	@get(expected_result={'payments': ('>0', {'calculatedPaymentId',
		'payrollId', 'taskId', 'subTaskId', 'workIntervalId', 'userId',
		'userName', 'amount', 'originalAmount', 'updated', 'receipt',
		'items', 'units', 'qaedItems', 'qaedUnits', 'accuracy'})},
		taskId=300464)
	def test_get_task_payments(self):
		# /tasks/<int:taskId>/payments/
		pass

	@get(expected_result={'rawPieces': ('>0', {'rawPieceId', 'rawText',
		'allocationContext', 'assemblyContext', 'words', 'hypothesis'})},
		taskId=999999)
	def test_get_task_raw_pieces(self):
		# /tasks/<int:taskId>/rawpieces/
		pass

	@get(expected_result={'subTasks': ('>0', {'subTaskId', 'name', 'modeId',
		'taskId', 'taskTypeId', 'taskType', 'workTypeId', 'workType',
		'maxPageSize', 'defaultLeaseLife'})}, taskId=999999)
	def test_get_task_sub_tasks(self):
		# /tasks/<int:taskId>/subtasks/
		pass

	def test_get_task_summary(self):
		# /tasks/<int:taskId>/summary/
		pass

	@get(expected_result={'supervisors': ('>0', {'taskId', 'userId',
		'userName', 'receivesFeedback', 'informLoads'})}, taskId=999999)
	def test_get_task_supervisors(self):
		# /tasks/<int:taskId>/supervisors/
		pass

	@get(expected_result={'selections': ('>0', {'selectionId', 'name',
		'taskId', 'userId', 'userName', 'random', ('filters', list)})},
		taskId=300735)
	def test_get_task_utterrance_selections(self):
		# /tasks/<int:taskId>/selections/
		pass

	def test_get_task_warnings(self):
		# /tasks/<int:taskId>/warnings/
		pass

	@get(expected_result={'workers': ('>0', {'userId', 'userName',
		'taskId', 'subTaskId', 'removed', 'isNew', 'paymentFactor',
		'hasReadInstructions'})}, taskId=999999)
	def test_get_task_workers(self):
		# /tasks/<int:taskId>/workers/
		pass

	@get(expected_result={'tasks': ('>0', {'taskId', 'name', 'projectId',
		'status', 'taskTypeId', 'taskType', 'migrated', 'migratedBy'})})
	def test_get_tasks(self):
		# /tasks/
		pass

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
		pass

	@get(expected_result={'tests': ('>0', {'testId', 'name', 'poolId',
		'taskTypeId', 'taskType', 'requirement', 'passingScore',
		'timeLimit', 'testType'})})
	def test_get_tests(self):
		# /tests/
		pass

	@get(expected_result={'words': int}, taskId=999999, groupId=814)
	def test_get_utterance_group_word_count(self):
		# /tasks/<int:taskId>/uttgroups/<int:groupId>/words
		pass

	def test_migrate_project(self):
		# /projects/<int:projectId>
		pass

	@put(data={'taskTypeId':1}, expected_result={
			'task': {'taskId', 'name', 'migrated', 'migratedBy',
				'taskTypeId', 'taskType'}},
		taskId=1500)
	def test_migrate_task(self):
		# /tasks/<int:taskId>
		pass

	def test_populate_task_utterrance_selection(self):
		# /tasks/<int:taskId>/selections/<int:selectionId>
		pass

	def test_remove_task_supervisor(self):
		# /tasks/<int:taskId>/supervisors/<int:userId>
		pass

	def test_submit_answer(self):
		# /sheets/<int:sheetId>/answers/
		pass

	def test_submit_marking(self):
		# /sheets/<int:sheetId>/markings/
		pass

	def test_submit_sheet(self):
		# /sheets/<int:sheetId>
		pass

	def test_unassign_all_task_workers(self):
		# /tasks/<int:taskId>/workers/
		pass

	def test_unassign_batch(self):
		# /batches/<int:batchId>/users/
		pass

	def test_update_batches(self):
		# /subtasks/<int:subTaskId>/batches/
		pass

	def test_update_label(self):
		# /labelsets/<int:labelSetId>/labels/<int:labelId>
		pass

	def test_update_label_group(self):
		# /labelsets/<int:labelSetId>/labelgroups/<int:labelGroupId>
		pass

	def test_update_sub_task(self):
		# /subtasks/<int:subTaskId>
		pass

	def test_update_sub_task_qa_settings(self):
		# /subtasks/<int:subTaskId>/qasettings/
		pass

	def test_update_tag(self):
		# /tagsets<int:tagSetId>/tags/<int:tagId>
		pass

	def test_update_task_error_types(self):
		# /tasks/<int:taskId>/errortypes/
		pass

	@put(
		data={'status': m.Task.STATUS_CLOSED},
		expected_result={'message': unicode},
		taskId=999999)
	def test_update_task_status(self):
		# /tasks/<int:taskId>/status
		pass

	@put(
		data={'informLoads': True},
		expected_result={
			'supervisor',
		},
		taskId=999999, userId=699)
	def test_update_task_supervisor_settings(self):
		# /tasks/<int:taskId>/supervisors/<int:userId>
		pass

	def test_upload_task_instruction_file(self):
		# /tasks/<int:taskId>/instructions/
		pass

	def test_index(self):
		# /
		pass

	def test_static(self):
		# /static/<path:filename>
		pass

	def test_webservices_apply_user_search_action(self):
		# /webservices/apply_user_search_action
		pass

	def test_webservices_apply_user_search_filters(self):
		# /webservices/apply_user_search_filters
		pass

	def test_webservices_get_available_qualification_tests(self):
		# /webservices/available_qualifications
		pass

	def test_webservices_get_available_work_entries(self):
		# /webservices/available_work
		pass

	def test_webservices_get_recent_work_entries(self):
		# /webservices/recent_work
		pass

	def test_webservices_get_user_details(self):
		# /webservices/user_details
		pass

	def test_webservices_get_user_details_css(self):
		# /webservices/get_user_details_css
		pass

	def test_webservices_get_user_details_js(self):
		# /webservices/get_user_details_js
		pass

	def test_webservices_get_user_search_actions(self):
		# /webservices/get_user_search_actions
		pass

	def test_webservices_get_user_search_filters(self):
		# /webservices/get_user_search_filters
		pass

	def test_webservices_update_payments(self):
		# /webservices/update_payments
		pass

if __name__ == '__main__':
	unittest.main()
