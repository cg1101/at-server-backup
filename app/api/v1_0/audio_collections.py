import logging

from flask import jsonify, request

from . import api_1_0 as bp
from .. import InvalidUsage
from app.api import api, caps
from db import database as db
from db.model import AudioCollection, Performance, RecordingPlatform
from lib.AmrConfigFile import AmrConfigFile
from lib.audio_import import ImportConfigAudioCollection, validate_import_data
from lib.metadata_validation import MetaValidator

log = logging.getLogger(__name__)


@bp.route("audiocollections/<int:audio_collection_id>")
@api
@caps()
def get_audio_collection(audio_collection_id):
	"""
	Returns the audio collection.
	"""
	audio_collection = AudioCollection.query.get(audio_collection_id)
	
	if not audio_collection:
		raise InvalidUsage("audio collection {0} not found".format(audio_collection_id), 404)
	
	return jsonify({"audioCollection": AudioCollection.dump(audio_collection)})


@bp.route("audiocollections/<int:audio_collection_id>/importconfig")
@api
@caps()
def get_import_config(audio_collection_id):
	"""
	Returns the import config for the collection.
	"""
	audio_collection = AudioCollection.query.get(audio_collection_id)
	
	if not audio_collection:
		raise InvalidUsage("audio collection {0} not found".format(audio_collection_id), 404)
	
	if not audio_collection.importable:
		raise InvalidUsage("cannot import audio into audio collection {0}".format(audio_collection_id), 400)

	schema = ImportConfigAudioCollection()
	import_config = schema.dump(audio_collection).data

	return jsonify({"importConfig": import_config})


@bp.route("audiocollections/<int:audio_collection_id>/import", methods=["POST"])
@api
@caps()
def import_audio_data(audio_collection_id):
	audio_import_data = request.json
	validate_import_data(audio_import_data)
	recording_platform_id = audio_import_data["recordingPlatformId"]
	recording_platform = RecordingPlatform.query.get(recording_platform_id)
	
	if not recording_platform:
		raise InvalidUsage("Unknown recording platform: {0}".format(recording_platform_id))

	if recording_platform.audio_collection_id != audio_collection_id:
		raise InvalidUsage("Invalid recording platform ({0}) for audio collection {1}".format(recording_platform_id, audio_collection_id))
		
	performance = Performance.from_import(audio_import_data, recording_platform)
	db.session.add(performance)
	db.session.commit()
	return jsonify(success=True)


@bp.route("audiocollections/<int:audio_collection_id>/recordingplatforms")
@api
@caps()
def get_audio_collection_recording_platforms(audio_collection_id):
	
	audio_collection = AudioCollection.query.get(audio_collection_id)
	
	if not audio_collection:
		raise InvalidUsage("audio collection {0} not found".format(audio_collection_id), 404)

	recording_platforms = RecordingPlatform.query.filter_by(audio_collection_id=audio_collection_id).all()
	return jsonify({"recordingPlatforms": RecordingPlatform.dump(recording_platforms)})


# TODO move this to recording platforms, or something more general
@bp.route("audiocollections/<int:audio_collection_id>/metadata/performances/upload", methods=["POST"])
@api
@caps()
def upload_metadata_config_file(audio_collection_id):
	
	if not "configFile" in request.files:
		raise InvalidUsage("No config file provided")

	amr_config_file = AmrConfigFile.load(request.files["configFile"])

	categories = []

	for category in amr_config_file.demographics:
		validator = MetaValidator.from_amr_demographic_category(category)
		categories.append({
			"name": category.title,
			"extractor": {"key": category.id},
			"validator": validator.to_dict(),
		})

	return jsonify(categories=categories)