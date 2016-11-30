import jsonschema
import logging

from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, simple_validators, validators
from db import database as db
from db.model import AudioCheckingGroup, AudioCheckingSection, CorpusCode, Performance, PerformanceMetaCategory, RecordingPlatform, RecordingPlatformType, Track
from lib.AmrConfigFile import AmrConfigFile
from lib.audio_cutup import validate_audio_cutup_config
from lib.metadata_validation import MetaValidator

log = logging.getLogger(__name__)


@bp.route("recordingplatformtypes", methods=["GET"])
@api
@caps()
def get_recording_platform_types():
	recording_platform_types = RecordingPlatformType.query.all()
	return jsonify({"recordingPlatformTypes": RecordingPlatformType.dump(recording_platform_types)})


@bp.route("recordingplatforms/<int:recording_platform_id>", methods=["GET"])
@api
@caps()
@get_model(RecordingPlatform)
def get_recording_platform(recording_platform):
	return jsonify({"recordingPlatform": RecordingPlatform.dump(recording_platform)})


@bp.route("recordingplatforms/<int:recording_platform_id>/tracks", methods=["GET"])
@api
@caps()
@get_model(RecordingPlatform)
def get_recording_platform_tracks(recording_platform):
	return jsonify(tracks=Track.dump(recording_platform.tracks))


@bp.route("recordingplatforms/<int:recording_platform_id>/tracks", methods=["POST"])
@api
@caps()
@get_model(RecordingPlatform)
def create_track(recording_platform):

	data = MyForm(
		Field("trackIndex", is_mandatory=True, validators=[
			simple_validators.is_number(min_value=0),
			Track.check_new_index_unique(recording_platform),
		]),
		Field("name", is_mandatory=True, validators=[
			validators.non_blank,
			Track.check_new_name_unique(recording_platform),
		]),
	).get_data()
	
	track = Track(
		recording_platform=recording_platform,
		track_index=data["trackIndex"],
		name=data["name"],
	)
	db.session.add(track)
	db.session.flush()

	return jsonify(track=Track.dump(track))


@bp.route("recordingplatforms/<int:recording_platform_id>/audiocutup", methods=["PUT"])
@api
@caps()
@get_model(RecordingPlatform)
def update_audio_cutup_config(recording_platform):
	audio_cutup_config = validate_audio_cutup_config(request.json)
	recording_platform.audio_cutup_config = audio_cutup_config
	db.session.commit()
	return jsonify({"recordingPlatform": RecordingPlatform.dump(recording_platform)})


@bp.route("recordingplatforms/<int:recording_platform_id>/corpuscodes", methods=["GET"])
@api
@caps()
@get_model(RecordingPlatform)
def get_recording_platform_corpus_codes(recording_platform):
	return jsonify({"corpusCodes": CorpusCode.dump(recording_platform.corpus_codes)})


@bp.route("recordingplatforms/<int:recording_platform_id>/corpuscodes", methods=["POST"])
@api
@caps()
@get_model(RecordingPlatform)
def create_corpus_code(recording_platform):

	data = MyForm(
		Field("code", default="", validators=[
			# TODO need to check code/platform uniqueness
		]),
		Field("regex"),
		Field("isScripted", is_mandatory=True, validators=[
			validators.is_bool
		]),
	).get_data()
	
	corpus_code = CorpusCode(
		recording_platform=recording_platform,
		code=data["code"],
		regex=data.get("regex"),
		is_scripted=data["isScripted"],
	)
	db.session.add(corpus_code)
	db.session.flush()
	return jsonify({"corpusCode": CorpusCode.dump(corpus_code)})


@bp.route("recordingplatforms/<int:recording_platform_id>/corpuscodes/scripted", methods=["GET"])
@api
@caps()
@get_model(RecordingPlatform)
def get_scripted_recording_platform_corpus_codes(recording_platform):
	corpus_codes = [corpus_code for corpus_code in recording_platform.corpus_codes if corpus_code.is_scripted]
	return jsonify({"corpusCodes": CorpusCode.dump(corpus_codes)})


@bp.route("recordingplatforms/<int:recording_platform_id>/corpuscodes/spontaneous", methods=["GET"])
@api
@caps()
@get_model(RecordingPlatform)
def get_spontaneous_recording_platform_corpus_codes(recording_platform):
	corpus_codes = [corpus_code for corpus_code in recording_platform.corpus_codes if not corpus_code.is_scripted]
	return jsonify({"corpusCodes": CorpusCode.dump(corpus_codes)})


@bp.route("recordingplatforms/<int:recording_platform_id>/corpuscodes/upload", methods=["POST"])
@api
@caps()
@get_model(RecordingPlatform)
def upload_recording_platform_corpus_codes(recording_platform):
	
	if recording_platform.corpus_codes:
		raise InvalidUsage("recording platform already has corpus codes")
	
	schema = {
		"type": "array",
		"minItems": 1,
		"items": {
			"type": "object",
			"required": ["code", "isScripted"],
			"properties": {
				"code": {
					"type": "string",
				},
				"isScripted": {
					"type": "boolean"
				},
				"regex": {
					"type": ["string", "null"]
				}
			}
		}
	}

	try:
		jsonschema.validate(request.json, schema)
	except jsonschema.ValidationError:
		raise InvalidUsage("invalid corpus code list uploaded")

	for data in request.json:
		corpus_code = CorpusCode(
			recording_platform=recording_platform,
			code=data["code"],
			regex=data.get("regex"),
			is_scripted=data["isScripted"],
		)
		db.session.add(corpus_code)

	db.session.flush()
	db.session.commit()
	return jsonify({"corpusCodes": CorpusCode.dump(recording_platform.corpus_codes)})


@bp.route("recordingplatforms/<int:recording_platform_id>/audiocheckinggroups", methods=["GET"])
@api
@caps()
@get_model(RecordingPlatform)
def get_recording_platform_audio_checking_groups(recording_platform):
	return jsonify({"audioCheckingGroups": AudioCheckingGroup.dump(recording_platform.audio_checking_groups)})


@bp.route("recordingplatforms/<int:recording_platform_id>/audiocheckinggroups", methods=["POST"])
@api
@caps()
@get_model(RecordingPlatform)
def create_audio_checking_group(recording_platform):

	data = MyForm(
		Field('name', is_mandatory=True,
			validators=[
				(AudioCheckingGroup.check_name_unique, (recording_platform,)),
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

	# create group
	audio_checking_group = AudioCheckingGroup(
		recording_platform=recording_platform,
		name=data["name"],
		selection_size=data["selectionSize"],
	)
	db.session.add(audio_checking_group)
	db.session.flush()

	# assign corpus codes
	audio_checking_group.assign_corpus_codes(data["corpusCodes"])
	db.session.commit()
	
	return jsonify({"audioCheckingGroup": AudioCheckingGroup.dump(audio_checking_group)})


@bp.route("recordingplatforms/<int:recording_platform_id>/performancemetacategories", methods=["GET"])
@api
@caps()
@get_model(RecordingPlatform)
def get_performance_meta_categories(recording_platform):
	return jsonify({"metaCategories": PerformanceMetaCategory.dump(recording_platform.performance_meta_categories)})


@bp.route("recordingplatforms/<int:recording_platform_id>/performancemetacategories", methods=["POST"])
@api
@caps()
@get_model(RecordingPlatform)
def create_performance_meta_category(recording_platform):

	data = MyForm(
		Field('name', is_mandatory=True,
			validators=[
				(PerformanceMetaCategory.check_name_unique, (recording_platform,)),
		]),
		Field('extractor', 
			validators=[
				recording_platform.check_extractor,
			]
		),
		Field('validatorSpec', is_mandatory=True,
			validators=[
				PerformanceMetaCategory.check_validator,
			]
		),
	).get_data()

	performance_meta_category = PerformanceMetaCategory(
		recording_platform=recording_platform,
		name=data["name"],
		extractor=data.get("extractor"),
		validator_spec=data["validatorSpec"],
	)
	db.session.add(performance_meta_category)
	db.session.commit()

	return jsonify({"metaCategory": PerformanceMetaCategory.dump(performance_meta_category)})


@bp.route("recording_platforms/<int:recording_platform_id>/performancemetacategories/upload", methods=["POST"])
@api
@caps()
@get_model(RecordingPlatform)
def upload_performance_meta_categories(recording_platform):

	# TODO check configured audio importer

	if recording_platform.performance_meta_categories:
		raise InvalidUsage("performance meta categories already exist; unable to upload config file")

	if not "file" in request.files:
		raise InvalidUsage("no config file provided")

	amr_config_file = AmrConfigFile.load(request.files["file"])

	for amr_category in amr_config_file.demographics:
		validator = MetaValidator.from_amr_demographic_category(amr_category)

		meta_category = PerformanceMetaCategory(
			recording_platform=recording_platform,
			name=amr_category.title,
			extractor={"source": "Log File", "key": amr_category.id},	# TODO get log file string from audio importer constant
			validator_spec=validator.to_dict(),
		)

		db.session.add(meta_category)

	db.session.commit()

	return jsonify({"metaCategories": PerformanceMetaCategory.dump(recording_platform.performance_meta_categories)})


@bp.route("recordingplatforms/<int:recording_platform_id>/audiocheckingsections", methods=["GET"])
@api
@caps()
@get_model(RecordingPlatform)
def get_audio_checking_sections(recording_platform):
	return jsonify({"audioCheckingSections": AudioCheckingSection.dump(recording_platform.audio_checking_sections)})


@bp.route("recordingplatforms/<int:recording_platform_id>/audiocheckingsections", methods=["POST"])
@api
@caps()
@get_model(RecordingPlatform)
def create_audio_checking_section(recording_platform):

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

	audio_checking_section = AudioCheckingSection(
		recording_platform=recording_platform,
		start_position=data["startPosition"],
		end_position=data["endPosition"],
		check_percentage=data["checkPercentage"],
	)
	db.session.add(audio_checking_section)
	db.session.flush()

	return jsonify({"audioCheckingSection": AudioCheckingSection.dump(audio_checking_section)})


@bp.route("recordingplatforms/<int:recording_platform_id>/corpuscodes/spontaneous/include", methods=["PUT"])
@api
@caps()
@get_model(RecordingPlatform)
def include_spontaneous_corpus_codes(recording_platform):
	data = MyForm(
		Field('corpusCodes', is_mandatory=True,
			validators=[
				validators.is_list,
				CorpusCode.check_all_exists,
			]
		),
	).get_data()

	included = set(data['corpusCodes'])

	for corpus_code in recording_platform.spontaneous_corpus_codes:
		corpus_code.included = corpus_code.corpus_code_id in included

	db.session.commit()

	return jsonify(success=True)


@bp.route("recordingplatforms/<int:recording_platform_id>/performances", methods=["GET"])
@api
@caps()
@get_model(RecordingPlatform)
def get_performances(recording_platform):
	return jsonify(performances=Performance.dump(recording_platform.performances))
