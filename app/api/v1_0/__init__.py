
from flask import Blueprint, jsonify

from .. import InvalidUsage

api_1_0 = Blueprint('api_1_0', __name__)

@api_1_0.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
	response = jsonify(error.to_dict())
	response.status_code = error.status_code
	return response

import audio_checking_groups
import audio_checking_sections
import audio_files
import batches
import batching_modes
import corpus_codes
import errorclasses
import errortypes
import filehandlers
import labelsets
import loaders
import misc
import performances
import performance_feedback
import performance_flags
import performance_meta_categories
import payrolls
import pools
import projects
import rates
import recordings
import recording_feedback
import recording_flags
import recording_platforms
import sheets
import subtasks
import tagsets
import tasks
import tests
import tracks
import transitions

# workflow control apis
import work
