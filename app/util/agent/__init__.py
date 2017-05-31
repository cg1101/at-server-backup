
import functools
import json
import os
import hashlib
import random
import string
from collections import OrderedDict

import requests
import jmespath
from lxml import etree

import db.model as m


class JsonObject(dict):
	def __new__(cls, *args, **kwargs):
		return dict.__new__(cls, *args, **kwargs)
	@classmethod
	def load(cls, json_data):
		return json.loads(json_data, object_hook=JsonObject)
	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError, e:
			raise AttributeError(key)


class AppAgent(object):
	@staticmethod
	def api_auth(url_template, query=None):
		def customized_decorator(fn):
			@functools.wraps(fn)
			def decorated(self, *args):
				server_path = url_template.format(*args)
				url = os.path.join(self.url_root, server_path.lstrip('/'))
				canonical_string = url + self.secret
				api_token = hashlib.md5(canonical_string).hexdigest()
				try:
					resp = requests.get(url, headers={'authorization':
						api_token})
					if resp.status_code != 200:
						resp.raise_for_status()
					result = JsonObject.load(resp.text)
					if query is not None:
						try:
							result = jmespath.search(query, result)
						except:
							raise RuntimeError('error getting {} from {}'.\
								format(query, resp.text))
				except requests.exceptions.ConnectionError, e:
					raise RuntimeError('connection error: {}'.format(e))
				except requests.exceptions.HTTPError, e:
					raise RuntimeError('http error: {}'.format(e))
				except requests.exceptions.Timeout, e:
					raise RuntimeError('timeout: {}'.format(e))
				except requests.exceptions.TooManyRedirects, e:
					raise RuntimeError('too many redirects: {}'.format(e))
				except requests.exceptions.RequestException, e:
					raise RuntimeError('other request exception: {}'.\
						format(e))
				return result
			return decorated
		return customized_decorator
	def __init__(self, url_root, secret):
		self.url_root = url_root
		self.secret = secret
	def get_url_root(self):
		return self.url_root


class TigerAgent(AppAgent):
	GUEST = 'guest'
	WORKER1 = 'worker1'
	WORKER2 = 'worker2'
	WORKER3 = 'worker3'
	WORKER4 = 'worker4'
	CLIENT = 'client'
	FINANCE = 'finance'
	PROJECT_MANAGER = 'project_manager'
	TENANT_ADMIN = 'tenant_admin'
	SYS_ADMIN = 'sys_admin'
	ROLE_CAPS_MAP = {
		GUEST: [],
		WORKER1: [],
		WORKER2: [],
		WORKER3: [],
		WORKER4: [],
		CLIENT: [],
		FINANCE: [],
		PROJECT_MANAGER: ['admin'],
		TENANT_ADMIN: ['admin'],
		SYS_ADMIN: ['admin'],
	}
	@AppAgent.api_auth('/projects/{0}/workers', 'workers')
	def get_task_workers(self, global_project_id):
		pass
	@AppAgent.api_auth('/projects/{0}/supervisors', 'supervisors')
	def get_task_supervisors(self, global_project_id):
		pass
	@AppAgent.api_auth('/project_users/{0}/roles')
	def get_user_roles(self, appen_id):
		pass
	def role2caps(self, global_user_role):
		return self.ROLE_CAPS_MAP.get(global_user_role, [])


class GoAgent(AppAgent):
	@AppAgent.api_auth('/auth/validate_token/{0}')
	def check_token_for_user(self, global_id):
		pass


class EdmAgent(AppAgent):
	ATTR_MAP = {
		'Person': {
			'primary_email_email_address': 'emailAddress',
			'family_name': 'familyName',
			'given_name': 'givenName',
			# 'mobile_phone_phone_number': None,
			# 'street_address_address1': None,
			# 'street_address_country': None,
			'nationality_country_id': 'countryId',
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
	@AppAgent.api_auth('/api/edm_countries/{0}')
	def get_country(self, iso3):
		pass
	@AppAgent.api_auth('/api/edm_languages/{0}')
	def get_language(self, iso3):
		pass
	@AppAgent.api_auth('/api/edm_people/{}')
	def get_user_data(self, global_id):
		pass
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
	def __init__(self, url_root, api_key, api_secret):
		self.url_root = url_root
		self.api_key = api_key
		self.api_secret = api_secret
		self.token = None
	def update_token(self):
		url = os.path.join(self.url_root, '/login'.lstrip('/'))
		resp = requests.post(url,
			headers={'Content-Type': 'application/json'},
			data=json.dumps({'apiKey': self.api_key, 'apiSecret': self.api_secret}))
		if resp.status_code == 200:
			try:
				self.token = resp.json()
			except Exception, e:
				# TODO: log this error
				pass
		else:
			# TODO: log this error
			pass
	def get_project(self, projectId):
		if self.token is None:
			self.update_token()
		if self.token:
			server_path = '/api/v1/projects/{}'.format(projectId)
			url = os.path.join(self.url_root, server_path.lstrip('/'))
			resp = requests.get(url, headers={'Authorization':
				self.token['accessToken']})
			if resp.status_code == 200:
				data = resp.json()
				return data['result']
	def get_task(self, taskId):
		if self.token is None:
			self.update_token()
		if self.token:
			server_path = '/api/v1/tasks/{}'.format(taskId)
			url = os.path.join(self.url_root, server_path.lstrip('/'))
			resp = requests.get(url, headers={'Authorization':
				self.token['accessToken']})
			if resp.status_code == 200:
				data = resp.json()
				return data['result']


class AppenOnlineAgent(object):
	PAYROLL_ATTR_MAP = {
		'status': 'status',
		'startdate': 'startDate',
		'enddate': 'endDate',
		'opened': 'opened',
		'migrated': 'migrated',
		'processing': 'processing',
		'paid': 'paid',
		'next': 'next',
		'closed': 'closed',
		'approved': 'approved',
		'name': 'name',
		'id': 'payrollId',
	}
	def __init__(self, url_root, api_secret):
		self.url_root = url_root
		self.api_secret = api_secret
	@classmethod
	def generate_salt(cls, length=5):
		return ''.join(random.choice(string.printable)
				for _ in xrange(length))
	def generate_key(self, salt):
		m = hashlib.sha512()
		m.update(self.api_secret)
		m.update(salt)
		return m.hexdigest()
	def generate_pair(self):
		salt = self.generate_salt()
		key = self.generate_key(salt)
		return (salt, key)
	def get_payroll(self):
		url = os.path.join(self.url_root, 'get_payrolls')
		salt, key = self.generate_pair()
		resp = requests.post(url, params={'salt': salt,
				'key': key, 'addPayroll': 'True'})
		if resp.status_code != 200:
			resp.raise_for_status()
		try:
			root = etree.XML(resp.text)
			entry = root.xpath('entry')[0]
			result = {}
			for i in entry.xpath('data'):
				name = i.attrib['name']
				type_ = i.attrib['type']
				key = self.PAYROLL_ATTR_MAP[name]
				if type_ == 'boolean':
					value = eval(i.attrib['value'])
				elif type_ == 'integer':
					value = int(i.attrib['value'])
				elif type_ == 'string':
					value = i.attrib['value']
				elif type_ == 'NoneType':
					assert i.attrib['value'] == ''
					value = None
				result[key] = value
		except Exception, e:
			raise RuntimeError('error decoding response: {}'.format(e))
		return result
	def send_payments(self, payments):
		if not payments:
			return
		# TODO: move code that compiles link to somewhere more appropriate
		app_root = os.environ['APP_ROOT_URL']

		task_by_id = {}
		for cp in payments:
			task_by_id.setdefault(cp.taskId, m.Task.query.get(cp.taskId))

		links = []
		supervisors = []
		for index, taskId in enumerate(sorted(task_by_id)):
			task = task_by_id[taskId]
			# TODO: use globalProjectId?
			links.append((taskId, '%s/#/tasks/%s' % (app_root, taskId)))
			for supervisor in task.supervisors:
				supervisors.append((taskId, supervisor.userId))

		data = OrderedDict()
		for index, (taskId, link) in enumerate(links):
			key = 'link_{}_{}'.format(taskId, index)
			data[key] = link
		for index, (taskId, userId) in enumerate(supervisors):
			key = 'supervisor_{}_{}'.format(taskId, index)
			data[key] = str(userId)
		for index, cp in enumerate(payments):
			p_item = cp.dump(cp, use='postage')
			try:
				assert p_item['units'] > 0
			except:
				raise RuntimeError('CalculatedPayment#{} has zero units')
			for attr, value in p_item.iteritems():
				key = 'payment_{}_{}'.format(attr, index)
				data[key] = value

		salt, key = self.generate_pair()

		data['salt'] = salt
		data['key'] = key
		data['_system'] = 'GNX'

		url = os.path.join(self.url_root, 'send_payments')
		resp = requests.post(url, data=data)
		if resp.status_code != 200:
			resp.raise_for_status()
		'''<root>
			<entry><original>1000152</original><receipt>163990</receipt></entry>
			<entry><original>1000153</original><receipt>163991</receipt></entry>
			<entry><original>1000154</original><receipt>163992</receipt></entry>
			<entry><original>1000155</original><receipt>163993</receipt></entry>
			<entry><original>1000156</original><receipt>163994</receipt></entry>
			<entry><original>1000157</original><receipt>163995</receipt></entry>
			<entry><original>1000158</original><receipt>163996</receipt></entry>
		</root>'''
		try:
			root = etree.XML(resp.text)
			if root.tag == 'error':
				raise RuntimeError('error: {}'.format(root.text))
			receipt_entries = root.xpath('entry')
			try:
				assert len(receipt_entries)
			except:
				raise RuntimeError('invalid response returned from server')
			receipts = {}
			for entry in receipt_entries:
				original, receipt = map(lambda x: int(x.text), entry)
				assert original not in receipts
				receipts[original] = receipt
		except Exception, e:
			raise RuntimeError('error decoding response:\n{}'.format(e))
		return receipts


assert os.environ['APP_ROOT_URL']

tiger = TigerAgent(os.environ['TIGER_URL'], os.environ['APPEN_API_SECRET_KEY'])
go = GoAgent(os.environ['GO_URL'], os.environ['APPEN_API_SECRET_KEY'])
edm = EdmAgent(os.environ['EDM_URL'], os.environ['APPEN_API_SECRET_KEY'])
pdb = PdbAgent(os.environ['PDB_API_URL'], os.environ['PDB_API_KEY'], os.environ['PDB_API_SECRET'])
ao = AppenOnlineAgent(os.environ['AO_WEB_SERVICES_URL'], os.environ['AO_WEB_SERVICES_KEY'])
