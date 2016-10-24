import logging

from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import CorpusCode, ScriptedCorpusCodeGroup

log = logging.getLogger(__name__)


@bp.route("scriptedcorpuscodegroups/<int:scripted_corpus_code_group_id>", methods=["PUT"])
@api
@caps()
@get_model(ScriptedCorpusCodeGroup)
def update_scripted_corpus_code_group(scripted_corpus_code_group):

	data = MyForm(
		Field('name', is_mandatory=True,
			validators=[
				scripted_corpus_code_group.check_other_name_unique
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
	scripted_corpus_code_group.name = data["name"]
	scripted_corpus_code_group.selection_size = data["selectionSize"]
	scripted_corpus_code_group.assign_corpus_codes(data["corpusCodes"])
	
	db.session.flush()
	db.session.commit()

	return jsonify({"scriptedCorpusCodeGroup": ScriptedCorpusCodeGroup.dump(scripted_corpus_code_group)})


@bp.route("scriptedcorpuscodegroups/<int:scripted_corpus_code_group_id>", methods=["DELETE"])
@api
@caps()
@get_model(ScriptedCorpusCodeGroup)
def delete_scripted_corpus_code_group(scripted_corpus_code_group):
	db.session.delete(scripted_corpus_code_group)
	db.session.commit()
	
	return jsonify(success=True)
