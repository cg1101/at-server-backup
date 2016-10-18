
import os
import glob
import datetime
import re
import json

from flask import request, session, jsonify, make_response, url_for, current_app
from sqlalchemy import or_
from sqlalchemy.orm import make_transient
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.utils import secure_filename
import pytz
# from sqlalchemy import and_

import db.model as m
from db.db import SS
from app.api import api, caps, MyForm, Field, validators
from app.i18n import get_text as _
from . import api_1_0 as bp, InvalidUsage
from app.util import Batcher, Loader, Selector, Extractor, Warnings, tiger, edm, pdb

_name = __file__.split('/')[-1].split('.')[0]


@bp.route(_name + '/', methods=['GET'])
@api
@caps()
def get_tasks():
	if request.args.get('t', '') == 'candidate':
		# TODO: check for capability
		if True:
			tasks = m.PdbTask.query.filter(m.PdbTask.taskId.notin_(
				SS.query(m.Task.taskId))).all()
		else:
			tasks = []
		rs = m.PdbTask.dump(tasks)
	else:
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
		rs = m.Task.dump(tasks)
	return jsonify({
		'tasks': rs,
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
	task = m.Task.query.get(taskId)
	if task:
		return jsonify(
			message=_('task {0} already exists').format(taskId),
			task=m.Task.dump(task),
		)

	if current_app.config['USE_PDB_API']:
		pdb_task = pdb.get_task(taskId)
		if not pdb_task:
			raise InvalidUsage(_('task {0} not found').format(taskId), 404)
		data = pdb_task
		class data_holder(object): pass
		pdb_task = data_holder()
		for k, v in data.iteritems():
			setattr(pdb_task, k, v)
		data = pdb.get_project(pdb_task.projectId)
		pdb_project = data_holder()
		for k, v in data.iteritems():
			setattr(pdb_project, k, v)
	else:
		pdb_task = m.PdbTask.query.get(taskId)
		if not pdb_task:
			raise InvalidUsage(_('task {0} not found').format(taskId), 404)
		pdb_project = m.PdbProject.query.get(pdb_task.projectId)

	me = session['current_user']

	data = MyForm(
		Field('taskTypeId', is_mandatory=True,
			normalizer=lambda data, key, value: int(value[-1]) if isinstance(value, list) else int(value),
			validators=[
				validators.is_number,
				check_task_type_existence,
		]),
		Field('globalProjectId', is_mandatory=True,
			normalizer=lambda data, key, value: int(value[-1]) if isinstance(value, list) else int(value),
			validators=[
				validators.is_number,
		]),
	).get_data(use_args=True)

	project = m.Project.query.get(pdb_task.projectId)
	migrate_project = not bool(project)
	if migrate_project:
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
		_migratedByUser=me, globalProjectId=data['globalProjectId'])
	SS.add(task)

	# reload task to make sure missing attributes are populated
	rs = {'task': m.Task.dump(m.Task.query.get(task.taskId))}
	if migrate_project:
		rs['message'] = _('migrated project {0} and task {1} successfully')\
			.format(task.projectId, taskId)
		rs['project'] = m.Project.dump(project)
	else:
		rs['message'] = _('migrated task {0} successfully').format(taskId)
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
	url = url_for('.configure_task_error_type', taskId=taskId,
		errorTypeId='-999999999', _method='PUT')
	# TODO: generate url pattern from app.url_map directly
	url = url.replace('/' + str(taskId) + '/', '/<int:taskId>/')
	url = url.replace('-999999999', '<int:errorTypeId>')
	raise InvalidUsage(_('this api endpoint has been removed'), 410,
		{'message': _('use {0} instead').format(url)})


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


def normalize_utterance_group_ids(data, key, groupIds):
	taskId= data['taskId']
	try:
		groupIds = set([int(i) for i in groupIds])
	except:
		raise ValueError(_('invalid groupIds input: {0}').format(groupIds))
	for groupId in groupIds:
		group = m.CustomUtteranceGroup.query.get(groupId)
		if not group:
			raise ValueError(_('custom utterance group {0} not found').format(groupId))
		if group.taskId != taskId:
			raise ValueError(_('custom utterance group {0} doesn\'t belong to task {1}'
				).format(groupId, taskId))
	return sorted(groupIds)


@bp.route(_name + '/<int:taskId>/extract_<timestamp>.txt', methods=['GET', 'POST'])
@caps()
def get_task_extract(taskId, timestamp):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	data = MyForm(
		Field('fileFormat', is_mandatory=True, validators=[
			(validators.enum, (Extractor.EXTRACT, Extractor.TABULAR)),
		]),
		Field('sourceFormat', is_mandatory=True, validators=[
			(validators.enum, (Extractor.HTML, Extractor.XML, Extractor.TEXT)),
		]),
		Field('resultFormat', is_mandatory=True, validators=[
			(validators.enum, (Extractor.HTML, Extractor.XML, Extractor.TEXT)),
		]),
		Field('groupIds', is_mandatory=True, default=[],
			normalizer=normalize_utterance_group_ids,
		),
		Field('keepLineBreaks', is_mandatory=True, default=False, validators=[
			validators.is_bool,
		]),
		Field('withQaErrors', is_mandatory=True, default=False, validators=[
			validators.is_bool,
		]),
	).get_data()
	del data['timestamp']
	del data['taskId']
	data['compress'] = True
	extract = Extractor.extract(task, **data)
	response = make_response((extract, 200, {'Content-Type':
		'application/data', 'Content-Encoding': 'gzip'}))
	return response


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


def check_input_file(data, key, value):
	# value should an instance of FileStorage
	pass


from .pools import normalize_bool_literal


@bp.route(_name + '/<int:taskId>/instructions/', methods=['POST'])
@api
@caps()
def upload_task_instruction_file(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)

	data = MyForm(
		Field('dataFile', is_mandatory=True, validators=[
			check_input_file
		]),
		Field('overwrite', is_mandatory=True, default=False,
			normalizer=normalize_bool_literal,
			validators=[
				validators.is_bool,
		])
	).get_data(is_json=False)

	# TODO: use configuration
	root = '/audio2/AppenText'
	path = os.path.join(root, 'instructions', str(taskId))
	if not os.path.exists(path):
		os.makedirs(path)
	filename = secure_filename(data['dataFile'].filename)
	fullpath = os.path.join(path, filename)

	# TODO: check app's setting to pretty print message
	if os.path.exists(fullpath) and not data['overwrite']:
		resp = make_response(('', 409, {'Content-Type': 'application/json'}))
		resp.set_data(json.dumps({
			'error': _('File \'{0}\' already exists, overwrite it?').format(filename),
			'action': 'confirm',
		}))
		return resp
	try:
		with open(fullpath, 'w') as f:
			f.write(data['dataFile'].read())
	except Exception, e:
		resp = make_response(('', 500, {'Content-Type': 'application/json'}))
		resp.set_data(json.dumps({
			'error': _('error writing file {0}, please try later'
				).format(filename),
		}))
		return resp

	return jsonify({
		'message': _('uploaded instruction file {0} successfully'
			).format(filename),
		'filename': filename,
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


@bp.route(_name + '/<int:taskId>/loads/<int:loadId>/stats', methods=['GET'])
@api
@caps()
def get_task_load_stats(taskId, loadId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	load = m.Load.query.get(loadId)
	if not load or load.taskId != taskId:
		raise InvalidUsage(_('load {0} not found in task {1}').format(loadId, taskId), 404)

	words = sum([i.words for i in load.rawPieces])
	return jsonify({
		'stats': {
			'unitCount': words,
			'itemCount': len(load.rawPieces),
		}
	})


@bp.route(_name + '/<int:taskId>/labelsets/', methods=['POST'])
@api
@caps()
def create_task_label_set(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId))
	labelSet = m.LabelSet()
	task.labelSet = labelSet
	SS.flush()
	return jsonify({
		'labelSet': m.LabelSet.dump(labelSet),
	})


@bp.route(_name + '/<int:taskId>/labelsets/<int:labelSetId>', methods=['PUT'])
@api
@caps()
def share_task_label_set(taskId, labelSetId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId))
	labelSet = m.LabelSet.query.get(labelSetId)
	if not labelSet:
		raise InvalidUsage(_('label set {0} not found').format(labelSetId))
	task.labelSet = labelSet
	SS.flush()
	tasks = m.Task.query.filter_by(labelSetId=labelSetId).all()
	return jsonify({
		'labelSet': m.LabelSet.dump(labelSet),
		'tasks': m.Task.dump(tasks)
	})


def normalize_file_handler_options(data, key, value):
	try:
		options = json.loads(value)
	except ValueError:
		raise ValueError(_('invalid json value for options: {0}').format(value))
	return options


@bp.route(_name + '/<int:taskId>/loads/', methods=['POST'])
@api
@caps()
def create_task_load(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId))
	data = MyForm(
		Field('handlerId', is_mandatory=True, default=task.handlerId,
			validators=[
				validators.is_number,
				check_file_handler_existence,
			]),
		Field('options', is_mandatory=True, default='{}',
			normalizer=normalize_file_handler_options),
		Field('dataFile', is_mandatory=True,
			validators=[
				validators.is_file,
			]),
		Field('validation', default='false',
			normalizer=normalize_bool_literal,
			validators=[
				validators.is_bool,
			]),
	).get_data(is_json=False)
	handler = m.FileHandler.query.get(data['handlerId'])
	try:
		rawPieces = Loader.load(handler, task,
				data['dataFile'], **data['options'])
	except Exception, e:
		raise InvalidUsage(_('failed to load file: {0}').format(str(e)))
	if not rawPieces:
		raise InvalidUsage(_('file is empty'))

	if data['validation']:
		return jsonify({
			'message': 'data file validated'
		})

	me = session['current_user']
	load = m.Load(taskId=taskId, createdBy=me.userId)
	SS.add(load)
	# flush to generate loadId in order to populate attributes if needed
	SS.flush()

	unitCount = 0
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
		# use 'or 0' to prevent unwanted error message here
		# ultimate, null value of words will cause a 5xx error
		unitCount += (rawPiece.words or 0)
		load.rawPieces.append(rawPiece)
	SS.flush()
	return jsonify({
		'message': _('loaded {0} raw pieces into task {0} successfully'
			).format(len(rawPieces), taskId),
		'load': m.Load.dump(load),
		'stats': dict(itemCount=len(rawPieces), unitCount=unitCount)
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
def get_task_payment_records(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	paymentRecords = m.TaskPaymentRecord.query.filter_by(taskId=taskId
			).order_by(m.TaskPaymentRecord.payrollId).all()
	return jsonify({
		'paymentRecords': m.TaskPaymentRecord.dump(paymentRecords),
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
						raise ValueError(_('filter {0}: {1}: {2} must be \'true\' or \'false\', got \'{3}\''
							).format(filterIndex, i, field, value))
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

	SS.add(selection)
	SS.flush()
	for rawPieceId in rs:
		entry = m.SelectionCacheEntry(selectionId=selection.selectionId,
				rawPieceId=rawPieceId)
		SS.add(entry)

	summary = dict(
		identifier=selection.selectionId,
		number=len(rs),
		timestamp=selection.selected,
		action=selection.action,
		value=selection.subTaskId if selection.action == 'batch' else selection.name,
		user=m.User.dump(selection.user),
		link='???'
	)
	return jsonify({
		'message': _('created utterance selection {0} successfully'
			).format(selection.selectionId),
		'selection': m.UtteranceSelection.dump(selection),
		'summary': summary,
	})


@bp.route(_name + '/<int:taskId>/selections/<int:selectionId>', methods=['POST'])
def populate_task_utterance_selection(taskId, selectionId):
	selection = m.UtteranceSelection.query.get(selectionId)
	if not selection:
		raise InvalidUsage(_('utterance selection {0} not found').format(selectionId))
	if selection.taskId != taskId:
		raise InvalidUsage(_('utterance selection {0} does not belong to task {1}'
			).format(selectionId, taskId))
	if selection.processed is not None:
		raise InvalidUsage(_('utterance selection {0} has been processed already'
			).format(selectionId))

	me = session['current_user']
	if selection.userId != me.userId:
		raise InvalidUsage(_('utterance selection {0} does not belong to user {1}'
			).format(selectionId, me.userId))

	entries = m.SelectionCacheEntry.query.filter_by(selectionId=selectionId).all()
	if not entries:
		raise InvalidUsage(_('utterance selection {0} is corrupted: selection is empty'
			).format(selectionId))
	rawPieceIds = [entry.rawPieceId for entry in entries]
	itemCount = len(rawPieceIds)

	now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

	if selection.action == m.UtteranceSelection.ACTION_BATCH:
		subTask = m.SubTask.query.get(selection.subTaskId)
		if not subTask:
			raise InvalidUsage(_('utterance selection {0} is corrupted: sub task {1} not found'
				).format(selectionId, selection.subTaskId))
		if subTask.workType != m.WorkType.REWORK:
			raise InvalidUsage(_('utterance selection {0} is corrupted: sub task {1} is not a {2} sub task'
				).format(selectionId, selection.subTaskId, m.WorkType.REWORK))

		batches = Batcher.batch(subTask, rawPieceIds)
		for batch in batches:
			SS.add(batch)

		event = m.SubTaskContentEvent(subTaskId=subTask.subTaskId,
			selectionId=selectionId, itemCount=itemCount,
			isAdding=True, tProcessedAt=now, operator=me.userId)
		SS.add(event)

		resp = dict(message=_('created {0} batches into sub task {1}'
			).format(len(batches), subTask.subTaskId),
		)
	elif selection.action == m.UtteranceSelection.ACTION_CUSTOM:
		if not selection.name:
			raise InvalidUsage(_('utterance selection {0} is corrupted: invalid custom utterance group name: {1}'
				).format(selectionId, selection.name))
		if m.CustomUtteranceGroup.query.filter_by(taskId=selection.taskId
			).filter_by(name=selection.name).first():
			raise InvalidUsage(_('custom utterance group name \'{0}\' is already in use for task {1}'
				).format(selection.name, taskId))

		group = m.CustomUtteranceGroup(name=selection.name,
			taskId=taskId, selectionId=selectionId, utterances=itemCount)
		for rawPieceId in rawPieceIds:
			member = m.CustomUtteranceGroupMember(rawPieceId=rawPieceId)
			group._members.append(member)
		SS.add(group)
		SS.flush()

		resp = dict(message=_('created custom utterance group \'{0}\' (#{1}) with {2} items'
			).format(group.name, group.groupId, itemCount))
	else:
		raise InvalidUsage(_('unsupported action {0}').format(selection.action))

	for entry in entries:
		SS.delete(entry)

	selection.processed = now
	selection.action = None
	selection.name = None
	selection.subTaskId = None

	return jsonify(resp)


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
	entries = m.SelectionCacheEntry.query.filter_by(selectionId=selectionId).all()
	for entry in entries:
		SS.delete(entry)
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

	check = request.args.get('check', '')
	if check:
		#
		# Notes for one-crowd integration:
		#
		# first get assigned supervisor list from tiger and compare with local record
		# for newly added users, create an entry
		# for removed users, remove them from local records
		# others remain unchanged
		#
		try:
			appenIds = tiger.get_task_supervisors(task.globalProjectId)
		except Exception, e:
			current_app.logger.error('error checking supervisors {}'.format(e))
			appenIds = None
		if isinstance(appenIds, list):
			user_ids_tiger = set()
			for appenId in appenIds:
				try:
					user = m.User.query.filter(m.User.globalId==appenId).one()
				except NoResultFound:
					try:
						user = edm.make_new_user(appenId)
						SS.add(user)
						SS.flush()
					except:
						current_app.logger.error('error adding new user {}'.format(appenId))
						SS.rollback()
					continue
				user_ids_tiger.add(user.userId)
			user_ids_gnx = set([r.userId for r in SS.query(m.TaskSupervisor.userId
				).distinct().filter(m.TaskSupervisor.taskId==taskId).all()])
			added = user_ids_tiger - user_ids_gnx
			removed = user_ids_gnx - user_ids_tiger
			for userId in added:
				entry = m.TaskSupervisor(taskId=taskId, userId=userId)
				SS.add(entry)
			for entry in m.TaskSupervisor.query.filter_by(taskId=taskId
					).filter(m.TaskSupervisor.userId.in_(removed)):
				SS.delete(entry)
			SS.flush()

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


@bp.route(_name + '/<int:taskId>/tagsets/', methods=['POST'])
@api
@caps()
def create_task_tag_set(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId))
	tagSet = m.TagSet()
	task.tagSet = tagSet
	SS.flush()
	return jsonify({
		'tagSet': m.TagSet.dump(tagSet),
	})


@bp.route(_name + '/<int:taskId>/tagsets/<int:tagSetId>', methods=['POST'])
@api
@caps()
def copy_task_tag_set(taskId, tagSetId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId))
	srcTagSet = m.TagSet.query.get(tagSetId)
	if not srcTagSet:
		raise InvalidUsage(_('tag set {0} not found').format(tagSetId))
	tagSet = m.TagSet()
	for t in srcTagSet.tags:
		SS.expunge(t)
		make_transient(t)
		t.tagId = None
		tagSet.tags.append(t)
	task.tagSet = tagSet
	SS.flush()
	return jsonify({
		'tagSet': m.TagSet.dump(tagSet),
	})


@bp.route(_name + '/<int:taskId>/tagsets/<int:tagSetId>', methods=['PUT'])
@api
@caps()
def share_task_tag_set(taskId, tagSetId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId))
	tagSet = m.TagSet.query.get(tagSetId)
	if not tagSet:
		raise InvalidUsage(_('tagSet {0} not found').format(tagSetId))
	task.tagSet = tagSet
	SS.flush()
	tasks = m.Task.query.filter_by(tagSetId=tagSetId).all()
	return jsonify({
		'tagSet': m.TagSet.dump(tagSet),
		'tasks': m.Task.dump(tasks)
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


@bp.route(_name + '/<int:taskId>/uttgroups/<int:groupId>/stats', methods=['GET'])
@api
@caps()
def get_task_utterance_group_stats(taskId, groupId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	group = m.CustomUtteranceGroup.query.get(groupId)
	if not group or group.taskId != taskId:
		raise InvalidUsage(_('utterance group {0} not found').format(taskId), 404)

	words = sum([i.words for i in group.rawPieces])
	return jsonify({
		'stats': {
			'unitCount': words,
			'itemCount': len(group.rawPieces),
		}
	})


@bp.route(_name + '/<int:taskId>/warnings/', methods=['GET'])
@api
@caps()
def get_task_warnings(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)

	warnings = Warnings()
	if task.status != m.Task.STATUS_ACTIVE:
		warnings.critical(_('Status is currently set to {0}.',
			'This task cannot be worked on while having this status.'
			).format(task.status))

	if len(task.supervisors) == 0:
		warnings.critical(_('This task has no supervisors assigned.',
			'Please assign a supervisor using the user search page.'))

	if not [x for x in task.supervisors if x.receivesFeedback]:
		warnings.critical(_('This task has no supervisors assigned to receive feedback.',
			'Please assign a supervisor to receive feedback on the Task Configuration page.'))

	root = '/audio2/AppenText'
	path = os.path.join(root, 'instructions', str(taskId))
	if not os.path.exists(path):
		warnings.non_critical(_('The default instructions directory for this task doesn\'t exists.'))

	subTaskNames = [subTask.name for subTask in
			filter(lambda x: x.workType == m.WorkType.WORK, task.subTasks)
			if not m.QaConfig.query.get(subTask.subTaskId)]
	if subTaskNames:
		warnings.non_critical(_('The following {0} sub tasks do not have QA configured: {1}'
			).format(m.WorkType.WORK, ', '.join(subTaskNames)))

	# training modules/qualification test are not applicable

	if m.TaskErrorType.query.filter_by(taskId=taskId).count() == 0:
		warnings.non_critical(_('This task has no QA error types enabled.'))

	subTaskNames = [subTask.name for subTask in task.subTasks if not
			m.SubTaskRate.query.filter_by(subTaskId=subTask.subTaskId).first()]
	if subTaskNames:
		warnings.critical(_('The following sub tasks cannnot be worked on as they do not have payment rates set: {0}'
			).format(', '.join(subTaskNames)))

	return jsonify(warnings=warnings)


@bp.route(_name + '/<int:taskId>/work/', methods=['GET'])
def get_task_work_queues(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)
	subTasks = []
	if task.status != m.Task.STATUS_ACTIVE:
		# task status is not active
		pass
	elif not [x for x in task.supervisors if x.receivesFeedback]:
		# no supervisors that receives feedback
		pass
	else:	
		me = session['current_user']
		candidates = m.SubTask.query.filter(m.SubTask.subTaskId.in_(
			SS.query(m.TaskWorker.subTaskId
				).filter_by(taskId=taskId
				).filter_by(userId=me.userId
				).filter(m.TaskWorker.removed==False))).all()
		for subTask in candidates:
			if not subTask.currentRate:
				# pay rate not configured
				continue
			if not m.Batch.query.filter_by(subTaskId=subTask.subTaskId
					).filter(or_(m.Batch.userId.is_(None), m.Batch.userId==me.userId)
					).filter(or_(m.Batch.onHold.is_(None), m.Batch.onHold==False)
					).filter(or_(m.Batch.notUserId.is_(None), m.Batch.notUserId!=me.userId)
					).order_by(m.Batch.priority.desc()
					).first():
				# no batches left
				continue
			subTasks.append(subTask)
	return jsonify(queues=m.SubTask.dump(subTasks))

@bp.route(_name + '/<int:taskId>/workers/', methods=['GET'])
def get_task_workers(taskId):
	task = m.Task.query.get(taskId)
	if not task:
		raise InvalidUsage(_('task {0} not found').format(taskId), 404)

	check = request.args.get('check', '')
	if check:
		#
		# Notes for one-crowd integration:
		#
		# first get assigned user list from tiger and compare with local record
		# for newly added users, create a dummy entry if necessary
		# for removed users, remove them from all sub tasks
		# others remain unchanged
		#
		try:
			appenIds = tiger.get_task_workers(task.globalProjectId)
		except Exception, e:
			current_app.logger.error('error checking workers {}'.format(e))
			appenIds = None

		current_app.logger.debug('global returned workers {}'.format(appenIds))
		if isinstance(appenIds, list):
			user_ids_tiger = set()
			for appenId in appenIds:
				try:
					user = m.User.query.filter(m.User.globalId==appenId).one()
				except NoResultFound:
					try:
						user = edm.make_new_user(appenId)
						SS.add(user)
						SS.flush()
					except:
						current_app.logger.error('error adding new user {}'.format(appenId))
						SS.rollback()
					continue
				user_ids_tiger.add(user.userId)
			current_app.logger.debug('translated user Ids {}'.format(user_ids_tiger))
			user_ids_gnx = set([r.userId for r in SS.query(m.TaskWorker.userId
				).distinct().filter(m.TaskWorker.taskId==taskId).all()])
			added = user_ids_tiger - user_ids_gnx
			removed = user_ids_gnx - user_ids_tiger
			current_app.logger.debug('added users {}'.format(added))
			current_app.logger.debug('removed users {}'.format(removed))
			if added:
				try:
					subTask = m.SubTask.query.filter(m.SubTask.taskId==taskId
						).order_by('subTaskId')[0]
					for userId in added:
						entry = m.TaskWorker(taskId=taskId,
							subTaskId=subTask.subTaskId,
							userId=userId, removed=True)
						SS.add(entry)
				except IndexError:
					# no sub tasks defined yet
					pass
			for entry in m.TaskWorker.query.filter_by(taskId=taskId
					).filter(m.TaskWorker.userId.in_(removed)):
				entry.removed = True
			SS.flush()

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

