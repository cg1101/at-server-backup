
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

	subTaskIds = [s.subTaskId for s in SS.query(m.SubTask.subTaskId
		).join(m.WorkType, m.SubTask.workTypeId==m.WorkType.workTypeId
		).filter(m.WorkType.modifiesTranscription
		).filter(m.Task.taskId==task.taskId)]

	q_latest = m.WorkEntry.query.filter(m.WorkEntry.taskId==task.taskId
		).filter(m.WorkEntry.subTaskId.in_(subTaskIds)
		).distinct(m.WorkEntry.rawPieceId
		).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())

	currently_batched = {}
	for r in m.PageMember.query.filter(
			m.PageMember.taskId==task.taskId).filter(m.PageMember.workType==m.WorkType.REWORK
			).all():
		currently_batched.setdefault(r.subTaskId, set()).add(r.rawPieceId)

	group_plan = {}
	for entry in q_latest.all():
		log.debug('checking raw piece {}, entry {}'.format(entry.rawPieceId, entry.entryId))
		qa_record = m.QaTypeEntry.query.filter(m.QaTypeEntry.qaedEntryId==entry.entryId
			).distinct(m.QaTypeEntry.qaedEntryId
			).order_by(m.QaTypeEntry.qaedEntryId, m.QaTypeEntry.created.desc()
			).all()
		if qa_record:
			qa_record = qa_record[0]
		else:
			log.debug('entry {} not qaed'.format(entry.entryId))
			continue
		rec = work_plan.get(qa_record.subTaskId, None)
		if not rec:
			log.debug('no auto-population configure for qa sub task {}'.format(qa_record.subTaskId))
			continue
		if entry.subTaskId not in rec:
			log.debug('sub task not configured for auto-population: {}'.format(entry.subTaskId))
			continue
		cfg = rec[entry.subTaskId]
		if qa_record.qaScore >= cfg['threshold']:
			log.debug('qa score passed')
			continue
		reworkSubTask = cfg['dest']
		if entry.rawPieceId in currently_batched.setdefault(reworkSubTask.subTaskId, set()):
			log.debug('already batched in sub task {}'.format(reworkSubTask.subTaskId))
			continue
		group_plan.setdefault(cfg['dest'], {}).setdefault(entry.userId, []).append(entry)

	#print 'group_plan', group_plan
	for reworkSubTask, workEntriesByUserId in group_plan.iteritems():
		for userId, entries in workEntriesByUserId.iteritems():
			batch = m.Batch(taskId=task.taskId,
				subTaskId=reworkSubTask.subTaskId,
				name='qa_failed_of_user#%s' % userId,
				priority=5)
			p = m.Page(pageIndex=0)
			batch.pages.append(p)
			for memberIndex, qaedEntry in enumerate(entries):
				memberEntry = m.PageMemberEntry(memberIndex=memberIndex)
				memberEntry.rawPieceId = qaedEntry.rawPieceId
				p.memberEntries.append(memberEntry)
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
