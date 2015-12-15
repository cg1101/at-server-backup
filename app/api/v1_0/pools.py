
import json

from flask import request, abort, session, jsonify

import db.model as m
from db.db import SS
from app.api import api, caps, MyForm, Field, validators
from app.i18n import get_text as _
from . import api_1_0 as bp, InvalidUsage

_name = __file__.split('/')[-1].split('.')[0]


@bp.route(_name + '/', methods=['GET'])
@api
@caps()
def get_pools():
	pools = m.Pool.query.order_by(m.Pool.poolId).all()
	return jsonify({
		'pools': m.Pool.dump(pools, context={'level': 0}),
	})


def normalize_pool_meta_data(data, key, meta):
	try:
		meta_data = json.loads(meta)
	except:
		raise ValueError, _('error decoding json object \'{0}\'').format(meta)
	return meta_data


def normalize_bool_literal(data, key, value):
	try:
		x = str(value).lower()
		if x in ('true', 'false'):
			return (x == 'true')
		# TODO: allow other values ('y', 'yes', 'n', 'no', '1', '0', etc.)
	except Exception, exc:
		pass
	raise ValueError, _('invalid bool value {0}').format(value)


def check_pool_name_uniqueness(data, key, name, poolId):
	if m.Pool.query.filter_by(name=name
			).filter(m.Pool.poolId!=poolId
			).count() > 0:
		raise ValueError, _('name \'{0}\' is already in use').format(name)


def check_task_type_existence(data, key, taskTypeId):
	taskType = m.TaskType.query.get(taskTypeId)
	if not taskType:
		raise ValueError, _('task type {0} not found').format(taskTypeId)


def check_tag_set_existence(data, key, tagSetId):
	if tagSetId is not None:
		tagSet = m.TagSet.query.get(tagSetId)
		if not tagSet:
			raise ValueError, _('tag set {0} not found').format('tagSetId')


def load_questions(data, key, value):
	# TODO: implement this function to actually validate
	# questions and load them
	return []

@bp.route(_name + '/', methods=['POST'])
@api
@caps()
def create_pool():
	data = MyForm(
		Field('name', is_mandatory=True, validators=[
			validators.non_blank,
			(check_pool_name_uniqueness, (None,)),
		]),
		Field('meta', is_mandatory=True, default='{}',
			normalizer=normalize_pool_meta_data),
		Field('taskTypeId', is_mandatory=True, validators=[
			validators.is_number,
			check_task_type_existence,
		]),
		Field('autoScoring', is_mandatory=True,
			normalizer=normalize_bool_literal, validators=[
			validators.is_bool,
		]),
		Field('tagSetId', validators=[check_tag_set_existence,]),
		Field('dataFile', is_mandatory=True),
		Field('questions', is_mandatory=True, default=[],
				normalizer=load_questions),
	).get_data(is_json=False)

	questions = data.pop('questions')
	del data['dataFile']

	pool = m.Pool(**data)
	SS.add(pool)
	for qd in questions:
		q = m.Question(**qd)
		pool.questions.append(q)

	SS.flush()
	return jsonify({
		'pool': m.Pool.dump(pool, context={'level': 0}),
	})


@bp.route(_name + '/<int:poolId>', methods=['GET'])
@api
@caps()
def get_pool(poolId):
	pool = m.Pool.query.get(poolId)
	if not pool:
		raise InvalidUsage(_('pool {0} not found').format(poolId), 404)
	return jsonify({
		'pool': m.Pool.dump(pool, context={'level': 0}),
	})

