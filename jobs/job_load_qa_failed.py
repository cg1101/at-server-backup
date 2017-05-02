
import logging
import cStringIO
import traceback

from db.db import SS
import db.model as m
from app.util import Batcher


log = logging.getLogger(__name__)


def load_qa_failed(task):
	print 'checking task %s' % task.taskId
	subTaskById = dict([(s.subTaskId, s) for s in task.subTasks])
	work_plan = {}
	for s in task.subTasks:
		if s.qaConfig and s.qaConfig.populateRework:
			qaSubTask = subTaskById[s.qaConfig.qaSubTaskId]
			reworkSubTask = subTaskById[s.qaConfig.reworkSubTaskId]
			rec = work_plan.setdefault(s.qaConfig.qaSubTaskId, {})
			if rec == {}:
				rec['qaSubTask'] = qaSubTask
			rec[s.subTaskId] = {
				'src': s,
				'dest': reworkSubTask,
				'threshold': s.qaConfig.accuracyThreshold
			}
	#
	# for each QA sub task referenced in work_plan, check its content
	# if a qaedEntry is done in source sub task, and fails qa, then
	# group its raw piece into target rework sub task
	#
	#print 'work_plan', work_plan
	group_plan = {}
	for qaSubTaskId, rec in work_plan.iteritems():
		q = m.QaTypeEntry.query.filter(m.QaTypeEntry.subTaskId==qaSubTaskId
			).distinct(m.QaTypeEntry.batchId, m.QaTypeEntry.qaedEntryId
			).order_by(m.QaTypeEntry.batchId, m.QaTypeEntry.qaedEntryId,
				m.QaTypeEntry.created.desc())
		for entry in q.all():
			qaedEntry = m.WorkEntry.query.get(entry.qaedEntryId)
			# if qaedEntry was done in other sub tasks, do nothing
			if qaedEntry.subTaskId not in rec:
				continue
			# else check qa score
			cfg = rec[qaedEntry.subTaskId]
			if entry.qaScore < cfg.accuracyThreshold:
				group_plan.setdefault(cfg.dest, []).append(qaedEntry.rawPieceId)
	#print 'group_plan', group_plan
	for reworkSubTask, rawPieceIds in group_plan.iteritems():
		batches = Batcher.batch(reworkSubTask, rawPieceIds)
		for batch in batches:
			SS.add(batch)


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
			load_qa_failed(task)
		except:
			out = cStringIO.StringIO()
			traceback.print_exc(file=out)
			log.error(out.getvalue())
			SS.rollback()
			# break
		else:
			log.info('task {} succeeded'.format(task.taskId))
			SS.commit()
