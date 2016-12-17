from flask import jsonify, session

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import AudioCheckingChangeMethod, AudioFile, Recording, RecordingFeedbackEntry, RecordingFlag


@bp.route("recordings/<int:recording_id>")
@api
@caps()
@get_model(Recording)
def get_recording(recording):
	return jsonify(recording=Recording.dump(recording))


@bp.route("recordings/<int:recording_id>/audiofiles")
@api
@caps()
@get_model(Recording)
def get_recording_audio_files(recording):
	return jsonify({"audioFiles": AudioFile.dump(recording.audio_files)})


@bp.route("recordings/<int:recording_id>/feedback", methods=["GET"])
@api
@caps()
@get_model(Recording)
def get_recording_feedback_entries(recording):
	return jsonify(entries=RecordingFeedbackEntry.dump(recording.feedback_entries))


@bp.route("recordings/<int:recording_id>/feedback", methods=["POST"])
@api
@caps()
@get_model(Recording)
def create_recording_feedback_entry(recording):
	data = MyForm(
		Field('comment', validators=[
			validators.is_string,
		]),
		Field('flags', validators=[
			validators.is_list,
			RecordingFlag.check_all_exists,
		]),
		Field('changeMethod', is_mandatory=True, validators=[
			AudioCheckingChangeMethod.is_valid,
		]),
	).get_data()

	change_method = AudioCheckingChangeMethod.from_name(data["changeMethod"])
	flags = RecordingFlag.get_list(*data.get('flags', []))

	entry = RecordingFeedbackEntry(
		recording=recording,
		user=session["current_user"],
		change_method=change_method,
		comment=data.get("comment"),
	)
	db.session.add(entry)
	db.session.flush()
	entry.add_flags(flags)
	db.session.commit()
	return jsonify(entry=RecordingFeedbackEntry.dump(entry))
