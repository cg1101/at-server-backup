import csv

from flask import request
from flask_restful import Resource

from . import api_v1
from app.api import Field, MyForm, api, caps, get_model, simple_validators, validators
from db import database as db
from db.model import AudioCheckingGroup, RecordingPlatform


class ListResource(Resource):
	
	method_decorators = [
		get_model(RecordingPlatform),
		caps(),
		api
	]

	def get(self, recording_platform):
		return {"audioCheckingGroups": AudioCheckingGroup.dump(recording_platform.audio_checking_groups)}

	def post(self, recording_platform):

		data = MyForm(
			Field('name', is_mandatory=True,
				validators=[
					(AudioCheckingGroup.check_name_unique, (recording_platform,)),
			]),
			Field('selectionSize', is_mandatory=True,
				validators=[
					(validators.is_number, (), dict(min_value=1)),
				]
			),
			Field('corpusCodes', is_mandatory=True,
				validators=[
					validators.is_list,
					CorpusCode.check_all_exists,
				]
			),
		).get_data()

		# create group
		audio_checking_group = AudioCheckingGroup(
			recording_platform=recording_platform,
			name=data["name"],
			selection_size=data["selectionSize"],
		)
		db.session.add(audio_checking_group)
		db.session.flush()

		# assign corpus codes
		audio_checking_group.assign_corpus_codes(data["corpusCodes"])
		db.session.commit()
		return {"audioCheckingGroup": AudioCheckingGroup.dump(audio_checking_group)}


api_v1.add_resource(
	ListResource,
	"recording-platforms/<int:recording_platform_id>/audiocheckinggroups",
	endpoint="recording_platform_audio_checking_groups"
)
