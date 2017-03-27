from flask import jsonify, request

from . import api_1_0 as bp
from app.api import InvalidUsage, api, caps
from db.model import Loader, TaskType


@bp.route("loaders", methods=["GET"])
@api
@caps()
def get_loaders():
	
	task_type_id = request.args.get("taskTypeId", None)

	if task_type_id:
		task_type = TaskType.query.get(task_type_id)

		if not task_type:
			raise InvalidUsage("unknown task type: {0}".format(task_type_id))

		loaders = Loader.get_valid_loaders(task_type.name)

	else:
		loaders = Loader.query.all()

	return jsonify(loaders=Loader.dump(loaders))

