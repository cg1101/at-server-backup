from flask import jsonify

from . import api_1_0 as bp
from app.api import api, caps, get_model
from db import database as db
from db.model import RecordingFeedbackEntry


@bp.route("recordingfeedback/<int:recording_feedback_entry_id>", methods=["DELETE"])
@api
@caps()
@get_model(RecordingFeedbackEntry)
def delete_recording_feedback_entry(entry):
	db.session.delete(entry)
	db.session.commit()
	return jsonify(success=True)
