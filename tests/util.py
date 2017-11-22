import json
import jwt
import pytest
import sqlalchemy

from flask import current_app

from db.model import ModelMixin, User
from tests.sample_data import keys as sample_data


# mime types
MIMETYPE_JSON = "application/json"

# status codes
STATUS_OK = 200
STATUS_BAD_REQUEST = 400
STATUS_UNAUTHORIZED = 401


def create_access_token(appen_id):
	payload = {
		"appenId": appen_id,

		# FIXME use real values
		"userType": None,
		"roles": None,
		"caps": None,		
	}

	token = jwt.encode(payload, current_app.config["APPEN_API_SECRET_KEY"], algorithm="HS256")
	return token.decode()


def send_auth_request(fn, *args, **kwargs):
		
	# test without authentication
	response = fn(*args, **kwargs)
	check_status_code(response, STATUS_UNAUTHORIZED)

	# test with authentication
	headers = kwargs.get("headers", {})
	headers.update({"X-Appen-Auth": create_access_token(sample_data.test_user_appen_id)})
	kwargs.update({"headers": headers})
	response = fn(*args, **kwargs)
	return response


def to_json_string(obj):
	return json.dumps(obj, sort_keys=True, indent=4)


def check_mimetype(response, expected):
	assert response.mimetype == expected, "bad mimetype - expected: {0}, actual: {1}".format(expected, response.mimetype)


def check_status_code(response, expected):
	assert response.status_code == expected, "bad status code - expected: {0}, actual: {1}".format(expected, response.status_code)


def check_model(obj):
	assert isinstance(obj, ModelMixin), "{0} is not a model".format(obj)


# endpoint validators

def validate_delete_endpoint(test_client, session, model, endpoint, protected=True, status_code=STATUS_OK, mimetype=MIMETYPE_JSON):
	"""
	Tests and endpoint that deletes a model.
	"""

	# check test params
	assert isinstance(endpoint, str), endpoint

	# get response

	if protected:
		response = send_auth_request(test_client.delete, endpoint)
	else:
		response = test_client.delete(endpoint)

	# validate response
	check_status_code(response, status_code)
	check_mimetype(response, mimetype)

	# for json response
	if response.mimetype == MIMETYPE_JSON:
					
		# should be valid json
		data = json.loads(response.data)
					
		# all end points should return a dict
		assert isinstance(data, dict), "endpoint did not return dict: {0}".format(data)

		# check response data
		assert "deleted" in data and data["deleted"] == True, "invalid delete response data: {0}".format(data)

	# unhandled
	else:
		raise RuntimeError("unhandled mimetype: {0}".format(response.mimetype))

	# check that model has been deleted
	with pytest.raises(sqlalchemy.exc.InvalidRequestError):
		session.refresh(model)


def validate_update_endpoint(test_client, session, endpoint, updates, return_key, id_key, model_cls, protected=True, status_code=STATUS_OK, mimetype=MIMETYPE_JSON):
	"""
	Tests an endpoint that updates a model.
	"""

	# check test params
	assert isinstance(endpoint, str), endpoint
	assert isinstance(return_key, str), return_key
	assert isinstance(id_key, str), id_key
	assert issubclass(model_cls, ModelMixin)

	# get response

	if protected:
		response = send_auth_request(test_client.put, endpoint, data=json.dumps(updates), content_type=MIMETYPE_JSON)
	else:
		response = test_client.put(endpoint, data=json.dumps(updates), content_type=MIMETYPE_JSON)

	# validate response
	check_status_code(response, status_code)
	check_mimetype(response, mimetype)

	# for json response
	if response.mimetype == MIMETYPE_JSON:
					
		# should be valid json
		data = json.loads(response.data)
					
		# all end points should return a dict
		assert isinstance(data, dict), "endpoint did not return dict: {0}".format(data)

		# check return key exists
		assert return_key in data, "return key '{0}' missing: {1}".format(return_key, data)

		# check id key exists
		assert id_key in data[return_key], "id key '{0}' missing: {1}".format(id_key, data[return_key])

		# get updated model from db
		model_id = data[return_key][id_key]
		model = session.query(model_cls).get(model_id)
		assert model, "model does not exist in db: {0}".format(data[return_key])
		session.refresh(model)

		# check serialization
		response_str = to_json_string(data[return_key])
		model_str = to_json_string(model.serialize())
		assert response_str == model_str, "response: {0}, model: {1}".format(response_str, model_str)
		return model

	# unhandled
	else:
		raise RuntimeError("unhandled mimetype: {0}".format(response.mimetype))


def validate_create_endpoint(test_client, session, endpoint, data, return_key, id_key, model_cls, protected=True, status_code=STATUS_OK, mimetype=MIMETYPE_JSON):
	"""
	Tests an endpoint that creates a model.
	"""

	# check test params
	assert isinstance(endpoint, str), endpoint
	assert isinstance(return_key, str), return_key
	assert isinstance(id_key, str), id_key
	assert issubclass(model_cls, ModelMixin)

	# get response

	if protected:
		response = send_auth_request(test_client.post, endpoint, data=json.dumps(data), content_type=MIMETYPE_JSON)
	else:
		response = test_client.post(endpoint, data=json.dumps(data), content_type=MIMETYPE_JSON)

	# validate response
	check_status_code(response, status_code)
	check_mimetype(response, mimetype)

	# for json response
	if response.mimetype == MIMETYPE_JSON:
					
		# should be valid json
		data = json.loads(response.data)
					
		# all end points should return a dict
		assert isinstance(data, dict), "endpoint did not return dict: {0}".format(data)

		# check return key exists
		assert return_key in data, "return key '{0}' missing: {1}".format(return_key, data)

		# check id key exists
		assert id_key in data[return_key], "id key '{0}' missing: {1}".format(id_key, data[return_key])

		# check model exists in db
		model_id = data[return_key][id_key]
		model = session.query(model_cls).get(model_id)
		assert model, "model does not exist in db: {0}".format(data[return_key])

		# check serialization
		response_str = to_json_string(data[return_key])
		model_str = to_json_string(model.serialize())
		assert response_str == model_str, "response: {0}, model: {1}".format(response_str, model_str)

	# unhandled
	else:
		raise RuntimeError("unhandled mimetype: {0}".format(response.mimetype))


def validate_get_endpoint(test_client, model, endpoint, return_key, protected=True, status_code=STATUS_OK, mimetype=MIMETYPE_JSON):
	"""
	Tests an endpoint that returns a model.
	"""

	# check test params
	assert isinstance(endpoint, str), endpoint
	check_model(model)

	# get response

	if protected:
		response = send_auth_request(test_client.get, endpoint)
	else:
		response = test_client.get(endpoint)
				
	# validate response
	check_status_code(response, status_code)
	check_mimetype(response, mimetype)

	# for json response
	if response.mimetype == MIMETYPE_JSON:
					
		# should be valid json
		data = json.loads(response.data)
					
		# all end points should return a dict
		assert isinstance(data, dict), "endpoint did not return dict: {0}".format(data)

		# check return key exists
		assert return_key in data, "return key '{0}' missing: {1}".format(return_key, data)

		# check expected output
		expected = to_json_string(model.serialize())
		actual = to_json_string(data[return_key])
		assert expected == actual, "expected: {0}, actual: {1}".format(expected, actual)

	# unhandled
	else:
		raise RuntimeError("unhandled mimetype: {0}".format(response.mimetype))


def validate_get_list_endpoint(test_client, models, endpoint, return_key, protected=True, status_code=STATUS_OK, mimetype=MIMETYPE_JSON):
	"""
	Tests an endpoint that returns a list of models.
	"""

	# check test params
	assert isinstance(endpoint, str), endpoint
	assert isinstance(models, list), models
	assert len(models), "empty model list:{0}".format(models)

	for model in models:
		check_model(model)

	# get response

	if protected:
		response = send_auth_request(test_client.get, endpoint)
	else:
		response = test_client.get(endpoint)
				
	# validate response
	check_status_code(response, status_code)
	check_mimetype(response, mimetype)

	# for json response
	if response.mimetype == MIMETYPE_JSON:
					
		# should be valid json
		data = json.loads(response.data)
					
		# all end points should return a dict
		assert isinstance(data, dict), "endpoint did not return dict: {0}".format(data)

		# check return key exists
		assert return_key in data, "return key '{0}' missing: {1}".format(return_key, data)

		# check expected output
		expected = to_json_string([model.serialize() for model in models])
		actual = to_json_string(data[return_key])
		assert expected == actual, "expected: {0}, actual: {1}".format(expected, actual)

	# unhandled
	else:
		raise RuntimeError("unhandled mimetype: {0}".format(response.mimetype))
