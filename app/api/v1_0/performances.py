import logging

from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import Performance, PerformanceMetaValue, Recording
from lib.metadata_validation import process_received_metadata, resolve_new_metadata

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


@bp.route("performances/<int:performance_id>/metavalues", methods=["PUT"])
@api
@caps()
@get_model(Performance)
def update_performance_meta_values(performance):
	meta_values = process_received_metadata(request.json, performance.recording_platform.performance_meta_categories)
	resolve_new_metadata(performance, meta_values)
	db.session.flush()
	return jsonify({"metaValues": PerformanceMetaValue.dump(performance.meta_values)})
