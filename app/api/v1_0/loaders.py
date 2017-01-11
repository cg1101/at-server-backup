from flask import jsonify

from . import api_1_0 as bp
from app.api import api, caps
from db.model import Loader


@bp.route("loaders", methods=["GET"])
@api
@caps()
def get_loaders():
	loaders = Loader.query.all()
	return jsonify(loaders=Loader.dump(loaders))

