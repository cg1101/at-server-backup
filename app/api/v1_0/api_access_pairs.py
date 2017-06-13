from flask import jsonify, request, session

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import ApiAccessPair, User


@bp.route("api-access-pairs", methods=["GET"])
@api
@caps()
def get_api_access_pairs():
	api_access_pairs = ApiAccessPair.query.filter_by(user=session["current_user"]).all()
	return jsonify({"apiAccessPairs": ApiAccessPair.dump(api_access_pairs)})


@bp.route("api-access-pairs/<int:api_access_pair_id>", methods=["GET"])
@api
@caps()
@get_model(ApiAccessPair)
def get_api_access_pair(api_access_pair):
	return jsonify({"apiAccessPair": ApiAccessPair.dump(api_access_pair)})


@bp.route("api-access-pairs/<int:api_access_pair_id>", methods=["PUT"])
@api
@caps()
@get_model(ApiAccessPair)
def update_api_access_pair(api_access_pair):

	data = MyForm(
		Field("enabled", is_mandatory=True,
			validators=[
				validators.is_bool
		]),
	).get_data()

	api_access_pair.enabled = data["enabled"]
	db.session.commit()

	return jsonify({"apiAccessPair": ApiAccessPair.dump(api_access_pair)})


@bp.route("api-access-pairs", methods=["POST"])
@api
@caps()
def add_api_access_pair():
	
	data = MyForm(
		Field("description", is_mandatory=True,
			validators=[
				validators.is_string
		]),
	).get_data()

	api_access_pair = ApiAccessPair.create(session["current_user"].user_id, data["description"])

	db.session.add(api_access_pair)
	db.session.flush()

	return jsonify({"apiAccessPair": ApiAccessPair.dump(api_access_pair)})
