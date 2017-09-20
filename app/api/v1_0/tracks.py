from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, simple_validators, validators
from db import database as db
from db.model import Track


@bp.route("tracks/<int:track_id>", methods=["PUT"])
@api
@caps()
@get_model(Track)
def update_track(track):
	
	data = MyForm(
		Field("trackIndex", validators=[
			simple_validators.is_number(min_value=0),
			track.check_updated_index_unique,
		]),
		Field("name", validators=[
			validators.non_blank,
			track.check_updated_name_unique,
		]),
		Field("mode", validators=[
			validators.is_string,
			Track.is_valid_mode(validator=True)
		]),
	).get_data()
	
	if "trackIndex" in data:
		track.track_index = data["trackIndex"]

	if "name" in data:
		track.name = data["name"]

	if "mode" in data:
		track.update_mode(data["mode"])

	db.session.commit()
	return jsonify(track=Track.dump(track))


@bp.route("tracks/<int:track_id>", methods=["DELETE"])
@api
@caps()
@get_model(Track)
def delete_track(track):
	db.session.delete(track)
	db.session.commit()
	return jsonify(success=True)
