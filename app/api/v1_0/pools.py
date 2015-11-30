
from flask import request, abort, session

import db.model as m
from db.db import SS
from app.api import ajax, caps, get_text as _
from . import api_1_0 as bp

_name = __file__.split('/')[-1].split('.')[0]

@bp.route(_name + '/', methods=['GET'])
@ajax
@caps()
def get_pools():
	pools = m.Pool.query.all()
	return {
		'pools': m.Pool.dump(pools, context={'level': 0}),
	}


@bp.route(_name + '/', methods=['POST'])
@ajax
@caps()
def create_pool():
	data = request.get_json()
	pool = m.Pool(**data)
	SS().add(pool)
	SS().flush()
	return {
		'pool': m.Pool.dump(pool, context={'level': 0}),
	}


@bp.route(_name + '/<int:poolId>', methods=['GET'])
@ajax
@caps()
def get_pool(poolId):
	pool = m.Pool.query.get(poolId)
	if not pool:
		abort(404)
	return {
		'pool': m.Pool.dump(pool, context={'level': 0}),
	}
