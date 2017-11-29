import csv

from flask import request
from flask_restful import Resource

from . import api_v1
from app.api import Field, MyForm, api, caps, get_model, simple_validators, validators
from db import database as db
from db.model import CorpusCode, RecordingPlatform


class ListResource(Resource):
	
	method_decorators = [
		get_model(RecordingPlatform),
		caps(),
		api
	]

	def get(self, recording_platform):
		return {"corpusCodes": CorpusCode.dump(recording_platform.corpus_codes)}

	def post(self, recording_platform):

		data = MyForm(
			Field("code", default="", validators=[
				CorpusCode.check_new_code_unique(recording_platform)
			]),
			Field("regex"),
			Field("isScripted", is_mandatory=True, validators=[
				validators.is_bool
			]),
		).get_data()
	
		corpus_code = CorpusCode(
			recording_platform=recording_platform,
			code=data["code"],
			regex=data.get("regex"),
			is_scripted=data["isScripted"],
		)
		
		db.session.add(corpus_code)
		db.session.flush()
		return {"corpusCode": CorpusCode.dump(corpus_code)}


class UploadResource(Resource):

	method_decorators = [
		get_model(RecordingPlatform),
		caps(),
		api
	]

	def post(self, recording_platform):
	
		if recording_platform.corpus_codes:
			raise InvalidUsage("recording platform already has corpus codes")

		if not "file" in request.files:
			raise InvalidUsage("no corpus code list uploaded")

		fp = request.files["file"]
		reader = csv.reader(fp)

		for row in reader:
			if not row:
				continue

			code = row[0]

			# if type included
			if len(row) > 1:
				type = row[1]
				type = type.strip()

				# type is non-empty
				if type:

					# check if scripted
					if type.lower() == CorpusCode.SCRIPTED.lower():
						type = CorpusCode.SCRIPTED

					# check if spontaneous
					elif type.lower() == CorpusCode.SPONTANEOUS.lower():
						type = CorpusCode.SPONTANEOUS

					# invalid type
					else:
						raise InvalidUsage("Line {0}: invalid type: {1}".format(reader.line_num, type))

				else:
					type = CorpusCode.SCRIPTED

			# no type included
			else:
				type = CorpusCode.SCRIPTED
		
			corpus_code = CorpusCode(
				recording_platform=recording_platform,
				code=code,
				is_scripted=(type==CorpusCode.SCRIPTED),
			)
		
			db.session.add(corpus_code)

		db.session.commit()
		return {"corpusCodes": CorpusCode.dump(recording_platform.corpus_codes)}


api_v1.add_resource(
	ListResource,
	"recording-platforms/<int:recording_platform_id>/corpuscodes",
	endpoint="recording_platform_corpus_codes"
)

api_v1.add_resource(
	UploadResource,
	"recording-platforms/<int:recording_platform_id>/corpuscodes/upload",
	endpoint="recording_platform_corpus_codes_upload"
)
