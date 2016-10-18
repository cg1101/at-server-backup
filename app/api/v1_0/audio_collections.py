import logging

from flask import jsonify, request

from . import api_1_0 as bp
from .. import InvalidUsage
from app.api import api, caps, get_model
from db import database as db
from db.model import AudioCollection, Performance, PerformanceFlag, RecordingPlatform
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


@bp.route("audiocollections/<int:audio_collection_id>/performanceflags", methods=["GET"])
@api
@caps()
@get_model(AudioCollection)
def get_audio_collection_performance_flags(audio_collection):
	performance_flags = PerformanceFlag.query.filter_by(audio_collection_id=audio_collection.audio_collection_id).all()
	return jsonify({"performanceFlags": PerformanceFlag.dump(performance_flags)})
