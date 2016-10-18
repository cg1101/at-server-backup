
import functools
import json
import os
import hashlib

import requests
import jmespath

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
					resp = requests.get(url, headers={'authorization': api_token})
					if resp.status_code != 200:
						resp.raise_for_status()
					result = JsonObject.load(resp.text)
					if query is not None:
						try:
							result = jmespath.search(query, result)
						except:
							raise RuntimeError('error getting {} from {}'.format(query, resp.text))
				except requests.exceptions.ConnectionError, e:
					raise RuntimeError('connection error: {}'.format(e))
				except requests.exceptions.HTTPError, e:
					raise RuntimeError('http error: {}'.format(e))
				except requests.exceptions.Timeout, e:
					raise RuntimeError('timeout: {}'.format(e))
				except requests.exceptions.TooManyRedirects, e:
					raise RuntimeError('too many redirects: {}'.format(e))
				except requests.exceptions.RequestException, e:
					raise RuntimeError('other request exception: {}'.format(e))
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
			data={'apiKey': self.api_key, 'apiSecret': self.api_secret})
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
