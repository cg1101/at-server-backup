
import os
import datetime

from flask import session, redirect, url_for, current_app, render_template
import pytz

import db.model as m
from db.db import SS
from app.i18n import get_text as _
from app.util import PolicyChecker, TestManager
from app.api import InvalidUsage

from . import views as bp

@bp.route('/')
def index():
	me = session['current_user']
	# doesn't have admin capability
	if me.userId != 699:
		return redirect(current_app.config['NON_ADMIN_REDIRECT_URL'])
	return render_template('index.html')


@bp.route('/work/<int:subTaskId>')
def get_batch_from_sub_task(subTaskId):
	me = session['current_user']

	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		raise InvalidUsage(_('sub task {0} not found').format(subTaskId))

	batch = m.Batch.query.filter_by(subTaskId=subTaskId
		).filter(m.Batch.userId==me.userId).first()
	if batch:
		# TODO: extend lease maybe?
		return redirect(url_for('.work_on_batch', batchId=batch.batchId))

	task = subTask.task
	taskId = subTask.taskId
	subTaskId = subTask.subTaskId

	permit = m.TaskWorker.query.get((me.userId, taskId, subTaskId))
	if not permit or permit.removed:
		raise InvalidUsage(_('Sorry, you are not assigned to this sub task.'))

	# TODO: decide when qualification is needed
	if permit.isNew and False:
		raise InvalidUsage(_('Sorry, you need to take qualification test first.'))

	# NOTE: reading of instructions is 
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

	return redirect(url_for('.work_on_batch', batchId=batch.batchId))


@bp.route('/do/<int:batchId>')
def work_on_batch(batchId):
	me = session['current_user']

	batch = m.Batch.query.get(batchId)
	if not batch:
		raise InvalidUsage(_('batch {0} not found').format(batchId))

	taskId = batch.taskId
	subTaskId = batch.subTaskId
	subTask = batch.subTask

	permit = m.TaskWorker.query.get((me.userId, taskId, subTaskId))
	if not permit or permit.removed:
		# TODO: take back assigned batch if user got removed?
		raise InvalidUsage(_('Sorry, you are not assigned to this sub task.'))

	if batch.userId != me.userId:
		raise InvalidUsage(_('Sorry, you have requested a batch that you don\'t own.'
			'If you have any questions, please contact your transcription supervisor.'))

	if batch.leaseExpires <= datetime.datetime.now():
		# TODO: take back expired batch
		raise InvalidUsage(_().format('Sorry, you current work lease is expired.',
			'Please select another item to work on.',
			'If you have any questions, please contact your transcription supervisor.'))

	if subTask.instructionPage != None and not permit.hasReadInstructions:
		return redirect(url_for('.sub_task_guideline', subTaskId=subTaskId))

	return 'you are on batch %s' % batchId


@bp.route('/tasks/<int:taskId>/')
def task_main(taskId):
	return 'task %s' % taskId


@bp.route('/tasks/<int:taskId>/config')
def task_config(taskId):
	return 'config of task %s' % taskId


@bp.route('/tasks/<int:taskId>/workers')
def task_workers(taskId):
	return 'workers of task %s' % taskId


@bp.route('/subtasks/<int:subTaskId>/guideline')
def sub_task_guideline(subTaskId):
	return 'guideline of %s' % subTaskId


@bp.route('/subtasks/<int:subTaskId>/rate')
def sub_task_rate(subTaskId):
	return 'rate of sub task %s' % subTaskId


@bp.route('/tests/<int:testId>/start')
def start_or_resume_test(testId):
	test = m.Test.query.get(testId)
	if not test:
		raise InvalidUsage(_('test {0} not found').format(testId))
	if not test.isEnabled:
		raise InvalidUsage(_('test {0} is not enabled').format(testId))

	me = session['current_user']
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
		return redirect(url_for('.work_on_sheet', sheetId=sheets[-1].sheetId))

	now = datetime.datetime.utcnow().replace(tzinfo=pytz.info)
	sheet = m.Sheet(userId=me.userId, testId=testId, nTimes=len(sheets),
		tStartedAt=now, tExpiresBy=(now+test.timeLimit))
	SS.add(sheet)
	SS.flush()
	for i, question in enumerate(TestManager.generate_questions(test)):
		entry = m.SheetEntry(sheetId=sheet.sheetId, index=i,
			questionId=question.questionId)
		sheet.entries.append(sheet)

	return redirect(url_for('.work_on_sheet', sheetId=sheet.sheetId))


@bp.route('/sheets/<int:sheetId>')
def work_on_sheet(sheetId):
	return 'answering test using sheet %s' % sheetId

