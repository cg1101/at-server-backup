
import os
import glob
import datetime
import re

from flask import request, session, jsonify
from sqlalchemy.orm.exc import NoResultFound
# from sqlalchemy import and_

import db.model as m
from db.db import SS
from app.api import api, caps, MyForm, Field, validators
from app.i18n import get_text as _
from . import api_1_0 as bp, InvalidUsage
from app.util import Loader, Selector

_name = __file__.split('/')[-1].split('.')[0]


@bp.route(_name + '/', methods=['GET'])
@api
@caps()
def get_tasks():
	q = m.Task.query
	if request.args:
		if 'projectId' in request.args:
			try:
				projectId = int(request.args['projectId'])
			except:
				pass
			else:
				q = q.filter_by(projectId=projectId)
	tasks = q.all()
	return jsonify({
		'tasks': m.Task.dump(tasks),
	})


@bp.route(_name + '/<int:taskId>', methods=['GET'])
@api
@caps()
def get_task(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	return jsonify({
		'task': m.Task.dump(task),
	})


from .pools import check_task_type_existence


@bp.route(_name + '/<int:taskId>', methods=['PUT'])
@api
@caps()
def migrate_task(taskId):
	pdb_task = m.PdbTask.query.get(taskId)
	if not pdb_task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)

	if m.Task.query.get(taskId):
		raise InvalidUsage(_('task {0} already exists').format(taskId))

	me = session['current_user']

	data = MyForm(
		Field('taskTypeId', is_mandatory=True, validators=[
			validators.is_number,
			check_task_type_existence,
		]),
	).get_data()

	project = m.Project.query.get(pdb_task.projectId)
	migrate_project = not bool(project)
	if migrate_project:
		pdb_project = m.PdbProject.query.get(pdb_task.projectId)
		if not pdb_project:
			# this should never happen, just in case
			raise InvalidUsage(_('unable to migrate project {0}'
				).format(pdb_task.projectId))
		project = m.Project(projectId=pdb_task.projectId,
			name=pdb_project.name, _migratedByUser=me)
		SS.add(project)
		SS.flush()

	task = m.Task(taskId=pdb_task.taskId, name=pdb_task.name,
		taskTypeId=data['taskTypeId'], projectId=project.projectId,
		_migratedByUser=me)
	SS.add(task)

	rs = {'task': m.Task.dump(task)}
	if migrate_project:
		rs['message'] = _('migrated project {0} and task {0} successfully')\
			.format(task.projectId, taskId)
		rs['project'] = m.Project.dump(project)
	else:
		rs['message'] = _('migrated task {0} successfully').format(taskId),
	return jsonify(rs)


@bp.route(_name + '/<int:taskId>/dailysubtotals/', methods=['GET'])
@api
@caps()
def get_task_daily_subtotals(taskId):
	subtotals = m.DailySubtotal.query.filter(m.DailySubtotal.subTaskId.in_(
			SS.query(m.SubTask.subTaskId).filter_by(taskId=taskId))).all()
	return jsonify({
		'subtotals': m.DailySubtotal.dump(subtotals),
	})


@bp.route(_name + '/<int:taskId>/errorclasses/', methods=['GET'])
@api
@caps()
def get_task_error_classes(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	errorClasses = m.ErrorClass.query.filter(m.ErrorClass.errorClassId.in_(
			SS.query(m.ErrorType.errorClassId).join(m.TaskErrorType
			).filter(m.TaskErrorType.taskId==taskId).distinct())).all()
	return jsonify({
		'errorClasses': m.ErrorClass.dump(errorClasses)
	})


@bp.route(_name + '/<int:taskId>/errortypes/', methods=['GET'])
@api
@caps()
def get_task_error_types(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	taskErrorTypes = m.TaskErrorType.query.filter_by(taskId=taskId).all()
	return jsonify({
		'taskErrorTypes': m.TaskErrorType.dump(taskErrorTypes),
	})


@bp.route(_name + '/<int:taskId>/errortypes/', methods=['PUT'])
@api
@caps()
def update_task_error_types(taskId):
	# TODO: modify multiple error types
	return jsonify({
	})


def check_error_type_existence(data, key, errorTypeId):
	if not m.ErrorType.query.get(errorTypeId):
		raise ValueError, _('error type {0} not found').format(errorTypeId)


@bp.route(_name + '/<int:taskId>/errortypes/<int:errorTypeId>', methods=['PUT'])
@api
@caps()
def configure_task_error_type(taskId, errorTypeId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)

	data = MyForm(
		Field('errorTypeId', is_mandatory=True, default=errorTypeId,
			validators=[
				check_error_type_existence,
		]),
		Field('severity', is_mandatory=True,
			normalizer=lambda data, key, value: float(value),
			validators=[
				(validators.is_number, (), dict(max_value=1, min_value=0)),
		]),
		Field('disabled', is_mandatory=True, default=False, validators=[
			validators.is_bool,
		]),
	).get_data()

	rs = {}
	try:
		taskErrorType = m.TaskErrorType.query.filter_by(taskId=taskId
			).filter_by(errorTypeId=errorTypeId).one()
	except NoResultFound:
		taskErrorType = m.TaskErrorType(**data)
		SS.add(taskErrorType)
		rs['message'] = _('added error type {0} to task {1}').format(errorTypeId, taskId)
	else:
		for key in data.keys():
			value = data[key]
			if getattr(taskErrorType, key) != value:
				setattr(taskErrorType, key, value)
			else:
				del data[key]
		rs['message'] = _('updated error type {0} of task {1}').format(errorTypeId, taskId)
		rs['updatedFields'] = data.keys()
	# reload instance to populate relationships
	taskErrorType = m.TaskErrorType.query.get((taskId, errorTypeId))
	rs['taskErrorType'] = m.TaskErrorType.dump(taskErrorType)
	return jsonify(rs)


@bp.route(_name + '/<int:taskId>/errortypes/<int:errorTypeId>', methods=['DELETE'])
@api
@caps()
def disable_task_error_type(taskId, errorTypeId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	try:
		taskErrorType = m.TaskErrorType.query.filter_by(taskId=taskId
			).filter_by(errorTypeId=errorTypeId).one()
	except NoResultFound:
		# TODO: do not flag this as error?
		raise InvalidUsage(_('error type {0} not configured for task {1}'
			).format(errorTypeId, taskId))
	taskErrorType.disabled = True
	SS.flush()
	return jsonify({
		'message': _('disabled error type {0} of task {1}').format(errorTypeId, taskId),
		'taskErrorType': m.TaskErrorType.dump(taskErrorType),
	})


@bp.route(_name + '/<int:taskId>/extract_<timestamp>.txt', methods=['GET', 'POST'])
def get_task_extract(taskId, timestamp):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	# TODO: implement this
	return 'extract of task %s' % taskId


def check_file_handler_existence(data, key, handlerId):
	if not m.FileHandler.query.get(handlerId):
		raise ValueError, _('file handler {0} not found').format(handlerId)


@bp.route(_name + '/<int:taskId>/filehandlers/', methods=['PUT'])
@api
@caps()
def configure_task_file_handler(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	data = MyForm(
		Field('handlerId', is_mandatory=True, validators=[
			validators.is_number,
			check_file_handler_existence,
		]),
	).get_data()
	task.handlerId = data['handlerId']
	return jsonify({
		'message': _('configured task {0} to use file handler {1}'
			).format(taskId, data['handlerId'])
	})


@bp.route(_name + '/<int:taskId>/instructions/', methods=['GET'])
@api
@caps()
def get_task_instruction_files(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	# TODO: get root path from configuration
	root = '/audio2/AppenText'
	path = os.path.join(root, 'docs', 'tasks', str(taskId))
	files = glob.glob(os.path.join(path, '*'))
	return jsonify({
		'instructions': [dict(basename=os.path.basename(i), path=i)
			for i in files],
	})


@bp.route(_name + '/<int:taskId>/instructions/', methods=['POST'])
@api
@caps()
def upload_task_instruction_file(taskId):
	# TODO: implement this
	return jsonify({
	})


@bp.route(_name + '/<int:taskId>/loads/')
@api
@caps()
def get_task_loads(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	loads = m.Load.query.filter_by(taskId=taskId).all()
	return jsonify({
		'loads': m.Load.dump(loads),
	})


@bp.route(_name + '/<int:taskId>/loads/', methods=['POST'])
@api
@caps()
def create_task_load(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId))
	handler = (None if task.handlerId is None else
			m.FileHandler.query.get(task.handlerId))
	if not handler:
		raise InvalidUsage(_('no handler configured for task {0}').format(taskId))
	# TODO: add validation
	data = MyForm(
		Field('options'),
		Field('dataFile')
	).get_data(is_json=False)
	data['options'] = {}
	try:
		rawPieces = Loader.load(handler, task,
				data['dataFile'], **data['options'])
	except Exception, e:
		raise InvalidUsage(_('failed to load file: {0}').format(str(e)))
	me = session['current_user']
	load = m.Load(taskId=taskId, createdBy=me.userId)
	SS.add(load)
	SS.flush()
	for i, rawPiece in enumerate(rawPieces):
		# no need to populate: rawPieceId, isNew, groupId
		# inferred from context: taskId
		# context-free fields: rawText, words, meta, hypothesis
		# populated in context: allocationContext, assemblyContext
		# auto-populated: loadId
		rawPiece.taskId = taskId
		rawPiece.loadId = load.loadId
		if getattr(rawPiece, 'allocationContext') is None:
			rawPiece.allocationContext = 'L%05d' % load.loadId
		if getattr(rawPiece, 'assemblyContext') is None:
			rawPiece.assemblyContext = 'L%05d_%05d' % (load.loadId, i)
		load.rawPieces.append(rawPiece)
	return jsonify({
		'message': _('loaded {0} raw pieces into task {0} successfully'
			).format(len(rawPieces), taskId),
		'load': m.Load.dump(load),
	})


@bp.route(_name + '/<int:taskId>/payments/', methods=['GET'])
@api
@caps()
def get_task_payments(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	payments = m.CalculatedPayment.query.filter_by(taskId=taskId).all()
	return jsonify({
		'payments': m.CalculatedPayment.dump(payments),
	})


@bp.route(_name + '/<int:taskId>/paystats/', methods=['GET'])
@api
@caps()
def get_task_payment_statistics(taskId):
	# TODO: implement this
	return jsonify({
	})


@bp.route(_name + '/<int:taskId>/rawpieces/', methods=['GET'])
def get_task_raw_pieces(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	rawPieces = m.RawPiece.query.filter_by(taskId=taskId).all()
	return jsonify({
		'rawPieces': m.RawPiece.dump(rawPieces),
	})


@bp.route(_name + '/<int:taskId>/selections/', methods=['GET'])
def get_task_utterance_selections(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	me = session['current_user']
	selections = m.UtteranceSelection.query.filter_by(taskId=taskId
			).filter_by(userId=me.userId
			).filter_by(processed=None).all()
	return jsonify({
		'selections': m.UtteranceSelection.dump(selections),
	})


from .subtasks import (check_sub_task_existence, check_sub_task_type_in,
	check_sub_task_attribute)


def check_sub_task_batching_mode_in(data, key, subTaskId, *modes):
	subTask = m.SubTask.query.get(subTaskId)
	if subTask.batchingMode not in modes:
		raise ValueError(_('batching mode not allowed').format(subTask.batchingMode))


def check_custom_utterance_group_name_uniqueness(data, key, name, taskId):
	if m.CustomUtteranceGroup.query.filter_by(taskId=taskId
			).filter_by(name=name).count() > 0:
		raise ValueError(_('name {0} is already in use').format(name))


def normalize_utterance_selection_value_input(data, key, value):
	taskId = data['taskId']
	action = data['action']
	if action == m.UtteranceSelection.ACTION_CUSTOM:
		try:
			check_custom_utterance_group_name_uniqueness(data, key, value, taskId)
		except ValueError:
			raise
		else:
			data['name'] = value
			data['subTaskId'] = None
	elif action == m.UtteranceSelection.ACTION_BATCH:
		try:
			subTaskId = int(value)
		except:
			raise ValueError(_('invalid sub task id {0}').format(value))
		try:
			check_sub_task_existence(data, key, subTaskId)
			check_sub_task_attribute(data, key, subTaskId, taskId=taskId)
			check_sub_task_type_in(data, key, subTaskId, m.WorkType.REWORK)
			check_sub_task_batching_mode_in(data, key, subTaskId, m.BatchingMode.NONE)
		except:
			raise
		data['subTaskId'] = subTaskId
		data['name'] = None
	else:
		raise InvalidUsage(_('can\'t validate value due to unsupported action {0}'
			).format(action))
	return value


def check_utterance_selection_limit(data, key, value):
	if value is None:
		return
	try:
		value = int(value)
		if value < 0:
			raise ValueError
	except:
		raise InvalidUsage(_('invalid limit value {0}').format(value))


def normalize_utterance_selection_filters(data, key, value):
	# load filters spec into tmp
	tmp = {}
	p = re.compile('(?P<isInclusive>include|exclude)_(?P<filterIndex>\d+)_(?P<paramIndex>\d+)$')
	for key, value in data.iteritems():
		match_obj = p.match(key)
		if not match_obj:
			continue
		x = match_obj.groups()
		isInclusive = x[0] == 'include'
		filterIndex = int(x[1])
		paramIndex = int(x[2])
		tmp.setdefault(isInclusive, {}).setdefault(filterIndex, {})[paramIndex] = value

	# validate tmp
	filters = []
	for isInclusive in (True, False):
		for filterIndex in sorted(tmp.setdefault(isInclusive, {})):
			input_dict = tmp[isInclusive][filterIndex]
			output_dict = {}
			output_dict['isInclusive'] = isInclusive
			for i, field in enumerate(['description', 'isMandatory', 'filterType']):
				if i not in input_dict:
					raise ValueError(
						_('filter {0}: {1}: mandatory field \'{2}\' missing'
					).format(filterIndex, i, field))
				value = input_dict[i]
				if i == 0 and not (isinstance(value,
						basestring) and value.strip()):
					raise ValueError(_('filter {0}: {1}: {2} must be non-blank string'
						).format(filterIndex, i, field))
				elif i == 1:
					if value not in ('true', 'false'):
						raise ValueError(_('filter {0}: {1}: {2} must be \'true\' or \'false\''
							).format(filterIndex, i, field))
					else:
						value = (value == 'true')
				elif i == 2 and value not in Selector.FILTER_TYPES.values():
					raise ValueError(_('filter {0}: {1}: {2} not found {3}'
						).format(filterIndex, i, field, value))
				output_dict[field] = value
			output_dict['pieces'] = [input_dict[i] for i in sorted(input_dict) if i > 2]
			filters.append(output_dict)
	if len(filters) == 0:
		raise ValueError(_('must specify at least one filter'))
	return filters


@bp.route(_name + '/<int:taskId>/selections/', methods=['POST'])
def create_task_utterance_selection(taskId):
	data = MyForm(
		Field('action', is_mandatory=True, validators=[
			# NOTE: action 'pp' is not supported
			(validators.enum, (m.UtteranceSelection.ACTION_CUSTOM,
				m.UtteranceSelection.ACTION_BATCH)),
		]),
		Field('value', is_mandatory=True,
			normalizer=normalize_utterance_selection_value_input),
		Field('limit', is_mandatory=True, default=lambda: None,
			validators=[
				check_utterance_selection_limit,
		]),
		Field('random', is_mandatory=True, default=True, validators=[
			validators.is_bool,
		]),
		Field('filters', is_mandatory=True, default=[],
			normalizer=normalize_utterance_selection_filters),
	).get_data(copy=True)

	me = session['current_user']
	selection = m.UtteranceSelection(taskId=taskId, userId=me.userId,
		limit=data['limit'], action=data['action'], name=data['name'],
		subTaskId=data['subTaskId'], random=data['random'])
	for x in data['filters']:
		pieces = x.pop('pieces')
		selectionFilter = m.SelectionFilter(**x)
		for i, data_literal in enumerate(pieces):
			piece = m.SelectionFilterPiece(index=i, data=data_literal)
			selectionFilter.pieces.append(piece)
		selection.filters.append(selectionFilter)

	# TODO: run query, if no result found, notify user, otherwise save in cache
	rs = Selector.select(selection)
	if not rs:
		raise InvalidUsage(_('no result found'))

	# SS.add(selection)
	# SS.flush()

	# summary = dict(
	# 	identifier=selection.selectionId,
	# 	number=len(selection.cached),
	# 	timestamp=
	# 	action=selection.action,
	# 	value=selection.value,
	# 	user=
	# 	link=
	# )
	return jsonify({
		'message': _('created utterance selection {0} successfully'
			).format(selection.selectionId),
		'selection': m.UtteranceSelection.dump(selection),
		# 'summary': summary,
	})


@bp.route(_name + '/<int:taskId>/selections/<int:selectionId>', methods=['POST'])
def populate_task_utterance_selection(taskId):
	# TODO: implement this
	return jsonify({
	})


@bp.route(_name + '/<int:taskId>/selections/<int:selectionId>', methods=['DELETE'])
def delete_task_utterance_selection(taskId, selectionId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	selection = m.UtteranceSelection.query.get(selectionId)
	if not selection:
		raise InvalidUsage(_('selection {0} not found').format(selectionId), 404)
	if selection.processed is not None:
		raise InvalidUsage(_('This utterance selection has already processed.',
			'Please refresh the page.'))
	SS.delete(selection)
	return jsonify({
		'message': _('selection {0} has been deleted').format(selectionId),
	})


def check_task_status_transition(data, key, newStatus, currentStatus):
	if newStatus == currentStatus:
		raise ValueError, _('status not changing')
	if currentStatus == m.Task.STATUS_ARCHIVED:
		raise ValueError, _('cannot change status of archived task')


@bp.route(_name + '/<int:taskId>/status', methods=['PUT'])
def update_task_status(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	data = MyForm(
		Field('status', is_mandatory=True, validators=[
			(validators.enum, (m.Task.STATUS_ACTIVE,
				m.Task.STATUS_DISABLED, m.Task.STATUS_FINISHED,
				m.Task.STATUS_CLOSED, m.Task.STATUS_ARCHIVED)),
			(check_task_status_transition, (task.status,)),
		]),
	).get_data()

	# When reopening a closed task, we need to make sure that every sub task
	# under current task has an active work interval, if not, we create one.
	if task.status == m.Task.STATUS_CLOSED:
		for subTask in m.SubTask.query.filter_by(taskId=taskId).all():
			try:
				workInterval = m.WorkInterval.query.filter_by(subTaskId=subTaskId
					).filter_by(endTime=None).order_by(m.WorkInterval.startTime).all()[0]
			except IndexError:
				workInterval = m.WorkInterval(taskId=taskId, subTaskId=subTask.subTaskId)
				SS.add(workInterval)
	task.status = data['status']
	return jsonify({
		'message': _('changed status of task {0} to {1}').format(taskId, task.status),
	})


@bp.route(_name + '/<int:taskId>/summary/', methods=['GET'])
@api
@caps()
def get_task_summary(taskId):
	rs = SS.query(m.RawPiece.rawPieceId, m.RawPiece.isNew, m.RawPiece.words
		).filter_by(taskId=taskId).all()
	nrs = [x for x in rs if x.isNew]
	itemCount = len(rs)
	unitCount = sum([x.words for x in rs])
	newItemCount = len(nrs)
	newUnitCount = sum([x.words for x in nrs])

	#
	# following query is not necessary because WorkEntry has workType already
	# qaed = SS.query(m.WorkEntry.qaedEntryId.distinct()
	# 	).filter(m.WorkEntry.subTaskId.in_(
	# 		SS.query(m.SubTask.subTaskId).filter(
	# 			and_(m.SubTask.taskId==999999,
	# 				m.SubTask.workTypeId==m.WorkType.workTypeId,
	# 				m.WorkType.name==m.WorkType.QA))))
	#

	qaed = SS.query(m.WorkEntry.qaedEntryId.distinct()
		).filter(m.WorkEntry.taskId==taskId
		).filter(m.WorkEntry.workType==m.WorkType.QA)
	rqaed = SS.query(m.WorkEntry.rawPieceId.distinct()
		).filter(m.WorkEntry.entryId.in_(qaed))
	qrs = SS.query(m.RawPiece.rawPieceId, m.RawPiece.isNew, m.RawPiece.words
		).filter(m.RawPiece.rawPieceId.in_(rqaed)).all()
	qaedItemCount = len(qrs)
	qaedUnitCount = sum([x.words for x in qrs])

	return jsonify({
		'summary': {
			'itemCount': itemCount,
			'unitCount': unitCount,
			'finishedItemCount': itemCount - newItemCount,
			'finishedUnitCount': unitCount - newUnitCount,
			'newItemCount': newItemCount,
			'newUnitCount': newUnitCount,
			'completionRate': None if itemCount == 0 else (1 - float(newItemCount) / itemCount),
			'qaedItemCount': qaedItemCount,
			'qaedUnitCount': qaedUnitCount,
			'overallQaScore': None,
			'overallAccuracy': None,
		}
	})


@bp.route(_name + '/<int:taskId>/subtasks/', methods=['GET'])
@api
@caps()
def get_task_sub_tasks(taskId):
	# task = m.Task.query.get(taskId)
	# if not task:
	# 	raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	subTasks = m.SubTask.query.filter_by(taskId=taskId).all()
	return jsonify({
		'subTasks': m.SubTask.dump(subTasks),
	})


def check_sub_task_name_uniqueness(data, key, name, taskId, subTaskId):
	if m.SubTask.query.filter_by(taskId=taskId
			).filter_by(name=name
			).filter(m.SubTask.subTaskId!=subTaskId).count() > 0:
		raise ValueError, _('name \'{0}\' is already in use').format(name)


def check_work_type_existence(data, key, workTypeId):
	if not m.WorkType.query.get(workTypeId):
		raise ValueError, _('work type {0} not found').format(workTypeId)


def check_batching_mode_existence(data, key, modeId):
	if not m.BatchingMode.query.get(modeId):
		raise ValueError, _('batching mode {0} not found').format(modeId)


def normalize_interval_as_seconds(data, key, value):
	try:
		value = int(value)
	except:
		raise ValueError, _('invalid interval {0}').format(value)
	return datetime.timedelta(seconds=value)


def check_lease_life_minimal_length(data, key, value, min_value):
	if value < min_value:
		raise ValueError, _('lease life must not be less than 5 minutes')


@bp.route(_name + '/<int:taskId>/subtasks/', methods=['POST'])
@api
@caps()
def create_sub_task(taskId):
	# TODO: define constants for ltr/rtl, nolimit/oneonly
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	data = MyForm(
		Field('name', is_mandatory=True, validators=[
			validators.non_blank,
			(check_sub_task_name_uniqueness, (taskId, None)),
		]),
		Field('taskId', is_mandatory=True, default=task.taskId,
				normalizer=lambda data, key, value: task.taskId),
		Field('workTypeId', is_mandatory=True, validators=[
			check_work_type_existence,
		]),
		Field('maxPageSize', default=20, validators=[
			(validators.is_number, (), dict(min_value=1)),
		]),
		Field('dstDir', is_mandatory=True, default='ltr', validators=[
			(validators.enum, ('ltr', 'rtl')),
		]),
		Field('modeId', is_mandatory=True, validators=[
			check_batching_mode_existence,
		]),
		Field('getPolicy', is_mandatory=True, default='nolimit', validators=[
			(validators.enum, ('nolimit', 'oneonly')),
		]),
		Field('expiryPolicy', is_mandatory=True, default='noextend', validators=[
			(validators.enum, ('noextend',)),
		]),
		Field('allowPageSkip', is_mandatory=True, default=True, validators=[
			validators.is_bool,
		]),
		Field('needItemContext', is_mandatory=False, default=False, validators=[
			validators.is_bool,
		]),
		Field('allowEditing', is_mandatory=True, default=True, validators=[
			validators.is_bool,
		]),
		Field('allowAbandon', is_mandatory=True, default=False, validators=[
			validators.is_bool,
		]),
		Field('lookAhead', is_mandatory=True, default=0, validators=[
			(validators.is_number, (), dict(min_value=0)),
		]),
		Field('lookBehind', is_mandatory=True, default=0, validators=[
			(validators.is_number, (), dict(min_value=0)),
		]),
		Field('allowCheckout', is_mandatory=True, default=False, validators=[
			validators.is_bool,
		]),
		Field('isSecondPassQa', validators=[
			validators.is_bool,
		]),
		Field('defaultLeaseLife', is_mandatory=True, default=7*24*60*60,
			normalizer=normalize_interval_as_seconds, validators=[
			(check_lease_life_minimal_length, (datetime.timedelta(seconds=300),)),
		]),
		Field('needDynamicTagSet', default=False, validators=[
			validators.is_bool,
		]),
		Field('instructionPage'),
		Field('useQaHistory', default=False, validators=[
			validators.is_bool,
		]),
		Field('hideLabels', default=False, validators=[
			validators.is_bool,
		]),
		Field('validators', validators=[
			validators.is_string,
		]),
	).get_data()

	subTask = m.SubTask(**data)
	SS.add(subTask)
	SS.flush()
	workInterval = m.WorkInterval(taskId=subTask.taskId, subTaskId=subTask.subTaskId)
	SS.add(workInterval)
	return jsonify({
		'message': _('created sub task {0} sucessfully').format(subTask.name),
		'subTask': m.SubTask.dump(subTask),
		'workInterval': m.WorkInterval.dump(workInterval),
	})


@bp.route(_name + '/<int:taskId>/supervisors/', methods=['GET'])
@api
@caps()
def get_task_supervisors(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	return jsonify({
		'supervisors': m.TaskSupervisor.dump(task.supervisors),
	})


@bp.route(_name + '/<int:taskId>/supervisors/<int:userId>', methods=['PUT'])
@api
@caps()
def update_task_supervisor_settings(taskId, userId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	try:
		supervisor = m.TaskSupervisor.query.filter_by(taskId=taskId
			).filter_by(userId=userId).one()
	except NoResultFound:
		raise InvalidUsage(_('supervisor {0} not found').format(userId), 404)

	data = MyForm(
		Field('receivesFeedback', validators=[
			validators.is_bool,
		]),
		Field('informLoads', validators=[
			validators.is_bool,
		]),
	).get_data()

	for key in data.keys():
		value = data[key]
		if getattr(supervisor, key) != value:
			setattr(supervisor, key, value)
		else:
			del data[key]
	SS.flush()

	return jsonify({
		'message': _('updated supervisor {0} of task {1} successfully').format(
			supervisor.userName, supervisor.taskId),
		'updatedFields': data.keys(),
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
		raise InvalidUsage(_('supervisor {0} not found').format(userId), 404)
	SS.delete(supervisor)
	return jsonify({
		'message': _('removed supervisor {0} from task {1}').format(supervisor.userName, taskId),
	})


@bp.route(_name + '/<int:taskId>/uttgroups/', methods=['GET'])
@api
@caps()
def get_task_custom_utterance_groups(taskId):
	groups = m.CustomUtteranceGroup.query.filter_by(taskId=taskId).all()
	return jsonify({
		'utteranceGroups': m.CustomUtteranceGroup.dump(groups),
	})


@bp.route(_name + '/<int:taskId>/uttgroups/<int:groupId>', methods=['DELETE'])
@api
@caps()
def delete_custom_utterance_group(taskId, groupId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId))
	if task.status == m.Task.STATUS_ARCHIVED:
		raise InvalidUsage(_('can\'t delete utterance groups from archived task'))
	group = m.CustomUtteranceGroup.query.get(groupId)
	if not group or group.taskId != taskId:
		raise InvalidUsage(_('utterance group {0} not found').format(taskId), 404)
	SS.delete(group)
	SS.delete(group.selection)
	return jsonify({
		'message': _('deleted custom utterance group {0} of task {1} successfully'
			).format(groupId, taskId),
	})


@bp.route(_name + '/<int:taskId>/uttgroups/<int:groupId>/words', methods=['GET'])
@api
@caps()
def get_utterance_group_word_count(taskId, groupId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	group = m.CustomUtteranceGroup.query.get(groupId)
	if not group or group.taskId != taskId:
		raise InvalidUsage(_('utterance group {0} not found').format(taskId), 404)

	words = sum([i.words for i in group.rawPieces])
	return jsonify({
		'words': words,
		'totalItems': len(group.rawPieces),
	})


@bp.route(_name + '/<int:taskId>/warnings/', methods=['GET'])
@api
@caps()
def get_task_warnings(taskId):
	# TODO: generate warnings
	return jsonify({
		'warnings': [],
	})


@bp.route(_name + '/<int:taskId>/workers/', methods=['GET'])
def get_task_workers(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)

	workers = m.TaskWorker.query.filter_by(taskId=taskId).all()
	return jsonify({
		'workers': m.TaskWorker.dump(workers),
	})


@bp.route(_name + '/<int:taskId>/workers/', methods=['DELETE'])
def unassign_all_task_workers(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	for i in m.TaskWorker.query.filter_by(taskId=taskId).all():
		i.removed = True
	return jsonify({
		'message': _('removed all workers from task {0}').format(taskId),
	})

