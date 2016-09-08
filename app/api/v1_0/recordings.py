import logging

from flask import jsonify

from . import api_1_0 as bp
from app.api import InvalidUsage, api, caps
from db.model import AudioFile, Recording

log = logging.getLogger(__name__)


@bp.route("recordings/<int:recording_id>")
@api
@caps()
def get_recording(recording_id):
	recording = Recording.query.get(recording_id)
	
	if not recording:
		raise InvalidUsage("recording {0} not found".format(recording_id), 404)

	return jsonify(recording=Recording.dump(recording))


@bp.route("recordings/<int:recording_id>/audiofiles")
@api
@caps()
def get_recording_audio_files(recording_id):
	
	recording = Recording.query.get(recording_id)
	
	if not recording:
		raise InvalidUsage("recording {0} not found".format(recording_id), 404)
	
	audio_files = AudioFile.query.filter_by(recording_id=recording_id).all()

	return jsonify({"audioFiles": AudioFile.dump(audio_files)})
