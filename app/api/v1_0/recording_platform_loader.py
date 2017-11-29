from flask import request
from flask_restful import Resource

from . import api_v1
from app.api import api, caps, get_model
from db import database as db
from db.model import RecordingPlatform


class ModelResource(Resource):
	
	method_decorators = [
		get_model(RecordingPlatform),
		caps(),
		api
	]

	def put(self, recording_platform):
		recording_platform.set_loader(request.json)
		db.session.commit()
		return {"success": True}


	def delete(self, recording_platform):
		recording_platform.set_loader(None)
		db.session.commit()
		return {"success": True}


api_v1.add_resource(
	ModelResource,
	"recording-platforms/<int:recording_platform_id>/loader",
	endpoint="recording_platform_loader"
)
