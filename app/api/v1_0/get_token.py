from flask import current_app, jsonify

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from . import api_1_0 as bp
from app import create_access_token
from app.api import Field, InvalidUsage, MyForm, api, validators
from db.model import ApiAccessPair
from utils import to_timestamp


@bp.route("get-token", methods=["POST"])
@api
def get_token():

	data = MyForm(
		Field("emailAddress", is_mandatory=True,
			validators=[
				validators.is_string
		]),
		Field("key", is_mandatory=True,
			validators=[
				validators.is_string
			]
		),
		Field("secret", is_mandatory=True,
			validators=[
				validators.is_string,
			]
		),
	).get_data()

	try:
		api_access_pair = ApiAccessPair.query.filter_by(key=data["key"], secret=data["secret"]).one()
	except (NoResultFound, MultipleResultsFound):
		raise InvalidUsage("access pair not found", 401)

	if api_access_pair.user.email_address != data["emailAddress"]:
		raise InvalidUsage("incorrect email address for access pair: {0}".format(data["emailAddress"]), 401)

	if not api_access_pair.enabled:
		raise InvalidUsage("access pair is disabled", 401)

	access_token, expires_at = create_access_token(api_access_pair.user.appen_id)
	
	current_app.logger.info("access token created for user {0}: {1}".format(
		api_access_pair.user.appen_id,
		access_token
	))

	return jsonify({
		"accessToken": access_token,
		"expiresAt": to_timestamp(expires_at),
	})
