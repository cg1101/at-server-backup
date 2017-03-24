from flask import jsonify

from . import api_1_0 as bp
from app.api import api


@bp.route("status")
@api
def api_status():
	return jsonify(success=True)
