from flask import jsonify

from . import api_1_0 as bp
from app.api import api, caps
from db.model import AudioCheckingChangeMethod, BatchingMode, CorpusCode, RecordingPlatformType, Task, TaskType, Track, WorkType
from lib.loaders import AudioCheckingLoaders, TranscriptionLoaders


@bp.route("constants", methods=["GET"])
@api
@caps()
def get_constants():
	task_statuses = {}
	
	for status in Task.get_statuses():
		task_statuses[status.upper()] = status

	return jsonify({
		"audioCheckingChangeMethods": AudioCheckingChangeMethod.get_constants(),
		"audioCheckingLoaders": AudioCheckingLoaders.get_constants(),
		"batchingModes": BatchingMode.get_constants(),
		"corpusCodes": CorpusCode.get_constants(),
		"recordingPlatformTypes": RecordingPlatformType.get_constants(),
		"taskStatuses": task_statuses,
		"taskTypes": TaskType.get_constants(),
		"tracks": Track.get_constants(),
		"transcriptionLoaders": TranscriptionLoaders.get_constants(),
		"workTypes": WorkType.get_constants(),
	})

