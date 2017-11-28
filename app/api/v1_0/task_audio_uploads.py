from flask import request
from flask_restful import Resource

from . import api_v1
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, normalizers, simple_validators, validators
from db import database as db
from db.model import AudioUpload, Task, TaskType


class ListResource(Resource):
	
	method_decorators = [
		get_model(Task),
		caps(),
		api
	]

	def get(self, task):

		if not task.is_type(TaskType.TRANSCRIPTION, TaskType.AUDIO_CHECKING):
			raise InvalidUsage("audio uploads are only available for audio tasks", 400)

		data = MyForm(
			Field("visibleOnly", normalizer=normalizers.to_json, validators=[
				validators.is_bool,
			])
		).get_data(is_json=False, use_args=True)

		query = AudioUpload.query.filter_by(task=task)

		if data.get("visibleOnly"):
			query = query.filter_by(hidden=False)

		audio_uploads = query.all()
		return {"audioUploads": AudioUpload.dump(audio_uploads)}

	def post(self, task):

		if not task.is_type(TaskType.TRANSCRIPTION, TaskType.AUDIO_CHECKING):
			raise InvalidUsage("audio uploads are only available for audio tasks", 400)

		data = MyForm(
			Field("loadManager", is_mandatory=True, validators=[
				simple_validators.is_dict(),
			]),
			Field("isEmpty", is_mandatory=True, validators=[
				validators.is_bool,
			]),
		).get_data()

		audio_upload = AudioUpload(
			task=task,
			data=data["loadManager"],
			hidden=AudioUpload.get_hidden_flag(data["loadManager"], data["isEmpty"]),
		)

		db.session.add(audio_upload)
		db.session.commit()
		return {"audioUpload": audio_upload.serialize()}


api_v1.add_resource(
	ListResource,
	"tasks/<int:task_id>/audio-uploads",
	endpoint="task_audio_uploads"
)
