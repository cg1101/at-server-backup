
import datetime

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
def get_tests():
	tests = m.Test.query.order_by(m.Test.testId).all()
	return jsonify({
		'tests': m.Test.dump(tests),
	})


def check_test_name_uniqueness(data, key, name, testId):
	if m.Test.query.filter_by(name=name
			).filter(m.Test.testId!=testId).count() > 0:
		raise ValueError, _('name \'{0}\' is already in use').format(name)


def check_pool_existence(data, key, poolId):
	if not m.Pool.query.get(poolId):
		raise ValueError, _('pool {0} not found').format(poolId)


def normalize_test_size(data, key, value):
	if data['testType'] == 'static':
		value = None
	else:
		if value is None:
			raise ValueError, _('size must be specified for dynamic tests')
		try:
			value = int(value)
		except:
			raise ValueError, _('invalid test size: {0}').format(size)
	return value


def check_test_size(data, key, size):
	if data['testType'] == 'static':
		if size is not None:
			raise ValueError, _('size must not be specified for static tests')
	else:
		pool = m.Pool.query.get(data['poolId'])
		if size > len(pool.questions):
			raise ValueError, _('test size must not be greater than pool size')


def normalize_test_requirement(data, key, value):
	if value is None:
		pool = m.Pool.query.get(data['poolId'])
		value = pool.meta
	else:
		try:
			d = json.loads(str(value))
		except:
			raise ValueError, _('invalid requirement value: {0}').format(value)
		value = d
	return value


from .tasks import normalize_interval_as_seconds, check_lease_life_minimal_length
from .pools import check_task_type_existence


@bp.route(_name + '/', methods=['POST'])
@api
@caps()
def create_test():
	data = MyForm(
		Field('name', is_mandatory=True, validators=[
			validators.non_blank,
			(check_test_name_uniqueness, (None,)),
		]),
		Field('description', validators=[
			validators.is_string,
		]),
		Field('taskTypeId', is_mandatory=True,
			normalizer=lambda data, key, value: int(value),
			validators=[
				validators.is_number,
				check_task_type_existence,
		]),
		Field('timeLimit', default=7200,
			normalizer=normalize_interval_as_seconds,
			validators=[
				(check_lease_life_minimal_length, (datetime.timedelta(seconds=300),)),
		]),
		Field('passingScore', is_mandatory=True,
			normalizer=lambda data, key, value: float(value),
			validators=[
				(validators.is_number, (), dict(ge=0, le=100)),
		]),
		Field('isEnabled', is_mandatory=True, default=True,
			normalizer=lambda data, key, value: str(value).lower() == 'true',
			validators=[
				validators.is_bool,
		]),
		Field('poolId', is_mandatory=True,
			normalizer=lambda data, key, value: int(value),
			validators=[
				validators.is_number,
				check_pool_existence,
		]),
		Field('testType', is_mandatory=True, validators=[
			(validators.enum, ('static', 'dynamic')),
		]),
		Field('size', is_mandatory=True, default=lambda: None,
			normalizer=normalize_test_size,
			validators=[
				check_test_size,
		]),
		Field('requirement', is_mandatory=True, default=lambda: None,
			normalizer=normalize_test_requirement),
	).get_data(is_json=False)
	test = m.Test(**data)
	SS.add(test)
	SS.flush()
	return jsonify({
		'message': _('created test {0} successfully').format(test.testId),
		'test': m.Test.dump(test),
	})


@bp.route(_name + '/<int:testId>', methods=['GET'])
@api
@caps()
def get_test(testId):
	test = m.Test.query.get(testId)
	if not test:
		raise InvalidUsage(_('test {0} not found').format(testId), 404)
	return jsonify({
		'test': m.Test.dump(test),
	})


@bp.route(_name + '/<int:testId>/sheets/', methods=['GET'])
@api
@caps()
def get_test_sheets(testId):
	test = m.Test.query.get(testId)
	if not test:
		raise InvalidUsage(_('test {0} not found').format(testId), 404)
	sheets = m.Sheet.query.filter_by(testId=testId
			).order_by(m.Sheet.userId
			).order_by(m.Sheet.nTimes).all()
	return jsonify({
		'sheets': m.Sheet.dump(sheets),
	})

