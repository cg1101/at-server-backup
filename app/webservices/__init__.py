
import re
from collections import OrderedDict

from flask import Blueprint, render_template, url_for
from sqlalchemy import func

import db.model as m
from db.db import SS
from app.util import TestManager, Filterable
from app.i18n import get_text as _
from app.api import MyForm, Field, validators

webservices = bp = Blueprint('webservices', __name__, template_folder='./')


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


@bp.route('/apply_user_search_action', methods=['GET', 'POST'])
def apply_user_search_action():
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
	return render_template('apply_user_search_action.xml', reply=reply)


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


@bp.route('/apply_user_search_filters', methods=['GET', 'POST'])
def apply_user_search_filters():
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
	return render_template('get_user_details_CSS.xml', entries=entries)


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
	def add_action(cls, system, identifier, name, button, func, data=[]):
		sys_dict = cls._registry.setdefault(system, OrderedDict())
		if identifier in sys_dict:
			raise ValueError('action \'{0}\' of \'{1}\' already exists'\
				.format(identifier, system))
		if not callable(func):
			raise ValueError('func must be a callable')
		action = super(UserSearchAction, cls).__new__(cls)
		setattr(action, 'system', system)
		setattr(action, 'identifier', identifier)
		setattr(action, 'name', name)
		setattr(action, 'button', button)
		setattr(action, 'func', func)
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
	def add_at_action(cls, identifier, name, button, func, data=[]):
		return cls.add_action(system=cls.APPEN_TEXT, identifier=identifier,
			name=name, button=button, func=func, data=data)
	@classmethod
	def get_at_action(cls, identifier):
		return cls.get_action(system=cls.APPEN_TEXT, identifier=identifier)
	@classmethod
	def get_at_actions(cls):
		return cls.get_system_actions(system=cls.APPEN_TEXT)
	def __init__(self):
		raise RuntimeError('UserSearchAction cannot be instantiated '
			'directly, use add_action() instead.')

def action_assign_task_workers(userIds, taskId):
	subTask = m.SubTask.query.filter_by(taskId=taskId
		).filter(m.SubTask.workType==m.WorkType.WORK
		).order_by(m.subTask.subTaskId).first()
	if not SubTask:
		raise RuntimeError(_('no sub task found under task {0}'
			).format(taskId))
	for userId in userIds:
		s = m.TaskWorker.query.get((userId, taskId, subTask.subTaskId))
		if not s:
			s = m.TaskWorker(userId=userId, taskId=taskId,
				subTaskId=subTask.subTaskId)
			SS.add(s)
	total = len(userIds)
	message = _('Assigned the user as a worker for task {0}' if total == 1
		else 'Assigned {1} users as workers for task {0}'
		).format(taskId, total)
	url = url_for('index', _external=True)
	return {'message': message, 'link': url}

UserSearchAction.add_at_action('assign_task_workers',
	name=_('Assign Task Workers'),
	button=_('Assign'),
	func=action_assign_task_workers,
	data=[dict(value=t.taskId, display=t.displayName)
		for t in m.Task.query.filter(m.Task.status.in_([m.Task.STATUS_ACTIVE,
			m.Task.STATUS_DISABLED])).order_by(m.Task.taskId)])

def action_assign_task_supervisor(userIds, taskId):
	for userId in userIds:
		s = m.TaskSupervisor.query.get((taskId, userId))
		if not s:
			s = m.TaskSupervisor(taskId=taskId, userId=userId)
			SS.add(s)
	total = len(userIds)
	message = _('Assigned the user as a supervisor of task {0}' if total == 1
		else 'Assigned {1} users as supervisors of task {0}'
		).format(taskId, len(userIds))
	url = url_for('index', _external=True)
	return {'message': message, 'link': url}

UserSearchAction.add_at_action('assign_task_supervisor',
	name=_('Assign Task Supervisor'),
	button=_('Assign'),
	func=action_assign_task_supervisor,
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
	def add_filter(cls, system, identifier, name, text, complement,
			func, pieces=[]):
		sys_dict = cls._registry.setdefault(system, OrderedDict())
		if identifier in sys_dict:
			raise ValueError('filter \'{0}\' of \'{1}\' already exists'\
				.format(identifier, system))
		if not callable(func):
			raise ValueError('func must be a callable')
		filter = super(UserSearchFilter, cls).__new__(cls)
		setattr(filter, 'system', system)
		setattr(filter, 'identifier', identifier)
		setattr(filter, 'name', name)
		setattr(filter, 'text', text)
		setattr(filter, 'complement', complement)
		setattr(filter, 'func', func)
		setattr(filter, 'pieces', list(pieces))
		return sys_dict.setdefault(identifier, filter)
	@classmethod
	def get_filter(cls, system, identifier):
		return cls._registry.setdefault(system, OrderedDict()).get(identifier)
	@classmethod
	def get_system_filters(cls, system):
		return cls._registry.setdefault(system, OrderedDict()).values()
	@classmethod
	def add_at_filter(cls, identifier, name, text, complement, func,
			pieces=[]):
		return cls.add_filter(system=cls.APPEN_TEXT, identifier=identifier,
			name=name, text=text, complement=complement, func=func,
			pieces=pieces)
	@classmethod
	def get_at_filter(cls, identifier):
		return cls.get_filter(system=cls.APPEN_TEXT, identifier=identifier)
	@classmethod
	def get_at_filters(cls):
		return cls.get_system_filters(system=cls.APPEN_TEXT)
	def __init__(self):
		raise RuntimeError('UserSearchFilter cannot be instantiated '
			'directly, use add_filter() instead.')

def filter_assigned_task(taskId):
	return SS.query(m.TaskWorker.userId.distinct()
		).filter_by(taskId=taskId
		).filter(m.TaskWorker.removed==False).all()

UserSearchFilter.add_at_filter('assigned_task',
	name=_('Task'),
	text=_('Users who are currently assigned to'),
	complement=_('Users who are not currently assigned to'),
	func=filter_assigned_task,
	pieces=[
	{
		'type': UserSearchFilter.PIECE_TYPE_SELECT,
		'data': [dict(value=t.displayName,
			key=t.taskId) for t in m.Task.query.filter(
			m.Task.status.notin_([m.Task.STATUS_ARCHIVED])
			).order_by(m.Task.taskId)]
	}],)

def filter_unused():
	return SS.query(m.TaskWorker.userId.distinct()
		).filter(m.TaskWorker.removed==False
		).filter(m.TaskWorker.taskId.in_(
			SS.query(m.Task.taskId
				).filter_by(taskType=m.TaskType.TRANSLATION
				).filter(m.Task.status.in_([
					m.Task.STATUS_ACTIVE,
					m.Task.STATUS_DISABLED])
				)
			)
		).all()

UserSearchFilter.add_at_filter('unused',
	name=_('Unused'),
	text=_('Users who are assigned to a current translation task'),
	complement=_('Users who are not assigned to a current translation task'),
	func=filter_unused,
	pieces=[],)

def filter_qualification_test(testId):
	return SS.query(m.Sheet.userId.distinct()).filter_by(testId=testId).all()

UserSearchFilter.add_at_filter('attempted_qualification_test',
	name=_('Attempted Qualification Test'),
	text=_('Users who have attempted the'),
	complement=_('Users who have not attempted the'),
	func=filter_qualification_test,
	pieces=[
	{
		'type': UserSearchFilter.PIECE_TYPE_SELECT,
		'data': [dict(value=t.name, key=t.testId) for t
			in m.Test.query.order_by(m.Test.testId)]
	}],)

def filter_qualification_test_result(testId):
	return SS.query(m.Sheet.userId.distinct()
		).filter_by(testId=testId
		).join(m.Test, m.Sheet.testId==m.Test.testId
		).filter(m.Sheet.score>=m.Test.passingScore)

UserSearchFilter.add_at_filter('qualification_test_result',
	name=_('Qualification Test Result'),
	text=_('passed'),
	complement=_('failed'),
	func=filter_qualification_test_result,
	pieces=[
	{
		'type': UserSearchFilter.PIECE_TYPE_SELECT,
		'data': [dict(value=t.name, key=t.testId) for t
			in m.Test.query.order_by(m.Test.testId)]
	}],)

def filter_qualification_test_score(score, testId):
	return SS.query(m.Sheet.userId.distinct()
		).filter_by(testId=testId
		).filter(m.Sheet.score>=score).all()

UserSearchFilter.add_at_filter('qualification_test_score',
	name=_('Qualification Test Score'),
	text=_('at least'),
	complement=_('less than'),
	func=filter_qualification_test_score,
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
	return render_template('get_user_details_CSS.xml', entries=[url])


@bp.route('/get_user_details_JS', methods=['GET', 'POST'])
def get_user_details_js():
	url = url_for('static', filename='css/userDetails.js', _external=True)
	return render_template('get_user_details_CSS.xml', entries=[url])


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

