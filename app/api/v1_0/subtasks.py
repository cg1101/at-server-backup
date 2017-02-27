
import os
import re
import datetime

from flask import request, session, jsonify
import pytz
import iso8601

import db.model as m
from db.db import SS
from db.model import Performance, SubTask, Transition
from app.api import api, caps, MyForm, Field, validators, get_model
from app.i18n import get_text as _
from . import api_1_0 as bp, InvalidUsage
from app.util import Batcher, Warnings
from app.util.tx_loader import TxLoader

_name = __file__.split('/')[-1].split('.')[0]


@bp.route(_name + '/<int:subTaskId>', methods=['GET'])
@api
def get_sub_task(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId), 404)
	return jsonify({
		'subTask': m.SubTask.dump(subTask, context={}),
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


from .tasks import check_sub_task_name_uniqueness,\
	check_work_type_existence,\
	check_batching_mode_existence,\
	check_lease_life_minimal_length,\
	normalize_interval_as_seconds

@bp.route(_name + '/<int:subTaskId>', methods=['PUT'])
@api
@caps()
def update_sub_task(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId), 404)

	taskId = subTask.taskId

	# TODO: implement this
	data = MyForm(
		Field('name', is_mandatory=True, validators=[
			validators.non_blank,
			(check_sub_task_name_uniqueness, (taskId, subTask.subTaskId)),
		]),
		Field('taskId', is_mandatory=True, default=taskId,
				normalizer=lambda data, key, value: taskId),
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
	# print 'leaseExpires literal', `literal`
	try:
		if literal.startswith('+'):
			delay = int(literal[1:])
			delta = datetime.timedelta(seconds=delay * 60 * 60)
			return lambda x: None if x is None else x + delta
		expires_by = iso8601.parse_date(literal)
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
		'updatedBatches': m.Batch.dump(updated, use='brief'),
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


@bp.route(_name + '/<int:subTaskId>/confirm', methods=['PUT'])
@api
@caps()
def confirm_having_read_guidelines(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId), 404)

	me = session['current_user']

	try:
		entry = m.TaskWorker.query.filter(m.TaskWorker.subTaskId==subTaskId
			).filter(m.TaskWorker.userId==me.userId).one()
	except:
		raise InvalidUsage(_('user is not assigned to sub task {0}').format(subTaskId))
	if entry.removed:
		raise InvalidUsage(_('user is removed from sub task {0}').format(subTaskId))
	entry.hasReadInstructions = True
	return jsonify(message='user {0} confirmed having read instructions of sub task {1}'.format(
		me.userId, subTaskId))


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
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId), 404)

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
				(validators.is_number, (), dict(min_value=0)),
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
		'stats': {
			'batchCount': len(batches),
			'offlineBatchCount': len([b for b in batches if b.checkedOut]),
			'itemCount': sum([b.itemCount for b in batches]),
			'unitCount': sum([b.unitCount for b in batches]),
			'meanAmount': subTask.meanAmount,
			'maxAmount': subTask.maxAmount,
			'accuray': subTask.accuracy,
			'medianWorkRate': subTask.medianWorkRate,
			'maxWorkRate': subTask.maxWorkRate,
		}
	})


@bp.route(_name + '/<int:subTaskId>/shadowed-label-ids', methods=['GET'])
@api
@caps()
def get_sub_task_disabled_label_ids(subTaskId):
	rs = m.ShadowedLabel.query.filter_by(subTaskId=subTaskId).all()
	return jsonify(labelIds=[i.labelId for i in rs])


@bp.route(_name + '/<int:subTaskId>/shadowed-tag-ids', methods=['GET'])
@api
@caps()
def get_sub_task_disabled_tag_ids(subTaskId):
	rs = m.ShadowedTag.query.filter_by(subTaskId=subTaskId).all()
	return jsonify(tagIds=[i.tagId for i in rs])


@bp.route(_name + '/<int:subTaskId>/label/<int:labelId>', methods=['PUT'])
@api
@caps()
def enable_label_for_sub_task(subTaskId, labelId):
	rec = m.ShadowedLabel.query.get((subTaskId, labelId))
	if rec:
		SS.delete(rec)
	return jsonify(message=_('label {0} has been enabled for sub task {1}'
		).format(labelId, subTaskId))


@bp.route(_name + '/<int:subTaskId>/tag/<int:tagId>', methods=['PUT'])
@api
@caps()
def enable_tag_for_sub_task(subTaskId, tagId):
	rec = m.ShadowedTag.query.get((subTaskId, tagId))
	if rec:
		SS.delete(rec)
	return jsonify(message=_('tag {0} has been enabled for sub task {1}'
		).format(tagId, subTaskId))


@bp.route(_name + '/<int:subTaskId>/label/<int:labelId>', methods=['DELETE'])
@api
@caps()
def disable_label_for_sub_task(subTaskId, labelId):
	rec = m.ShadowedLabel.query.get((subTaskId, labelId))
	if not rec:
		rec = m.ShadowedLabel(subTaskId=subTaskId, labelId=labelId)
		SS.add(rec)
	return jsonify(message=_('label {0} has been disabled for sub task {1}'
		).format(labelId, subTaskId))


@bp.route(_name + '/<int:subTaskId>/tag/<int:tagId>', methods=['DELETE'])
@api
@caps()
def disable_tag_for_sub_task(subTaskId, tagId):
	rec = m.ShadowedTag.query.get((subTaskId, tagId))
	if not rec:
		rec = m.ShadowedTag(subTaskId=subTaskId, tagId=tagId)
		SS.add(rec)
	return jsonify(message=_('tag {0} has been disabled for sub task {1}'
		).format(tagId, subTaskId))


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

from .pools import normalize_bool_literal

@bp.route(_name + '/<int:subTaskId>/populate', methods=['POST'])
@api
@caps()
def populate_rework_sub_task_from_extract(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId), 404)
	if not subTask.workType == m.WorkType.REWORK:
		raise InvalidUsage(_('work type {0} not supported').format(m.WorkType.REWORK))
	data = MyForm(
		Field('srcSubTaskId',),
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
	if data['validation']:
		return jsonify(message=_('data file validated'))

	srcSubTask = m.SubTask.query.get(data['srcSubTaskId'])
	dstSubTask = subTask
	fakeUser = m.User.query.get(os.environ['CURRENT_USER_ID'])

	tx_loader = TxLoader(subTask.taskId)
	result = tx_loader.load_tx_file(data['dataFile'], srcSubTask, fakeUser, dstSubTask)
	itemCount = result['itemCount']

	me = session['current_user']
	now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

	# add rework content event
	content_event = m.SubTaskContentEvent(subTaskId=subTaskId,
		isAdding=True, tProcessedAt=now, itemCount=itemCount,
		operator=me.userId)
	SS.add(content_event)
	SS.flush()
	return jsonify(
		message=_('okay'),
		event=m.SubTaskContentEvent.dump(content_event),
	)


@bp.route(_name + '/<int:subTaskId>/workers/<int:userId>', methods=['PUT'])
@api
@caps()
def update_sub_task_worker_settings(subTaskId, userId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId), 404)
	user = m.User.query.get(userId)
	if not user:
		raise InvalidUsage(_('user {0} not found').format(userId), 404)

	data = MyForm(
		Field('hasReadInstructions', validators=[
			validators.is_bool,
		]),
		Field('isNew', validators=[
			validators.is_bool,
		]),
		Field('paymentFactor', normalizer=lambda data, key, value: float(value),
			validators=[
				(validators.is_number, (), dict(min_value=0)),
			]),
		Field('removed', validators=[
			validators.is_bool,
		]),
	).get_data()

	worker = m.TaskWorker.query.get((userId, subTask.taskId, subTaskId))
	if not worker:
		worker = m.TaskWorker(taskId=subTask.taskId, **data)
		SS.add(worker)
	else:
		for key in data:
			setattr(worker, key, data[key])
	SS.flush()

	return jsonify({
		'worker': m.TaskWorker.dump(worker),
	})


# TODO check audio checking task
@bp.route("subtasks/<int:sub_task_id>/transitions", methods=["GET"])
@api
@caps()
@get_model(SubTask)
def get_sub_task_transitions(sub_task):
	return jsonify(transitions=Transition.dump(sub_task.transitions))


# TODO check audio checking task
@bp.route("subtasks/<int:sub_task_id>/performances", methods=["GET"])
@api
@get_model(SubTask)
def get_sub_task_performances(sub_task):
	performances = []

	for batch in sub_task.batches:
		for page in batch.pages:
			for page_member in page.members:
				performance = Performance.query.get(page_member.raw_piece_id)
				performances.append(performance)

	return jsonify(performances=Performance.dump(performances))


# TODO check audio checking task
@bp.route("subtasks/<int:sub_task_id>/audiostats", methods=["GET"])
@api
@get_model(SubTask)
def get_sub_task_audio_stats(sub_task):
	num_performances = len(sub_task.batches)
	num_recordings = 0
	total_duration = datetime.timedelta(0)

	for batch in sub_task.batches:
		for page in batch.pages:
			for member in page.members:
				performance = member.rawPiece
				num_recordings += len(performance.recordings)
				
				for recording in performance.recordings:
					total_duration += recording.duration
					
	return jsonify(stats=dict(
		numPerformances=num_performances,
		numRecordings=num_recordings,
		duration=total_duration.total_seconds(),
	))
