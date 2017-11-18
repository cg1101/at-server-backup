from flask import jsonify

from . import api_1_0 as bp
from app.api import api


@bp.route("status", methods=["GET"])
@api
def get_status():
	return jsonify(success=True)


@bp.route("test", methods=["GET"])
def test_endpoint():
	from db.model import User
	from db import database as db
	user = User(
		userId=101,
		emailAddress="admin@socialinstinct.com",
		givenName="new",
		familyName="user",
	)
	print("one")
	db.session.add(user)
	print("two")
	db.session.flush()
	print("three")
	db.session.commit()
	print("four")
	return jsonify(ok=True)
