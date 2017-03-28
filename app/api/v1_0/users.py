from flask import jsonify

from . import api_1_0 as bp
from app.api import api, caps, get_model
from db.model import User


@bp.route("users/<int:user_id>", methods=["GET"])
@api
@caps()
@get_model(User)
def user(user):
	return jsonify(user=User.dump(user))
