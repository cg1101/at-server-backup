from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import AudioCheckingGroup, CorpusCode


@bp.route("audiocheckinggroups/<int:audio_checking_group_id>", methods=["PUT"])
@api
@caps()
@get_model(AudioCheckingGroup)
def update_audio_checking_group(audio_checking_group):

	data = MyForm(
		Field('name', is_mandatory=True,
			validators=[
				audio_checking_group.check_other_name_unique
		]),
		Field('selectionSize', is_mandatory=True,
			validators=[
				(validators.is_number, (), dict(min_value=1)),
			]
		),
		Field('corpusCodes', is_mandatory=True,
			validators=[
				validators.is_list,
				CorpusCode.check_all_exists,
			]
		),
	).get_data()

	# update group
	audio_checking_group.name = data["name"]
	audio_checking_group.selection_size = data["selectionSize"]
	audio_checking_group.assign_corpus_codes(data["corpusCodes"])
	
	db.session.flush()
	db.session.commit()

	return jsonify({"audioCheckingGroup": AudioCheckingGroup.dump(audio_checking_group)})


@bp.route("audiocheckinggroups/<int:audio_checking_group_id>", methods=["DELETE"])
@api
@caps()
@get_model(AudioCheckingGroup)
def delete_audio_checking_group(audio_checking_group):
	db.session.delete(audio_checking_group)
	db.session.commit()
	return jsonify(success=True)
