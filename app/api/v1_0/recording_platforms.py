import logging

from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, validators
from db import database as db
from db.model import CorpusCode, RecordingPlatform, Track
from lib.audio_cutup import validate_audio_cutup_config

log = logging.getLogger(__name__)


@bp.route("recordingplatforms/<int:recording_platform_id>", methods=["GET"])
@api
@caps()
def get_recording_platform(recording_platform_id):
	
	recording_platform = RecordingPlatform.query.get(recording_platform_id)
	
	if not recording_platform:
		raise InvalidUsage("recording platform {0} not found".format(recording_platform_id), 404)
	
	return jsonify({"recordingPlatform": RecordingPlatform.dump(recording_platform)})


@bp.route("recordingplatforms/<int:recording_platform_id>/tracks", methods=["GET"])
@api
@caps()
def get_recording_platform_tracks(recording_platform_id):
	
	recording_platform = RecordingPlatform.query.get(recording_platform_id)
	
	if not recording_platform:
		raise InvalidUsage("recording platform {0} not found".format(recording_platform_id), 404)
	
	tracks = Track.query.filter_by(recording_platform_id=recording_platform_id).all()
	return jsonify(tracks=Track.dump(tracks))


@bp.route("recordingplatforms/<int:recording_platform_id>/audiocutup", methods=["PUT"])
@api
@caps()
def update_audio_cutup_config(recording_platform_id):
	
	recording_platform = RecordingPlatform.query.get(recording_platform_id)
	
	if not recording_platform:
		raise InvalidUsage("recording platform {0} not found".format(recording_platform_id), 404)
	
	audio_cutup_config = request.json
	validate_audio_cutup_config(audio_cutup_config)
	recording_platform.audio_cutup_config = audio_cutup_config
	return jsonify(success=True)


@bp.route("recordingplatforms/<int:recording_platform_id>/corpuscodes", methods=["GET"])
@api
@caps()
def get_recording_platform_corpus_codes(recording_platform_id):
	
	recording_platform = RecordingPlatform.query.get(recording_platform_id)
	
	if not recording_platform:
		raise InvalidUsage("recording platform {0} not found".format(recording_platform_id), 404)
	
	corpus_codes = CorpusCode.query.filter_by(recording_platform_id=recording_platform_id).all()
	return jsonify({"corpusCodes": CorpusCode.dump(corpus_codes)})