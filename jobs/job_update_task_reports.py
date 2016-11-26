
import logging
import cStringIO
import traceback

from db.db import SS
import db.model as m


log = logging.getLogger(__name__)


def update_task_reports(task):
	print 'update task reports', task.taskId


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
			update_task_reports(task)
		except:
			out = cStringIO.StringIO()
			traceback.print_exc(file=out)
			log.error(out.getvalue())
			SS.rollback()
			# break
		else:
			log.info('task {} succeeded'.format(task.taskId))
			# SS.commit()
