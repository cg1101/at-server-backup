
import logging
import cStringIO
import traceback
import os
import datetime

import pytz

from db.db import SS
import db.model as m
from app.util import Selector, Batcher
from app.i18n import get_text as _


log = logging.getLogger(__name__)


def run_recurring_utterance_selections(task):
	rs = m.UtteranceSelection.query.filter(m.UtteranceSelection.taskId==task.taskId
			).filter(m.UtteranceSelection.recurring
			).filter(m.UtteranceSelection.enabled).all()
	for selection in rs:
		subTask = m.SubTask.query.get(selection.subTaskId)
		if not subTask:
			log.error(_('utterance selection {0} is corrupted: sub task {1} not found'
				).format(selectionId, selection.subTaskId))
			continue
		if subTask.workType != m.WorkType.REWORK:
			log.error(_('utterance selection {0} is corrupted: sub task {1} is not a {2} sub task'
				).format(selectionId, selection.subTaskId, m.WorkType.REWORK))
			continue

		rawPieceIds = Selector.select(selection)
		if not rawPieceIds:
			log.info(_('no matches found'))
			continue

		batches = Batcher.batch(subTask, rawPieceIds)
		for batch in batches:
			SS.add(batch)

		itemCount = len(rawPieceIds)
		now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
		event = m.SubTaskContentEvent(subTaskId=subTask.subTaskId,
			selectionId=selectionId, itemCount=itemCount,
			isAdding=True, tProcessedAt=now, operator=selection.userId)
		SS.add(event)


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
			run_recurring_utterance_selections(task)
		except:
			out = cStringIO.StringIO()
			traceback.print_exc(file=out)
			log.error(out.getvalue())
			SS.rollback()
			# break
		else:
			# log.info('task {} succeeded'.format(task.taskId))
			SS.commit()
			pass
