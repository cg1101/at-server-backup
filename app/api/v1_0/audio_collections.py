import logging

from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import AudioCollection, AudioImporter, Performance, PerformanceFlag, RecordingPlatform, RecordingPlatformType
from lib.audio_import import ImportConfigAudioCollection, validate_import_data


log = logging.getLogger(__name__)


@bp.route("audiocollections/<int:audio_collection_id>")
@api
@caps()
@get_model(AudioCollection)
def get_audio_collection(audio_collection):
	"""
	Returns the audio collection.
	"""
	return jsonify({"audioCollection": AudioCollection.dump(audio_collection)})


@bp.route("audiocollections/<int:audio_collection_id>/importconfig")
@api
@get_model(AudioCollection)
def get_import_config(audio_collection):
	"""
	Returns the import config for the collection.
	"""
	if not audio_collection.importable:
		raise InvalidUsage("cannot import audio into audio collection {0}".format(audio_collection.audio_collection_id), 400)

	schema = ImportConfigAudioCollection()
	import_config = schema.dump(audio_collection).data

	return jsonify({"importConfig": import_config})


@bp.route("audiocollections/<int:audio_collection_id>/import", methods=["POST"])
@api
@get_model(AudioCollection)
def import_audio_data(audio_collection):
	audio_import_data = request.json
	validate_import_data(audio_import_data)
	recording_platform_id = audio_import_data["recordingPlatformId"]
	recording_platform = RecordingPlatform.query.get(recording_platform_id)
	
	if not recording_platform:
		raise InvalidUsage("unknown recording platform: {0}".format(recording_platform_id))

	if recording_platform.audio_collection_id != audio_collection.audio_collection_id:
		raise InvalidUsage("invalid recording platform ({0}) for audio collection {1}".format(recording_platform_id, audio_collection.audio_collection_id))
		
	performance = Performance.from_import(audio_import_data, recording_platform)
	db.session.add(performance)
	db.session.commit()
	return jsonify(success=True)


@bp.route("audiocollections/<int:audio_collection_id>/recordingplatforms")
@api
@caps()
@get_model(AudioCollection)
def get_audio_collection_recording_platforms(audio_collection):
	recording_platforms = RecordingPlatform.query.filter_by(audio_collection_id=audio_collection.audio_collection_id).all()
	return jsonify({"recordingPlatforms": RecordingPlatform.dump(recording_platforms)})


@bp.route("audiocollections/<int:audio_collection_id>/recordingplatforms", methods=["POST"])
@api
@caps()
@get_model(AudioCollection)
def create_recording_platform(audio_collection):
	data = MyForm(
		Field('recordingPlatformTypeId', is_mandatory=True,
			validators=[
				RecordingPlatformType.check_exists
		]),
		Field('audioImporterId',
			validators=[
				AudioImporter.check_exists
		]),
		Field('storageLocation', validators=[
			validators.is_string,
		]),
		Field('masterScriptFile', validators=[
			RecordingPlatform.is_valid_master_file,
		]),
		Field('masterHypothesisFile', validators=[
			RecordingPlatform.is_valid_master_file,
		]),
	).get_data()
	
	recording_platform = RecordingPlatform(
		audio_collection=audio_collection,
		recording_platform_type_id=data["recordingPlatformTypeId"],
		audio_importer_id=data.get("audioImporterId"),
		storage_location=data.get("storageLocation"),
		master_script_file=data.get("masterScriptFile"),
		master_hypothesis_file=data.get("masterHypothesisFile"),
	)
	db.session.add(recording_platform)
	db.session.commit()

	return jsonify({"recordingPlatform": RecordingPlatform.dump(recording_platform)})


@bp.route("audiocollections/<int:audio_collection_id>/performanceflags", methods=["GET"])
@api
@caps()
@get_model(AudioCollection)
def get_audio_collection_performance_flags(audio_collection):
	return jsonify({"performanceFlags": PerformanceFlag.dump(audio_collection.performance_flags)})


@bp.route("audiocollections/<int:audio_collection_id>/performanceflags", methods=["POST"])
@api
@caps()
@get_model(AudioCollection)
def create_performance_flag(audio_collection):

	data = MyForm(
		Field('name', is_mandatory=True,
			validators=[
				PerformanceFlag.check_new_name_unique(audio_collection),
		]),
		Field('severity', is_mandatory=True,
			validators=[
				PerformanceFlag.check_valid_severity
		]),
	).get_data()

	performance_flag = PerformanceFlag(
		audio_collection=audio_collection,
		name=data["name"],
		severity=data["severity"],
		enabled=True
	)
	db.session.add(performance_flag)
	db.session.commit()

	return jsonify({"performanceFlag": PerformanceFlag.dump(performance_flag)})
