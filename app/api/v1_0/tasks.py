
from flask import request, abort, session, jsonify
from sqlalchemy.orm.exc import NoResultFound

import db.model as m
from db.db import SS
from app.api import api, caps
from app.i18n import get_text as _
from . import api_1_0 as bp

_name = __file__.split('/')[-1].split('.')[0]

@bp.route(_name + '/', methods=['GET'])
@api
@caps()
def get_tasks():
	tasks = m.Task.query.all()
	return jsonify({
		'tasks': m.Task.dump(tasks),
	})


@bp.route(_name + '/<int:taskId>', methods=['GET'])
@api
@caps()
def get_task(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		abort(404)
	return jsonify({
		'task': m.Task.dump(task),
	})


@bp.route(_name + '/<int:taskId>', methods=['PUT'])
@api
@caps()
def migrate_task(taskId):
	pdb_task = m.PdbTask.query.get(taskId)
	if not pdb_task:
		abort(404)
	task = m.Task()
	return jsonify({
		'task': m.Task.dump(task)
	})

@bp.route(_name + '/<int:taskId>/dailysubtotals/', methods=['GET'])
@api
@caps()
def get_task_daily_subtotals(taskId):
	return jsonify({

	})

@bp.route(_name + '/<int:taskId>/errorclasses/', methods=['GET'])
@api
@caps()
def get_task_error_classes(taskId):
	return jsonify({

	})

@bp.route(_name + '/<int:taskId>/errortypes/', methods=['GET'])
@api
@caps()
def get_task_error_types(taskId):
	taskErrorTypes = m.TaskErrorType.query.filter_by(taskId=taskId).all()
	return jsonify({
		'taskErrorTypes': m.TaskErrorType.dump(taskErrorTypes),
	})

@bp.route(_name + '/<int:taskId>/errortypes/', methods=['PUT'])
@api
@caps()
def update_task_error_types(taskId):
	return jsonify({
	})

@bp.route(_name + '/<int:taskId>/errortypes/<int:errorTypeId>', methods=['PUT'])
@api
@caps()
def configure_task_error_type(taskId, errorTypeId):
	task = m.Task.query.get(taskId)
	if not task:
		abort(404)
	try:
		taskErrorType = m.TaskErrorType.query.filter_by(taskId=taskId
	 		).filter_by(errorTypeId=errorTypeId).one()
	except NoResultFound:
		data = request.get_json()
	 	taskErrorType = m.TaskErrorType(**data)
	return jsonify({
		'taskErrorType': m.TaskErrorType.dump(taskErrorType),
	})

@bp.route(_name + '/<int:taskId>/errortypes/<int:errorTypeId>', methods=['DELETE'])
@api
@caps()
def disable_task_error_type(taskId, errorTypeId):
	task = m.Task.query.get(taskId)
	if not task:
		abort(404)
	try:
		taskErrorType = m.TaskErrorType.query.filter_by(taskId=taskId
			).filter_by(errorTypeId=errorTypeId).one()
	except NoResultFound:
		abort(404)
	taskErrorType.removed = True
	SS.flush()
	return jsonify({
		'taskErrorType': m.TaskErrorType.dump(taskErrorType)
	})

@bp.route(_name + '/<int:taskId>/extract_<timestamp>.txt', methods=['GET', 'POST'])
def getTaskExtract(taskId, timestamp):
	return 'extract of task %s' % taskId

@bp.route(_name + '/<int:taskId>/filehandlers/', methods=['PUT'])
@api
@caps()
def get_s(taskId):
	return jsonify({

	})

@bp.route(_name + '/<int:taskId>/instructions/', methods=['GET'])
def get_task_instruction_files(taskId):
	return jsonify({
	})

@bp.route(_name + '/<int:taskId>/instructions/', methods=['POST'])
def upload_task_instruction_file(taskId):
	return jsonify({
	})

@bp.route(_name + '/<int:taskId>/loads/', methods=['POST'])
def create_task_load(taskId):
	return jsonify({
	})

@bp.route(_name + '/<int:taskId>/payments/', methods=['GET'])
@api
@caps()
def get_task_payments(taskId):
	return jsonify({
	})

@bp.route(_name + '/<int:taskId>/paystats/', methods=['GET'])
@api
@caps()
def get_task_payment_statistics(taskId):
	return jsonify({
	})

@bp.route(_name + '/<int:taskId>/rawpieces/', methods=['GET'])
def get_task_raw_pieces(taskId):
	rawPieces = m.RawPiece.query.filter_by(taksId=taskId).all()
	return jsonify({
		'rawPieces': m.RawPiece.dump(rawPieces),
	})

@bp.route(_name + '/<int:taskId>/selections/', methods=['GET'])
def get_task_utterrance_selection(taskId):
	return jsonify({
	})

@bp.route(_name + '/<int:taskId>/selections/', methods=['POST'])
def create_task_utterrance_selection(taskId):
	return jsonify({
	})

@bp.route(_name + '/<int:taskId>/selections/<int:selectionId>', methods=['POST'])
def populate_task_utterrance_selection(taskId):
	return jsonify({
	})

@bp.route(_name + '/<int:taskId>/selections/<int:selectionId>', methods=['DELETE'])
def delete_task_utterrance_selection(taskId):
	return jsonify({
	})

@bp.route(_name + '/<int:taskId>/status', methods=['GET'])
def get_task_status(taskId):
	return jsonify({
	})

@bp.route(_name + '/<int:taskId>/status', methods=['PUT'])
def update_task_status(taskId):
	return jsonify({

	})

@bp.route(_name + '/<int:taskId>/summary/', methods=['GET'])
@api
@caps()
def get_task_summary(taskId):
	return jsonify({
	})

@bp.route(_name + '/<int:taskId>/subtasks/', methods=['GET'])
@api
@caps()
def get_task_sub_tasks(taskId):
	subTasks = m.SubTask.query.filter_by(taskId=taskId).all()
	return jsonify({
		'subTask': m.SubTask.dump(subTasks),
	})

@bp.route(_name + '/<int:taskId>/subtasks/', methods=['POST'])
@api
@caps()
def create_sub_task(taskId):
	data = request.get_json()
	subTask = m.SubTask(**data)
	workInterval = m.WorkInterval()
	SS().add(subTask)
	SS().add(workInterval)
	return jsonify({
		'subTask': m.SubTask.dump(subTask),
	})

@bp.route(_name + '/<int:taskId>/supervisors/', methods=['GET'])
@api
@caps()
def get_task_supervisors(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		abort(404)
	return jsonify({
		'supervisors': m.TaskSupervisor.dump(task.supervisors),
	})

@bp.route(_name + '/<int:taskId>/supervisors/<int:userId>', methods=['PUT'])
@api
@caps()
def update_task_supervisor_settings(taskId, userId):
	try:
		supervisor = m.TaskSupervisor.query.filter_by(taskId=taskId
			).filter_by(userId=userId).one()
	except NoResultFound:
		abort(404)
	return jsonify({
		'supervisor': m.TaskSupervisor.dump(supervisor),
	})

@bp.route(_name + '/<int:taskId>/supervisors/<int:userId>', methods=['DELETE'])
@api
@caps()
def remove_task_supervisor(taskId, userId):
	try:
		supervisor = m.TaskSupervisor.query.filter_by(taskId=taskId
			).filter_by(userId=userId).one()
	except NoResultFound:
		abort(404)
	SS().delete(supervisor)
	return 'remove supervisor %s from task %s' % (userId, taskId)

@bp.route(_name + '/<int:taskId>/uttgroups/', methods=['GET'])
@api
@caps()
def get_task_custom_utterance_groups(taskId):
	uttGroups = m.CustomUtteranceGroup.query.filter_by(taskId=taskId).all()
	return jsonify({
		'uttgroups': m.CustomUtteranceGroup.dump(uttGroups),
	})

@bp.route(_name + '/<int:taskId>/uttgroups/<int:groupId>', methods=['DELETE'])
@api
@caps()
def delete_custom_utterance_group(taskId, groupId):
	uttGroup = m.CustomUtteranceGroup.query.get(groupId)
	if not uttGroup:
		abort(404)
	if not uttGroup.taskId == taskId:
		abort(404)
	# TODO: delete custom utterance group
	return jsonify({
	})

@bp.route(_name + '/<int:taskId>/uttgroups/<int:groupId>/words', methods=['GET'])
@api
@caps()
def get_utterance_group_word_count(taskId, groupId):
	return 'get utterance group word count'

@bp.route(_name + '/<int:taskId>/warnings/', methods=['GET'])
@api
@caps()
def get_task_warnings(taskId):
	return jsonify({
		'warnings': [],
	})

@bp.route(_name + '/<int:taskId>/workers/', methods=['GET'])
def get_task_workers(taskId):
	return 'gettaskworkers'

@bp.route(_name + '/<int:taskId>/workers/', methods=['DELETE'])
def unassign_all_task_workers(taskId):
	return jsonify({
	})
