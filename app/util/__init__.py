
import random
import os
import hashlib
from collections import OrderedDict

from flask import url_for
import requests

from app.i18n import get_text as _
import db.model as m
from db.db import SS
from .converter import Converter
from .extractor import Extractor
from .selector  import Selector
from .filehandler import get_handler

def split_by_size(seq, size):
	if not size >= 1:
		raise ValueError('size must be greater than or equal to 1')
	return [seq[offset:offset+size] for offset in range(0, len(seq), size)]


class _batcher(object):
	@staticmethod
	def _create_work_batches(subTask, rawPieces, priority):
		if subTask.batchingMode == m.BatchingMode.NONE:
			key_gen = lambda i, x: (None, i / subTask.maxPageSize)
		elif subTaks.batchingMode == m.BatchingMode.ALLOCATION_CONTEXT:
			key_gen = lambda i, x: x
		else:
			raise RuntimeError(_('unsupported batching mode {0}'
				).format(subTask.batchingMode))

		loads = OrderedDict()
		for i, rawPiece in enumerate(rawPieces):
			loads.setdefault(key_gen(i, rawPiece.allocationContext), []
				).append(rawPiece.rawPieceId)

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
		elif subTask.workType == m.WorkType.REWORK:
			return _batcher._create_rework_batches(subTask, things, priority)
		else:
			raise RuntimeError(_('work type not supported {0}'
				).format(subTask.workType))


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


class TigerAgent(object):
	def __init__(self, url_root, secret):
		self.url_root = url_root
		self.secret = secret
	def get_url_root(self):
		return self.url_root
	def get_task_workers(self, task):
		server_path = '/projects/{0}/workers'.format(task.globalProjectId)
		url = os.path.join(self.url_root, server_path.lstrip('/'))
		canonical_string = url + self.secret
		token = hashlib.md5(canonical_string).hexdigest()
		try:
			resp = requests.get(url, headers={'authorization': token})
			if resp.status_code == 200:
				result = resp.json()['workers']
			else:
				result = None
		except Exception, e:
			result = None
		return result
	def get_task_supervisors(self, task):
		server_path = '/projects/{0}/supervisors'.format(task.globalProjectId)
		url = os.path.join(self.url_root, server_path.lstrip('/'))
		canonical_string = url + self.secret
		token = hashlib.md5(canonical_string).hexdigest()
		try:
			resp = requests.get(url, headers={'authorization': token})
			if resp.status_code == 200:
				result = resp.json()['supervisors']
			else:
				result = None
		except Exception, e:
			result = None
		return result


class GoAgent(object):
	def __init__(self, url_root):
		self.url_root = url_root
	def get_url_root(self):
		return self.url_root
	def check_token_for_user(self, global_id):
		server_path = '/auth/validate_token/{}'.format(global_id)
		url = os.path.join(self.url_root, server_path.lstrip('/'))
		try:
			resp = requests.get(url)
			if resp.status_code == 200:
				result = resp.json()
				if 'token' not in result or 'error' in result:
					raise RuntimeError('token validation failed')
		except:
			result = None
		return result


class EdmAgent(object):
	def __init__(self, url_root, secret):
		self.url_root = url_root
		self.secret = secret
	def get_url_root(self):
		return self.url_root
	def get_user(self, global_id):
		server_path = '/api/edm_people/{}'.format(global_id)
		url = os.path.join(self.url_root, server_path.lstrip('/'))
		canonical_string = url + self.secret
		token = hashlib.md5(canonical_string).hexdigest()
		try:
			resp = requests.get(url, headers={'authorization': token})
			if resp.status_code == 200:
				result = resp.json()
			else:
				result = None
		except Exception, e:
			result = None
		return result


tiger = TigerAgent(os.environ['TIGER_URL'], os.environ['APPEN_API_SECRET_KEY'])
go = GoAgent(os.environ['GO_URL'])
edm = EdmAgent(os.environ['EDM_URL'], os.environ['APPEN_API_SECRET_KEY'])
