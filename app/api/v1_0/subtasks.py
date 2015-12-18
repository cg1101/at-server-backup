
from flask import request, session, jsonify

import db.model as m
from db.db import SS
from app.api import api, caps, MyForm, Field, validators
from app.i18n import get_text as _
from . import api_1_0 as bp, InvalidUsage

_name = __file__.split('/')[-1].split('.')[0]


@bp.route(_name + '/<int:subTaskId>', methods=['GET'])
@api
@caps()
def get_sub_task(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId), 404)
	return jsonify({
		'subTask': m.SubTask.dump(subTask, context={}),
	})


@bp.route(_name + '/<int:subTaskId>', methods=['PUT'])
@api
@caps()
def update_sub_task(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId), 404)

	data = MyForm(
	).get_data()

	for key in data.keys():
		value = data[key]
		if getattr(subTask, key) != value:
			setattr(subTask, key, value)
		else:
			del data[key]
	SS.flush()
	return jsonify({
		'message': _('updated sub task {0} successfully').format(subTaskId),
		'subTask': m.SubTask.dump(subTask, context={}),
	})

@bp.route(_name + '/<int:subTaskId>/batches/', methods=['GET'])
@api
@caps()
def get_sub_task_batches(subTaskId):
	batches = m.Batch.query.filter_by(subTaskId=subTaskId
		).order_by(m.Batch.batchId).all()
	return jsonify({
		'batches': m.Batch.dump(batches),
	})


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
	subtotals = m.DailySubtotal.query.filter_by(subTaskId=subTaskId).all()
	return jsonify({
		'subtotals': m.DailySubtotal.dump(subtotals),
	})

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
	rates = m.SubTaskRate.query.filter_by(subTaskId=subTaskId
		).order_by(m.SubTaskRate.validFrom).all()
	return jsonify({
		'subTaskRates': m.SubTaskRate.dump(rates),
	})

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
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId), 404)

