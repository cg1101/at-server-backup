from flask import jsonify, request, session

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, simple_validators, validators
from db import database as db
from db.model import BatchRouter


@bp.route("batch-routers/<int:batch_router_id>", methods=["GET"])
@api
@caps()
@get_model(BatchRouter)
def get_batch_router(batch_router):
	return jsonify({"batchRouter": batch_router.serialize()})


@bp.route("batch-routers/<int:batch_router_id>", methods=["PUT"])
@api
@caps()
@get_model(BatchRouter)
def update_batch_router(batch_router):

	data = MyForm(
		Field("enabled", validators=[
			validators.is_bool,
		]),
		Field("name", validators=[
			validators.is_string,
			# TODO check unique
		]),
		Field("subTasks", validators=[
			simple_validators.is_dict,
			# TODO more complex?
		])
	).get_data()

	if "enabled" in data:
		batch_router.enabled = data["enabled"]

	if "name" in data:
		batch_router.name = data["name"]

	if "subTasks" in data:
		
		for sub_task in batch_router.sub_tasks:
			db.session.delete(sub_task)

		db.session.flush()
		batch_router.update_sub_task_criteria(data["subTasks"])
	
	db.session.commit()
	return jsonify({"batchRouter": batch_router.serialize()})


@bp.route("batch-routers/<int:batch_router_id>", methods=["DELETE"])
@api
@caps()
@get_model(BatchRouter)
def delete_batch_router(batch_router):
	db.session.delete(batch_router)
	db.session.commit()
	return jsonify(deleted=True)
