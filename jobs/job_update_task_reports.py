
import logging
import cStringIO
import traceback
import os
import datetime
import json

import numpy
import pytz
from jinja2 import Environment, FileSystemLoader

from LRUtilities.Audio import AudioSpec, AudioDataPointer
from db.db import SS
import db.model as m
from db.model import TaskType
from app.util import logistics
from .job_update_task_report_metrics import RegularCounter, SubtotalCounter


log = logging.getLogger(__name__)


def encode_regular_counter(obj):
	if isinstance(obj, RegularCounter):
		return dict(
			itemCount=obj.itemCount,
			unitCount=obj.unitCount,
			qaedItemCount=obj.qaedItemCount,
			qaedUnitCount=obj.qaedUnitCount,
			totalQaScore=obj.totalQaScore,
			workRate=obj.workRate,
			accuracy=obj.accuracy,
			flaggedErrors=obj.flaggedErrors,
			abnormalTagUsage=obj.abnormalTagUsage,
			abnormalLabelUsage=obj.abnormalLabelUsage,
		)
	return json.JSONEncoder.default(self, obj)


class ReportWorker(object):

	UTT_DURATION_BINS = 10

	def __init__(self, task):
		self.task = task
		self.per_user = {}
		self.overall = None
		self.tag_stats = {}
		self.label_stats = {}
		self.labels = []
		self.taskErrorTypeById = {}
		self.error_stats = {}
		self.error_classes = []
		self.qaer_data = {}
		self.timestamp = None
	def iter_work_entries(self):
		# NOTE: search condition is different from a similar query
		# in job_update_task_report_metrics, the latter is done on
		# sub task level while this one is done on task level
		entries = m.WorkEntry.query.filter(
				m.WorkEntry.taskId==self.task.taskId
			).filter(m.WorkEntry.workType.in_(
				[m.WorkType.WORK, m.WorkType.REWORK])
			).distinct(m.WorkEntry.batchId,
				m.WorkEntry.pageId, m.WorkEntry.rawPieceId
			).order_by(
				m.WorkEntry.batchId, m.WorkEntry.pageId,
				m.WorkEntry.rawPieceId, m.WorkEntry.created.desc()
			).all()
		for entry in entries:
			qa_record = m.QaTypeEntry.query.filter(
					m.QaTypeEntry.qaedEntryId==entry.entryId
				).order_by(m.QaTypeEntry.created.desc()
				).first()
			yield (entry, qa_record)
	def iter_error_classes(self):
		for i in self.error_classes:
			yield i
	def count_work_entries(self):
		for entry, qa_record in self.iter_work_entries():
			subTaskId = entry.subTaskId
			userId = entry.userId
			time_slot_key = entry.timeSlotKey
			units = entry.rawPiece.words
			tags = entry.tags
			labels = entry.labels
			if qa_record is not None:
				is_qaed = True
				qa_score = qa_record.qaScore
				errors = qa_record.errors
				self.qaer_data.setdefault(qa_record.userId, []
					).append(qa_record)
			else:
				is_qaed = False
				qa_score = 0
				errors = []
			self.per_user.setdefault(userId, RegularCounter())(time_slot_key,
				units, tags, labels, is_qaed, qa_score, errors)

	def get_utt_duration_stats(self):
		"""
		Returns the utterance duration stats
		for a transcription task.
		"""
		log.info("generating utt duration stats for: {0}".format(self.task.task_id))

		data = {}
		overall_durations = []
		transcribed_durations = []
		untranscribed_durations = []

		log.debug("# raw pieces: {0}".format(len(self.task.raw_pieces)))
		for utt in self.task.raw_pieces:
			start_at = utt.data.get("startAt")
			end_at = utt.data.get("endAt")
			audio_spec = AudioSpec(**utt.data["audioSpec"])
			audio_data_pointer = AudioDataPointer(**utt.data["audioDataPointer"])
			file_duration = audio_spec.get_duration(audio_data_pointer.size)

			# start offset or 0
			if start_at is None:
				start_at = datetime.timedelta(seconds=0)
			else:
				start_at = datetime.timedelta(seconds=float(start_at))

			# end offset or file duration
			if end_at is None:
				end_at = file_duration
			else:
				end_at = datetime.timedelta(seconds=float(end_at))

			duration = (end_at - start_at).total_seconds()

			# add to duration lists
			overall_durations.append(duration)

			if utt.isNew:
				untranscribed_durations.append(duration)
			else:
				transcribed_durations.append(duration)

		log.debug("# overall: {0}".format(len(overall_durations)))
		log.debug("# untranscribed: {0}".format(len(untranscribed_durations)))
		log.debug("# transcribed: {0}".format(len(transcribed_durations)))
		
		# order durations for analysis
		overall_durations.sort()
		untranscribed_durations.sort()
		transcribed_durations.sort()

		# report sections
		sections = [
			("overall", overall_durations),
			("transcribed", transcribed_durations),
			("untranscribed", untranscribed_durations),
		]

		# calculate stats for each section
		for key, durations in sections:
			log.info("calculating stats for {0}".format(key))
			section_data = {}

			section_data["count"] = len(durations)
			if durations:
				section_data["totalDuration"] = sum(durations)
				section_data["minDuration"] = durations[0]
				section_data["maxDuration"] = durations[-1]
				section_data["meanDuration"] = float(numpy.mean(durations))
				section_data["medianDuration"] = float(numpy.median(durations))
				section_data["stdDev"] = float(numpy.std(durations))
				section_data["distribution"] = self.get_utt_duration_distribution(durations)

			data[key] = section_data
		
		log.debug("report data: {0}".format(data))
		return data

	def get_utt_duration_distribution(self, durations):
		"""
		Return the distribution counts for
		the given durations in UTT_DURATION_BINS
		number of bins. Assumes the durations
		list is ordered and non-empty.
		"""

		# define bin width
		min_duration = durations[0]
		max_duration = durations[-1]

		bin_width = (max_duration - min_duration) / self.UTT_DURATION_BINS

		current_bin = min_duration + bin_width
		count = 0
		distribution = []

		for duration in durations:

			# reach bin limit, update current bin
			if duration > current_bin:
				distribution.append(count)
				current_bin += bin_width
				count = 1

			# within current bin
			else:
				count += 1

		# add last bin count
		distribution.append(count)

		return distribution

	def add_task_stats(self, key, data):
		"""
		Add data to task stats.
		"""
		if self.task.stats is None:
			self.task.stats = {}

		self.task.stats[key] = data

	def run_stats(self):

		# utt duration stats
		if self.task.is_type(TaskType.TRANSCRIPTION):
			utt_duration_stats = self.get_utt_duration_stats()
			self.task.update_stats({"uttDurationReport": utt_duration_stats})

		if not self.per_user:
			return
		self.timestamp = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

		user_counters = self.per_user.values()
		self.overall = overall = SubtotalCounter(user_counters)
		overall.check_usage()

		error_classes = set()
		for i in self.task.taskErrorTypes:
			self.taskErrorTypeById.setdefault(i.errorTypeId, i)
			error_classes.add(i.errorClass)
		self.error_classes = list(error_classes)

		# populate error_stats
		for userId, c in self.per_user.iteritems():
			self.error_stats[userId] = user_stats = {}
			# print userId
			for errorTypeId in c.flaggedErrors:
				errorClass = self.taskErrorTypeById[errorTypeId].errorClass
				user_stats[errorClass] = user_stats.setdefault(errorClass, 0) + c.flaggedErrors[errorTypeId]
			user_stats[None] = sum(c.flaggedErrors.values())
		# print self.error_stats

		if self.task.tagSet:
			self.tag_stats.clear()
			for t in self.task.tagSet.tags:
				tagId = t.tagId
				usage = [c.get_tag_rate(tagId) for c in user_counters]
				self.tag_stats[tagId] = {
					'tagId': tagId,
					'total': overall.usedTags.get(tagId, 0),
					'overall_chance': overall.usedTags.get(tagId, 0) / overall.itemCount,
					'avg_usage': numpy.mean(usage),
					'median_usage': numpy.median(usage),
					'std': numpy.std(usage)
				}
				# print 'tag:', self.tag_stats[tagId]
		if self.task.labelSet:
			self.labels = labels = [l for lg in self.task.labelSet.labelGroups for l in lg.labels]
			self.labels.extend([l for l in self.task.labelSet.ungroupedLabels])
			self.label_stats = {}
			for l in labels:
				labelId = l.labelId
				usage = [c.get_label_rate(labelId) for c in user_counters]
				self.label_stats[labelId] = {
					'labelId': labelId,
					'total': overall.usedLabels.get(labelId, 0),
					'overall_chance': overall.usedLabels.get(labelId, 0) / overall.itemCount,
					'avg_usage': numpy.mean(usage),
					'median_usage': numpy.median(usage),
					'std': numpy.std(usage)
				}
				# print 'label:', self.label_stats[labelId]

		# populate qaer_stats
		self.qaer_stats = {}
		now = self.timestamp
		m1 = now - datetime.timedelta(days=7)
		m2 = now - datetime.timedelta(days=1)
		for qaerUserId, qa_records in self.qaer_data.iteritems():
			prev_week = [] #i for i in qa_records if i.created >= m1]
			prev_day = [] #i for i in qa_records if i.created >= m2]
			good0 = [] #i for i in qa_records if len(i.errors) == 0]
			good1 = [] #i for i in prev_week if len(i.errors) == 0]
			good2 = [] #i for i in prev_day if len(i.errors) == 0]
			histogram = {}
			for i in qa_records:
				no_error = len(i.errors) == 0
				if no_error:
					good0.append(i)
				if i.created >= m1:
					prev_week.append(i)
					if no_error:
						good1.append(i)
				if i.created >= m2:
					prev_day.append(i)
					if no_error:
						good1.append(i)
				for errorTypeId in i.errors:
					histogram[errorTypeId] = histogram.get(errorTypeId, 0) + 1
			bad0 = len(qa_records) - len(good0)
			bad1 = len(prev_week) - len(good1)
			bad2 = len(prev_day) - len(good2)
			self.qaer_stats[qaerUserId] = dict(
				qaedCount=len(qa_records),
				qaedWithErrorCount=len(good0),
				qaedWithoutErrorCount=bad0,
				qaedCountPreviousWeek=len(prev_week),
				qaedWithErrorCountPreviousWeek=len(good1),
				qaedWithoutErrorCountPreviousWeek=bad1,
				qaedCountPreviousDay=len(prev_day),
				qaedWithErrorCountPreviousDay=len(good2),
				qaedWithoutErrorCountPreviousDay=bad2,
				histogram=histogram,
			)
	def generate_report(self):
		task = self.task
		if not self.per_user:
			return

		# print 'update task reports', self.task.taskId

		_dir = os.path.dirname(__file__)
		env = Environment(loader=FileSystemLoader(_dir, followlinks=True),
			trim_blocks=True, lstrip_blocks=True)
		# env.filters['formatDateTime'] = lambda t: t.strftime('%Y-%m-%d %H:%M:%S')

		for report_name in ['qa_progress_report', 'qa_error_class_report',
				'tag_usage_report', 'label_usage_report']:
			template = env.get_template(report_name + '.template')
			data = template.render(task=self.task, datetime=datetime,
				data=self).encode('utf-8')
			relpath = 'tasks/{0}/reports/{1}.html'.format(task.taskId, report_name)
			logistics.save_file(relpath, data)

		now = self.timestamp
		fp = cStringIO.StringIO()
		json.dump({
			'timestamp': now.strftime('%Y-%m-%dT%H:%M:%S%z'),
			'tag_stats': self.tag_stats,
			'label_stats': self.label_stats,
			'error_stats': self.error_stats,
			'per_user': dict([(userId, encode_regular_counter(c)) for
					userId, c in self.per_user.iteritems()]),
			'qaer_stats': self.qaer_stats,
		}, fp, indent=2)
		relpath = 'tasks/{0}/reports/report_stats.json'.format(task.taskId)
		logistics.save_file(relpath, fp.getvalue())
		fp.close()

	def __call__(self):
		self.count_work_entries()
		self.run_stats()
		self.generate_report()


def update_task_reports(task):
	ReportWorker(task)()


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
			# log.info('task {} succeeded'.format(task.taskId))
			SS.commit()
			pass
