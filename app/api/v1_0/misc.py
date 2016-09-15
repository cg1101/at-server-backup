import logging

from flask import jsonify

from . import api_1_0 as bp


log = logging.getLogger(__name__)


@bp.route("status")
def get_status():
	return jsonify(success=True)