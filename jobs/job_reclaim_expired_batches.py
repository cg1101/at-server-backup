
import logging
import cStringIO
import traceback
import os

from sqlalchemy import func

from db.db import SS
import db.model as m
from db.schema import t_batchhistory


log = logging.getLogger(__name__)


def reclaim_expired_batches(task):
	q_expired = m.Batch.query.filter(m.Batch.taskId==task.taskId
			).filter(m.Batch.leaseExpires<=func.now())
	expired_batches = q_expired.all()
	count = len(expired_batches)
	if count == 0:
		log.debug('task {0}: no expired batches found'.format(task.taskId))
	else:
		log.debug('task {0}: found {1} expired batch(es)'.format(task.taskId, count))

	operatorId = os.environ['CURRENT_USER_ID']

	for batch in expired_batches:
		query = t_batchhistory.insert(dict(
			batchId=batch.batchId,
			userId=operatorId,
			event='revoked',
		))
		SS.execute(query)
		batch.userId = None
		batch.leaseGranted = None
		batch.leaseExpires = None
		batch.checkedOut = False
		batch.priority = batch.priority + 1


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
			reclaim_expired_batches(task)
		except:
			out = cStringIO.StringIO()
			traceback.print_exc(file=out)
			log.error(out.getvalue())
			SS.rollback()
		else:
			log.info('task {} succeeded'.format(task.taskId))
			SS.commit()
