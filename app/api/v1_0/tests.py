
from flask import request, abort, session

import db.model as m
from db.db import SS
from app.api import api, caps, get_text as _
from . import api_1_0 as bp

_name = __file__.split('/')[-1].split('.')[0]

@bp.route(_name + '/', methods=['GET'])
@api
@caps()
def get_tests():
	tests = m.Test.query.all()
	return {
		'tests': m.Test.dump(tests),
	}


@bp.route(_name + '/', methods=['POST'])
@api
@caps()
def create_test():
	test = m.Test(**data)
	SS().add(test)
	SS().flush()
	return {
		'test': m.Test.dump(test),
	}


@bp.route(_name + '/<int:testId>', methods=['GET'])
@api
@caps()
def get_test(testId):
	test = m.Test.query.get(testId)
	if not test:
		return abort()
	return {
		'test': m.Test.dump(test),
	}


@bp.route(_name + '/<int:testId>/sheets/', methods=['GET'])
@api
@caps()
def get_test_sheets(testId):
	sheets = m.Sheet.query.filter_by(testId=testId).order_by(m.Sheet.userId).order_by(m.Sheet.nTimes).all()
	return {
		'sheets': m.Sheet.dump(sheets),
	}
