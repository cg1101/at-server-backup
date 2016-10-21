import logging

from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import Performance, PerformanceMetaValue, Recording

log = logging.getLogger(__name__)


@bp.route("performances/<int:performance_id>", methods=["GET"])
@api
@caps()
@get_model(Performance)
def get_performance(performance):
	return jsonify(performance=Performance.dump(performance))


@bp.route("performances/<int:performance_id>/recordings", methods=["GET"])
@api
@caps()
@get_model(Performance)
def get_performance_recordings(performance):
	return jsonify(recordings=Recording.dump(performance.recordings))
	
	
@bp.route("performances/<int:performance_id>/metavalues", methods=["GET"])
@api
@caps()
@get_model(Performance)
def get_performance_meta_values(performance):
	return jsonify({"metaValues": PerformanceMetaValue.dump(performance.meta_values)})
