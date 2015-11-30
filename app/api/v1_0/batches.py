
from flask import request, abort, session

import db.model as m
from db.db import SS
from app.api import ajax, caps, get_text as _
from . import api_1_0 as bp

_name = __file__.split('/')[-1].split('.')[0]

@bp.route(_name + '/<int:batchId>', methods=['GET'])
@ajax
@caps()
def get_batch(batchId):
	batch = m.Batch.get(batchId)
	if not batch:
		abort(404)
	return {
		'batch': m.Batch.dump(batch),
	}

@bp.route(_name + '/<int:batchId>/stat', methods=['GET'])
@ajax
@caps()
def get_batch_stats(batchId):
	pass

@bp.route(_name + '/<int:batchId>/users/<int:userId>', methods=['PUT'])
@ajax
@caps()
def assign_batch_to_user(batchId, userId):
	batch = m.Batch.get(batchId)
	user = m.User.get(userId)
	if not batch:
		abort(404)
	if batch.userId != None:
		pass
	batch.user = user
	return {

	}

@bp.route(_name + '/<int:batchId>/users/', methods=['DELETE'])
@ajax
@caps()
def unassign_batch(batchId):
	batch = m.Batch.get(batchId)
	if not batch:
		abort(404)
	if batch.userId != None:
		batch.userId = Nnone
	return {
	
	}
