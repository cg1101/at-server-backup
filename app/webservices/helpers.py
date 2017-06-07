
from collections import OrderedDict

from flask import url_for
from sqlalchemy import func

import db.model as m
from db.db import SS
from app.api import InvalidUsage
from app.i18n import get_text as _


def action_assign_task_workers(userIds, taskId):
	subTask = m.SubTask.query.filter_by(taskId=taskId
		).filter(m.SubTask.workType==m.WorkType.WORK
		).order_by(m.subTask.subTaskId).first()
	if not SubTask:
		raise InvalidUsage(_('no sub task found under task {0}'
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
	url = url_for('views.task_workers', taskId=taskId, _external=True)
	return {'message': message, 'link': url}


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
	url = url_for('views.task_config', taskId=taskId,
		_anchor='supervisors', _external=True)
	return {'message': message, 'link': url}


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


def filter_assigned_task(taskId):
	return SS.query(m.TaskWorker.userId.distinct()
		).filter_by(taskId=taskId
		).filter(m.TaskWorker.removed==False).all()


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


def filter_qualification_test(testId):
	return SS.query(m.Sheet.userId.distinct()).filter_by(testId=testId).all()


def filter_qualification_test_result(testId):
	return SS.query(m.Sheet.userId.distinct()
		).filter_by(testId=testId
		).join(m.Test, m.Sheet.testId==m.Test.testId
		).filter(m.Sheet.score>=m.Test.passingScore)


def filter_qualification_test_score(score, testId):
	return SS.query(m.Sheet.userId.distinct()
		).filter_by(testId=testId
		).filter(m.Sheet.score>=score).all()


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


def calculate_task_payment_record(taskId, payrollId):
	cutOffTime = SS.query(func.max(m.WorkInterval.endTime
		).filter(m.WorkInterval.workIntervalId.in_(
			SS.query(m.CalculatedPayment.workIntervalId.distinct()
			).filter_by(taskId=taskId
			).filter_by(payrollId=payrollId))
		)).first()[0] or m.Payroll.query.get(payrollId).endDate
	itemCount, unitCount = SS.query(func.count(m.RawPiece.rawPieceId),
		func.sum(m.RawPiece.words)).filter(m.RawPiece.rawPieceId.in_(
			SS.query(m.WorkEntry.rawPieceId.distinct()
				).filter_by(taskId=taskId
				).filter(m.WorkEntry.created<=cutOffTime)
			)).first()
	unitCount = unitCount or 0
	calculatedSubtotal = SS.query(func.sum(m.CalculatedPayment.amount
		).filter(m.CalculatedPayment.taskId==taskId
		).filter(m.CalculatedPayment.payrollId<=payrollId)
		).first()[0] or 0
	otherSubtotal = SS.query(func.sum(m.OtherPayment.amount
		).filter(m.OtherPayment.taskId==taskId
		).filter(m.OtherPayment.payrollId<=payrollId)
		).first()[0] or 0

	return m.TaskPaymentRecord(taskId=taskId, payrollId=payrollId,
		itemCount=itemCount, unitCount=unitCount, cutOffTime=cutOffTime,
		paymentSubtotal=calculatedSubtotal+otherSubtotal)


def init_data():
	UserSearchAction.add_at_action('assign_task_workers',
		name=_('Assign Task Workers'),
		button=_('Assign'),
		func=action_assign_task_workers,
		data=[dict(value=t.taskId, display=t.displayName)
			for t in m.Task.query.filter(m.Task.status.in_([m.Task.STATUS_ACTIVE,
				m.Task.STATUS_DISABLED])).order_by(m.Task.taskId)])
	UserSearchAction.add_at_action('assign_task_supervisor',
		name=_('Assign Task Supervisor'),
		button=_('Assign'),
		func=action_assign_task_supervisor,
		data=[dict(value=t.taskId, display=t.displayName)
			for t in m.Task.query.filter(m.Task.status.in_([m.Task.STATUS_ACTIVE,
				m.Task.STATUS_DISABLED])).order_by(m.Task.taskId)])


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
	UserSearchFilter.add_at_filter('unused',
		name=_('Unused'),
		text=_('Users who are assigned to a current translation task'),
		complement=_('Users who are not assigned to a current translation task'),
		func=filter_unused,
		pieces=[],)
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

