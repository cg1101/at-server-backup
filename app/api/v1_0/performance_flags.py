from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import PerformanceFlag


@bp.route("performanceflags/<int:performance_flag_id>", methods=["PUT"])
@api
@caps()
@get_model(PerformanceFlag)
def update_performance_flag(performance_flag):

	data = MyForm(
		Field('name', validators=[
			performance_flag.check_updated_name_unique,
		]),
		Field('severity', validators=[
			PerformanceFlag.check_valid_severity
		]),
		Field('enabled', validators=[
			validators.is_bool,
		]),
	).get_data()

	if "name" in data:
		performance_flag.name = data["name"]

	if "severity" in data:
		performance_flag.severity = data["severity"]

	if "enabled" in data:
		performance_flag.enabled = data["enabled"]

	db.session.flush()
	return jsonify({"performanceFlag": PerformanceFlag.dump(performance_flag)})
