import pytz

from datetime import datetime
from flask import request, session, jsonify

import db.model as m
from . import api_1_0 as bp
from .. import InvalidUsage
from app.api import api, caps, get_model
from app.i18n import get_text as _
from app.policies import BatchAssignmentPolicy as policy
from db import database as db
from db.model import Batch
from db.db import SS
from db.errors import AudioCheckingBatch


_name = __file__.split('/')[-1].split('.')[0]


@bp.route(_name + '/<int:batchId>', methods=['GET'])
@api
@caps()
def get_batch(batchId):
	batch = m.Batch.query.get(batchId)
	if not batch:
		raise InvalidUsage(_('batch {0} not found').format(batchId), 404)
	return jsonify({
		'batch': m.Batch.dump(batch),
	})


@bp.route("batches/<int:batch_id>", methods=["DELETE"])
@api
@caps()
@get_model(Batch)
def delete_batch(batch):
	try:
		batch.delete()
	except AudioCheckingBatch:
		raise InvalidUsage("unable to delete batch in audio checking task", 400)

	db.session.commit()
	return jsonify(success=True)


@bp.route(_name + '/<int:batchId>/stat', methods=['GET'])
@api
@caps()
def get_batch_stats(batchId):
	batch = m.Batch.query.get(batchId)
	if not batch:
		raise InvalidUsage(_('batch {0} not found').format(batchId), 404)
	return jsonify({
		'stat': {
			'pageCount': len(batch.pages),
			'itemCount': sum([len(p.members) for p in batch.pages]),
			'unitCount': sum([i.rawPiece.words for p in batch.pages for i in p.members]),
		}
	})


@bp.route(_name + '/<int:batchId>/users/<int:userId>', methods=['PUT'])
@api
@caps()
def assign_batch_to_user(batchId, userId):
	batch = m.Batch.query.get(batchId)
	if not batch:
		raise InvalidUsage(_('batch {0} not found').format(batchId), 404)
	user = m.User.query.get(userId)
	if not user:
		raise InvalidUsage(_('user {0} not found').format(userId), 404)

	# TODO: perform more checks according to policy
	if policy.active_worker_only:
		if m.TaskWorker.query.filter_by(taskId=batch.taskId
				).filter_by(subTaskId=batch.subTaskId
				).filter_by(userId=userId
				).filter_by(removed=False).count() == 0:
			raise InvalidUsage(_('user {0} is not working on sub task {1}'
					).format(userId, batch.subTaskId))

	# TODO: change time from naive to timezone aware
	batch.leaseGranted = datetime.utcnow().replace(tzinfo=pytz.utc)
	# batch.leaseGranted = datetime.now()
	batch.leaseExpires = batch.leaseGranted + batch.subTask.defaultLeaseLife
	batch.user = user
	SS.flush()
	return jsonify({
		'message': _('batch {0} has been assigned to user {1}, expires at {2}'
			).format(batchId, user.userName, batch.leaseExpires),
		'batch': m.Batch.dump(batch),
	})


@bp.route(_name + '/<int:batchId>/users/', methods=['DELETE'])
@api
@caps()
def unassign_batch(batchId):
	batch = m.Batch.query.get(batchId)
	if not batch:
		raise InvalidUsage(_('batch {0} not found').format(batchId), 404)
	# TODO: check policy
	# TODO: update history?
	if batch.userId != None:
		batch.unassign()
		message = _('batch {0} has been un-assigned').format(batchId)
	else:
		message = _('batch {0} is not assigned to anyone').format(batchId)
	SS.flush()
	return jsonify({
		'message': message,
		'batch': m.Batch.dump(batch),
	})
