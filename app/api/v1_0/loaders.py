from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, validators
from db.model import RecordingPlatformType, TaskType
from lib.loaders import get_available_loaders


@bp.route("loaders", methods=["GET"])
@api
@caps()
def get_loaders():
	
	data = MyForm(
		Field("taskTypeId", validators=[
			validators.is_number,
			TaskType.check_exists
		]),
		Field("recordingPlatformTypeId", validators=[
			validators.is_number,
			RecordingPlatformType.check_exists
		]),
	).get_data(is_json=False, use_args=True)

	if "taskTypeId" in data:
		task_type = TaskType.query.get(data["taskTypeId"])
		loaders = get_available_loaders(task_type=task_type.name)

	elif "recordingPlatformTypeId" in data:
		recording_platform_type = RecordingPlatformType.query.get(data["recordingPlatformTypeId"])
		loaders = get_available_loaders(recording_platform_type=recording_platform_type.name)

	else:
		loaders = []

	return jsonify(loaders=loaders)

