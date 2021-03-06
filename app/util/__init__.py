import os
import random
from collections import OrderedDict

from flask import url_for

from app.i18n import get_text as _
import db.model as m
from db.model import BatchingMode
from db.db import SS
from .converter import Converter
from .extractor import Extractor
from .selector  import Selector
from .filehandler import get_handler
from .agent import tiger, go, edm
from .logistics import logistics

def split_by_size(seq, size):
	if not size >= 1:
		raise ValueError('size must be greater than or equal to 1')
	return [seq[offset:offset+size] for offset in range(0, len(seq), size)]


class _batcher(object):

	@classmethod
	def _get_key_gen(cls, batching_mode, page_size):

		key_gen = None
		order_by = None

		# no context
		if batching_mode == m.BatchingMode.NONE:
			key_gen = lambda i, x: (None, i / page_size)

		# allocation context
		elif batching_mode == m.BatchingMode.ALLOCATION_CONTEXT:
			key_gen = lambda i, x: x.allocationContext

		# file
		elif batching_mode == BatchingMode.FILE:
			key_gen = lambda index, raw_piece: raw_piece.data["filePath"]
			order_by = lambda raw_piece: raw_piece.data.get("startAt")

		# performance
		elif batching_mode == BatchingMode.PERFORMANCE:
			key_gen = lambda index, raw_piece: raw_piece.data["performance"]["id"]
			order_by = lambda raw_piece: (raw_piece.data["filePath"], raw_piece.data.get("startAt"))

		# custom
		elif batching_mode == BatchingMode.CUSTOM_CONTEXT:
			raise NotImplementedError #TODO

		# folder
		elif batching_mode == BatchingMode.FOLDER:
			key_gen = lambda index, raw_piece: os.path.dirname(raw_piece.data["filePath"])
			order_by = lambda raw_piece: (raw_piece.data["filePath"], raw_piece.data.get("startAt"))

		# unknown
		else:
			raise RuntimeError(_('unknown batching mode {0}'
				).format(batching_mode))

		assert key_gen
		return key_gen, order_by

	@classmethod
	def _group_into_batches(cls, rawPieces, key_gen, order_by):
		# group raw pieces into batches
		loads = OrderedDict()
		for i, rawPiece in enumerate(rawPieces):
			key = key_gen(i, rawPiece)
			loads.setdefault(key, []).append(rawPiece)

		# apply batch ordering if required
		if order_by is not None:
			for key, batch_raw_pieces in loads.items():
				batch_raw_pieces = sorted(batch_raw_pieces, key=order_by)
				loads[key] = batch_raw_pieces

		return loads

	@classmethod
	def _create_work_batches(cls, subTask, rawPieces, priority):

		key_gen, order_by = cls._get_key_gen(subTask.batchingMode, subTask.maxPageSize)
		loads = cls._group_into_batches(rawPieces, key_gen, order_by)

		# create batches
		batches = []
		
		for key, batch_load in loads.iteritems():

			if isinstance(key, tuple):
				name = key[0]
			else:
				name = key

			b = m.Batch(
				taskId=subTask.taskId,
				subTaskId=subTask.subTaskId,
				priority=priority,
				name=name
			)

			for pageIndex, page_load in enumerate(split_by_size(batch_load, subTask.maxPageSize)):
				p = m.Page(pageIndex=pageIndex)
				b.pages.append(p)

				for memberIndex, rawPiece in enumerate(page_load):
					memberEntry = m.PageMemberEntry(memberIndex=memberIndex)
					memberEntry.rawPieceId = rawPiece.rawPieceId
					p.memberEntries.append(memberEntry)

			batches.append(b)

		return batches

	@staticmethod
	def _create_qa_batches(subTask, workEntries, priority):
		raise NotImplementedError

	@staticmethod
	def _create_rework_batches(subTask, rawPieceIds, priority):
		key_gen = lambda i, x: (None, i / subTask.maxPageSize)

		loads = OrderedDict()
		for i, rawPieceId in enumerate(rawPieceIds):
			loads.setdefault(key_gen(i, None), []).append(rawPieceId)

		batches = []
		for batch_load in loads.values():
			b = m.Batch(taskId=subTask.taskId,
				subTaskId=subTask.subTaskId, priority=priority)
			for pageIndex, page_load in enumerate(split_by_size(
					batch_load, subTask.maxPageSize)):
				p = m.Page(pageIndex=pageIndex)
				b.pages.append(p)
				for memberIndex, rawPieceId in enumerate(page_load):
					memberEntry = m.PageMemberEntry(memberIndex=memberIndex)
					memberEntry.rawPieceId = rawPieceId
					p.memberEntries.append(memberEntry)
			batches.append(b)
		return batches


class Batcher(object):

	@staticmethod
	def batch(subTask, things, priority=5):
		if subTask.workType == m.WorkType.WORK:
			return _batcher._create_work_batches(subTask, things, priority)
		elif subTask.workType == m.WorkType.QA:
			return _batcher._create_qa_batches(subTask, things, priority)
		elif subTask.workType in (m.WorkType.REWORK, m.WorkType.TRANSCRIPTION_SOURCE):
			return _batcher._create_rework_batches(subTask, things, priority)
		else:
			raise RuntimeError(_('work type not supported {0}'
				).format(subTask.workType))

	@staticmethod
	def route(batch_router, raw_pieces, priority=5):

		# get routed sub tasks
		sub_tasks = [s.sub_task for s in batch_router.sub_tasks]
		assert sub_tasks

		# check consistent batching mode and get page size
		batching_mode = sub_tasks[0].batchingMode
		page_size = None	# this will only be used for None batching mode

		for sub_task in sub_tasks:
			if sub_task.batchingMode != batching_mode:
				raise ValueError("inconsistent batching modes")

			if page_size is None:
				page_size = sub_task.maxPageSize
			else:
				page_size = min(page_size, sub_task.maxPageSize)

		key_gen, order_by = _batcher._get_key_gen(batching_mode, page_size)
		loads = _batcher._group_into_batches(raw_pieces, key_gen, order_by)

		batches = []
		
		for key, batch_load in loads.iteritems():

			if isinstance(key, tuple):
				name = key[0]
			else:
				name = key

			sub_task = batch_router.get_routed_sub_task(key)

			b = m.Batch(
				taskId=sub_task.taskId,
				subTaskId=sub_task.subTaskId,
				priority=priority,
				name=name
			)

			for pageIndex, page_load in enumerate(split_by_size(batch_load, sub_task.maxPageSize)):
				p = m.Page(pageIndex=pageIndex)
				b.pages.append(p)

				for memberIndex, rawPiece in enumerate(page_load):
					memberEntry = m.PageMemberEntry(memberIndex=memberIndex)
					memberEntry.rawPieceId = rawPiece.rawPieceId
					p.memberEntries.append(memberEntry)

			batches.append(b)

		return batches


class Loader(object):
	@staticmethod
	def load(handler, task, dataFile, **options):
		fileHandler = get_handler(handler.name)
		itemDicts = fileHandler.load_data(dataFile, **options)
		rawPieces = [m.RawPiece(**d) for d in itemDicts]
		# TODO: (optional) save input data file somewhere for future reference
		return rawPieces


class Warnings(dict):
	CRITICAL = 'Critical'
	NON_CRITICAL = 'Non-Critical'
	NOTES = 'Notes'
	def critical(self, message):
		self.setdefault(self.CRITICAL, []).append(message)
	def non_critical(self, message):
		self.setdefault(self.NON_CRITICAL, []).append(message)
	def notes(self, message):
		self.setdefault(self.NOTES, []).append(message)


class Filterable(list):
	def __init__(self, iterable=[]):
		list.__init__(self, iterable)
	def __or__(self, func):
		if not callable(func):
			raise TypeError, 'func must be callable'
		return Filterable(filter(func, self))


class TestManager(object):
	@staticmethod
	def report_eligibility(test, user, *args, **kwargs):
		is_eligible = True

		if not is_eligible:
			return None

		d = OrderedDict()
		d['url'] = url_for('views.start_or_resume_test',
			testId=test.testId, _external=True)
		d['language'] = test.description
		d['name'] = test.name

		lastSheet = m.Sheet.query.filter_by(testId=test.testId
			).filter_by(userId=user.userId
			).order_by(m.Sheet.nTimes.desc()).first()

		if lastSheet:
			if lastSheet.status == m.Sheet.STATUS_FINISHED:
				d['completed'] = 'at {0}'.format(
					lastSheet.tFinishedAt.strftime('%H:%M:%S on %y-%m-%d'))
				if lastSheet.score is None:
					d['delayed'] = True
					del d['url']
				else:
					d['marked'] = True
					if lastSheet.score >= test.passingScore:
						d['passed'] = True
					else:
						d['failed'] = True
					d['score'] = lastSheet.score
					if not lastSheet.moreAttempts:
						del d['url']
		return d
	@staticmethod
	def generate_questions(test):
		pool = m.Pool.query.get(test.poolId)
		if test.testType == 'static':
			questions = pool.questions[:]
		else:
			# dynamic
			questions = random.sample(pool.questions, test.size)
		return questions


class PolicyChecker(object):
	@staticmethod
	def check_get_policy(subTask, user):
		if subTask.getPolicy == m.SubTask.POLICY_NO_LIMIT:
			return None
		elif subTask.getPolicy == m.SubTask.POLICY_ONE_ONLY:
			# check if user has submitted any batch
			q = SS.query(m.WorkEntry.batchId.distinct()
				).filter(m.WorkEntry.subTaskId==subTask.subTaskId
				).filter(m.WorkEntry.userId==user.userId
				).filter(m.WorkEntry.batchId.notin_(
					SS.query(m.Batch.batchId
						).filter(m.Batch.subTaskId==subTask.subTaskId)))
			if q.count() > 0:
				return _('user has done work on this sub task before').format()
		# return _('unknown policy \'{0}\' of sub task {1}'
		# 	).format(subTask.getPolicy, subTask.subTaskId)
		return None

