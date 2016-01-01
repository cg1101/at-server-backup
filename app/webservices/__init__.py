
from collections import OrderedDict

from flask import Blueprint, render_template, url_for
from sqlalchemy import func

import db.model as m
from db.db import SS
from app.util import TestManager, Filterable
from app.i18n import get_text as _

webservices = bp = Blueprint('webservices', __name__, template_folder='./')


@bp.route('/apply_user_search_action', methods=['GET', 'POST'])
def apply_user_search_action():
	return 'apply_user_search_action'


@bp.route('/apply_user_search_filters', methods=['GET', 'POST'])
def apply_user_search_filters():
	return 'apply_user_search_filters'


@bp.route('/available_qualifications', methods=['GET', 'POST'])
def get_available_qualification_tests():
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
	return render_template('available_work.xml', entries=result)


def format_available_work_entry(subTask):
	task = subTask.task
	rate = subTask.currentRate
	d = OrderedDict()
	d['url'] = url_for('index', _external=True)
	d['task'] = task.displayName
	d['language'] = 'N/A'
	d['worktype'] = subTask.workType
	d['worktypedetail'] = subTask.name
	d['contact'] = ','.join([str(s.userId) for s in task.supervisors])
	d['applypaymentratio'] = False
	d['rate'] = rate.standardValue * rate.multiplier
	d['targetaccuracy'] = rate.targetAccuracy
	d['rateurl'] = url_for('index', _external=True)
	return d


@bp.route('/available_work', methods=['GET', 'POST'])
def get_available_work_entries():
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
	return render_template('available_work.xml', entries=result)


class UserSearchAction(object):
	APPEN_TEXT = 'AppenText'
	_registry = OrderedDict()
	@classmethod
	def add_action(cls, system, identifier, name, button, data=[]):
		sys_dict = cls._registry.setdefault(system, OrderedDict())
		if identifier in sys_dict:
			raise ValueError('action \'{0}\' of \'{1}\' already exists'\
				.format(identifier, system))
		action = super(UserSearchAction, cls).__new__(cls)
		setattr(action, 'system', system)
		setattr(action, 'identifier', identifier)
		setattr(action, 'name', name)
		setattr(action, 'button', button)
		setattr(action, 'data', list(data))
		return sys_dict.setdefault(identifier, action)
	@classmethod
	def get_action(cls, system, identifier):
		return cls._registry.setdefault(system, OrderedDict()).get(identifier)
	@classmethod
	def get_system_actions(cls, system):
		return cls._registry.setdefault(system, OrderedDict()).values()
	#
	# Python 3.4+ feature
	# add_at_action = partialmethod(add_action, system=APPEN_TEXT)
	# get_at_action = partialmethod(get_action, system=APPEN_TEXT)
	# get_at_actions = partialmethod(get_system_actions, system=APPEN_TEXT)
	#
	@classmethod
	def add_at_action(cls, identifier, name, button, data=[]):
		return cls.add_action(system=cls.APPEN_TEXT, identifier=identifier,
			name=name, button=button, data=data)
	@classmethod
	def get_at_action(cls, identifier):
		return cls.get_action(system=cls.APPEN_TEXT, identifier=identifier)
	@classmethod
	def get_at_actions(cls):
		return cls.get_system_actions(system=cls.APPEN_TEXT)
	def __init__(self):
		raise RuntimeError('UserSearchAction cannot be instantiated '
			'directly, use add_action() instead.')

UserSearchAction.add_at_action('assign_task_workers',
	name=_('Assign Task Workers'),
	button=_('Assign'),
	data=[dict(value=t.taskId, display=t.displayName)
		for t in m.Task.query.filter(m.Task.status.in_([m.Task.STATUS_ACTIVE,
			m.Task.STATUS_DISABLED])).order_by(m.Task.taskId)])
UserSearchAction.add_at_action('assign_task_supervisor',
	name=_('Assign Task Supervisor'),
	button=_('Assign'),
	data=[dict(value=t.taskId, display=t.displayName)
		for t in m.Task.query.filter(m.Task.status.in_([m.Task.STATUS_ACTIVE,
			m.Task.STATUS_DISABLED])).order_by(m.Task.taskId)])


@bp.route('/get_user_search_actions', methods=['GET', 'POST'])
def get_user_search_actions():
	actions = UserSearchAction.get_at_actions()
	return render_template('get_user_search_actions.xml', actions=actions)


class UserSearchFilter(object):
	APPEN_TEXT = 'AppenText'
	PIECE_TYPE_SELECT = 'select'
	_registry = OrderedDict()
	@classmethod
	def add_filter(cls, system, identifier, name, text, complement, pieces=[]):
		sys_dict = cls._registry.setdefault(system, OrderedDict())
		if identifier in sys_dict:
			raise ValueError('filter \'{0}\' of \'{1}\' already exists'\
				.format(identifier, system))
		filter = super(UserSearchFilter, cls).__new__(cls)
		setattr(filter, 'system', system)
		setattr(filter, 'identifier', identifier)
		setattr(filter, 'name', name)
		setattr(filter, 'text', text)
		setattr(filter, 'complement', complement)
		setattr(filter, 'pieces', list(pieces))
		return sys_dict.setdefault(identifier, filter)
	@classmethod
	def get_filter(cls, system, identifier):
		return cls._registry.setdefault(system, OrderedDict()).get(identifier)
	@classmethod
	def get_system_filters(cls, system):
		return cls._registry.setdefault(system, OrderedDict()).values()
	@classmethod
	def add_at_filter(cls, identifier, name, text, complement, pieces=[]):
		return cls.add_filter(system=cls.APPEN_TEXT, identifier=identifier,
			name=name, text=text, complement=complement, pieces=pieces)
	@classmethod
	def get_at_filter(cls, identifier):
		return cls.get_filter(system=cls.APPEN_TEXT, identifier=identifier)
	@classmethod
	def get_at_filters(cls):
		return cls.get_system_filters(system=cls.APPEN_TEXT)
	def __init__(self):
		raise RuntimeError('UserSearchFilter cannot be instantiated '
			'directly, use add_filter() instead.')

UserSearchFilter.add_at_filter('assigned_task',
	name=_('Task'),
	text=_('Users who are currently assigned to'),
	complement=_('Users who are not currently assigned to'),
	pieces=[
	{
		'type': UserSearchFilter.PIECE_TYPE_SELECT,
		'data': [dict(value=t.displayName,
			key=t.taskId) for t in m.Task.query.filter(
			m.Task.status.notin_([m.Task.STATUS_ARCHIVED])
			).order_by(m.Task.taskId)]
	}],)
UserSearchFilter.add_at_filter('unused',
	name=_('Unused'),
	text=_('Users who are assigned to a current translation task'),
	complement=_('Users who are not assigned to a current translation task'),
	pieces=[],)
UserSearchFilter.add_at_filter('attempted_qualification_test',
	name=_('Attempted Qualification Test'),
	text=_('Users who have attempted the'),
	complement=_('Users who have not attempted the'),
	pieces=[
	{
		'type': UserSearchFilter.PIECE_TYPE_SELECT,
		'data': [dict(value=t.name, key=t.testId) for t
			in m.Test.query.order_by(m.Test.testId)]
	}],)
UserSearchFilter.add_at_filter('qualification_test_result',
	name=_('Qualification Test Result'),
	text=_('passed'),
	complement=_('failed'),
	pieces=[
	{
		'type': UserSearchFilter.PIECE_TYPE_SELECT,
		'data': [dict(value=t.name, key=t.testId) for t
			in m.Test.query.order_by(m.Test.testId)]
	}],)
UserSearchFilter.add_at_filter('qualification_test_score',
	name=_('Qualification Test Score'),
	text=_('at least'),
	complement=_('less than'),
	pieces=[
	{
		'type': UserSearchFilter.PIECE_TYPE_SELECT,
		'data': [dict(value=('%.1f%% on' % i), key=i) for i
			in range(0, 95, 5)],
	},
	{
		'type': UserSearchFilter.PIECE_TYPE_SELECT,
		'data': [dict(value=t.name, key=t.testId) for t
			in m.Test.query.order_by(m.Test.testId)]
	}],)

@bp.route('/get_user_search_filters', methods=['GET', 'POST'])
def get_user_search_filters():
	filters = UserSearchFilter.get_at_filters()
	return render_template('get_user_search_filters.xml', filters=filters)


@bp.route('/get_user_details_CSS', methods=['GET', 'POST'])
def get_user_details_css():
	url = url_for('static', filename='css/userDetails.css', _external=True)
	return render_template('get_user_details_CSS.xml', url=url)


@bp.route('/get_user_details_JS', methods=['GET', 'POST'])
def get_user_details_js():
	url = url_for('static', filename='css/userDetails.js', _external=True)
	return render_template('get_user_details_CSS.xml', url=url)


def format_recent_work_entry():
	pass

@bp.route('/recent_work', methods=['GET', 'POST'])
def get_recent_work_entries():
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
	return render_template('recent_work.xml', entries=result)


@bp.route('/update_payments', methods=['GET', 'POST'])
def update_payments():
	return 'update_payments'


@bp.route('/user_details', methods=['GET', 'POST'])
def get_user_details():
	return 'user_details'

