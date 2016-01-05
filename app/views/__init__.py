
from flask import Blueprint, make_response, render_template

from app.api import InvalidUsage

views = Blueprint('views', __name__, template_folder='../templates')

@views.errorhandler(InvalidUsage)
def handle_invalid_usage(error=None):
	response = make_response(render_template('error.html', message=error.message))
	response.status_code = error.status_code
	return response

import handlers
