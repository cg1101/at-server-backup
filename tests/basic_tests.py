
import sys
import os
import json
import unittest

sys.path.insert(0, os.path.abspath(os.path.normpath(
		os.path.join(os.path.dirname(__file__), '..'))))

from app import create_app

class MyTestCase(unittest.TestCase):

	def setUp(self):
		# set up stuff
		app = create_app('testing')
		self.app = app.test_client()
		# print app.config['SQLALCHEMY_DATABASE_URI']
		pass

	def tearDown(self):
		pass

	def test_configure_task_error_type(self):
		# /tasks/<int:taskId>/errortypes/<int:errorTypeId>
		pass

	def test_create_error_class(self):
		# /errorclasses/
		pass

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
		pass

	def test_get_error_types(self):
		# /errortypes/
		pass

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
		pass

	def test_get_pools(self):
		# /pools/
		pass

	def test_get_project(self):
		# /projects/<int:projectId>
		pass

	def test_get_projects(self):
		# /projects/
		rv = self.app.get('/projects')
		assert rv.status_code == 301
		rv = self.app.get('/projects/')
		assert rv.mimetype == 'application/json'
		data = json.loads(rv.get_data())
		assert 'projects' in data
		assert len(data['projects']) == 0
		rv = self.app.get('/projects/?t=candidate')
		assert rv.mimetype == 'application/json'
		data = json.loads(rv.get_data())
		assert 'projects' in data
		assert len(data['projects']) == 0

	def test_get_rate(self):
		# /rates/<int:rateId>
		pass

	def test_get_rates(self):
		# /rates/
		pass

	def test_get_s(self):
		# /tasks/<int:taskId>/filehandlers/
		pass

	def test_get_sheet(self):
		# /sheets/<int:sheetId>
		pass

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
		pass

	def test_get_task_error_classes(self):
		# /tasks/<int:taskId>/errorclasses/
		pass

	def test_get_task_error_types(self):
		# /tasks/<int:taskId>/errortypes/
		pass

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

	def test_get_task_status(self):
		# /tasks/<int:taskId>/status
		pass

	def test_get_task_sub_tasks(self):
		# /tasks/<int:taskId>/subtasks/
		pass

	def test_get_task_summary(self):
		# /tasks/<int:taskId>/summary/
		pass

	def test_get_task_supervisors(self):
		# /tasks/<int:taskId>/supervisors/
		pass

	def test_get_task_utterrance_selection(self):
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
		pass

	def test_get_test(self):
		# /tests/<int:testId>
		pass

	def test_get_test_sheets(self):
		# /tests/<int:testId>/sheets/
		pass

	def test_get_tests(self):
		# /tests/
		pass

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
