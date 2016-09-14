import logging

from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, validators
from db import database as db
from db.model import CorpusCode, RecordingPlatform
from lib.audio_cutup import validate_audio_cutup_config

log = logging.getLogger(__name__)


def check_corpus_code_uniqueness(data, key, code, recording_platform_id, corpus_code_id):
	query = CorpusCode.query.filter_by(
		code=code,
		recording_platform_id=recording_platform_id
	)

	query = query.filter(CorpusCode.corpus_code_id != corpus_code_id)

	if query.count() > 0:
		raise ValueError("corpus code '{0}' already exists".format(code))


@bp.route("corpuscodes", methods=["POST"])
@api
@caps()
def create_corpus_code():

	data = MyForm(
		Field("code", is_mandatory=True, validators=[
			validators.non_blank,
			# TODO need to check code/platform uniqueness
		]),
		Field("regex"),
		Field("isScripted", is_mandatory=True, validators=[
			validators.is_bool
		]),
		Field("recordingPlatformId", is_mandatory=True, validators=[
			validators.is_number,
		]),
	).get_data()
	
	recording_platform = RecordingPlatform.query.get(data["recordingPlatformId"])
	
	if not recording_platform:
		raise InvalidUsage("recording platform {0} not found".format(recording_platform_id), 404)

	corpus_code = CorpusCode(
		audio_collection_id=recording_platform.audio_collection_id,
		recording_platform=recording_platform,
		code=data["code"],
		regex=data.get("regex"),
		is_scripted=data["isScripted"],
	)
	db.session.add(corpus_code)
	db.session.flush()
	return jsonify({"corpusCode": CorpusCode.dump(corpus_code)})


@bp.route("corpuscodes/<int:corpus_code_id>", methods=["GET"])
@api
@caps()
def get_corpus_code(corpus_code_id):

	corpus_code = CorpusCode.query.get(corpus_code_id)
	
	if not corpus_code:
		raise InvalidUsage("corpus code {0} not found".format(corpus_code_id), 404)

	return jsonify({"corpusCode": CorpusCode.dump(corpus_code)})


@bp.route("corpuscodes/<int:corpus_code_id>", methods=["PUT"])
@api
@caps()
def update_corpus_code(corpus_code_id):

	corpus_code = CorpusCode.query.get(corpus_code_id)
	
	if not corpus_code:
		raise InvalidUsage("corpus code {0} not found".format(corpus_code_id), 404)
	
	data = MyForm(
		Field("code", is_mandatory=True, validators=[
			validators.non_blank,
			(check_corpus_code_uniqueness, (corpus_code.recording_platform_id, corpus_code_id)),
		]),
		Field("regex"),
		Field("isScripted", is_mandatory=True, validators=[
			validators.is_bool
		]),
	).get_data()
	
	corpus_code.code = data["code"]
	corpus_code.regex = data["regex"]
	corpus_code.is_scripted = data["isScripted"]
	db.session.commit()
	
	return jsonify({"corpusCode": CorpusCode.dump(corpus_code)})


@bp.route("corpuscodes/<int:corpus_code_id>", methods=["DELETE"])
@api
@caps()
def delete_corpus_code(corpus_code_id):

	corpus_code = CorpusCode.query.get(corpus_code_id)
	
	if not corpus_code:
		raise InvalidUsage("corpus code {0} not found".format(corpus_code_id), 404)
	
	db.session.delete(corpus_code)
	db.session.commit()
	
	return jsonify(success=True)
