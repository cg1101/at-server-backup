
import logging
import cStringIO
import traceback
import random

from db.db import SS
import db.model as m


log = logging.getLogger(__name__)


class QaGenerator(object):
	Z_VALUES = {
		0.80: 1.28,
		0.90: 1.64,
		0.95: 1.96,
		0.97: 2.17,
		0.99: 2.58,
	}

	@classmethod
	def get_sample_set_size(cls, population, sampling_error,
			estimated_accuracy, confidence_interval, cap_accuracy=True):
		print (cls, population, sampling_error,
			estimated_accuracy, confidence_interval, cap_accuracy)
		if sampling_error > 1 or sampling_error < 0:
			raise ValueError('sampling error must be in [0, 1]')
		if estimated_accuracy > 1 or estimated_accuracy < 0:
			raise ValueError('estimated accuracy must be in [0, 1]')
		if confidence_interval not in cls.Z_VALUES:
			raise ValueError('z-value not defined for given confidence interval')
		z = cls.Z_VALUES[confidence_interval]
		n = z ** 2 * estimated_accuracy * (1 - estimated_accuracy) / sampling_error
		try:
			samples = n / (1 + (n - 1.0) / population)
		except ZeroDevisionError:
			samples = 0
		return int(samples)

	def iter_sub_tasks(self, taskId):
		q = m.SubTask.query.\
			filter(m.SubTask.taskId==taskId).\
			filter(m.SubTask.workTypeId.in_(
				SS.query(m.WorkType.workTypeId).\
				filter(m.WorkType.name.in_(
					[m.WorkType.WORK, m.WorkType.REWORK]))
				))
		for subTask in q.all():
			yield subTask
	def iter_intervals(self, subTaskId):
		q_target_intervals = m.WorkInterval.query.\
			filter(m.WorkInterval.subTaskId==subTaskId).\
			filter(m.WorkInterval.status.in_([
				m.WorkInterval.STATUS_CURRENT,
				m.WorkInterval.STATUS_ADDING_FINAL_CHECKS]))
		for interval in q_target_intervals.all():
			print 'find interval {}'.format(interval.workIntervalId)
			yield interval
	def iter_user_work_pool(self, subTask, interval):
		q_entries = SS.query(m.WorkEntry.entryId, m.WorkEntry.userId).\
			filter(m.WorkEntry.subTaskId==subTask.subTaskId).\
			filter(m.WorkEntry.batchId.notin_(
				SS.query(m.Batch.batchId).filter(
					m.Batch.subTaskId==subTask.subTaskId))).\
			filter(m.WorkEntry.created>=interval.startTime).\
			distinct(m.WorkEntry.userId, m.WorkEntry.rawPieceId).\
			order_by(m.WorkEntry.userId, m.WorkEntry.rawPieceId,\
					m.WorkEntry.created.desc())
		if interval.endTime:
			q_entries = q_entries.filter(m.WorkEntry.created<=interval.endTime)
		pools = {}
		for entryId, userId in q_entries.all():
			pools.setdefault(userId, set()).add(entryId)
		for userId, entryIds in pools.iteritems():
			yield (userId, entryIds)
	def get_qa_samples(self, subTask, userId, entryIds):

		population = len(entryIds)
		sampling_error = subTask.qaConfig.samplingError
		estimated_accuracy = subTask.qaConfig.defaultExpectedAccuracy
		confidence_interval = subTask.qaConfig.confidenceInterval
		samples_needed = self.get_sample_set_size(population,\
 			sampling_error, estimated_accuracy, confidence_interval)

		# entries which QA has been planned
		q_planned = SS.query(m.PageMember.workEntryId
			).filter(m.PageMember.taskId==subTask.taskId
			).filter(m.PageMember.workType==m.WorkType.QA
			).distinct(m.PageMember.workEntryId)

		# entries that have been QA already
		q_qaed = SS.query(m.WorkEntry.qaedEntryId).\
			filter(m.WorkEntry.taskId==subTask.taskId).\
			distinct(m.WorkEntry.qaedEntryId)

		all_planned = set([i.workEntryId for i in q_planned.all()])
		all_qaed = set([i.qaedEntryId for i in q_qaed.all()])

		planned = all_planned & entryIds
		qaed = all_qaed & entryIds

		to_add = samples_needed - len(qaed) - len(planned)
		if to_add <= 0:
			return []
		sample_pool = list(entryIds - planned - qaed)
		random.shuffle(sample_pool)
		return sample_pool[:to_add]
	def paginate(self, samples, size):
		if not size >= 1:
			raise ValueError('size must be greater than or equal to 1')
		return [samples[offset:offset+size] for offset in range(0, len(samples), size)]
	def create_qa_batches(self, qaSubTask, userId, intervalId, samples, priority=5):
		if not samples:
			return
		for load in self.paginate(samples, qaSubTask.maxPageSize):
			b = m.Batch(taskId=qaSubTask.taskId,
				subTaskId=qaSubTask.subTaskId,
				notUserId=userId,
				workIntervalId=intervalId,
				priority=priority)
			p = m.Page(pageIndex=0)
			b.pages.append(p)
			for memberIndex, workEntryId in enumerate(load):
				memberEntry = m.PageMemberEntry(memberIndex=memberIndex)
				memberEntry.workEntryId = workEntryId
				p.memberEntries.append(memberEntry)
			SS.add(b)
		SS.flush()
	def __call__(self, taskId):
		task = m.Task.query.get(taskId)
		if not task:
			raise ValueError('task {0} not found'.format(taskId))
		print 'generating qa for task', taskId
		if task.status in (m.Task.STATUS_ARCHIVED, m.Task.STATUS_CLOSED):
			# TODO: add checks for lastStatusChange
			return
		for subTask in self.iter_sub_tasks(taskId):
			for interval in self.iter_intervals(subTask.subTaskId):
				if subTask.qaConfig:
					print 'scanning interval {}'.format(interval.workIntervalId)
					for userId, pool in self.iter_user_work_pool(subTask, interval):
						print 'userId:', userId, 'work pool:', pool
						samples = self.get_qa_samples(subTask, userId, pool)
						qaSubTask = m.SubTask.query.get(subTask.qaConfig.qaSubTaskId)
						self.create_qa_batches(qaSubTask, userId,
								interval.workIntervalId, samples)
				if interval.status == m.WorkInterval.STATUS_ADDING_FINAL_CHECKS:
					interval.status = m.WorkInterval.STATUS_CHECKING


def create_qa(task):
	if task.status in (m.Task.STATUS_ARCHIVED, m.Task.STATUS_CLOSED):
		# TODO: add checks for lastStatusChange so that
		# recently closed tasks may still get QA created
		return
	QaGenerator()(task.taskId)


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
			create_qa(task)
		except:
			out = cStringIO.StringIO()
			traceback.print_exc(file=out)
			log.error(out.getvalue())
			SS.rollback()
			# break
		else:
			log.info('task {} succeeded'.format(task.taskId))
			SS.commit()
