from flask_restful import Resource

from . import api_v1
from app.api import api, caps
from db.model import RecordingPlatformType


class ListResource(Resource):

	method_decorators = [
		caps(),
		api,
	]

	def get(self):
		recording_platform_types = RecordingPlatformType.query.all()
		return {"recordingPlatformTypes": RecordingPlatformType.dump(recording_platform_types)}
		

api_v1.add_resource(ListResource, "recording-platform-types")
