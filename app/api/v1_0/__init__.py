from flask import Blueprint, jsonify
from flask_restful import Api

from .. import InvalidUsage

api_1_0 = Blueprint('api_1_0', __name__)
api_v1 = Api(api_1_0)

@api_1_0.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
	response = jsonify(error.to_dict())
	response.status_code = error.status_code
	return response

import albums
import alphabets
import api_access_pairs
import audio_checking_groups
import audio_checking_sections
import audio_files
import audio_sandboxes
import audio_sandbox_files
import audio_stats_types
import audio_uploads
import batch_routers
import batches
import batching_modes
import constants
import corpus_codes
import countries
import dialects
import errorclasses
import errortypes
import filehandlers
import get_token
import labelsets
import loaders
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
import recording_platform_audio_checking_groups
import recording_platform_corpus_codes
import recording_platform_loader
import recording_platform_session_meta_categories
import recording_platform_types
import recording_platform_tracks
import sheets
import status
import subtasks
import tagsets
import tasks
import task_audio_uploads
import tests
import tracks
import transitions
import users

# workflow control apis
import work
import workentries
