
import re
from collections import OrderedDict

from flask import render_template, url_for, make_response
from sqlalchemy import func
from lxml import etree

import db.model as m
from db.db import SS
from app.util import TestManager, Filterable
from app.i18n import get_text as _
from app.api import MyForm, Field, validators

from .helpers import UserSearchAction, UserSearchFilter, calculate_task_payment_record

from . import webservices as bp, ws


def check_action_identifier(data, key, identifier):
	if not UserSearchAction.get_at_action(identifier):
		raise ValueError(_('action \'{0}\' not found in system \'{1}\''
				).format(identifier, UserSearchAction.APPEN_TEXT))


def normalize_user_ids(data, key, value):
	userIds = set()
	for i in data['users'].split(','):
		try:
			userId = int(i)
		except ValueError:
			raise ValueError(_('invalid user id: {0}').format(i))
		else:
			userIds.add(userId)
	confirmed = [r[0] for r in SS.query(m.User.userId).filter(
		m.User.userId.in_(userIds))]
	missing = userIds - set(confirmed)
	if missing:
		raise ValueError(_('user not found: {0}'
			).format(','.join(missing)))
	return userIds


def normalize_filters_input(data, key, value):
	p1 = re.compile('(\d+)_(.*)$')
	p2 = re.compile('piece(\d+)')
	filters = {}
	for k in data.keys():
		if k in ('salt', 'key', 'limit', 'userID'):
			continue
		match = p1.match(k)
		if not match:
			# TODO: raise Error or simply ignore
			continue
		filterIndex = int(match.group(1))
		param = match.group(2)
		filterDict = filters.setdefault(filterIndex, {})
		if param in filterDict:
			# TODO: raise Error or simply ignore
			# allow overwriting
			pass
		match = p2.match(param)
		if match:
			pieceIndex = int(match.group(1))
			filterDict.setdefault('pieces', {})[pieceIndex] = data[k]
		else:
			if param == 'pieces':
				# TODO: raise Error or simply ignore
				# must not overwrite pieces
				continue
			filterDict[param] = data[k]
	filterIndice = sorted(filters)
	# TODO: raise Error on missing index or simply ignore
	# assert filterIndice == range(0, len(filterIndice))
	result = []
	for filterIndex in filterIndice:
		filterDict = filters[filterIndex]
		for k in ('system', 'identifier', 'inclusive'):
			if k not in filterDict:
				raise ValueError(_('mandatory parameter \'{0}\' missing'
					).format(k))
		system = filterDict['system']
		identifier = filterDict['identifier']
		inclusive = str(filterDict['inclusive']).lower() == 'true'
		targetFilter = UserSearchFilter.get_filter(system, identifier)
		if not targetFilter:
			raise ValueError(_('filter \'{0}\' not found in system \'{1}\''
				).format(identifier, system))
		if 'pieces' in filterDict:
			pieceIndice = sorted(filterDict['pieces'])
			# TODO: check piece index or simply ignore
			# assert pieceIndice == range(0, len(pieceIndice))
			pieceValues = [filterDict['pieces'][i] for i in pieceIndice]
		else:
			pieceValues = []
		c1 = len(targetFilter.pieces)
		c2 = len(pieceValues)
		if c1 != c2:
			raise ValueError(_('invalid number of pieces'
				' for filter \'{0}\', expecting {1}, got {2}'
				).format(identifier, c1, c2))
		result.append((targetFilter, inclusive, pieceValues))
	return result


def format_available_work_entry(subTask):
	task = subTask.task
	rate = subTask.currentRate
	d = OrderedDict()
	d['url'] = url_for('views.get_batch_from_sub_task',
		subTaskId=subTask.subTaskId, _external=True)
	d['task'] = task.displayName
	d['language'] = 'N/A'
	d['worktype'] = subTask.workType
	d['worktypedetail'] = subTask.name
	d['contact'] = ','.join([str(s.userId) for s in task.supervisors])
	d['applypaymentratio'] = False
	d['rate'] = rate.standardValue * rate.multiplier
	d['targetaccuracy'] = rate.targetAccuracy
	d['rateurl'] = url_for('views.sub_task_rate',
		subTaskId=subTask.subTaskId, _external=True)
	return d


def format_recent_work_entry():
	pass


def check_payroll_existence(data, key, payrollId):
	if not m.Payroll.query.get(payrollId):
		raise ValueError(_('payroll {0} not found').format(payrollId))


def normalize_calculated_payments(data, key, value):
	try:
		root = etree.fromstring(value)
	except:
		raise ValueError(_('failed to decode input as xml {0}'
			).format(value))
	result = []
	# TODO: be more lienient, silent ignore errors
	for payment in root.xpath('payment'):
		d = {}
		d['amount'] = int(payment.xpath('amount')[0].text)
		d['calculatedPaymentId'] = int(payment.xpath('identifier')[0].text)
		result.append(d)
	return result


def normalize_non_calculated_payments(data, key, value):
	try:
		root = etree.fromstring(value)
	except:
		raise ValueError(_('failed to decode input as xml {0}'
			).format(value))
	result = []
	for payment in root.xpath('payment'):
		d = {}
		d['amount'] = int(payment.xpath('amount')[0].text)
		d['identifier'] = payment.xpath('identifier')[0].text
		d['taskId'] = int(payment.xpath('taskid')[0].text)
		d['userId'] = int(payment.xpath('userid')[0].text)
		d['paymentType'] = payment.xpath('paymenttype')[0].text
		result.append(d)
	return result


@bp.route('/apply_user_search_action', methods=['GET', 'POST'])
@ws('apply_user_search_action.xml')
def webservices_apply_user_search_action():
	data = MyForm(
		Field('identifier', is_mandatory=True, validators=[
			check_action_identifier,
		]),
		Field('option', is_mandatory=True),
		Field('users', is_mandatory=True, validators=[
			validators.non_blank,
		]),
		Field('userIds', is_mandatory=True, default=[],
			normalizer=normalize_user_ids),
	).get_data(is_json=False, copy=True)

	action = UserSearchAction.get_at_action(data['identifier'])
	userIds = data['userIds']
	option = data['option']

	reply = action.func(userIds, option)
	return dict(reply=reply)


@bp.route('/apply_user_search_filters', methods=['GET', 'POST'])
@ws('get_user_details_CSS.xml')
def webservices_apply_user_search_filters():
	data = MyForm(
		Field('filters', is_mandatory=True, default=[],
			normalizer=normalize_filters_input),
	).get_data(is_json=False, copy=True)

	filters = data['filters']
	inclusiveFilters = [x for x in filters if x[1]]
	exclusiveFilters = [x for x in filters if not x[1]]

	result = set() if inclusiveFilters else set(SS.query(m.User.userId))

	for aFilter, inclusive, pieceValues in inclusiveFilters:
		rs = aFilter.func(*pieceValues)
		result |= set(rs)
	for aFilter, inclusive, pieceValues in exclusiveFilters:
		rs = aFilter.func(*pieceValues)
		result -= set(rs)

	entries = [i[0] for i in result]
	return dict(entries=entries)


@bp.route('/available_qualifications', methods=['GET', 'POST'])
@ws('available_work.xml')
def webservices_available_qualifications():
	# TODO: get userId from incoming request
	userId = 699
	languageIds = [1, 2, 3, 4]

	user = m.User.query.get(userId)
	if not user or not user.isActive:
		raise RuntimeError

	candidates = m.Test.query.filter_by(isEnabled=True
		).order_by(m.Test.testId).all()
	result = Filterable()
	for test in candidates:
		record = TestManager.report_eligibility(test, user, languageIds)
		if record is None:
			continue
		result.append(record)
	return dict(entries=result)


@bp.route('/available_work', methods=['GET', 'POST'])
@ws('available_work.xml')
def webservices_available_work():
	# TODO: get userId from incoming request
	userId = 699
	user = m.User.query.get(userId)
	if not user or not user.isActive:
		raise RuntimeError

	# is_active = lambda subTask: subTask.task.status == m.Task.STATUS_ACTIVE
	# has_supervisor = lambda subTask: len([x for x in subTask.task.supervisors
	# 	if x.receivesFeedback]) > 0
	# pay_rate_set = lambda subTask: bool(
	# 	m.SubTaskRate.query.filter_by(subTaskId=subTask.subTaskId
	# 			).filter(m.SubTaskRate.validFrom<=func.now()
	# 			).order_by(m.SubTaskRate.validFrom.desc()
	# 			).first())
	# has_batch = lambda subTask: bool(
	# 	m.Batch.query.filter_by(subTaskId=subTask.subTaskId
	# 			).filter(m.Batch.userId==None
	# 			).filter(m.Batch.onHold==False
	# 			).order_by(m.Batch.priority.desc()
	# 			).first())
	# candidates = Filterable(m.SubTask.query.filter(m.SubTask.subTaskId.in_(
	# 	SS.query(m.TaskWorker.subTaskId).filter_by(userId=userId
	# 	).filter(m.TaskWorker.removed==False))).all())
	# subTasks = candidates | is_active | has_supervisor | pay_rate_set | has_batch

	candidates = m.SubTask.query.filter(m.SubTask.subTaskId.in_(
		SS.query(m.TaskWorker.subTaskId).filter_by(userId=userId
			).filter(m.TaskWorker.removed==False))).all()
	subTasks = []
	for subTask in candidates:
		if subTask.task.status != m.Task.STATUS_ACTIVE:
			continue
		if not [x for x in subTask.task.supervisors if x.receivesFeedback]:
			continue
		if not subTask.currentRate:
			continue
		if not m.Batch.query.filter_by(subTaskId=subTask.subTaskId
				).filter(m.Batch.userId==None
				).filter(m.Batch.onHold==False
				).order_by(m.Batch.priority.desc()
				).first():
			continue
		subTasks.append(subTask)
	result = map(format_available_work_entry, subTasks)
	return dict(entries=result)


@bp.route('/get_user_search_actions', methods=['GET', 'POST'])
@ws('get_user_search_actions.xml')
def webservices_get_user_search_actions():
	actions = UserSearchAction.get_at_actions()
	return dict(actions=actions)


@bp.route('/get_user_search_filters', methods=['GET', 'POST'])
@ws('get_user_search_filters.xml')
def webservices_get_user_search_filters():
	filters = UserSearchFilter.get_at_filters()
	return dict(filters=filters)


@bp.route('/get_user_details_CSS', methods=['GET', 'POST'])
@ws('get_user_details_CSS.xml')
def webservices_get_user_details_css():
	url = url_for('static', filename='css/userDetails.css', _external=True)
	return dict(entries=[url])


@bp.route('/get_user_details_JS', methods=['GET', 'POST'])
@ws('get_user_details_CSS.xml')
def webservices_get_user_details_js():
	url = url_for('static', filename='css/userDetails.js', _external=True)
	return dict(entries=[url])


@bp.route('/recent_work', methods=['GET', 'POST'])
@ws('recent_work.xml')
def webservices_recent_work():
	# TODO: get userId from incoming request
	userId = 699
	user = m.User.query.get(userId)
	if not user or not user.isActive:
		raise RuntimeError

	eventsBySubTaskId = {}
	for ev in m.PayableEvent.query.filter_by(userId=userId
			).filter(m.PayableEvent.calculatedPaymentId==None
			).order_by(m.PayableEvent.created):
		eventsBySubTaskId.setdefault(ev.subTaskId, []).append(ev)

	workIntervalsBySubTaskId = {}
	for subTaskId in eventsBySubTaskId:
		workIntervalsBySubTaskId[subTaskId] = m.WorkInterval.query.filter_by(
			subTaskId=subTaskId).order_by(m.WorkInterval.endTime).all()

	eventsByWorkInterval = {}
	for subTaskId, intervals in workIntervalsBySubTaskId.iteritems():
		#
		# NOTE: do not process payable events of sub tasks that don't
		# have any work intervals
		#
		if not intervals:
			# TODO: notify supervisor to add in intervals
			continue
		events = eventsBySubTaskId[subTaskId]
		receivingInterval = intervals.pop(0)
		#
		# events created before the first interval's start time will be
		# included in the first, events created after the last interval's
		# end time will be included in the last. other events that don't
		# have a corresponding interval will go into the next available
		# interval
		#
		while events:
			event = events.pop(0)
			if event.created > receivingInterval.endTime:
				if intervals:
					# move to next if available
					receivingInterval = intervals.pop(0)
			eventsByWorkInterval.setdefault(
				receivingInterval, []).append(event)

	taskById = {}
	subTaskById = {}
	result = []
	for interval in sorted(eventsByWorkInterval, key=lambda i:
			(i.taskId, i.subTaskId, i.endTime)):
		events = eventsByWorkInterval[interval]
		subTask = subTaskById.setdefault(interval.subTaskId,
				m.SubTask.query.get(interval.subTaskId))
		task = taskById.setdefault(subTask.taskId, subTask.task)
		d = OrderedDict()
		d['weekending'] = (interval.endTime.strftime('%Y-%m-%d')
				if interval.endTime else None)
		d['task'] = task.displayName
		d['details'] = '{0} ({1})'.format(subTask.name, subTask.workType)
		d['unitspending'] = 0
		d['unitscompleted'] = 0
		d['accuracy'] = None
		d['calcacc'] = None
		d['contact'] = ','.join([str(s.userId) for s in task.supervisors])

		slot = 'unitscompleted' if (interval.status ==
				m.WorkInterval.STATUS_FINISHED) else 'unitspending'
		if True: # count by item
			d[slot] += len(events)
		else:
			# TODO: add code to flag events which rawPieceId is None
			rawPieceIds = [event.rawPieceId for event in events
				if event.rawPieceId is not None]
			d[slot] += sum([r.words for r in map(
				lambda rawPieceId: m.RawPiece.query.get(rawPieceId),
				rawPieceIds)])
		result.append(d)
	return dict(entries=result)


@bp.route('/update_payments', methods=['GET', 'POST'])
@ws('get_user_details_CSS.xml')
def webservices_update_payments():
	data = MyForm(
		Field('payroll_id', is_mandatory=True,
			normalizer=lambda data, key, value: int(value),
			validators=[
				check_payroll_existence,
		]),
		Field('calculated_payments', is_mandatory=True,
			normalizer=normalize_calculated_payments,
		),
		Field('non_calculated_payments', is_mandatory=True,
			normalizer=normalize_non_calculated_payments,
		),
	).get_data(is_json=False, copy=True)

	payrollId = data['payroll_id']

	updated = set()

	for d in data['calculated_payments']:
		cp = m.CalculatedPayment.query.get(d['calculatedPaymentId'])
		if not cp or cp.payrollId != payrollId:
			continue
		if cp.amount != d['amount']:
			cp.amount = d['amount']
			updated.add(cp.taskId)

	existingByReceiptId = dict([(i.identifier, i)
		for i in m.OtherPayment.query.filter_by(payrollId=payrollId)])
	confirmedByReceiptId = dict([(i['identifier'], i)
		for i in data['non_calculated_payments']])
	existing = set(existingByReceiptId)
	confirmed = set(confirmedByReceiptId)
	to_delete = existing - confirmed
	to_add = confirmed - existing
	to_update = existing & confirmed
	for i in to_update:
		ncp = existingByReceiptId[i]
		d = confirmedByReceiptId[i]
		if ncp.amount != d['amount']:
			ncp.amount = d['amount']
			updated.add(ncp.taskId)
	for i in to_delete:
		ncp = existingByReceiptId[i]
		updated.add(ncp.taskId)
		SS.delete(ncp)

	taskIds = set([i[0] for i in SS.query(m.Task.taskId)])
	paymentTypeByName = dict([(i.name, i.paymentTypeId)
		for i in m.PaymentType.query])
	for i in to_add:
		d = confirmedByReceiptId[i]
		if not m.User.query.get(d['userId']):
			raise RuntimeError(_('user {0} not found').format(d['userId']))
		if d['taskId'] not in taskIds:
			# TODO: raise Error instead of ignoring it
			# raise RuntimeError(_('task {0} not found').format(d['taskId']))
			continue
		paymentTypeId = paymentTypeByName.get(d['paymentType'])
		if paymentTypeId is None:
			raise RuntimeError(_('payment type \'{0}\' not found'
				).format(d['paymentType']))
		ncp = m.OtherPayment(payrollId=payrollId,
			identifier=d['identifier'], paymentTypeId=paymentTypeId,
			taskId=d['taskId'], userId=d['userId'], amount=d['amount'])
		updated.add(d['taskId'])
		SS.add(ncp)

	# update impacted entries in t_costperutterance
	if updated:
		for taskId in updated:
			existingRecord = m.TaskPaymentRecord.query.get((taskId, payrollId))
			if existingRecord:
				SS.delete(existingRecord)
			newRecord = calculate_task_payment_record(taskId, payrollId)
			SS.add(newRecord)

	return dict(entries=['success'])


@bp.route('/user_details', methods=['GET', 'POST'])
@ws('user_details.xml')
def webservices_user_details():
	# TODO: get userId from incoming request
	userId = 699
	test_records = SS.query(m.Test, m.Sheet
			).filter(m.Sheet.userId==userId
			).filter(m.Sheet.testId==m.Test.testId
			).filter(m.Sheet.score!=None
			).order_by(m.Sheet.testId, m.Sheet.nTimes.desc()
			).distinct(m.Sheet.testId).all()

	assignments = SS.query(m.Task, m.TaskWorker.removed
			).filter(m.Task.taskId==m.TaskWorker.taskId
			).filter(m.TaskWorker.userId==userId
			).order_by(m.TaskWorker.taskId,m.TaskWorker.removed.desc()
			).distinct(m.TaskWorker.taskId).all()

	return dict(test_records=test_records, assignments=assignments)

