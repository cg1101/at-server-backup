
from flask import request, abort, session

import db.model as m
from db.db import SS
from app.api import ajax, caps, get_text as _
from . import api_1_0 as bp

_name = __file__.split('/')[-1].split('.')[0]

@bp.route(_name + '/', methods=['GET'])
@ajax
@caps()
def get_rates():
	'''
	returns a list of rate curves
	'''
	rates = m.Rate.query.order_by(m.Rate.rateId).all()
	return {
		'rates': m.Rate.dump(rates),
	}

@bp.route(_name + '/<int:rateId>', methods=['GET'])
@ajax
@caps()
def get_rate(rateId):
	'''
	returns specified rate curve
	'''
	rate = m.Rate.query.get(rateId)
	if not rate:
		abort(404)
	return {
		'rate': m.Rate.dump(rate),
	}