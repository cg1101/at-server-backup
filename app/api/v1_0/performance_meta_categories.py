import logging

from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import PerformanceMetaCategory, RecordingPlatform

log = logging.getLogger(__name__)


@bp.route("performancemetacategories/<int:performance_meta_category_id>", methods=["PUT"])
@api
@caps()
@get_model(PerformanceMetaCategory)
def update_performance_meta_category(performance_meta_category):

	data = MyForm(
		Field('name', is_mandatory=True,
			validators=[
				performance_meta_category.check_other_name_unique,
		]),
		Field('extractor', 
			validators=[
				performance_meta_category.recording_platform.check_extractor
			]
		),
		Field('validator', is_mandatory=True,
			validators=[
				PerformanceMetaCategory.check_validator
			]
		),
	).get_data()

	performance_meta_category.name = data["name"]
	performance_meta_category.extractor = data.get("extractor")
	performance_meta_category.validator = data["validator"]
	db.session.flush()

	return jsonify({"metaCategory": PerformanceMetaCategory.dump(performance_meta_category)})


@bp.route("performancemetacategories/<int:performance_meta_category_id>", methods=["DELETE"])
@api
@caps()
@get_model(PerformanceMetaCategory)
def delete_performance_meta_category(performance_meta_category):
	db.session.delete(performance_meta_category)
	db.session.commit()
	return jsonify(success=True)
