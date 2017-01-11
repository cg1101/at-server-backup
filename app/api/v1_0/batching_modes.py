from flask import jsonify

from . import api_1_0 as bp
from app.api import api, caps
from db.model import BatchingMode


@bp.route("batchingmodes", methods=["GET"])
@api
@caps()
def get_batching_modes():
	batching_modes = BatchingMode.query.all()
	return jsonify({"batchingModes": BatchingMode.dump(batching_modes)})

