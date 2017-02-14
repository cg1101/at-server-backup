
import os

from flask import session, redirect, url_for, send_file, request, abort

import db.model as m
from . import views as bp
from app.util import logistics

@bp.route('/')
def index():
	me = session['current_user']
	# TODO: add check to see if user doesn't have admin capability
	#if me.userId != 699:
	#	return redirect(current_app.config['NON_ADMIN_REDIRECT_URL'])
	index_html = os.path.join(os.path.dirname(__file__), '../index.html')
	return send_file(index_html, cache_timeout=0)


@bp.route('/work/<int:subTaskId>')
def get_batch_from_sub_task(subTaskId):
	return redirect('/#' + request.path)


@bp.route('/do/<int:batchId>')
def work_on_batch(batchId):
	return redirect('/#' + request.path)


@bp.route('/tasks/<int:taskId>/config')
def task_config(taskId):
	return redirect('/#' + request.path)


@bp.route('/tasks/<int:taskId>/workers')
def task_workers(taskId):
	return redirect('/#' + request.path)


@bp.route('/tasks/<int:taskId>/instructions/<filename>')
def task_guideline(taskId, filename):
	return logistics.get_guideline(taskId, filename)


@bp.route('/subtasks/<int:subTaskId>/rate')
def sub_task_rate(subTaskId):
	return redirect('/#' + request.path)


@bp.route('/subtasks/<int:subTaskId>/guideline')
def sub_task_guideline(subTaskId):
	subTask = m.SubTask.query.get(subTaskId)
	if not subTask:
		abort(404)
	if not subTask.instructionPage or not subTask.instructionPage.strip():
		abort(404)
	path = os.path.join('docs', 'tasks', str(subTask.taskId),
		os.path.basename(subTask.instructionPage))
	return redirect(url_for('static', filename=path))

@bp.route('/tests/<int:testId>/start')
def start_or_resume_test(testId):
	return redirect('/#' + request.path)


@bp.route('/sheets/<int:sheetId>')
def work_on_sheet(sheetId):
	return redirect('/#' + request.path)

