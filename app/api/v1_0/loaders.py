from flask import jsonify, request

from . import api_1_0 as bp
from app.api import InvalidUsage, api, caps
from db.model import RecordingPlatformType, TaskType
from lib.loaders import get_available_loaders


@bp.route("loaders", methods=["GET"])
@api
@caps()
def get_loaders():
	
	task_type_id = request.args.get("taskTypeId", None)
	recording_platform_type_id = request.args.get("recordingPlatformTypeId", None)

	if task_type_id:
		task_type = TaskType.query.get(task_type_id)

		if not task_type:
			raise InvalidUsage("unknown task type: {0}".format(task_type_id))

		loaders = get_available_loaders(task_type=task_type.name)

	if recording_platform_type_id:
		recording_platform_type = RecordingPlatformType.query.get(recording_platform_type_id)

		if not recording_platform_type:
			raise InvalidUsage("unknown recording platform type: {0}".format(recording_platform_type_id))
			
		loaders = get_available_loaders(recording_platform_type=recording_platform_type.name)

	else:
		loaders = []

	return jsonify(loaders=loaders)

