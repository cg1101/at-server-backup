from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import CorpusCode, RecordingPlatform


@bp.route("corpuscodes/<int:corpus_code_id>", methods=["GET"])
@api
@caps()
@get_model(CorpusCode)
def get_corpus_code(corpus_code):
	return jsonify({"corpusCode": CorpusCode.dump(corpus_code)})


@bp.route("corpuscodes/<int:corpus_code_id>", methods=["PUT"])
@api
@caps()
@get_model(CorpusCode)
def update_corpus_code(corpus_code):

	data = MyForm(
		Field("code", is_mandatory=True, validators=[
			corpus_code.check_updated_code_unique,
		]),
		Field("regex"),
		Field("isScripted", is_mandatory=True, validators=[
			validators.is_bool
		]),
	).get_data()
	
	corpus_code.code = data.get("code")
	corpus_code.regex = data["regex"]
	corpus_code.is_scripted = data["isScripted"]
	db.session.commit()
	
	return jsonify({"corpusCode": CorpusCode.dump(corpus_code)})


@bp.route("corpuscodes/<int:corpus_code_id>", methods=["DELETE"])
@api
@caps()
@get_model(CorpusCode)
def delete_corpus_code(corpus_code):
	db.session.delete(corpus_code)
	db.session.commit()
	return jsonify(success=True)
