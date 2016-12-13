
import logging
import cStringIO
import traceback

from db.db import SS
import db.model as m


log = logging.getLogger(__name__)


def progress_work_intervals(task=None):
	"""
	For all intervals which status is 'checking', if there are no
	more QA batches (for that inteval) left, change status to 'finished'
	"""
	q = m.WorkInterval.query.filter(
		m.WorkInterval.status==m.WorkInterval.STATUS_CHECKING)
	if task is not None:
		q = q.filter(m.WorkInterval.taskId==task.taskId)
	for wi in q.all():
		if SS.query(m.Batch.batchId).\
				filter(m.Batch.workIntervalId==wi.workIntervalId).\
				count() == 0:
			wi.status = m.WorkInterval.STATUS_FINISHED


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
			progress_work_intervals(task)
		except:
			out = cStringIO.StringIO()
			traceback.print_exc(file=out)
			log.error(out.getvalue())
			SS.rollback()
		else:
			log.info('task {} succeeded'.format(task.taskId))
			SS.commit()
