
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
def get_countries():
	'''
	returns a list of countries
	'''
	countries = m.Country.query.all()
	return jsonify({
		'countries': m.Country.dump(countries),
	})
