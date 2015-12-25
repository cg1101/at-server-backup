
from flask import request, session, jsonify

import db.model as m
from db.db import SS
from app.api import api, caps, MyForm, Field, validators
from app.i18n import get_text as _
from . import api_1_0 as bp, InvalidUsage

_name = __file__.split('/')[-1].split('.')[0]


@bp.route(_name + '/', methods=['GET'])
@api
@caps()
def get_error_types():
	'''
	returns a list of error types
	'''
	errorTypes = m.ErrorType.query.order_by(m.ErrorType.errorTypeId).all()
	return jsonify({
		'errorTypes': m.ErrorType.dump(errorTypes),
	})


def check_name_uniqueness(data, key, name):
	if m.ErrorType.query.filter_by(name=name).count() > 0:
		raise ValueError, _('name \'{0}\' is already in use').format(name)


def check_error_class_existence(data, key, errorClassId):
	if not m.ErrorClass.query.get(errorClassId):
		raise ValueError, _('error class {0} not found').format(errorClassId)


@bp.route(_name + '/', methods=['POST'])
@api
@caps()
def create_error_type():
	'''
	creates a new error type
	'''
	data = MyForm(
		Field('name', is_mandatory=True, validators=[
			validators.non_blank,
			check_name_uniqueness,
		]),
		Field('errorClassId', is_mandatory=True, validators=[
			check_error_class_existence,
		]),
		Field('defaultSeverity', is_mandatory=True,
			normalizer=lambda data, key, value: float(value), validators=[
			(validators.is_number, (), dict(max_value=1, min_value=0)),
		]),
	).get_data()

	errorType = m.ErrorType(**data)
	SS.add(errorType)
	SS.flush()
	return jsonify({
		'message': _('created error type {0} successfully').format(errorType.name),
		'errorType': m.ErrorType.dump(errorType),
	})

