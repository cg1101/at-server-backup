
import sys
import os
import json
import unittest
from functools import wraps

from flask import url_for

sys.path.insert(0, os.path.abspath(os.path.normpath(
		os.path.join(os.path.dirname(__file__), '..'))))

from app import create_app
import db.model as m


def post(keyword, has_data=True, enc_type='json', data={},
		expected_keys=[], **values):
	if not isinstance(keyword, basestring) or not keyword.strip():
		raise RuntimeError, 'keyword must be non-blank string'
	request_data = data
	def customized_decorator(fn):
		@wraps(fn)
		def routine_injected(*args, **kwargs):
			self = args[0]
			with self.app.test_request_context():
				url = url_for('api_1_0.' + fn.__name__[5:], **values)
			if enc_type == 'json':
				rv = self.client.post(url,
					content_type='application/json',
					data=json.dumps(request_data),
					)
			else:
				rv = self.client.post(url, data=request_data)
			assert rv.mimetype == 'application/json'
			data = json.loads(rv.get_data())
			if has_data:
				assert keyword in data
				result = data[keyword]
				assert isinstance(result, dict)
				first = result
				assert isinstance(first, dict)
				for key in expected_keys:
					if isinstance(key, tuple):
						key, value_type = key
						assert key in first
						assert isinstance(first[key], value_type)
					else:
						assert key in first
			else:
				if rv.status_code == 404:
					assert 'error' in data
					assert data['error'].endswith('not found')
				elif rv.status_code == 200:
					assert 'message' in data
			return fn(*args, **kwargs)
		return routine_injected
	return customized_decorator


def put(keyword, has_data=True, enc_type='json', data={},
		expected_keys=[], **values):
	if not isinstance(keyword, basestring) or not keyword.strip():
		raise RuntimeError, 'keyword must be non-blank string'
	request_data = data
	def customized_decorator(fn):
		@wraps(fn)
		def routine_injected(*args, **kwargs):
			self = args[0]
			with self.app.test_request_context():
				url = url_for('api_1_0.' + fn.__name__[5:], **values)
			if enc_type == 'json':
				rv = self.client.put(url,
					content_type='application/json',
					data=json.dumps(request_data),
					)
			else:
				rv = self.client.put(url, data=request_data)
			assert rv.mimetype == 'application/json'
			data = json.loads(rv.get_data())
			if has_data:
				assert keyword in data
				result = data[keyword]
				assert isinstance(result, dict)
				first = result
				assert isinstance(first, dict)
				for key in expected_keys:
					if isinstance(key, tuple):
						key, value_type = key
						assert key in first
						assert isinstance(first[key], value_type)
					else:
						assert key in first
			else:
				if rv.status_code == 404:
					assert 'error' in data
					assert data['error'].endswith('not found')
				elif rv.status_code == 200:
					assert 'message' in data
			return fn(*args, **kwargs)
		return routine_injected
	return customized_decorator


def single_retrieveal(keyword, has_data=True, expected_keys=[], **values):
	if not isinstance(keyword, basestring) or not keyword.strip():
		raise RuntimeError, 'keyword must be non-blank string'
	def customized_decorator(fn):
		@wraps(fn)
		def routine_injected(*args, **kwargs):
			self = args[0]
			with self.app.test_request_context():
				url = url_for('api_1_0.' + fn.__name__[5:], **values)
			rv = self.client.get(url)
			assert rv.mimetype == 'application/json'
			data = json.loads(rv.get_data())
			if has_data:
				assert keyword in data
				result = data[keyword]
				assert isinstance(result, dict)
				first = result
				assert isinstance(first, dict)
				for key in expected_keys:
					if isinstance(key, tuple):
						key, value_type = key
						assert key in first
						assert isinstance(first[key], value_type)
					else:
						assert key in first
			else:
				if rv.status_code == 404:
					assert 'error' in data
					assert data['error'].endswith('not found')
			return fn(*args, **kwargs)
		return routine_injected
	return customized_decorator


def collection_retrieval(keyword, has_data=True, expected_keys=[], **values):
	if not isinstance(keyword, basestring) or not keyword.strip():
		raise RuntimeError, 'keyword must be non-blank string'
	def customized_decorator(fn):
		@wraps(fn)
		def routine_injected(*args, **kwargs):
			self = args[0]
			with self.app.test_request_context():
				url = url_for('api_1_0.' + fn.__name__[5:], **values)
			assert url.endswith('/')
			rv = self.client.get(url[:-1])
			assert rv.status_code == 301
			assert rv.headers['location'].endswith(url)
			rv = self.client.get(url)
			assert rv.mimetype == 'application/json'
			data = json.loads(rv.get_data())
			assert keyword in data
			result = data[keyword]
			assert isinstance(result, list)
			if has_data:
				assert len(result) > 0
				first = result[0]
				assert isinstance(first, dict)
				for key in expected_keys:
					if isinstance(key, tuple):
						key, value_type = key
						assert key in first
						assert isinstance(first[key], value_type)
					else:
						assert key in first
			return fn(*args, **kwargs)
		return routine_injected
	return customized_decorator


class MyTestCase(unittest.TestCase):

	def setUp(self):
		# set up stuff
		self.app = app = create_app('testing')
		self.client = app.test_client()

	def tearDown(self):
		pass

	@put('taskErrorType', data={'severity': 0.5}, expected_keys=['taskId',
		'errorTypeId', 'severity', 'disabled', 'errorType',
		'defaultSeverity', 'errorClassId', 'errorClass'], taskId=999999,
		errorTypeId=1)
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

	@post('subTask', data={'name': 'mygreat', 'workTypeId': 1, 'modeId': 1},
		expected_keys=['subTaskId', 'name'], taskId=999999)
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

	@collection_retrieval('errorClasses', expected_keys=['errorClassId',
		'name'])
	def test_get_error_classes(self):
		# /errorclasses/
		pass

	@collection_retrieval('errorTypes', expected_keys=['errorTypeId', 
		'name', 'errorClassId', 'errorClass', 'defaultSeverity',
		'isStandard'])
	def test_get_error_types(self):
		# /errortypes/
		pass

	@collection_retrieval('fileHandlers', expected_keys=['handlerId',
		'name', 'description', ('options', list)])
	def test_get_file_handlers(self):
		# /filehandlers/
		pass

	def test_get_label_set(self):
		# /labelsets/<int:labelSetId>
		pass

	@collection_retrieval('labelSets', expected_keys=['labelSetId',
		'created'])
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

	@collection_retrieval('pools', expected_keys=['poolId', 'name',
		'autoScoring', 'meta', 'taskTypeId', 'taskType', 'questions'])
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

	@collection_retrieval('projects', expected_keys=['projectId', 'name',
		'description', 'migratedBy', 'created'])
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

	@collection_retrieval('rates', expected_keys=['rateId', 'name',
		'standardValue', 'targetAccuracy', 'maxValue', 'details'])
	def test_get_rates(self):
		# /rates/
		pass

	@put('message', data={'handlerId': 1}, has_data=False, taskId=999999)
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

	@collection_retrieval('batches', expected_keys=['batchId',
		], subTaskId=1664)
	def test_get_sub_task_batches(self):
		# /subtasks/<int:subTaskId>/batches/
		pass

	@collection_retrieval('subtotals', expected_keys=['totalId', 'date',
		'subTaskId', 'userId', 'userName', 'items', 'units'], subTaskId=1802)
	def test_get_sub_task_daily_subtotals(self):
		# /subtasks/<int:subTaskId>/dailysubtotals/
		pass

	def test_get_sub_task_qa_settings(self):
		# /subtasks/<int:subTaskId>/qasettings/
		pass

	@collection_retrieval('subTaskRates', expected_keys=['subTaskRateId',
		'subTaskId', 'rateId', 'rateName', 'multiplier', 'updatedAt',
		'updatedBy', 'validFrom'], subTaskId=1802)
	def test_get_sub_task_rate_records(self):
		# /subtasks/<int:subTaskId>/rates/
		pass

	@collection_retrieval('events', expected_keys=['subTaskId',
		'selectionId', 'amount', 'populating', 'tProcessedAt',
		'operator'], subTaskId=2728)
	def test_get_sub_task_rework_load_records(self):
		# /subtasks/<int:subTaskId>/loads/
		pass

	@single_retrieveal('batchCount', has_data=False, subTaskId=2148)
	def test_get_sub_task_statistics(self):
		# /subtasks/<int:subTaskId>/stats/
		pass

	def test_get_sub_task_warnings(self):
		# /subtasks/<int:subTaskId>/warnings/
		pass

	@collection_retrieval('intervals', expected_keys=['workIntervalId',
		'taskId', 'subTaskId', 'startTime', 'endTime', 'status'], subTaskId=1802)
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

	@collection_retrieval('tagSets', expected_keys=['tagSetId', 'created',
		'lastUpdated', ('tags', list)])
	def test_get_tag_sets(self):
		# /tagsets/
		pass

	@single_retrieveal('task', expected_keys=['taskId', 'name', 'projectId',
		'status', 'srcDir', 'migratedBy'], taskId=999999)
	@single_retrieveal('task', has_data=False, taskId=382)
	def test_get_task(self):
		# /tasks/<int:taskId>
		pass

	@collection_retrieval('utteranceGroups', expected_keys=['groupId',
		'name', 'created', 'rawPieces'], taskId=999999)
	def test_get_task_custom_utterance_groups(self):
		# /tasks/<int:taskId>/uttgroups/
		pass

	@collection_retrieval('subtotals', expected_keys=['totalId', 'date',
		'subTaskId', 'userId', 'userName', 'items', 'units'], taskId=999999)
	def test_get_task_daily_subtotals(self):
		# /tasks/<int:taskId>/dailysubtotals/
		pass

	@collection_retrieval('errorClasses', expected_keys=['errorClassId',
		'name'], taskId=999999)
	def test_get_task_error_classes(self):
		# /tasks/<int:taskId>/errorclasses/
		pass

	@collection_retrieval('taskErrorTypes', expected_keys=['taskId',
		'errorTypeId', 'errorType', 'errorClassId', 'errorClass',
		'severity', 'defaultSeverity', 'disabled'], taskId=999999)
	def test_get_task_error_types(self):
		# /tasks/<int:taskId>/errortypes/
		pass

	@collection_retrieval('instructions', expected_keys=['basename',
		'path'], taskId=999999)
	def test_get_task_instruction_files(self):
		# /tasks/<int:taskId>/instructions/
		pass

	@collection_retrieval('loads', expected_keys=['loadId', 'taskId',
		'createdAt', ('createdBy', dict)], taskId=999999)
	def test_get_task_loads(self):
		# /tasks/<int:taskId>/loads/
		pass

	def test_get_task_payment_statistics(self):
		# /tasks/<int:taskId>/paystats/
		pass

	@collection_retrieval('payments', expected_keys=['calculatedPaymentId',
		'payrollId', 'taskId', 'subTaskId', 'workIntervalId', 'userId',
		'userName', 'amount', 'originalAmount', 'updated', 'receipt',
		'items', 'units', 'qaedItems', 'qaedUnits', 'accuracy'],
		taskId=300464)
	def test_get_task_payments(self):
		# /tasks/<int:taskId>/payments/
		pass

	@collection_retrieval('rawPieces', expected_keys=['rawPieceId',
		'rawText', 'allocationContext', 'assemblyContext', 'words',
		'hypothesis'], taskId=999999)
	def test_get_task_raw_pieces(self):
		# /tasks/<int:taskId>/rawpieces/
		pass

	@collection_retrieval('subTasks', expected_keys=['subTaskId', 'name',
		'modeId', 'taskId', 'taskTypeId', 'taskType', 'workTypeId',
		'workType', 'maxPageSize', 'defaultLeaseLife'], taskId=999999)
	def test_get_task_sub_tasks(self):
		# /tasks/<int:taskId>/subtasks/
		pass

	def test_get_task_summary(self):
		# /tasks/<int:taskId>/summary/
		pass

	@collection_retrieval('supervisors', expected_keys=['taskId',
		'userId', 'userName', 'receivesFeedback', 'informLoads'],
		taskId=999999)
	def test_get_task_supervisors(self):
		# /tasks/<int:taskId>/supervisors/
		pass

	@collection_retrieval('selections', expected_keys=['selectionId', 'name',
		'taskId', 'userId', 'userName', 'random', ('filters', list)], taskId=300735)
	def test_get_task_utterrance_selections(self):
		# /tasks/<int:taskId>/selections/
		pass

	def test_get_task_warnings(self):
		# /tasks/<int:taskId>/warnings/
		pass

	@collection_retrieval('workers', expected_keys=['userId', 'userName',
		'taskId', 'subTaskId', 'removed', 'isNew', 'paymentFactor',
		'hasReadInstructions'], taskId=999999)
	def test_get_task_workers(self):
		# /tasks/<int:taskId>/workers/
		pass

	@collection_retrieval('tasks', expected_keys=['taskId', 'name',
		'projectId', 'status', 'taskTypeId', 'taskType', 'migrated',
		'migratedBy'])
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

	@collection_retrieval('sheets', expected_keys=['sheetId', 'testId',
		'nTimes', 'user', 'tStartedAt', 'tExpiresBy', 'tExpiredAt',
		'tFinishedAt', 'score', 'comment', 'moreAttempts',
		('entries', list)], testId=1)
	def test_get_test_sheets(self):
		# /tests/<int:testId>/sheets/
		pass

	@collection_retrieval('tests', expected_keys=['testId', 'name',
		'poolId', 'taskTypeId', 'taskType', 'requirement',
		'passingScore', 'timeLimit', 'testType'])
	def test_get_tests(self):
		# /tests/
		pass

	@single_retrieveal('words', has_data=False, taskId=999999, groupId=814)
	def test_get_utterance_group_word_count(self):
		# /tasks/<int:taskId>/uttgroups/<int:groupId>/words
		pass

	def test_migrate_project(self):
		# /projects/<int:projectId>
		pass

	@put('task', data={'taskTypeId':1}, expected_keys=['taskId', 'name',
		'migrated', 'migratedBy', 'taskTypeId', 'taskType'], taskId=1500)
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

	@put('message', data={'status': m.Task.STATUS_CLOSED}, has_data=False,
		taskId=999999)
	def test_update_task_status(self):
		# /tasks/<int:taskId>/status
		pass

	@put('supervisor', data={'informLoads': True}, taskId=999999, userId=699)
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
