
import logging
import cStringIO
import traceback
import datetime

import pytz

from db.db import SS
import db.model as m


log = logging.getLogger(__name__)


def end_work_intervals(task=None):
	q = m.WorkInterval.query.filter(
		m.WorkInterval.status==m.WorkInterval.STATUS_CURRENT)
	if task is not None:
		q = q.filter(m.WorkInterval.taskId==task.taskId)

	now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
	endTime = datetime.datetime(now.year, now.month, now.day,
			23, 59, 59, 999999, tzinfo=pytz.utc)

	for wi in q.all():
		wi.endTime = endTime
		wi.status = wi.STATUS_ADDING_FINAL_CHECKS
		newWorkInterval = m.WorkInterval(
			taskId=wi.taskId,
			subTaskId=wi.subTaskId,
			status=wi.STATUS_CURRENT,
			startTime=endTime,
			endTime=None,
		)
		SS.add(newWorkInterval)


def main(taskId=None):
	logging.basicConfig(level=logging.DEBUG)
	if taskId is None:
		tasks = m.Task.query.filter(m.Task.status.notin_([
				m.Task.STATUS_ARCHIVED, m.Task.STATUS_CLOSED,
				m.Task.STATUS_FINISHED])).all()
	else:
		task = m.Task.query.get(taskId)
		if not task:
			raise ValueError('task {0} not found'.format(taskId))
		tasks = [task]

	for task in tasks:
		try:
			end_work_intervals(task)
		except:
			out = cStringIO.StringIO()
			traceback.print_exc(file=out)
			log.error(out.getvalue())
			SS.rollback()
			break
		else:
			log.info('task {} succeeded'.format(task.taskId))
			SS.commit()
