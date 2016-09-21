
from flask import Blueprint, jsonify

from .. import InvalidUsage

api_1_0 = Blueprint('api_1_0', __name__)

@api_1_0.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
	response = jsonify(error.to_dict())
	response.status_code = error.status_code
	return response

import audio_collections
import batches
import corpus_codes
import errorclasses
import errortypes
import filehandlers
import labelsets
import misc
import performance_flags
import pools
import projects
import rates
import recordings
import recording_platforms
import sheets
import subtasks
import tagsets
import tasks
import tests

# workflow control apis
import work
