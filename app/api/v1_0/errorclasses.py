
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
def get_error_classes():
	'''
	returns a list of error classes
	'''
	errorClasses = m.ErrorClass.query.order_by(m.ErrorClass.errorClassId).all()
	return jsonify({
		'errorClasses': m.ErrorClass.dump(errorClasses),
	})


def check_name_uniqueness(data, key, name):
	if m.ErrorClass.query.filter_by(name=name).count() > 0:
		raise ValueError, _('name \'{0}\' is already in use').format(name)


@bp.route(_name + '/', methods=['POST'])
@api
@caps()
def create_error_class():
	'''
	creates a new error class
	'''
	data = MyForm(
		Field('name', is_mandatory=True, validators=[
			validators.non_blank, check_name_uniqueness]),
	).get_data()

	errorClass = m.ErrorClass(**data)
	SS.add(errorClass)
	SS.flush()
	return jsonify({
		'message': _('created error class {0} successfully').format(errorClass.name),
		'errorClass': m.ErrorClass.dump(errorClass),
	})

