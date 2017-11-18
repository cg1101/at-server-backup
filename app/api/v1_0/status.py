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
	import psycopg2
	import sqlalchemy
	user = User(
		userId=101,
		emailAddress="admin@socialinstinct.com",
		givenName="new",
		familyName="user",
	)
	print("one")
	db.session.add(user)
	print("two")
	#db.session.flush()
	print("three")
	try:
		db.session.commit()
	except sqlalchemy.exc.IntegrityError, e:
		print("caught error")
		db.session.rollback()
		return jsonify(error=True), 500

	except Exception, e:
		print("HERE", e)
		print(isinstance(e, psycopg2.Error))
		print(e.__class__)
		raise
		
	print("four")
	return jsonify(ok=True)
