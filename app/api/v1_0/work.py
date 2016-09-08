
import datetime

from flask import request, session, jsonify, redirect
import pytz

import db.model as m
from db.schema import t_batchhistory
from db.db import SS
from app.api import api, caps, MyForm, Field, validators
from app.i18n import get_text as _
from . import api_1_0 as bp
from .. import InvalidUsage

from app.util import TestManager

def is_local_address(ipAddress):
	if ipAddress.startswith('192.168.') or ipAddress.startswith('165.228.178.104'):
		return True
	if ipAddress.startswith('127.'):
		return True
	return False

_name = __file__.split('/')[-1].split('.')[0]


@bp.route(_name + '/get/<int:subTaskId>')
@api
def get_batch_from_sub_task(subTaskId):
	me = session['current_user']

	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId))

	task = subTask.task
	taskId = subTask.taskId
	subTaskId = subTask.subTaskId

	permit = m.TaskWorker.query.get((me.userId, taskId, subTaskId))
	if not permit or permit.removed:
		raise InvalidUsage(_('Sorry, you are not assigned to this sub task.'))

	batch = m.Batch.query.filter_by(subTaskId=subTaskId
		).filter(m.Batch.userId==me.userId).first()
	if batch:
		return jsonify(batchId=batch.batchId,
			hasReadInstructions=permit.hasReadInstructions)


	# TODO: decide when qualification is needed
	if permit.isNew and False:
		raise InvalidUsage(_('Sorry, you need to take qualification test first.'))

	if task.status != m.Task.STATUS_ACTIVE:
		# use the same message as there are no more batches left
		raise InvalidUsage(_('Sorry, there are no more batches left.',
			'Please check later.'))

	# TODO: check sub tasks' policy
	objection = PolicyChecker.check_get_policy(subTask, me)
	if objection:
		raise InvalidUsage(_('Sorry, {0}').format(objection))

	batch = m.Batch.query.filter_by(subTaskId=subTaskId
		).filter(m.Batch.onHold==False
		).filter(m.Batch.userId==None
		).filter(m.Batch.notUserId!=me.userId
		).order_by(m.Batch.priority.desc(), m.Batch.batchId
		).first()
	if not batch:
		raise InvalidUsage(_('Sorry, there are no more batches left.',
			'Please check later.'))

	# TODO: change to TZ aware
	now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc
		).replace(tzinfo=None)
	batch.userId = me.userId
	batch.leaseGranted = now
	batch.leaseExpires = now + subTask.defaultLeaseLife

	return jsonify(batchId=batch.batchId,
			hasReadInstructions=permit.hasReadInstructions)


@bp.route(_name + '/do/<int:batchId>')
@api
def load_batch_context(batchId):
	me = session['current_user']

	batch = m.Batch.query.get(batchId)
	if not batch:
		raise InvalidUsage(_('batch {0} not found').format(batchId), 404)

	task = batch.task
	subTask = batch.subTask
	tagSet = None if task.tagSetId is None else m.TagSet.query.get(task.tagSetId)
	labelSet = None if task.labelSetId is None else m.LabelSet.query.get(task.labelSetId)
	taskErrorTypes = m.TaskErrorType.query.filter_by(taskId=task.taskId).all()

	# check if current user has the capability to view batch
	# this allows supervisors to check progress
	has_cap = True

	if batch.userId != me.userId and not has_cap:
		raise InvalidUsage(_('Sorry, you have requested a batch that you don\'t own.'
			'If you have any questions, please contact your transcription supervisor.'))

	permit = m.TaskWorker.query.get((me.userId, task.taskId, subTask.subTaskId))
	if (not permit or permit.removed) and not has_cap:
		# TODO: take back assigned batch if user got removed?
		raise InvalidUsage(_('Sorry, you are not assigned to this sub task.'))

	now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
	if batch.leaseExpires <= now and not has_cap:
		# TODO: take back expired batch
		raise InvalidUsage(_().format('Sorry, you current work lease is expired.',
			'Please select another item to work on.',
			'If you have any questions, please contact your transcription supervisor.'))

	showGuideline = (subTask.instructionPage != None
				and subTask.instructionPage.strip()
				and permit
				and not permit.hasReadInstructions)

	return jsonify(
		contextType='batch',
		task=m.Task.dump(batch.task),
		subTask=m.SubTask.dump(batch.subTask),
		tagSet=m.TagSet.dump(tagSet) if tagSet else None,
		labelSet=m.LabelSet.dump(labelSet) if labelSet else None,
		taskErrorTypes=m.TaskErrorType.dump(taskErrorTypes),
		batch=m.Batch.dump(batch),
		showGuideline=showGuideline,
	)


@bp.route(_name + '/do/<int:batchId>/abandon')
@api
def abandon_batch(batchId):
	batch = m.Batch.query.get(batchId)
	if not batch:
		raise InvalidUsage(_('batch {0} not found').format(batchId))
	me = session['current_user']
	if batch.userId != me.userId:
		raise InvalidUsage(_('batch {0} is not owned by user {1}').format(batchId, me.userId))

	batch.log_event('abandoned')
	batch.reset_ownership()
	batch.increase_priority()

	return jsonify(message=_('batch {0} has been abandoned by user {1}').format(batchId, me.userId))


def check_page_existence(data, key, pageId, batchId):
	page = m.Page.query.get(pageId)
	if not page or page.batchId != batchId:
		raise ValueError(_('page {0} not found in batch {1}').format(pageId, batchId))


def check_member_existence(data, key, memberIndex):
	pageId = data['pageId']
	memberEntry = m.PageMemberEntry.query.get((pageId, memberIndex))
	if not memberEntry:
		raise ValueError(_('page number ({}, {}) not found').format(pageId, memberIndex))


def normalize_label_ids(data, key, labelIds):
	task = data['task']
	rs = []
	if task.labelSetId != None:
		try:
			input_ids = set([int(i) for i in labelIds])
		except:
			raise ValueError(_('invalid labelIds input: {0}').format(labelIds))
		for labelId in input_ids:
			label = m.Label.query.get(labelId)
			if not label or label.labelSetId != task.labelSetId:
				continue
			rs.append(labelId)
	return sorted(rs)


def normalize_error_type_ids(data, key, errorTypeIds):
	task = data['task']
	rs = []
	valid_ids = set([r.errorTypeId for r in SS.query(m.TaskErrorType.errorTypeId
		).filter(m.TaskErrorType.taskId==task.taskId
		).filter(m.TaskErrorType.disabled.is_(False))])
	try:
		input_ids = set([int(i) for i in errorTypeIds])
	except:
		raise ValueError(_('invalid errorTypeIds input: {0}').format(errorTypeIds))
	return sorted(valid_ids & input_ids)


@bp.route(_name + '/do/<int:batchId>/save', methods=['POST'])
@api
def save_work_entry(batchId):
	batch = m.Batch.query.get(batchId)
	if not batch:
		raise InvalidUsage(_('batch {0} not found').format(batchId))
	me = session['current_user']
	if batch.userId != me.userId:
		raise InvalidUsage(_('batch {0} is not owned by user {1}').format(batchId, me.userId))
	if batch.isExpired:
		raise InvalidUsage(_('batch {0} has expired already').format(batchId))

	subTask = batch.subTask

	data = MyForm(
		Field('task', is_mandatory=True, default=batch.task),
		Field('pageId', is_mandatory=True, validators=[
			(check_page_existence, (batchId,)),
		]),
		Field('memberIndex', is_mandatory=True, validators=[
			check_member_existence,
		]),
		Field('result', is_mandatory=True, default=''),
		Field('labels', is_mandatory=True, default=[],
			normalizer=normalize_label_ids),
		Field('errors', is_mandatory=True, default=[],
			normalizer=normalize_error_type_ids),
	).get_data()

	ipAddress = request.environ['REMOTE_ADDR']

	memberEntry = m.PageMemberEntry.query.get((data['pageId'], data['memberIndex']))
	assert memberEntry

	if subTask.workType == m.WorkType.QA:
		qaedEntryId = memberEntry.workEntryId
		qaedEntry = m.WorkEntry.query.get(qaedEntryId)
		qaedUserId = qaedEntry.userId
		rawPieceId = qaedEntry.rawPieceId
		taskErrorTypeById = dict([(i.errorTypeId, i) for i
			in m.TaskErrorType.query.filter_by(taskId=batch.taskId).all()])
	else:
		qaedEntryId = None
		qaedEntry = None
		qaedUserId = None
		rawPieceId = memberEntry.rawPieceId
		taskErrorTypeById = {}
		data['errors'] = []

	# add new Entry
	newEntry = m.BasicWorkEntry(**{
		# 'entryId': None, # TBD
		# 'created': None, # auto-fill
		'result': data['result'],
		'rawPieceId': rawPieceId,
		'batchId': batchId,
		'taskId': batch.taskId,
		'subTaskId': batch.subTaskId,
		'workTypeId': batch.subTask.workTypeId,
		'userId': me.userId,
		# 'notes': None,
		'qaedUserId': qaedUserId,
		'qaedEntryId': qaedEntryId,
		'pageId': data['pageId']
	})
	SS.add(newEntry)
	SS.flush()
	# add labels
	for labelId in data['labels']:
		SS.add(m.AppliedLabel(entryId=newEntry.entryId, labelId=labelId))
	# add errors, (if applicable)
	for errorTypeId in data['errors']:
		e = taskErrorTypeById.get(errorTypeId, None)
		SS.add(m.AppliedError(entryId=newEntry.entryId,
			errorTypeId=e.errorTypeId, severity=e.severity))

	# add payable event
	event = m.PayableEvent(**{
		# 'eventId': None, # TBD
		'userId': me.userId,
		'taskId': batch.taskId,
		'subTaskId': batch.subTaskId,
		# 'created': None, # auto-fill
		'batchId': batchId,
		'pageId': data['pageId'],
		'rawPieceId': rawPieceId,
		'workEntryId': newEntry.entryId,
		'calculatedPaymentId': None, # explicitly set to NULL
		'localConnection': is_local_address(ipAddress),
		'ipAddress': ipAddress,
		'ratio': 1.0,
	})
	SS.add(event)

	SS.flush()
	newEntry = m.WorkEntry.query.get(newEntry.entryId)
	return jsonify(
		entry=m.WorkEntry.dump(newEntry),
		event=m.PayableEvent.dump(event),
	)


@bp.route(_name + '/do/<int:batchId>/submit')
@api
def submit_batch(batchId):
	batch = m.Batch.query.get(batchId)
	if not batch:
		raise InvalidUsage(_('batch {0} not found').format(batchId))
	me = session['current_user']
	if batch.userId != me.userId:
		raise InvalidUsage(_('batch {0} is not owned by user {1}').format(batchId, me.userId))
	if not batch.isFinished:
		raise InvalidUsage(_('batch {0} is not finished').format(batchId))

	SS.rollback()
	batch = m.Batch.query.get(batchId)
	batch.log_event('submitted')
	for p in batch.pages:
	# 	for member in p.members:
	# 		SS.delete(member)
		for memberEntry in p.memberEntries:
			SS.delete(memberEntry)
		SS.delete(p)
	SS.delete(batch)
	SS.flush()

	remaining = m.Batch.query.filter_by(subTaskId=batch.subTaskId
		).filter(m.Batch.onHold.isnot(True)
		).filter(m.Batch.userId.is_(None)).count()
	return jsonify(
		message=_('batch {1} has been submitted by user {1}').format(batchId, me.userId),
		remainingBatches=remaining,
	)


@bp.route(_name + '/tests/<int:testId>/start')
@api
def start_or_resume_test(testId):
	me = session['current_user']

	test = m.Test.query.get(testId)
	if not test:
		raise InvalidUsage(_('test {0} not found').format(testId))
	if not test.isEnabled:
		raise InvalidUsage(_('test {0} is not enabled').format(testId))

	# TODO: need to find out ids of languages current user speaks
	languageIds = [1,2, 3, 4]
	record = TestManager.report_eligibility(test, me, languageIds)
	if not record.get('url'):
		raise InvalidUsage(_('user {0} is not eligible for test {1}'
			).format(me.userId, testId))

	sheets = m.Sheet.query.filter_by(testId=testId
			).filter_by(userId=me.userId
			).order_by(m.Sheet.nTimes.desc()
			).all()
	# # NOTE: uncomment this block if nTimes needs to be fixed automatically
	# for i, sheet in enumerate(sheets):
	# 	if sheet.nTimes != i:
	# 		sheet.nTimes = i

	if sheets and sheets[-1].status == m.Sheet.STATUS_ACTIVE:
		return jsonify(sheetId=sheets[-1].sheetId)

	now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
	sheet = m.Sheet(userId=me.userId, testId=testId, nTimes=len(sheets),
		tStartedAt=now, tExpiresBy=(now+test.timeLimit))
	SS.add(sheet)
	SS.flush()
	for i, question in enumerate(TestManager.generate_questions(test)):
		entry = m.SheetEntry(sheetId=sheet.sheetId, index=i,
			questionId=question.questionId)
		sheet.entries.append(entry)

	return jsonify(sheetId=sheet.sheetId)

