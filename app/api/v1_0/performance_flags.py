import logging

from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import AudioCollection, PerformanceFlag

log = logging.getLogger(__name__)


@bp.route("performanceflags/<int:performance_flag_id>", methods=["PUT"])
@api
@caps()
@get_model(PerformanceFlag)
def update_performance_flag(performance_flag):

	data = MyForm(
		Field('name', is_mandatory=True,
			validators=[
				performance_flag.check_other_name_unique,
		]),
		Field('severity', is_mandatory=True,
			validators=[
				PerformanceFlag.check_valid_severity
		]),
		Field('enabled', is_mandatory=True, validators=[
			validators.is_bool,
		]),
	).get_data()

	performance_flag.name = data["name"]
	performance_flag.severity = data["severity"]
	performance_flag.enabled = data["enabled"]
	db.session.flush()

	return jsonify({"performanceFlag": PerformanceFlag.dump(performance_flag)})


@bp.route("performanceflags", methods=["POST"])
@api
@caps()
def create_performance_flag():

	data = MyForm(
		Field('audioCollectionId', is_mandatory=True,
			validators=[
				AudioCollection.check_exists,
		]),
		Field('name', is_mandatory=True,
			validators=[
				PerformanceFlag.check_name_unique,
		]),
		Field('severity', is_mandatory=True,
			validators=[
				PerformanceFlag.check_valid_severity
		]),
	).get_data()

	performance_flag = PerformanceFlag(
		audio_collection_id=data["audioCollectionId"],
		name=data["name"],
		severity=data["severity"],
		enabled=True
	)
	db.session.add(performance_flag)
	db.session.commit()

	return jsonify({"performanceFlag": PerformanceFlag.dump(performance_flag)})
