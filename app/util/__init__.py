
import random
import os
import hashlib
import json
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
	def __init__(self, url_root, secret):
		self.url_root = url_root
		self.secret = secret
	def get_url_root(self):
		return self.url_root
	def check_token_for_user(self, global_id):
		server_path = '/auth/validate_token/{}'.format(global_id)
		url = os.path.join(self.url_root, server_path.lstrip('/'))
		canonical_string = url + self.secret
		token = hashlib.md5(canonical_string).hexdigest()
		try:
			resp = requests.get(url, headers={'authorization': token})
			if resp.status_code == 200:
				result = resp.json()
				if 'token' not in result or 'error' in result:
					raise RuntimeError('token validation failed')
		except:
			result = None
		return result


class EdmAgent(object):
	ATTR_MAP = {
		'Person': {
			'primary_email_email_address': 'emailAddress',
			'family_name': 'familyName',
			'given_name': 'givenName',
			# 'mobile_phone_phone_number': None,
			# 'street_address_address1': None,
			# 'street_address_country': None,
			# 'nationality_country_id': None,
			# 'salutation': None,
			# 'street_address_city': None,
		},
		'Country': {
			'name_eng': 'name',
			'iso2': 'iso2',
			'iso3': 'iso3',
			'iso_num': 'isoNum',
			'internet': 'internet',
			'active': 'active'
		},
		'Language': {
			'name_eng': 'name',
			'iso2': 'iso2',
			'iso3': 'iso3',
			'active': 'active'
		}
	}
	def __init__(self, url_root, secret):
		self.url_root = url_root
		self.secret = secret
	def get_url_root(self):
		return self.url_root
	def get_country(self, iso3):
		server_path = '/api/edm_countries/{}'.format(iso3)
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
	def get_language(self, iso3):
		server_path = '/api/edm_languages/{}'.format(iso3)
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
	def get_user_data(self, global_id):
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
	def make_new_user(self, global_id):
		result = self.get_user_data(global_id)
		data = dict(
			familyName=result['family_name'],
			givenName=result['given_name'],
			emailAddress=result['primary_email_email_address'],
			globalId=result['global_id'],
		)
		user = m.User(**data)
		return user
	def decode_changes(self, entity, changes):
		lookup = self.ATTR_MAP[entity]
		data = {}
		for c in changes:
			if 'attribute_name' in c:
				key = lookup.get(c['attribute_name'])
				if key:
					data[key] = c['after_value']
			elif 'jkvp' in c:
				for cc in c['jkvp']:
					attr = cc.get('attribute_name', None)
					key = lookup.get(attr, None)
					if key:
						data[key] = cc['after_value']
			else:
				# unknown format, ignore it
				continue
		return data


class PdbAgent(object):
	token = None
	def __init__(self, url_root, api_key, api_secret):
		self.url_root = url_root
		self.api_key = api_key
		self.api_secret = api_secret
	def update_token(self):
		url = os.path.join(self.url_root, '/login'.lstrip('/'))
		resp = requests.post(url, headers={'Content-Type': 'application/json'},
			data=json.dumps({'apiKey': self.api_key, 'apiSecret': self.api_secret}))
		if resp.status_code == 200:
			try:
				self.token = resp.json()
			except:
				pass
	def get_project(self, projectId):
		if self.token is None:
			self.update_token()
		if self.token:
			server_path = '/api/v1/projects/{}'.format(projectId)
			url = os.path.join(self.url_root, server_path.lstrip('/'))
			resp = requests.get(url, headers={'Authorization': self.token['accessToken']})
			if resp.status_code == 200:
				data = resp.json()
				return data['result']
	def get_task(self, taskId):
		if self.token is None:
			self.update_token()
		if self.token:
			server_path = '/api/v1/tasks/{}'.format(taskId)
			url = os.path.join(self.url_root, server_path.lstrip('/'))
			resp = requests.get(url, headers={'Authorization': self.token['accessToken']})
			if resp.status_code == 200:
				data = resp.json()
				return data['result']


tiger = TigerAgent(os.environ['TIGER_URL'], os.environ['APPEN_API_SECRET_KEY'])
go = GoAgent(os.environ['GO_URL'], os.environ['APPEN_API_SECRET_KEY'])
edm = EdmAgent(os.environ['EDM_URL'], os.environ['APPEN_API_SECRET_KEY'])
pdb = PdbAgent(os.environ['PDB_API_URL'], os.environ['PDB_API_KEY'], os.environ['PDB_API_SECRET'])
