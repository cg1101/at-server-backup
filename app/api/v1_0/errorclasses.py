
from flask import request, abort, session, jsonify

import db.model as m
from db.db import SS
from app.api import api, caps
from app.i18n import get_text as _
from . import api_1_0 as bp

_name = __file__.split('/')[-1].split('.')[0]

@bp.route(_name + '/', methods=['GET'])
@api
@caps()
def get_error_classes():
	'''
	returns a list of error classes
	'''
	errorClasses = m.ErrorClass.query.order_by(m.ErrorClass.errorClassId).all()
	return jsonify({
		'errorClasses': m.ErrorClass.dump(errorClasses),
	})

@bp.route(_name + '/', methods=['POST'])
@api
@caps()
def create_error_class():
	'''
	creates a new error class
	'''
	s = m.ErrorClassSchema()
	data = request.get_json()
	if not data:
		try:
			data = s.load(request.values).data
		except Exception, e:
			raise RuntimeError, _('error parsing parameters: {0}').format(e)

	if not data.has_key('name'):
		raise RuntimeError, _('must provide parameter \'name\'')
	elif not isinstance(data['name'], basestring):
		raise RuntimeError, _('parameter \'name\' must be string')
	elif not data['name'].strip():
		raise RuntimeError, _('parameter \'name\' must not be blank')
	if m.ErrorClass.query.filter_by(name=data['name']).count() > 0:
		raise RuntimeError, _('name \'{0}\' is already in use').format(data['name'])

	if data.has_key('errorClassId'):
		del data['errorClassId']

	errorClass = m.ErrorClass(**data)
	SS.add(errorClass)
	SS.flush()
	return jsonify({
		'status': _('new error class {0} successfully created').format(errorClass.name),
		'errorClass': m.ErrorClass.dump(errorClass),
	})
