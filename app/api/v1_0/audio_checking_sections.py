import logging

from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import AudioCheckingSection

log = logging.getLogger(__name__)


@bp.route("audiocheckingsections/<int:audio_checking_section_id>", methods=["PUT"])
@api
@caps()
@get_model(AudioCheckingSection)
def update_audio_checking_section(audio_checking_section):
	
	data = MyForm(
		Field("startPosition", is_mandatory=True,
			validators=[
				(validators.is_number, (), dict(ge=0, lt=1))
		]),
		Field("endPosition", is_mandatory=True,
			validators=[
				(validators.is_number, (), dict(gt=0, le=1))
		]),
		Field("checkPercentage", is_mandatory=True,
			validators=[
				(validators.is_number, (), dict(gt=0, le=1))
		]),
	).get_data()

	audio_checking_section.start_position = data["startPosition"]
	audio_checking_section.end_position = data["endPosition"]
	audio_checking_section.check_percentage = data["checkPercentage"]
	db.session.commit()
	
	return jsonify({"audioCheckingSection": AudioCheckingSection.dump(audio_checking_section)})


@bp.route("audiocheckingsections/<int:audio_checking_section_id>", methods=["DELETE"])
@api
@caps()
@get_model(AudioCheckingSection)
def delete_audio_checking_section(audio_checking_section):
	db.session.delete(audio_checking_section)
	db.session.commit()
	return jsonify(success=True)
