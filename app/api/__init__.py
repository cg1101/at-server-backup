#!/usr/bin/env python

import json
import cStringIO
import traceback
from functools import wraps
from types import NoneType, BooleanType, IntType, StringType, DictType

from flask import Response, request

from db.db import SS

def ajax(fn):
	@wraps(fn)
	def decorated(*args, **kwargs):
		'''
		always return result as json object
		'''
		resp = Response(mimetype='application/json')
		try:
			result = fn(*args, **kwargs)
		except Exception, e:
			# TODO: hide debug information for production deployment
			print '\033[1;31mERROR:\033[0m %r' % e
			resp.status_code = 500
			result = {'error': '%s' % e}
			# TODO: here or after_request?
			SS.rollback()
		else:
			SS.commit()
		resp.set_data(json.dumps(result, indent=2))
		# TODO:
		# return (resp, status, headers)
		return resp
	return decorated


def get_text(s):
	return s
_ = get_text


def caps(*caps):
	def customized_decorator(fn):
		@wraps(fn)
		def decorated(*args, **kwargs):
			if False:
				# TODO: check required capabilities here
				raise RuntimeError, _('user does not have required capabilities: {}').format(repr(caps))
			return fn(*args, **kwargs)
		return decorated
	return customized_decorator


def validate_input(input_spec):
	'''
	validate request input according to input_spec

	input_spec is a sequence of key specs, each has following fields:

	key
	mandatory
	default
	validator
	args
	kwargs
	'''
	data = request.get_json()
	if not data:
		try:
			data = request.values
		except Exception, e:
			out = cStringIO.StringIO()
			traceback.print_exc(file=out)
			print out.getvalue()
			raise RuntimeError, _('error parsing parameters: {0}').format(e)
	validated = {}
	for key, mandatory, default, validator, args, kwargs in input_spec:
		if data.has_key(key):
			value = data[key]
			try:
				if isinstance(validator, tuple):
					if value not in validator:
						raise ValueError, _('must be one of {0}, got \'{1}\'').format(validator, value)
				elif validator in (NoneType, BooleanType, IntType, StringType, DictType):
					if not isinstance(value, validator):
						raise ValueError, _('expected {0}, got {1}').format(
							validator.__name__, type(value).__name__)
				elif callable(validator):
					kwargs = dict([(k, data.get(k)) for k in kwargs])
					value = validator(data, key, value, *args, **kwargs)
			except ValueError, e:
				reason = '%s' % e
				raise RuntimeError, _('invalid parameter \'{0}\': {1}').format(key, reason)
			else:
				validated[key] = value
		elif mandatory:
			raise RuntimeError, _('must provide parameter \'{0}\'').format('name')
		else:
			if default != None:
				validated[key] = default
	return validated

class Spec(object):
	def __init__(self, name, mandatory=False, default=None, normalizer=None, validators=[]):
		if not isinstance(name, basestring):
			raise TypeError, 'name must be of string type'
		elif not name.strip():
			raise ValueError, 'name must not be blank'
		if normalizer is None:
			normalizer = lambda x: x
		elif not isinstance(normalizer, callable):
			raise TypeError, 'normalizer must be a callable'

		self.name = name
		self.mandatory = mandatory
		self.default = default
		self.normalizer = normalizer
		self.validators = validators
	def __call__(self, input, output, errors):
		if self.name in input:
			value = input[self.name]
		if not found and self.mandatory:
			errors[self.name] = 'mandatory parameter missing'

class Validator(object):
	def __init__(self, *args):
		self.input_spec = []
		for spec in args:
			if not isinstance(spec, Spec):
				raise TypeError, 'input spec must be instances of Spec'
			self.input_spec.append(i)
	def __call__(self, data):
		result = {}
		errors = {}
		for spec in self.input_spec:
			key, value, err = spec(data)
			if key:
				result[key] 
			if err:
				errors[spec.name] = err
		return result, errors



def v_mandatory(data, key):
	if key not in data:
		raise ValueError, _('mandatory parameter missing')


from v1_0 import api_1_0
