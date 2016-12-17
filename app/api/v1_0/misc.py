from flask import jsonify

from . import api_1_0 as bp


@bp.route("status")
def get_status():
	return jsonify(success=True)
