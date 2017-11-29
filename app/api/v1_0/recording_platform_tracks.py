from flask import request
from flask_restful import Resource

from . import api_v1
from app.api import Field, MyForm, api, caps, get_model, simple_validators, validators
from db import database as db
from db.model import RecordingPlatform, Track


class ListResource(Resource):
	
	method_decorators = [
		get_model(RecordingPlatform),
		caps(),
		api
	]

	def get(self, recording_platform):
		return {"tracks": Track.dump(recording_platform.tracks)}

	def post(self, recording_platform):

		data = MyForm(
			Field("trackIndex", is_mandatory=True, validators=[
				simple_validators.is_number(min_value=0),
				Track.check_new_index_unique(recording_platform),
			]),
			Field("name", is_mandatory=True, validators=[
				validators.non_blank,
				Track.check_new_name_unique(recording_platform),
			]),
		).get_data()
	
		track = Track(
			recording_platform=recording_platform,
			track_index=data["trackIndex"],
			name=data["name"],
		)

		db.session.add(track)
		db.session.flush()
		return {"track": Track.dump(track)}


api_v1.add_resource(
	ListResource,
	"recording-platforms/<int:recording_platform_id>/tracks",
	endpoint="recording_platform_tracks"
)
