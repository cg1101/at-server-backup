from flask_restful import Resource

from . import api_v1
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import PerformanceMetaCategory


class ModelResource(Resource):
	
	method_decorators = [
		get_model(PerformanceMetaCategory),
		caps(),
		api
	]

	def get(self, performance_meta_category):
		return {"metaCategory": performance_meta_category.serialize()}

	def put(self, performance_meta_category):

		data = MyForm(
			Field('name', is_mandatory=True,
				validators=[
					performance_meta_category.check_other_name_unique,
			]),
			Field('extractor', is_mandatory=True,
				normalizer=PerformanceMetaCategory.normalize_extractor,
				validators=[
					performance_meta_category.recording_platform.check_extractor
				]
			),
			Field('validatorSpec', is_mandatory=True,
				validators=[
					PerformanceMetaCategory.check_validator
				]
			),
		).get_data()

		performance_meta_category.name = data["name"]
		performance_meta_category.extractor = data.get("extractor")
		performance_meta_category.validator_spec = data["validatorSpec"]
		db.session.flush()
		return {"metaCategory": PerformanceMetaCategory.dump(performance_meta_category)}

	def delete(self, performance_meta_category):
		db.session.delete(performance_meta_category)
		db.session.commit()
		return {"deleted": True}


api_v1.add_resource(
	ModelResource,
	"performancemetacategories/<int:performance_meta_category_id>",
	endpoint="performance_meta_categories"
)
