from flask import jsonify, request, session

from LRUtilities.Audio import AudioSpec
from . import api_1_0 as bp
from app import audio_server
from app.api import Field, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import AudioSandbox, AudioSandboxFile


@bp.route("audio-sandboxes", methods=["GET"])
@api
@caps()
def get_audio_sandboxes():
	audio_sandboxes = AudioSandbox.query.all()
	return jsonify({"audioSandboxes": AudioSandbox.dump(audio_sandboxes)})


@bp.route("audio-sandboxes", methods=["POST"])
@api
@caps()
def create_audio_sandboxes():

	data = MyForm(
		Field("name", is_mandatory=True, validators=[
			validators.non_blank,
			AudioSandbox.check_new_name_unique(),
		]),
	).get_data()
	
	audio_sandbox = AudioSandbox(
		name=data["name"],
		user=session["current_user"]
	)

	db.session.add(audio_sandbox)
	db.session.flush()

	return jsonify({"audioSandbox": AudioSandbox.dump(audio_sandbox)})


@bp.route("audio-sandboxes/<int:audio_sandbox_id>", methods=["GET"])
@api
@caps()
@get_model(AudioSandbox)
def get_audio_sandbox(audio_sandbox):
	return jsonify({"audioSandbox": AudioSandbox.dump(audio_sandbox)})


@bp.route("audio-sandboxes/<int:audio_sandbox_id>", methods=["DELETE"])
@api
@caps()
@get_model(AudioSandbox)
def delete_audio_sandbox(audio_sandbox):
	db.session.delete(audio_sandbox)
	db.session.commit()
	return jsonify(success=True)


@bp.route("audio-sandboxes/<int:audio_sandbox_id>/files", methods=["GET"])
@api
@caps()
@get_model(AudioSandbox)
def get_audio_sandbox_files(audio_sandbox):
	return jsonify(files=AudioSandboxFile.dump(audio_sandbox.files))


@bp.route("audio-sandboxes/<int:audio_sandbox_id>/files/raw", methods=["POST"])
@api
@caps()
@get_model(AudioSandbox)
def add_raw_audio_sandbox_file(audio_sandbox):

	data = MyForm(
		Field("filePath", is_mandatory=True, validators=[
			validators.non_blank,
		]),
		Field("audioSpec", is_mandatory=True, validators=[
			# TODO audio spec validator
		]),
	).get_data()
	
	spec = AudioSpec(**data["audioSpec"])
	data_pointer = audio_server.api.get_data_pointer(data["filePath"])
	waveform_data = audio_server.api.get_waveform(spec, data_pointer, data["filePath"])

	audio_sandbox_file = AudioSandboxFile(
		audio_sandbox=audio_sandbox,
		file_path=data["filePath"],
		audio_spec=spec.to_dict(),
		audio_data_pointer=data_pointer.to_dict(),
		is_wav=False,
		data={
			"stats": {
				"waveform": waveform_data,
			}
		}
	)

	db.session.add(audio_sandbox_file)
	db.session.flush()

	return jsonify({"audioSandboxFile": AudioSandboxFile.dump(audio_sandbox_file)})


@bp.route("audio-sandboxes/<int:audio_sandbox_id>/files/wav", methods=["POST"])
@api
@caps()
@get_model(AudioSandbox)
def add_wav_audio_sandbox_file(audio_sandbox):

	data = MyForm(
		Field("filePath", is_mandatory=True, validators=[
			validators.non_blank,
		]),
	).get_data()
	
	spec, data_pointer = audio_server.api.parse_wav(data["filePath"])
	waveform_data = audio_server.api.get_waveform(spec, data_pointer, data["filePath"])

	audio_sandbox_file = AudioSandboxFile(
		audio_sandbox=audio_sandbox,
		file_path=data["filePath"],
		audio_spec=spec.to_dict(),
		audio_data_pointer=data_pointer.to_dict(),
		is_wav=True,
		data={
			"stats": {
				"waveform": waveform_data,
			}
		}
	)

	db.session.add(audio_sandbox_file)
	db.session.flush()

	return jsonify({"audioSandboxFile": AudioSandboxFile.dump(audio_sandbox_file)})
