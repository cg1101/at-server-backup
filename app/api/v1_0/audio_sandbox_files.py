import datetime

from flask import jsonify, request, session

from . import api_1_0 as bp
from app import audio_server
from app.api import Field, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import AudioSandboxFile


@bp.route("audio-sandbox-files/<int:audio_sandbox_file_id>", methods=["GET"])
@api
@caps()
@get_model(AudioSandboxFile)
def get_audio_sandbox_file(audio_sandbox_file):
	return jsonify({"audioSandboxFile": AudioSandboxFile.dump(audio_sandbox_file)})


@bp.route("audio-sandbox-files/<int:audio_sandbox_file_id>", methods=["DELETE"])
@api
@caps()
@get_model(AudioSandboxFile)
def delete_audio_sandbox_file(audio_sandbox_file):
	db.session.delete(audio_sandbox_file)
	db.session.commit()
	return jsonify(success=True)


@bp.route("audio-sandbox-files/<int:audio_sandbox_file_id>/cutup", methods=["POST"])
@api
@caps()
@get_model(AudioSandboxFile)
def cutup_audio_sandbox_file(audio_sandbox_file):

	segmenter = audio_server.api.Segmenter(**request.json)
	
	if audio_sandbox_file.is_wav:
		segments = audio_server.api.cutup_wav_file(
			audio_sandbox_file.file_path,
			segmenter
		)

	else:
		segments = audio_server.api.cutup_raw_file(
			audio_sandbox_file.file_path,
			audio_sandbox_file.audio_spec,
			segmenter
		)

	return jsonify(segments=segments)


@bp.route("audio-sandbox-files/<int:audio_sandbox_file_id>/url", methods=["GET"])
@api
@caps()
@get_model(AudioSandboxFile)
def get_audio_sandbox_file_url(audio_sandbox_file):

	start_at = request.args.get("startAt")
	end_at = request.args.get("endAt")

	if start_at:
		start_at = datetime.timedelta(seconds=float(start_at))
	
	if end_at:
		end_at = datetime.timedelta(seconds=float(end_at))

	url = audio_server.api.get_ogg_url(
		audio_sandbox_file.audio_spec,
		audio_sandbox_file.audio_data_pointer,
		audio_sandbox_file.file_path,
		start_at=start_at,
		end_at=end_at
	)

	return jsonify(url=url)
