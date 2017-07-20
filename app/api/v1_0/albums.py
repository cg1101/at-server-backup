from flask import jsonify

from . import api_1_0 as bp
from app.api import api, caps, get_model
from db.model import Album, Performance


@bp.route("albums/<int:album_id>", methods=["GET"])
@api
@caps()
@get_model(Album)
def get_album(album):
	return jsonify({"album": Album.dump(album)})


@bp.route("albums/<int:album_id>/performances", methods=["GET"])
@api
@caps()
@get_model(Album)
def get_album_performances(album):
	return jsonify({"performances": Performance.dump(album.performances)})
