from flask import jsonify, request, session

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, simple_validators, validators
from db import database as db
from db.model import (
	AudioCheckingChangeMethod,
	MetadataChangeLogEntry,
	Performance,
	PerformanceFeedbackEntry,
	PerformanceFlag,
	PerformanceTransitionLogEntry,
	PerformanceMetaValue,
	Recording,
	SubTask,
	Transition
)
from lib.metadata_validation import process_received_metadata, resolve_new_metadata


@bp.route("performances/<int:raw_piece_id>", methods=["GET"])
@api
@caps()
@get_model(Performance)
def get_performance(performance):
	kwargs = {}
	
	if request.args.get("full"):
		kwargs.update(dict(use="full"))

	return jsonify(performance=Performance.dump(performance, **kwargs))


@bp.route("performances/<int:raw_piece_id>/recordings", methods=["GET"])
@api
@get_model(Performance)
def get_performance_recordings(performance):
	return jsonify(recordings=Recording.dump(performance.recordings))
	
	
@bp.route("performances/<int:raw_piece_id>/metavalues", methods=["GET"])
@api
@caps()
@get_model(Performance)
def get_performance_meta_values(performance):
	return jsonify({"metaValues": PerformanceMetaValue.dump(performance.meta_values)})


@bp.route("performances/<int:raw_piece_id>/metavalues", methods=["PUT"])
@api
@caps()
@get_model(Performance)
def update_performance_meta_values(performance):
	data = MyForm(
		Field("method", is_mandatory=True, validators=[AudioCheckingChangeMethod.is_valid]),
		Field("values", is_mandatory=True, validators=[simple_validators.is_dict()]),	# TODO all keys should be valid categories
	).get_data()
	
	meta_values = process_received_metadata(
		data["values"],
		performance.recording_platform.performance_meta_categories
	)
	
	resolve_new_metadata(
		performance,
		meta_values,
		session["current_user"],
		data["method"],
		add_log_entries=True
	)
	
	db.session.flush()
	return jsonify({"metaValues": PerformanceMetaValue.dump(performance.meta_values)})


@bp.route("performances/<int:raw_piece_id>/move", methods=["PUT"])
@api
@caps()
@get_model(Performance)
def move_performance(performance):
	data = MyForm(
		Field("subTaskId", is_mandatory=True,
			validators=[
				SubTask.check_exists,
				SubTask.for_task(performance.sub_task.task.task_id),
				Transition.is_valid_destination(performance.sub_task.sub_task_id),
		]),
	).get_data()

	performance.move_to(
		data["subTaskId"],
		AudioCheckingChangeMethod.ADMIN,
		session["current_user"].user_id
	)
	db.session.flush()
	return jsonify(performance=Performance.dump(performance))


@bp.route("performances/<int:raw_piece_id>/feedback", methods=["GET"])
@api
@caps()
@get_model(Performance)
def get_performance_feedback_entries(performance):
	return jsonify(entries=PerformanceFeedbackEntry.dump(performance.feedback_entries))


@bp.route("performances/<int:raw_piece_id>/feedback", methods=["POST"])
@api
@caps()
@get_model(Performance)
def create_performance_feedback_entry(performance):
	data = MyForm(
		Field('comment', validators=[
			validators.is_string,
		]),
		Field('flags', validators=[
			validators.is_list,
			PerformanceFlag.check_all_exists,
		]),
		Field('changeMethod', is_mandatory=True, validators=[
			AudioCheckingChangeMethod.is_valid,
		]),
	).get_data()

	entry = performance.add_feedback(session["current_user"], data["changeMethod"], data.get("comment"), data.get("flags", []))
	db.session.commit()

	return jsonify(entry=PerformanceFeedbackEntry.dump(entry))


@bp.route("performances/<int:raw_piece_id>/feedback/current", methods=["GET"])
@api
@caps()
@get_model(Performance)
def get_current_performance_feedback_entry(performance):
	return jsonify(entry=PerformanceFeedbackEntry.dump(performance.current_feedback))


@bp.route("performances/<int:raw_piece_id>/transitionlog", methods=["GET"])
@api
@caps()
@get_model(Performance)
def get_performance_transition_log_entries(performance):
	return jsonify(entries=PerformanceTransitionLogEntry.dump(performance.transition_log_entries))


@bp.route("performances/<int:raw_piece_id>/metadatachangelog", methods=["GET"])
@api
@caps()
@get_model(Performance)
def get_performance_metadata_change_log_entries(performance):
	return jsonify(entries=MetadataChangeLogEntry.dump(performance.metadata_change_log_entries))
