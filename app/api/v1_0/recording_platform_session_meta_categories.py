import csv

from flask import request
from flask_restful import Resource

from LRUtilities.DataCollection import AmrConfigFile
from . import api_v1
from app.api import Field, MyForm, api, caps, get_model, simple_validators, validators
from db import database as db
from db.model import PerformanceMetaCategory, RecordingPlatform
from lib.metadata_validation import MetaValidator


class ListResource(Resource):
	
	method_decorators = [
		get_model(RecordingPlatform),
		caps(),
		api
	]

	def get(self, recording_platform):
		return {"metaCategories": PerformanceMetaCategory.dump(recording_platform.performance_meta_categories)}

	def post(self, recording_platform):

		data = MyForm(
			Field('name', is_mandatory=True,
				validators=[
					(PerformanceMetaCategory.check_name_unique, (recording_platform,)),
			]),
			Field('extractor', is_mandatory=True,
				normalizer=PerformanceMetaCategory.normalize_extractor,
				validators=[
					recording_platform.check_extractor,
				]
			),
			Field('validatorSpec', is_mandatory=True,
				validators=[
					PerformanceMetaCategory.check_validator,
				]
			),
		).get_data()

		performance_meta_category = PerformanceMetaCategory(
			recording_platform=recording_platform,
			name=data["name"],
			extractor=data.get("extractor"),
			validator_spec=data["validatorSpec"],
		)

		db.session.add(performance_meta_category)
		db.session.commit()
		return {"metaCategory": performance_meta_category.serialize()}


class UploadResource(Resource):

	method_decorators = [
		get_model(RecordingPlatform),
		caps(),
		api
	]

	def post(self, recording_platform):

		# TODO check configured loader

		if recording_platform.performance_meta_categories:
			raise InvalidUsage("performance meta categories already exist; unable to upload config file")

		if not "file" in request.files:
			raise InvalidUsage("no config file provided")

		amr_config_file = AmrConfigFile.load(request.files["file"])

		for amr_category in amr_config_file.demographics:
			validator = MetaValidator.from_amr_demographic_category(amr_category)

			meta_category = PerformanceMetaCategory(
				recording_platform=recording_platform,
				name=amr_category.title,
				extractor={"source": "Log File", "key": amr_category.id},	# TODO get log file string from loader constant
				validator_spec=validator.to_dict(),
			)

			db.session.add(meta_category)

		db.session.commit()
		return {"metaCategories": PerformanceMetaCategory.dump(recording_platform.performance_meta_categories)}



api_v1.add_resource(
	ListResource,
	"recording-platforms/<int:recording_platform_id>/performancemetacategories",
	endpoint="recording_platform_session_meta_categories"
)

api_v1.add_resource(
	UploadResource,
	"recording-platforms/<int:recording_platform_id>/performancemetacategories/upload",
	endpoint="recording_platform_session_meta_categories_upload"
)
