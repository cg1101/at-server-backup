from flask import request
from flask_restful import Resource

from . import api_v1
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import AudioUpload


class ModelResource(Resource):
	
	method_decorators = [
		get_model(AudioUpload),
		caps(),
		api
	]

	def put(self, audio_upload):
		
		data = MyForm(
			Field("hidden", validators=[
				validators.is_bool,
			])
		).get_data()

		if "hidden" in data:
			audio_upload.hidden = data["hidden"]

		db.session.commit()
		return {"audioUpload": audio_upload.serialize()}


api_v1.add_resource(
	ModelResource,
	"audio-uploads/<int:audio_upload_id>",
	endpoint="audio_upload"
)
