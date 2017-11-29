import csv
import json
import jsonschema

from flask import jsonify, request, session

from LRUtilities.Api import format_audio_cutup_config
from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, normalizers, simple_validators, validators
from db import database as db
from db.model import (
	AudioCheckingChangeMethod,
	AudioCheckingGroup,
	AudioCheckingSection,
	AudioStatsType,
	CorpusCode,
	Load,
	Performance,
	PerformanceMetaCategory,
	RecordingPlatform,
	SubTask,
)
from lib.audio_load import decompress_load_data


@bp.route("recording-platforms/<int:recording_platform_id>", methods=["GET"])
@api
@caps()
@get_model(RecordingPlatform)
def get_recording_platform(recording_platform):
	return jsonify({"recordingPlatform": RecordingPlatform.dump(recording_platform)})


# TODO determine if still required
@bp.route("recording-platforms/<int:recording_platform_id>/corpuscodes/scripted", methods=["GET"])
@api
@caps()
@get_model(RecordingPlatform)
def get_scripted_recording_platform_corpus_codes(recording_platform):
	corpus_codes = [corpus_code for corpus_code in recording_platform.corpus_codes if corpus_code.is_scripted]
	return jsonify({"corpusCodes": CorpusCode.dump(corpus_codes)})


# TODO determine if still required
@bp.route("recording-platforms/<int:recording_platform_id>/corpuscodes/spontaneous", methods=["GET"])
@api
@caps()
@get_model(RecordingPlatform)
def get_spontaneous_recording_platform_corpus_codes(recording_platform):
	corpus_codes = [corpus_code for corpus_code in recording_platform.corpus_codes if not corpus_code.is_scripted]
	return jsonify({"corpusCodes": CorpusCode.dump(corpus_codes)})


@bp.route("recording-platforms/<int:recording_platform_id>/audiocheckingsections", methods=["GET"])
@api
@caps()
@get_model(RecordingPlatform)
def get_audio_checking_sections(recording_platform):
	return jsonify({"audioCheckingSections": AudioCheckingSection.dump(recording_platform.audio_checking_sections)})


@bp.route("recording-platforms/<int:recording_platform_id>/audiocheckingsections", methods=["POST"])
@api
@caps()
@get_model(RecordingPlatform)
def create_audio_checking_section(recording_platform):

	data = MyForm(
		Field("startPosition", is_mandatory=True,
			validators=[
				(validators.is_number, (), dict(ge=0, lt=1))
		]),
		Field("endPosition", is_mandatory=True,
			validators=[
				(validators.is_number, (), dict(gt=0, le=1))
		]),
		Field("checkPercentage", is_mandatory=True,
			validators=[
				(validators.is_number, (), dict(gt=0, le=1))
		]),
	).get_data()

	audio_checking_section = AudioCheckingSection(
		recording_platform=recording_platform,
		start_position=data["startPosition"],
		end_position=data["endPosition"],
		check_percentage=data["checkPercentage"],
	)
	db.session.add(audio_checking_section)
	db.session.flush()

	return jsonify({"audioCheckingSection": AudioCheckingSection.dump(audio_checking_section)})


@bp.route("recording-platforms/<int:recording_platform_id>/corpuscodes/spontaneous/include", methods=["PUT"])
@api
@caps()
@get_model(RecordingPlatform)
def include_spontaneous_corpus_codes(recording_platform):
	data = MyForm(
		Field('corpusCodes', is_mandatory=True,
			validators=[
				validators.is_list,
				CorpusCode.check_all_exists,
			]
		),
	).get_data()

	included = set(data['corpusCodes'])

	for corpus_code in recording_platform.spontaneous_corpus_codes:
		corpus_code.included = corpus_code.corpus_code_id in included

	db.session.commit()

	return jsonify(success=True)


@bp.route("recording-platforms/<int:recording_platform_id>/performances", methods=["GET"])
@api
@caps()
@get_model(RecordingPlatform)
def get_performances(recording_platform):
	kwargs = {}
	
	if request.args.get("full"):
		kwargs.update(dict(use="full"))

	return jsonify(performances=Performance.dump(recording_platform.performances, **kwargs))


@bp.route("recording-platforms/<int:recording_platform_id>/audioquality", methods=["PUT"])
@api
@caps()
@get_model(RecordingPlatform)
def update_audio_quality(recording_platform):
	recording_platform.audio_quality = request.json
	db.session.commit()
	return jsonify({"recordingPlatform": RecordingPlatform.dump(recording_platform)})


@bp.route("recording-platforms/<int:recording_platform_id>/moveperformances", methods=["PUT"])
@api
@caps()
@get_model(RecordingPlatform)
def move_performances(recording_platform):

	data = MyForm(
		Field("changeMethod", is_mandatory=True, validators=[AudioCheckingChangeMethod.is_valid]),
		Field("subTaskId", is_mandatory=True, validators=[SubTask.check_exists]),
		Field("rawPieceIds", is_mandatory=True,
			validators=[
				validators.is_list,
				Performance.check_all_exists,
			]
		),
	).get_data()

	destination = SubTask.query.get(data["subTaskId"])

	performances = []

	for raw_piece_id in data["rawPieceIds"]:
		performance = Performance.query.get(raw_piece_id)
		performances.append(performance)

	moved, at_destination, no_transition, locked = recording_platform.move_performances(
		performances,
		destination,
		session["current_user"].user_id,
		data["changeMethod"]
	)
	db.session.flush()

	return jsonify({
		"atDestination": len(at_destination),
		"noTransition": len(no_transition),
		"moved": len(moved),
		"locked": len(locked),
		"performances": Performance.dump(performances, use="full"),
	})


@bp.route("recording-platforms/<int:recording_platform_id>/move-performances/upload", methods=["POST"])
@api
@caps()
@get_model(RecordingPlatform)
def upload_performance_list(recording_platform):

	data = MyForm(
		Field("changeMethod", is_mandatory=True, validators=[AudioCheckingChangeMethod.is_valid]),
		Field("subTaskId", is_mandatory=True, validators=[SubTask.check_exists]),
		Field("performanceNames", is_mandatory=True,
			validators=[
				validators.is_list,
			]
		),
	).get_data()

	destination = SubTask.query.get(data["subTaskId"])

	performances = []

	for performance_name in data["performanceNames"]:
		# TODO handle exception
		performance = Performance.query.filter_by(
			recording_platform=recording_platform,
			name=performance_name
		).one()
		performances.append(performance)

	moved, at_destination, no_transition, locked = recording_platform.move_performances(
		performances,
		destination,
		session["current_user"].user_id,
		data["changeMethod"]
	)
	db.session.flush()

	return jsonify({
		"atDestination": len(at_destination),
		"noTransition": len(no_transition),
		"moved": len(moved),
		"locked": len(locked),
		"performances": Performance.dump(performances, use="full"),
	})


@bp.route("recording-platforms/<int:recording_platform_id>/audio-stats-types", methods=["GET"])
@api
@caps()
@get_model(RecordingPlatform)
def get_recording_platform_audio_stats_types(recording_platform):
	return jsonify({"audioStatsTypes": AudioStatsType.dump(recording_platform.audio_stats_types)})


@bp.route("recording-platforms/<int:recording_platform_id>/audio-stats-types", methods=["PUT"])
@api
@caps()
@get_model(RecordingPlatform)
def update_recording_platform_audio_stats_types(recording_platform):
	data = MyForm(
		Field("audioStatsTypeIds", is_mandatory=True, validators=[
			validators.is_list,
			AudioStatsType.check_all_exists
		]),
	).get_data()

	recording_platform.selected_audio_stats_types = []
	
	for audio_stats_type_id in data["audioStatsTypeIds"]:
		audio_stats_type = AudioStatsType.query.get(audio_stats_type_id)
		recording_platform.selected_audio_stats_types.append(audio_stats_type)

	db.session.commit()
	return jsonify({"audioStatsTypes": AudioStatsType.dump(recording_platform.audio_stats_types)})
