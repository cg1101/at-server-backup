from flask import jsonify

from . import api_1_0 as bp
from app.api import api, caps, get_model
from db import database as db
from db.model import Transition


@bp.route("transitions/<int:transition_id>", methods=["DELETE"])
@api
@caps()
@get_model(Transition)
def delete_transition(transition):
	db.session.delete(transition)
	db.session.commit()
	return jsonify(success=True)
