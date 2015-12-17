
from flask import request, session, jsonify

import db.model as m
from db.db import SS
from app.api import api, caps
from app.i18n import get_text as _
from . import api_1_0 as bp, InvalidUsage

_name = __file__.split('/')[-1].split('.')[0]


@bp.route(_name + '/', methods=['GET'])
@api
@caps()
def get_rates():
	'''
	returns a list of rate curves
	'''
	rates = m.Rate.query.order_by(m.Rate.rateId).all()
	return jsonify({
		'rates': m.Rate.dump(rates),
	})


@bp.route(_name + '/<int:rateId>', methods=['GET'])
@api
@caps()
def get_rate(rateId):
	'''
	returns specified rate curve
	'''
	rate = m.Rate.query.get(rateId)
	if not rate:
		raise InvalidUsage(_('rate {0} not found').format(rateId), 404)
	return jsonify({
		'rate': m.Rate.dump(rate),
	})
