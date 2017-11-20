import json
import jwt

from app import create_app
from db import database as db
from db.model import User


class UnitTestUtil(object):
	"""
	Utilities for unit tests.
	"""

	# mime types
	MIMETYPE_JSON = "application/json"

	# status codes
	STATUS_OK = 200
	STATUS_BAD_REQUEST = 400
	STATUS_UNAUTHORIZED = 401

	def __init__(self):
		self.app = create_app("testing")
		self.test_client = self.app.test_client()
		self.user = self.get_test_user()
		self.access_token = self.create_access_token()

	# TODO include as sample data - run before this object is created
	def get_test_user(self):

		email_address = "test-user@appen.com"

		# check if user exists
		with self.app.app_context():
		
			query = db.session.query(User).filter_by(email_address=email_address)
			
			if not query.count():

				user = User(
					appen_id=1,
					email_address=email_address,
					given_name="Test",
					family_name="User",
				)

				db.session.add(user)
				db.session.commit()

			user = query.one()
			user = user.serialize()
		
		return user
	
	def create_access_token(self):
		payload = {
			"appenId": self.user["userId"],

			# FIXME use real values
			"userType": None,
			"roles": None,
			"caps": None,		
		}

		token = jwt.encode(payload, self.app.config["APPEN_API_SECRET_KEY"], algorithm="HS256")
		return token.decode()
	
	def send_auth_request(self, fn, *args, **kwargs):
		
		# test without authentication
		response = fn(*args, **kwargs)
		assert response.status_code == self.STATUS_UNAUTHORIZED, response.status_code

		# test with authentication
		headers = kwargs.get("headers", {})
		headers.update({"X-Appen-Auth": self.access_token})
		kwargs.update({"headers": headers})
		response = fn(*args, **kwargs)
		return response

	@staticmethod
	def serialize(obj):
		return json.dumps(obj, sort_keys=True)

	# unit test decorators

	def get_list_endpoint(self, return_key=None, protected=True, status_code=STATUS_OK, mimetype=MIMETYPE_JSON):
		"""
		Tests an endpoint that returns a list of models.
		"""
		
		def customized_decorator(fn):

			# validate customization
			assert return_key

			def decorator(*args, **kwargs):
				with self.app.app_context():
					endpoint, models = fn(*args, **kwargs)

					# check test params
					assert isinstance(endpoint, str), endpoint
					assert isinstance(models, list), models
					assert len(models), models

					# get response

					if protected:
						response = self.send_auth_request(self.test_client.get, endpoint)
					else:
						response = self.test_client.get(endpoint)
				
					# validate response
					assert response.status_code == status_code, response.status_code
					assert response.mimetype == mimetype, response.mimetype

					# for json response
					if response.mimetype == self.MIMETYPE_JSON:
					
						# should be valid json
						data = json.loads(response.data)
					
						# all end points should return a dict
						assert isinstance(data, dict), data

						# check return key exists
						assert return_key in data, data

						# check expected output
						expected = self.serialize([model.serialize() for model in models])
						actual = self.serialize(data[return_key])
						assert expected == actual, "expected: {0}, actual: {1}".format(expected, actual)

					# unhandled
					else:
						raise RuntimeError("unhandled mimetype: {0}".format(response.mimetype))

			return decorator

		return customized_decorator


util = UnitTestUtil()
