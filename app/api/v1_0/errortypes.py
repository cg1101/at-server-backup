
from flask import request, abort, session

import db.model as m
from db.db import SS
from app.api import api, caps, get_text as _
from . import api_1_0 as bp

_name = __file__.split('/')[-1].split('.')[0]

@bp.route(_name + '/', methods=['GET'])
@api
@caps()
def get_error_types():
	'''
	returns a list of error types
	'''
	errorTypes = m.ErrorType.query.order_by(m.ErrorType.errorTypeId).all()
	return {
		'errorTypes': m.ErrorType.dump(errorTypes),
	}

@bp.route(_name + '/', methods=['POST'])
@api
@caps()
def create_error_type():
	'''
	creates a new error type
	'''
	s = m.ErrorTypeSchema()
	data = request.get_json()
	if not data:
		try:
			data = s.load(request.values).data
		except Exception, e:
			raise RuntimeError, _('error parsing parameters: {0}').format(e)

	if not data.has_key('name'):
		raise RuntimeError, _('must provide parameter \'{0}\'').format('name')
	elif not isinstance(data['name'], basestring):
		raise RuntimeError, _('parameter \'{0}\' must be {1}').format('name', 'string')
	elif not data['name'].strip():
		raise RuntimeError, _('parameter \'{0}\' must not be blank').format('name')
	if m.ErrorType.query.filter_by(name=data['name']).count() > 0:
		raise RuntimeError, _('name \'{0}\' is already in use').format(data['name'])

	if not data.has_key('errorClassId'):
		raise RuntimeError, _('must provide parameter \'{0}\'').format('errorClassId')
	elif not isinstance(data['errorClassId'], int):
		raise RuntimeError, _('parameter \'{0}\' must be {1}').format('errorClassId', 'int')
	if not m.ErrorClass.get(data['errorClassId']):
		raise RuntimeError, _('ErrorClass #{0} not found').format(data['errorClassId'])


	if data.has_key('errorTypeId'):
		del data['errorTypeId']

	errorType = m.ErrorType(**data)
	SS.add(errorType)
	SS.flush()
	_errorType = m.ErrorType.query.filter_by(
			errorClassId=errorType.errorClassId).filter_by(
			name=errorType.name).one()
	assert errorType is _errorType
	return {
		'status': _('new error type {0} successfully created').format(errorType.name),
		'errorType': m.ErrorType.dump(errorType),
	}
