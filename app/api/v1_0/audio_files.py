import datetime
import logging

from flask import jsonify, request

from . import api_1_0 as bp
from app import audio_server
from app.api import api, caps, get_model
from db.model import AudioFile


log = logging.getLogger(__name__)


@bp.route("audiofiles/<int:audio_file_id>", methods=["GET"])
@api
@caps()
@get_model(AudioFile)
def get_audio_file(audio_file):
	return jsonify({"audioFile": AudioFile.dump(audio_file)})


@bp.route("audiofiles/<int:audio_file_id>/url", methods=["GET"])
@api
@caps()
@get_model(AudioFile)
def get_audio_file_url(audio_file):
	start_at = request.args.get("startAt")
	end_at = request.args.get("endAt")

	if start_at:
		start_at = datetime.timedelta(seconds=float(start_at))
	
	if end_at:
		end_at = datetime.timedelta(seconds=float(end_at))

	url = audio_server.api.get_ogg_url(
		audio_file.audio_spec,
		audio_file.audio_data_location,
		audio_file.file_path,
		start_at=start_at,
		end_at=end_at
	)
	return jsonify(url=url)
