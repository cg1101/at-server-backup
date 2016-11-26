
import logging
import cStringIO
import traceback
import datetime
import re
import operator

from sqlalchemy import func
import pytz
import numpy

from db.db import SS
import db.model as m


log = logging.getLogger(__name__)


def calculate_usage_stats(samples):
	mean = numpy.mean(samples)
	std = numpy.std(samples)
	return {'mean': mean, 'std': std}


class SimpleCounter(object):
	def __init__(self):
		self.itemCount = 0
		self.unitCount = 0
	def count(self, units):
		self.itemCount += 1
		self.unitCount += units


class RegularCounter(object):
	THRESHOLD = 2
	def __init__(self):
		self.itemCount = 0
		self.unitCount = 0
		self.qaedItemCount = 0
		self.qaedUnitCount = 0
		self.totalQaScore = 0
		self.flaggedErrors = {}
		self.usedTags = {}
		self.usedLabels = {}
		self.timeSlots = {}
		self.abnormalLabelUsage = {}
		self.abnormalTagUsage = {}
	@property
	def workRate(self):
		return self.itemCount * 4 / len(self.timeSlots)\
			if self.itemCount else None
	@property
	def accuracy(self):
		return self.totalQaScore / self.qaedItemCount\
			if self.qaedItemCount != 0 else None
	def __str__(self):
		return repr(dict(itemCount=self.itemCount,
			unitCount=self.unitCount,
			qaedItemCount=self.qaedItemCount,
			qaedUnitCount=self.qaedUnitCount,
			totalQaScore=self.totalQaScore,
			flaggedErrors=self.flaggedErrors,
			usedTags=self.usedTags,
			usedLabels=self.usedLabels,
			timeSlots=self.timeSlots))
	def __call__(self, time_slot_key, units, tags, labels, is_qaed, qa_score, errors):
		# use separate parameters to make testing easier
		self.itemCount += 1
		self.unitCount += units
		self.timeSlots[time_slot_key] =\
			self.timeSlots.setdefault(time_slot_key, 0) + 1
		if is_qaed:
			self.qaedItemCount += 1
			self.qaedUnitCount += units
			self.totalQaScore += qa_score
			for errorTypeId in errors:
				self.flaggedErrors[errorTypeId] =\
					self.flaggedErrors.setdefault(errorTypeId, 0) + 1
		for tagId in tags:
			self.usedTags[tagId] =\
				self.usedTags.setdefault(tagId, 0) + 1
		for labelId in labels:
			self.usedLabels[labelId] =\
				self.usedLabels.setdefault(labelId, 0) + 1
	def get_tag_rate(self, tagId):
		return self.usedTags.get(tagId, 0) / self.itemCount\
			if self.itemCount else None
	def get_label_rate(self, labelId):
		return self.usedLabels.get(labelId, 0) / self.itemCount\
			if self.itemCount else None
	def check_abnormal_usage(self, refTagUsage, refLabelUsage):
		self.abnormalLabelUsage.clear()
		self.abnormalTagUsage.clear()
		for tagId, stat in refTagUsage.iteritems():
			value = self.get_tag_rate(tagId)
			degree = round((value - stat['mean']) / stat['std'])\
				if stat['std'] else 0
			if abs(degree) > self.THRESHOLD:
				degree = self.THRESHOLD if value > stat['mean'] else -self.THRESHOLD
			if degree:
				self.abnormalTagUsage[tagId] = degree
		for labelId, stat in refLabelUsage.iteritems():
			value = self.get_label_rate(tagId)
			degree = round((value - stat['mean']) / stat['std'])\
				if stat['std'] else 0
			if abs(degree) > self.THRESHOLD:
				degree = self.THRESHOLD if value > stat['mean'] else -self.THRESHOLD
			if degree:
				self.abnormalLabelUsage[labelId] = degree


class SubtotalCounter(RegularCounter):
	def __init__(self, counters, check_usage=True):
		self.counters = counters

		self.itemCount = 0
		self.unitCount = 0
		self.qaedItemCount = 0
		self.qaedUnitCount = 0
		self.totalQaScore = 0
		self.flaggedErrors = {}
		self.usedTags = {}
		self.usedLabels = {}
		self.timeSlots = {}
		for c in counters:
			for attr in ('itemCount', 'unitCount', 'qaedItemCount',
					'qaedUnitCount', 'totalQaScore'):
				new_value = getattr(self, attr) + getattr(c, attr)
				setattr(self, attr, new_value)
			for attr in ('flaggedErrors', 'usedTags', 'usedLabels',
					'timeSlots'):
				d = getattr(self, attr)
				for key, value in getattr(c, attr).iteritems():
					d[key] = d.setdefault(key, 0) + value

		self.tagUsage = {}
		self.labelUsage = {}
		for tagId in self.usedTags:
			tag_rates = [c.get_tag_rate(tagId) for c in counters]
			tag_usage = calculate_usage_stats(tag_rates)
			self.tagUsage[tagId] = tag_usage
		for labelId in self.usedLabels:
			label_rates = [c.get_label_rate(labelId) for c in counters]
			label_usage = calculate_usage_stats(label_rates)
			self.tagUsage[tagId] = tag_usage

		self.abnormalLabelUsage = {}
		self.abnormalTagUsage = {}

		if check_usage:
			self.check_usage()
	@property
	def maxAmount(self):
		return max([c.itemCount for c in self.counters]
			) if self.counters else None
	@property
	def meanAmount(self):
		return numpy.mean([c.itemCount for c in self.counters]
			) if self.counters else None
	@property
	def maxWorkRate(self):
		return max([c.workRate for c in self.counters]
			) if self.counters else None
	@property
	def medianWorkRate(self):
		return numpy.median([c.workRate for c in self.counters]
			) if self.counters else None
	def check_usage(self):
		for counter in self.counters:
			counter.check_abnormal_usage(self.tagUsage, self.labelUsage)


class SubTaskStatistician(object):
	_P = re.compile(r'''tagid=(["'])(\d+)\1''')
	def __init__(self, subTask):
		self.subTask = subTask
		self.task = subTask.task
		self.workIntervals = subTask.workIntervals
		if not len(self.workIntervals):
			raise RuntimeError('no work interals found for sub task {0}'.\
					format(self.subTaskId))
		self.per_user_per_day = {}
		self.per_user_per_interval = {}
		self.per_user = {}
		self.sub_task_stats = None
	def get_interval(self, moment):
		if moment < self.workIntervals[0].startTime:
			raise RuntimeError('earlier than first work interval')
		for next_interval in self.workIntervals:
			if moment >= next_interval.startTime and\
				(next_interval.endTime is None or\
					moment < next_interval.endTime):
				return next_interval
		raise RuntimeError('later than last work interval')
	def list_tags(self, text):
		# TODO: improve current implementation to be more error-proof
		return [int(m.group(2)) for m in self._P.finditer(text)]
	def iter_work_entries(self):
		entries = m.WorkEntry.query.\
				filter(m.WorkEntry.subTaskId==self.subTask.subTaskId).\
				distinct(m.WorkEntry.batchId, m.WorkEntry.pageId,\
					m.WorkEntry.rawPieceId).\
				order_by(m.WorkEntry.batchId, m.WorkEntry.pageId,\
					m.WorkEntry.rawPieceId,\
					m.WorkEntry.created.desc()).\
				all()
		for entry in entries:
			if entry.workType in (m.WorkType.WORK, m.WorkType.REWORK):
				qa_record = m.QaTypeEntry.query.\
					filter(m.QaTypeEntry.qaedEntryId==entry.entryId).\
					order_by(m.QaTypeEntry.created.desc()).\
					first()
			else:
				qa_record = None
			yield (entry, qa_record)
	def count_work_entries(self):
		for entry, qa_record in self.iter_work_entries():
			try:
				workInterval = self.get_interval(entry.created)
			except RuntimeError:
				log.error('no work interval for entry {}'.format(entry.entryId))
				raise

			subTaskId = entry.subTaskId
			userId = entry.userId
			workDate = entry.workDate
			time_slot_key = entry.timeSlotKey
			units = entry.rawPiece.words

			if entry.workType in (m.WorkType.WORK, m.WorkType.REWORK):
				tags = self.list_tags(entry.result or '')
				labels = entry.labels
			else:
				tags = []
				labels = []
			if qa_record is not None:
				is_qaed = True
				qa_score = qa_record.qaScore
				errors = qa_record.errors
			else:
				is_qaed = False
				qa_score = 0
				errors = []

			self.per_user_per_day.setdefault(
				(subTaskId, userId, workDate),
				SimpleCounter()
				).count(units)

			#
			# NOTE: set subTaskId to None to make it easier later
 			#
			self.per_user_per_interval.setdefault(
				(None, userId, workInterval.workIntervalId),
				RegularCounter())\
			(time_slot_key, units, tags, labels, is_qaed, qa_score, errors)
	def generate_subtotals(self):
		by_user = {}
		for (_, userId, workIntervalId), counter in\
				self.per_user_per_interval.iteritems():
			by_user.setdefault((self.subTask.subTaskId, userId, None),
				[]).append(counter)

		self.per_user.clear()
		for key, counters in by_user.iteritems():
			user_subtotal = SubtotalCounter(counters)
			self.per_user[key] = user_subtotal

		user_subtotals = self.per_user.values()
		self.sub_task_stats = SubtotalCounter(user_subtotals)

	def save_stats(self):
		# update dailysubtasktotals
		SS.bind.execute(m.DailySubtotal.__table__.\
				delete(m.DailySubtotal.subTaskId==self.subTask.subTaskId))
		for (subTaskId, userId, workDate), c in\
				self.per_user_per_day.iteritems():
			entry = m.DailySubtotal(subTaskId=subTaskId, userId=userId,
				totalDate=workDate, amount=c.itemCount, words=c.unitCount)
			SS.add(entry)

		# update subtaskmetrics/abnormalusage/subtaskmetricerrors
		# TODO: optionally delete existing entries from above 3 tables
		# TODO: configure server_default for lastUpdated
		now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
		for source in [self.per_user_per_interval, self.per_user]:
			for (subTaskId, userId, workIntervalId), c in source.iteritems():
				assert ((source == self.per_user_per_interval 
					and subTaskId is None) or (source == self.per_user
					and workIntervalId is None))
			
				metric = m.SubTaskMetric(userId=userId,
					workIntervalId=workIntervalId, subTaskId=subTaskId,
					itemCount=c.itemCount, unitCount=c.unitCount,
					workRate=c.workRate, accuracy=c.accuracy,
					lastUpdated=now)
				SS.add(metric)
				SS.flush()
				for errorTypeId, occurences in c.flaggedErrors.iteritems():
					entry = m.SubTaskMetricErrorEntry(
						metricId=metric.metricId,
						errorTypeId=errorTypeId,
						occurences=occurences)
					SS.add(entry)
				for tagId, degree in c.abnormalTagUsage.iteritems():
					entry = m.AbnormalUsageEntry(metricId=metric.metricId,
						tagId=tagId, labelId=None, degree=degree)
					SS.add(entry)
				for labelId, degree in c.abnormalLabelUsage.iteritems():
					entry = m.AbnormalUsageEntry(metricId=metric.metricId,
						tagId=None, labelId=labelId, degree=degree)
					SS.add(entry)

		# update subtasks
		self.subTask.meanAmount = self.sub_task_stats.meanAmount
		self.subTask.maxAmount = self.sub_task_stats.maxAmount
		self.subTask.accuracy = self.sub_task_stats.accuracy
		self.subTask.maxWorkRate = self.sub_task_stats.maxWorkRate
		self.subTask.medianWorkRate = self.sub_task_stats.medianWorkRate
	def __call__(self):
		self.count_work_entries()
		self.generate_subtotals()
		self.save_stats()


def update_task_report_metrics(task):
	if task.status in (m.Task.STATUS_ARCHIVED, m.Task.STATUS_CLOSED):
		return
	for subTask in task.subTasks:
		SubTaskStatistician(subTask)()


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
			update_task_report_metrics(task)
		except:
			log.info('task {} failed'.format(task.taskId))
			out = cStringIO.StringIO()
			traceback.print_exc(file=out)
			log.error(out.getvalue())
			SS.rollback()
			# break
		else:
			log.info('task {} succeeded'.format(task.taskId))
			# SS.commit()
			pass
