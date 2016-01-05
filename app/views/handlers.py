
import os
import datetime

from flask import session, redirect, url_for, send_file
import pytz

import db.model as m
from db.db import SS
from app.i18n import get_text as _
from app.util import PolicyChecker
from app.api import InvalidUsage

from . import views as bp

@bp.route('/')
def index():
	dot = os.path.dirname(__file__)
	return send_file(os.path.join(dot, '..', 'index.html'))


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
	return 'start test %s' % testId


@bp.route('/sheets/<int:sheetId>')
def work_on_sheet(sheetId):
	return 'answering test using sheet %s' % sheetId

