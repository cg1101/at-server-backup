import logging

from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import RecordingFlag

log = logging.getLogger(__name__)


@bp.route("recordingflags/<int:recording_flag_id>", methods=["PUT"])
@api
@caps()
@get_model(RecordingFlag)
def update_recording_flag(recording_flag):

	data = MyForm(
		Field('name', is_mandatory=True,
			validators=[
				recording_flag.check_updated_name_unique,
		]),
		Field('severity', is_mandatory=True,
			validators=[
				RecordingFlag.check_valid_severity
		]),
		Field('enabled', is_mandatory=True, validators=[
			validators.is_bool,
		]),
	).get_data()

	recording_flag.name = data["name"]
	recording_flag.severity = data["severity"]
	recording_flag.enabled = data["enabled"]
	db.session.flush()

	return jsonify({"recordingFlag": RecordingFlag.dump(recording_flag)})
