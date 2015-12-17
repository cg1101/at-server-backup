
import sys
import os
import json
import unittest
from functools import wraps

from flask import url_for

sys.path.insert(0, os.path.abspath(os.path.normpath(
		os.path.join(os.path.dirname(__file__), '..'))))

from app import create_app

def collection_retrieval(keyword=None, has_data=True, expected_keys=[], **values):
	if keyword is None:
		raise RuntimeError, 'keyword must be specified'
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
					assert key in first
			return fn(*args, **kwargs)
		return routine_injected
	return customized_decorator


def _test_collection_retrieval(client, url, keyword, has_data=True, expected_keys=[]):
	assert url.endswith('/')
	rv = client.get(url[:-1])
	assert rv.status_code == 301
	assert rv.headers['location'].endswith(url)
	rv = client.get(url)
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
			assert key in first


class MyTestCase(unittest.TestCase):

	def setUp(self):
		# set up stuff
		self.app = app = create_app('testing')
		self.client = app.test_client()

	def tearDown(self):
		pass

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
		pass

	def test_dismiss_all_batches(self):
		# /subtasks/<int:subTaskId>/batches/
		pass

	def test_getTaskExtract(self):
		# /tasks/<int:taskId>/extract_<timestamp>.txt
		pass

	def test_get_batch(self):
		# /batches/<int:batchId>
		pass

	def test_get_batch_stats(self):
		# /batches/<int:batchId>/stat
		pass

	def test_get_error_classes(self):
		# /errorclasses/
		rv = self.client.get('/api/1.0/errorclasses')
		assert rv.status_code == 301
		rv = self.client.get('/api/1.0/errorclasses/')
		assert rv.mimetype == 'application/json'
		data = json.loads(rv.get_data())
		assert 'errorClasses' in data
		assert isinstance(data['errorClasses'], list)
		assert len(data['errorClasses']) > 0

	@collection_retrieval('errorTypes', expected_keys=['errorTypeId', 
		'name', 'errorClassId', 'errorClass', 'defaultSeverity',
		'isStandard'])
	def test_get_error_types(self):
		# /errortypes/
		pass
		# rv = self.client.get('/api/1.0/errortypes')
		# assert rv.status_code == 301
		# rv = self.client.get('/api/1.0/errortypes/')
		# assert rv.mimetype == 'application/json'
		# data = json.loads(rv.get_data())
		# assert 'errorTypes' in data
		# assert isinstance(data['errorTypes'], list)
		# assert len(data['errorTypes']) > 0
		# errorType = data['errorTypes'][0]
		# assert 'errorTypeId' in errorType
		# assert 'name' in errorType
		# assert 'errorClassId' in errorType
		# assert 'errorClass' in errorType
		# assert 'defaultSeverity' in errorType
		# assert 'isStandard' in errorType

	def test_get_file_handlers(self):
		# /filehandlers/
		pass

	def test_get_label_set(self):
		# /labelsets/<int:labelSetId>
		pass

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

	def test_get_pools(self):
		# /pools/
		_test_collection_retrieval(self.client, '/api/1.0/pools/',
				'pools', expected_keys=[
					'poolId',
					'name',
					'autoScoring',
					'meta',
					'taskTypeId',
					'taskType',
					'questions',
				])
		# rv = self.client.get('/api/1.0/pools')
		# assert rv.status_code == 301
		# rv = self.client.get('/api/1.0/pools/')
		# assert rv.mimetype == 'application/json'
		# data = json.loads(rv.get_data())
		# assert 'pools' in data
		# assert isinstance(data['pools'], list)
		# assert len(data['pools']) >= 0
		# assert data['pools'][0]['name'] == 'My Fake Test Pool'

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

	def test_get_projects(self):
		# /projects/
		_test_collection_retrieval(self.client, '/api/1.0/projects/',
				'projects', expected_keys=[
					'projectId',
					'name',
					'description',
					'migratedBy',
					'created',
				])
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

	def test_get_rates(self):
		# /rates/
		_test_collection_retrieval(self.client, '/api/1.0/rates/',
				'rates', expected_keys=[
					'rateId',
					'name',
					'standardValue',
					'targetAccuracy',
					'maxValue',
					'details',
				])
		# rv = self.client.get('/api/1.0/rates')
		# assert rv.status_code == 301
		# rv = self.client.get('/api/1.0/rates/')
		# assert rv.mimetype == 'application/json'
		# data = json.loads(rv.get_data())
		# assert 'rates' in data
		# assert isinstance(data['rates'], list)
		# assert len(data['rates']) > 0

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

	def test_get_sub_task_batches(self):
		# /subtasks/<int:subTaskId>/batches/
		pass

	def test_get_sub_task_daily_subtotals(self):
		# /subtasks/<int:subTaskId>/dailysubtotals/
		pass

	def test_get_sub_task_qa_settings(self):
		# /subtasks/<int:subTaskId>/qasettings/
		pass

	def test_get_sub_task_rate_records(self):
		# /subtasks/<int:subTaskId>/rates/
		pass

	def test_get_sub_task_rework_load_records(self):
		# /subtasks/<int:subTaskId>/loads/
		pass

	def test_get_sub_task_statistics(self):
		# /subtasks/<int:subTaskId>/stats/
		pass

	def test_get_sub_task_warnings(self):
		# /subtasks/<int:subTaskId>/warnings/
		pass

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

	def test_get_tag_sets(self):
		# /tagsets/
		pass

	def test_get_task(self):
		# /tasks/<int:taskId>
		pass

	def test_get_task_custom_utterance_groups(self):
		# /tasks/<int:taskId>/uttgroups/
		pass

	def test_get_task_daily_subtotals(self):
		# /tasks/<int:taskId>/dailysubtotals/
		with self.app.test_request_context():
			url = url_for('api_1_0.get_task_daily_subtotals', taskId=999999)

		_test_collection_retrieval(self.client, url,
			'subtotals', expected_keys=[
				'totalId',
				'date',
				'subTaskId',
				'userId',
				'userName',
				'items',
				'units',
			])

	def test_get_task_error_classes(self):
		# /tasks/<int:taskId>/errorclasses/
		_test_collection_retrieval(self.client, '/api/1.0/tasks/999999/errorclasses/',
			'errorClasses', expected_keys=[
				'errorClassId',
				'name',
			])

	def test_get_task_error_types(self):
		# /tasks/<int:taskId>/errortypes/
		_test_collection_retrieval(self.client, '/api/1.0/tasks/999999/errortypes/',
			'taskErrorTypes', expected_keys=[
				'taskId',
				'errorTypeId',
				'errorType',
				'errorClassId',
				'errorClass',
				'severity',
				'defaultSeverity',
				'disabled',
			])

	def test_get_task_instruction_files(self):
		# /tasks/<int:taskId>/instructions/
		pass

	def test_get_task_payment_statistics(self):
		# /tasks/<int:taskId>/paystats/
		pass

	def test_get_task_payments(self):
		# /tasks/<int:taskId>/payments/
		pass

	def test_get_task_raw_pieces(self):
		# /tasks/<int:taskId>/rawpieces/
		pass

	def test_get_task_sub_tasks(self):
		# /tasks/<int:taskId>/subtasks/
		pass

	def test_get_task_summary(self):
		# /tasks/<int:taskId>/summary/
		pass

	@collection_retrieval(keyword='supervisors', expected_keys=['taskId',
		'userId', 'userName', 'receivesFeedback', 'informLoads'],
		taskId=999999)
	def test_get_task_supervisors(self):
		# /tasks/<int:taskId>/supervisors/
		pass

	def test_get_task_utterrance_selections(self):
		# /tasks/<int:taskId>/selections/
		pass

	def test_get_task_warnings(self):
		# /tasks/<int:taskId>/warnings/
		pass

	def test_get_task_workers(self):
		# /tasks/<int:taskId>/workers/
		pass

	def test_get_tasks(self):
		# /tasks/
		_test_collection_retrieval(self.client, '/api/1.0/tasks/',
				'tasks', expected_keys=[
					'taskId',
					'name',
					'projectId',
					'status',
					'taskTypeId',
					'taskType',
					'migrated',
					'migratedBy',
				])
		# rv = self.client.get('/api/1.0/tasks')
		# assert rv.status_code == 301
		# rv = self.client.get('/api/1.0/tasks/')
		# assert rv.mimetype == 'application/json'
		# data = json.loads(rv.get_data())
		# assert 'tasks' in data
		# assert isinstance(data['tasks'], list)
		# assert len(data['tasks']) > 0
		# task = data['tasks'][0]
		# assert 'taskId' in task
		# assert 'name' in task
		# assert 'projectId' in task
		# assert 'status' in task
		# assert 'taskTypeId' in task
		# assert 'taskType' in task
		# assert 'migrated' in task
		# assert 'migratedBy' in task

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

	def test_get_test_sheets(self):
		# /tests/<int:testId>/sheets/
		_test_collection_retrieval(self.client, '/api/1.0/tests/1/sheets/',
				'sheets', expected_keys=[
					'sheetId',
					'testId',
					'nTimes',
					'user',
					'tStartedAt',
					'tExpiresBy',
					'tExpiredAt',
					'tFinishedAt',
					'score',
					'comment',
					'moreAttempts',
				])
		# rv = self.client.get('/api/1.0/tests/1/sheets')
		# assert rv.status_code == 301
		# rv = self.client.get('/api/1.0/tests/1/sheets/')
		# assert rv.mimetype == 'application/json'
		# data = json.loads(rv.get_data())
		# assert 'sheets' in data
		# assert isinstance(data['sheets'], list)
		# assert len(data['sheets']) > 0
		# sheet = data['sheets'][0]
		# assert 'sheetId' in sheet
		# assert 'testId' in sheet
		# assert 'nTimes' in sheet
		# assert 'user' in sheet
		# assert 'tStartedAt' in sheet
		# assert 'tExpiresBy' in sheet
		# assert 'tExpiredAt' in sheet
		# assert 'tFinishedAt' in sheet
		# assert 'score' in sheet
		# assert 'moreAttempts' in sheet
		# assert isinstance(sheet['entries'], list)


	def test_get_tests(self):
		# /tests/
		_test_collection_retrieval(self.client, '/api/1.0/tests/',
				'tests', expected_keys=[
					'testId',
					'name',
					'poolId',
					'taskTypeId',
					'taskType',
					'requirement',
					'passingScore',
					'timeLimit',
					'testType',
				])
		# rv = self.client.get('/api/1.0/tests')
		# assert rv.status_code == 301
		# rv = self.client.get('/api/1.0/tests/')
		# assert rv.mimetype == 'application/json'
		# data = json.loads(rv.get_data())
		# assert 'tests' in data
		# assert isinstance(data['tests'], list)
		# assert len(data['tests']) > 0


	def test_get_utterance_group_word_count(self):
		# /tasks/<int:taskId>/uttgroups/<int:groupId>/words
		pass

	def test_migrate_project(self):
		# /projects/<int:projectId>
		pass

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

	def test_update_task_status(self):
		# /tasks/<int:taskId>/status
		pass

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
