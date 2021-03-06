from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import RecordingFlag


@bp.route("recordingflags/<int:recording_flag_id>", methods=["PUT"])
@api
@caps()
@get_model(RecordingFlag)
def update_recording_flag(recording_flag):

	data = MyForm(
		Field('name', validators=[
			recording_flag.check_updated_name_unique,
		]),
		Field('severity', validators=[
			RecordingFlag.check_valid_severity
		]),
		Field('enabled', validators=[
			validators.is_bool,
		]),
	).get_data()

	if "name" in data:
		recording_flag.name = data["name"]

	if "severity" in data:
		recording_flag.severity = data["severity"]

	if "enabled" in data:
		recording_flag.enabled = data["enabled"]

	db.session.flush()
	return jsonify({"recordingFlag": RecordingFlag.dump(recording_flag)})
