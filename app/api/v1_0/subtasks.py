
from flask import request, abort, session

import db.model as m
from db.db import SS
from app.api import api, caps, get_text as _
from . import api_1_0 as bp

_name = __file__.split('/')[-1].split('.')[0]

@bp.route(_name + '/<int:subTaskId>', methods=['GET'])
@api
@caps()
def get_sub_task(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		abort(404)
	return {
		'subTask': m.SubTask.dump(subTask, context={}),
	}

@bp.route(_name + '/<int:subTaskId>', methods=['PUT'])
@api
@caps()
def update_sub_task(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		abort(404)
	data = request.get_json()
	# update subTask using data
	SS().flush()
	return {
		'subTask': m.SubTask.dump(subTask, context={}),
	}

@bp.route(_name + '/<int:subTaskId>/batches/', methods=['GET'])
@api
@caps()
def get_sub_task_batches(subTaskId):
	pass

@bp.route(_name + '/<int:subTaskId>/batches/', methods=['POST'])
@api
@caps()
def create_new_batches(subTaskId):
	pass

@bp.route(_name + '/<int:subTaskId>/batches/', methods=['PUT'])
@api
@caps()
def update_batches(subTaskId):
	pass

@bp.route(_name + '/<int:subTaskId>/batches/', methods=['DELETE'])
@api
@caps()
def dismiss_all_batches(subTaskId):
	pass

@bp.route(_name + '/<int:subTaskId>/dailysubtotals/', methods=['GET'])
@api
@caps()
def get_sub_task_daily_subtotals(subTaskId):
	pass

@bp.route(_name + '/<int:subTaskId>/intervals/', methods=['GET'])
@api
@caps()
def get_sub_task_work_intervals(subTaskId):
	pass

@bp.route(_name + '/<int:subTaskId>/loads/', methods=['GET'])
@api
@caps()
def get_sub_task_rework_load_records(subTaskId):
	pass


@bp.route(_name + '/<int:subTaskId>/metrics/', methods=['GET'])
@api
@caps()
def get_sub_task_work_metrics(subTaskId):
	pass


@bp.route(_name + '/<int:subTaskId>/performance/', methods=['GET'])
@api
@caps()
def get_sub_task_worker_performance_records(subTaskId):
	pass

@bp.route(_name + '/<int:subTaskId>/qasettings/', methods=['GET'])
@api
@caps()
def get_sub_task_qa_settings(subTaskId):
	pass

@bp.route(_name + '/<int:subTaskId>/qasettings/', methods=['PUT'])
@api
@caps()
def update_sub_task_qa_settings(subTaskId):
	pass

@bp.route(_name + '/<int:subTaskId>/qasettings/', methods=['DELETE'])
@api
@caps()
def delete_sub_task_qa_settings(subTaskId):
	pass

@bp.route(_name + '/<int:subTaskId>/rates/', methods=['GET'])
@api
@caps()
def get_sub_task_rate_records(subTaskId):
	pass

@bp.route(_name + '/<int:subTaskId>/rates/', methods=['POST'])
@api
@caps()
def create_sub_task_rate_record(subTaskId):
	pass

@bp.route(_name + '/<int:subTaskId>/stats/', methods=['GET'])
@api
@caps()
def get_sub_task_statistics(subTaskId):
	pass

@bp.route(_name + '/<int:subTaskId>/warnings/', methods=['GET'])
@api
@caps()
def get_sub_task_warnings(subTaskId):
	pass

@bp.route(_name + '/<int:subTaskId>/workers/', methods=['GET'])
@api
@caps()
def get_sub_task_workers(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		abort(404)

