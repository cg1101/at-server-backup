import logging

from flask import jsonify

from . import api_1_0 as bp
from app.api import InvalidUsage, api, caps
from db.model import RecordingPlatform, Track

log = logging.getLogger(__name__)


@bp.route("recordingplatforms/<int:recording_platform_id>/tracks")
@api
@caps()
def get_recording_platform_tracks(recording_platform_id):
	
	recording_platform = RecordingPlatform.query.get(recording_platform_id)
	
	if not recording_platform:
		raise InvalidUsage("recording platform {0} not found".format(recording_platform_id), 404)
	
	tracks = Track.query.filter_by(recording_platform_id=recording_platform_id).all()

	return jsonify(tracks=Track.dump(tracks))
