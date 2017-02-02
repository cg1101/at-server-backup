
import logging
import cStringIO
import traceback
import os
import datetime

import numpy
from jinja2 import Environment, FileSystemLoader

from db.db import SS
import db.model as m
from app.util import logistics
from .job_update_task_report_metrics import RegularCounter, SubtotalCounter


log = logging.getLogger(__name__)

class ReportWorker(object):
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
	def iter_work_entries(self):
		# NOTE: search condition is different from a similar query
		# in job_update_task_report_metrics, the latter is done on
		# sub task level while this one is done on task level
		entries = m.WorkEntry.query.\
				filter(m.WorkEntry.taskId==self.task.taskId).\
				filter(m.WorkEntry.workType.in_([m.WorkType.WORK, m.WorkType.REWORK])).\
				distinct(m.WorkEntry.batchId, m.WorkEntry.pageId,\
					m.WorkEntry.rawPieceId).\
				order_by(m.WorkEntry.batchId, m.WorkEntry.pageId,\
					m.WorkEntry.rawPieceId,\
					m.WorkEntry.created.desc()).\
				all()
		for entry in entries:
			qa_record = m.QaTypeEntry.query.\
				filter(m.QaTypeEntry.qaedEntryId==entry.entryId).\
				order_by(m.QaTypeEntry.created.desc()).\
				first()
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
			else:
				is_qaed = False
				qa_score = 0
				errors = []
			self.per_user.setdefault(userId, RegularCounter())(time_slot_key,
				units, tags, labels, is_qaed, qa_score, errors)
	def run_stats(self):
		if not self.per_user:
			return
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
			print userId
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