
from flask import request, abort, session, jsonify

import db.model as m
from db.db import SS
from app.api import api, caps
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


@bp.route(_name + '/', methods=['POST'])
@api
@caps()
def create_pool():
	data = request.get_json()
	pool = m.Pool(**data)
	SS().add(pool)
	SS().flush()
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

