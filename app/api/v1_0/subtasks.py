
import os
import re
import datetime

from flask import request, session, jsonify
import pytz

import db.model as m
from db.db import SS
from app.api import api, caps, MyForm, Field, validators
from app.i18n import get_text as _
from . import api_1_0 as bp, InvalidUsage
from app.util import Batcher, Warnings

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

	# TODO: implement this
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
		'updatedFields': data.keys(),
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
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId))
	if subTask.workType != m.WorkType.WORK:
		raise InvalidUsage(_('target sub task must be of type {0}').format(m.WorkType.WORK))
	# TODO: implement this
	rawPieces = m.RawPiece.query.filter_by(taskId=subTask.taskId
		).filter(m.RawPiece.isNew==True
		).filter(m.RawPiece.rawPieceId.notin_(
			SS.query(m.PageMember.rawPieceId
				).filter_by(taskId=subTask.taskId
				).filter(m.PageMember.rawPieceId!=None
				).distinct())
		).all()
	batches = Batcher.batch(subTask, rawPieces)
	for batch in batches:
		SS.add(batch)
	return jsonify({
		'message': _('created {0} batches').format(len(batches)),
	})


def normalize_batch_ids(data, key, value):
	validIds = data['validIds']
	if not isinstance(value, list):
		raise ValueError, _('must be a list of batch Ids')
	try:
		batchIds = [int(i) for i in value]
	except:
		raise ValueError, _('error unpacking batch Id list')
	batchIds = list(set(batchIds) & validIds)
	if not batchIds:
		raise ValueError, _('no batches to update')
	return batchIds


def normalize_prority_expression(data, key, value):
	literal = str(value)
	if not re.match(r'\+?\d+$', literal):
		raise ValueError, _('invalid priority expression')
	if literal[0] == '+':
		value = lambda x: x + int(literal[1:])
	else:
		value = lambda x: int(literal)
	return value


def normalize_expiry_date_expression(data, key, value):
	literal = str(value)
	formatter = '%Y-%m-%dT%H:%M:%S.%fZ'
	# print 'leaseExpires literal', `literal`
	try:
		if literal.startswith('+'):
			delay = int(literal[1:])
			delta = datetime.timedelta(seconds=delay * 60 * 60)
			return lambda x: None if x is None else x + delta
		expires_by = datetime.datetime.strptime(literal, formatter)
		return lambda x: None if x is None else expires_by
	except:
		raise ValueError, _('invalid expiry date expression')


@bp.route(_name + '/<int:subTaskId>/batches/', methods=['PUT'])
@api
@caps()
def update_batches(subTaskId):
	batchById = dict([(b.batchId, b) for b in
		m.Batch.query.filter_by(subTaskId=subTaskId).all()])

	data = MyForm(
		Field('validIds', is_mandatory=True, default=set(),
			normalizer=lambda data, key, value: set(batchById)),
		Field('batchIds', is_mandatory=True, default=[],
			normalizer=normalize_batch_ids),
		Field('priority', normalizer=normalize_prority_expression),
		Field('onHold', validators=[
			validators.is_bool,
		]),
		Field('leaseExpires', normalizer=normalize_expiry_date_expression),
	).get_data()

	op = {
		'priority': None if 'priority' not in data else data['priority'],
		'onHold': None if 'onHold' not in data else lambda x: data['onHold'],
		'leaseExpires': None if 'leaseExpires' not in data else data['leaseExpires'],
	}

	# print data, op
	updated = []
	for batchId in data['batchIds']:
		batch = batchById[batchId]
		# print '=' * 80
		# print 'checking', batch.batchId
		updated_fields = {}
		for attr in op:
			if not op[attr]:
				# print attr, 'is not valid, skipping'
				continue
			# print attr, 'need to check value'

			old_value = getattr(batch, attr)
			new_value = op[attr](old_value)
			# print 'old_value', old_value, 'new_value', new_value
			if old_value != new_value:
				# print attr, 'detected change', old_value, new_value
				setattr(batch, attr, new_value)
				updated_fields[attr] = new_value
		if updated_fields:
			updated_fields['batchId'] = batch.batchId
			updated.append(updated_fields)

	message = (_('no batch was updated') if len(updated) == 0
			else _('1 batch was updated') if len(updated) == 1
			else _('{0} batches were updated')).format(len(updated))

	return jsonify({
		'message': message,
		'updatedBatches': updated,
	})


@bp.route(_name + '/<int:subTaskId>/batches/', methods=['DELETE'])
@api
@caps()
def dismiss_all_batches(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId), 404)

	batches = m.Batch.query.filter_by(subTaskId=subTaskId).all()
	itemCount = 0
	for b in batches:
		for p in b.pages:
			itemCount += len(p.memberEntries)
			for memberEntry in p.memberEntries:
				SS.delete(memberEntry)
			SS.delete(p)
		SS.delete(b)

	me = session['current_user']
	now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

	# add tracking information
	tracking_event = m.TrackingEvent(eventType='unbatch_all',
		userId=me.userId, tTriggeredAt=now,
		hostIp=request.environ['REMOTE_ADDR'],
		details=dict(taskId=subTask.taskId, subTaskId=subTaskId,
			count=len(batches)))
	SS.add(tracking_event)

	# add rework content event
	content_event = m.SubTaskContentEvent(subTaskId=subTaskId,
		isAdding=False, tProcessedAt=now, itemCount=itemCount,
		operator=me.userId)
	SS.add(content_event)

	SS.flush()
	return jsonify({
		'message': _('deleted {0} batches from sub task {1}').format(len(batches), subTaskId),
	})


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
	intervals = m.WorkInterval.query.filter_by(subTaskId=subTaskId
		).order_by(m.WorkInterval.workIntervalId).all()
	return jsonify({
		'intervals': m.WorkInterval.dump(intervals),
	})


@bp.route(_name + '/<int:subTaskId>/loads/', methods=['GET'])
@api
@caps()
def get_sub_task_rework_load_records(subTaskId):
	events = m.SubTaskContentEvent.query.filter_by(subTaskId=subTaskId
		).order_by(m.SubTaskContentEvent.tProcessedAt).all()
	return jsonify({
		'events': m.SubTaskContentEvent.dump(events),
	})


@bp.route(_name + '/<int:subTaskId>/metrics/', methods=['GET'])
@api
@caps()
def get_sub_task_work_metrics(subTaskId):
	# TODO: modify query condition to include interval metrics
	metrics = m.SubTaskMetric.query.filter_by(
		subTaskId=subTaskId).all()
	metrics_i = m.SubTaskMetric.query.filter(
			m.SubTaskMetric.workIntervalId.in_(
				SS.query(m.WorkInterval.workIntervalId
				).filter(m.WorkInterval.subTaskId==subTaskId)
			)
		).all()
	return jsonify({
		'metrics': m.SubTaskMetric.dump(metrics + metrics_i),
	})


@bp.route(_name + '/<int:subTaskId>/performance/', methods=['GET'])
@api
@caps()
def get_sub_task_worker_performance_records(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId))

	# TODO: filter result if user can't view all workers
	workers = m.TaskWorker.query.filter_by(subTaskId=subTaskId).all()

	r0 = m.WorkInterval.query.filter_by(subTaskId=subTaskId
			).filter(m.WorkInterval.endTime!=None
			).order_by(m.WorkInterval.endTime.desc()).all()
	lastFinishedInterval = r0[0] if r0 else None

	rs = []
	for i in workers:
		r1 = m.SubTaskMetric.query.filter_by(userId=i.userId
				).filter_by(subTaskId=subTaskId
				).all()
		overall = r1[0] if r1 else None

		r2 = m.SubTaskMetric.query.filter_by(userId=i.userId
				).filter_by(workIntervalId=lastFinishedInterval.workIntervalId
				).all()
		recent = r2[0] if r2 else None

		r3 = m.DailySubtotal.query.filter_by(userId=i.userId
				).filter_by(subTaskId=subTaskId
				).order_by(m.DailySubtotal.totalDate.desc()
				).all()
		lastWorked = r3[0].totalDate if r3 else None

		rs.append(dict(
			userId=i.userId,
			userName=i.userName,
			removed=i.removed,
			lastWorked=str(lastWorked),
			overall=m.SubTaskMetric.dump(overall) if overall else None,
			recent=m.SubTaskMetric.dump(recent) if recent else None,
		))

	return jsonify({
		'workers': rs,
	})


@bp.route(_name + '/<int:subTaskId>/qasettings/', methods=['GET'])
@api
@caps()
def get_sub_task_qa_settings(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId))
	qaConfig = subTask.qaConfig
	return jsonify({
		'qaConfig': m.QaConfig.dump(qaConfig),
	})


def check_sub_task_existence(data, key, subTaskId):
	if not m.SubTask.query.get(subTaskId):
		raise ValueError, _('sub task {0} not found').format(subTaskId)


def check_sub_task_type_in(data, key, subTaskId, *workTypes):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask or subTask.workType not in workTypes:
		raise ValueError, _('sub task {0} must be of type {1}'
			).format(subTaskId, ','.join(workTypes))


def check_sub_task_attribute(data, key, subTaskId, **kwargs):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise ValueError, _('sub task {0} not found')
	for key, value in kwargs.iteritems():
		if getattr(subTask, key) != value:
			raise ValueError, _('unexpected value of {0}, expecting {1}, got {2}'
				).format(key, value, getattr(subTask, key))


@bp.route(_name + '/<int:subTaskId>/qasettings/', methods=['PUT'])
@api
@caps()
def update_sub_task_qa_settings(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId))

	if subTask.workType != m.WorkType.WORK:
		raise InvalidUsage(_('only {0} sub tasks can have default QA settings'
			).format(m.WorkType.WORK))

	data = MyForm(
		Field('workSubTaskId', is_mandatory=True, default=lambda: subTaskId,
			normalizer=lambda data, key, value: subTaskId,
		),
		Field('samplingError', is_mandatory=True,
			normalizer=lambda data, key, value: float(value),
			validators=[
				(validators.is_number, (), dict(gt=0, le=0.1)),
		]),
		Field('defaultExpectedAccuracy', is_mandatory=True,
			normalizer=lambda data, key, value: float(value),
			validators=[
				(validators.is_number, (), dict(gt=0, lt=1)),
		]),
		Field('confidenceInterval', is_mandatory=True,
			normalizer=lambda data, key, value: float(value),
			validators=[
				(validators.is_number, (), dict(ge=0.9, lt=1)),
		]),
		Field('qaSubTaskId', is_mandatory=True, validators=[
			check_sub_task_existence,
			(check_sub_task_attribute, (), dict(taskId=subTask.taskId)),
			(check_sub_task_type_in, (m.WorkType.QA,)),
		]),
		# TODO: add in conditional check based on value of populateRework
		Field('populateRework', validators=[validators.is_bool]),
		Field('reworkSubTaskId', validators=[
			check_sub_task_existence,
			(check_sub_task_attribute, (), dict(taskId=subTask.taskId)),
			(check_sub_task_type_in, (m.WorkType.REWORK,)),
		]),
		Field('accuracyThreshold', validators=[
			(validators.is_number, (), dict(gt=0, lt=1)),
		]),
	).get_data(with_view_args=False)

	me = session['current_user']
	if subTask.qaConfig:
		qaConfig = subTask.qaConfig
		for key in data.keys():
			value = data[key]
			if getattr(qaConfig, key) != value:
				setattr(qaConfig, key, value)
			else:
				del data[key]
		message = _('updated default QA settings for sub task {0}').format(subTaskId)
	else:
		qaConfig = m.QaConfig(updatedBy=me.userId, **data)
		SS.add(qaConfig)
		message = _('added default QA settings for sub task {0}').format(subTaskId)
	SS.flush()
	return jsonify({
		'message': message,
		'qaConfig': m.QaConfig.dump(qaConfig),
		'updatedFields': data.keys(),
	})


@bp.route(_name + '/<int:subTaskId>/qasettings/', methods=['DELETE'])
@api
@caps()
def delete_sub_task_qa_settings(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId))
	if subTask.qaConfig:
		SS.delete(subTask.qaConfig)
		message = _('deleted default QA settings of sub task {0}').format(subTaskId)
	else:
		message = _('sub task {0} does not have default QA settings').format(subTaskId)
	return jsonify({
		'message': message,
	})


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
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId))

	data = MyForm(
		Field('rateId', is_mandatory=True, validators=[]),
		Field('multiplier', is_mandatory=True,
			normalizer=lambda data, key, value: float(value),
			validators=[
				(validators.is_number, (), dict(min_value=1)),
			]),
	).get_data()

	me = session['current_user']

	subTaskRate = m.SubTaskRate(taskId=subTask.taskId,
		updatedBy=me.userId, **data)
	SS.add(subTaskRate)
	SS.flush()
	return jsonify({
		'message': _('created sub task rate {0} successfully'
			).format(subTaskRate.subTaskRateId),
		'subTaskRate': m.SubTaskRate.dump(subTaskRate),
	})


@bp.route(_name + '/<int:subTaskId>/stats/', methods=['GET'])
@api
@caps()
def get_sub_task_statistics(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId))

	batches = m.Batch.query.filter_by(subTaskId=subTaskId).all()
	return jsonify({
		'batchCount': len(batches),
		'offlineCount': len([b for b in batches if b.checkedOut]),
		'itemCount': sum([len(p.members) for b in batches
			for p in b.pages]),
		'unitCount': sum([i.rawPiece.words for b in batches
			for p in b.pages for i in p.members]),
	})


@bp.route(_name + '/<int:subTaskId>/warnings/', methods=['GET'])
@api
@caps()
def get_sub_task_warnings(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId))

	warnings = Warnings()
	subTaskRate = m.SubTaskRate.query.filter_by(subTaskId=subTaskId).first()
	if not subTaskRate:
		warnings.critical(_('There is no payment rate set for this sub task.',
			'No work can be done on this sub task while there is no payment rate set.'))

	# TODO: get root path from configuration
	if subTask.instructionPage is not None:
		root = '/audio2/AppenText'
		path = os.path.join(root, 'instructions', str(subTask.taskId),
			os.path.basename(subTask.instructionPage))
		if not os.path.exists(path):
			warnings.non_critical(_('The selected instructions page, {0}, does not exist.'
				).format(os.path.basename(subTask.instructionPage)))

	if subTask.workType == m.WorkType.WORK:
		qaConfig = m.QaConfig.query.get(subTask.subTaskId)
		if not qaConfig:
			warnings.non_critical(_('There is no default QA configuration for this sub task.'))
	elif subTask.workType == m.WorkType.QA:
		if m.TaskErrorType.query.filter_by(taskId=subTask.taskId
				).filter_by(disabled=False).count() == 0:
			warnings.non_critical(
				_('There are no QA error types enabled for this task.',
					'Please assign error types on the Task Configuration page.'))
	return jsonify(warnings=warnings)


@bp.route(_name + '/<int:subTaskId>/workers/', methods=['GET'])
@api
@caps()
def get_sub_task_workers(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId), 404)
	workers = m.TaskWorker.query.filter_by(subTaskId=subTaskId).all()
	return jsonify({
		'workers': m.TaskWorker.dump(workers),
	})

