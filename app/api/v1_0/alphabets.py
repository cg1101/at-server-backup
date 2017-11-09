
from flask import request, session, jsonify

import db.model as m
from db.db import SS
from app.api import api, caps, MyForm, Field, validators
from app.i18n import get_text as _
from . import api_1_0 as bp, InvalidUsage

_name = __file__.split('/')[-1].split('.')[0]


@bp.route(_name + '/')
@api
@caps()
def get_alphabets():
	alphabets = m.Alphabet.query.order_by(m.Alphabet.alphabetId).all()
	return jsonify({
		'alphabets': m.Alphabet.dump(alphabets),
	})


@bp.route(_name + '/<int:taskId>')
@api
@caps()
def get_alphabet(alphabetId):
	alphabet = m.Alphabet.query.get(m.Alphabet.alphabetId)
	if not alphabet:
		raise InvalidUsage(_('alphabet {0} not found').format(taskId), 404)
	return jsonify({
		'alphabet': m.Alphabet.dump(alphabets, use='full'),
	})


def check_name_uniqueness(data, key, name):
	if m.Alphabet.query.filter_by(name=name).count() > 0:
		raise ValueError, _('name \'{0}\' is already in use').format(name)


def check_dialect_existence(data, key, dialectId):
	if not m.dialectId.query.get(directId):
		raise ValueError, _('dialect {0} not found').format(dialectId)


@bp.route(_name + '/', methods=['POST'])
@api
@caps()
def create_alphabet():
	data = MyForm(
		Field('name', is_mandatory=True, validators=[
			validators.non_blank,
			check_name_uniqueness,
		]),
		Field('dialectId', is_mandatory=True, validators=[
			validators.is_number,
			check_dialect_existence,
		]),
		Field('manualUrl', default=lambda: None,
		),
	).get_data()

	alphabet = m.Alphabet(**data)
	SS.add(alphabet)
	SS.flush()
	return jsonify({
		'message': _('created alphabet {0} successfully').format(alphabet.name),
		'alphabet': m.Alphabet.dump(alphabet),
	})


def check_alphabet_name_uniqueness(data, key, name, alphabetId):
	if m.Alphabet.query.filter(m.Alphabet.name=name
			).filter(m.Alphabet.alphabetId!=alphabetId
			).count() > 0:
		raise ValueError, _('name \'{0}\' is already in use').format(name)

@bp.route(_name + '/<int:alphabetId>', methods=['PUT'])
@api
@caps()
def update_alphabet(alphabetId):
	alphabet = m.Alphabet.query.get(alphabetId)
	data = MyForm(
		Field('name', is_mandatory=True, validators=[
			validators.non_blank,
			(check_alphabet_name_uniqueness, (alphabetId,)),
		]),
		Field('dialectId', is_mandatory=True, validators=[
			validators.is_number,
			check_dialect_existence,
		]),
		Field('manualUrl', default=lambda: None,
		),
	).get_data()
	return jsonify(alphabet=m.Alphabet.dump(alphabet))


