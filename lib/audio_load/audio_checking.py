import jsonschema
import os

from marshmallow import Schema, fields

from lib.loaders import AudioCheckingLoaders


PERFORMANCE_DATA_SCHEMA = {
	"type": "object",
	"required": ["rawPieceId", "recordingPlatformId", "name", "scriptId", "recordings", "metadata"],
	"properties": {
		"rawPieceId": {
			"type": ["integer", "null"]
		},
		"recordingPlatformId": {
			"type": "integer"
		},
		"name": {
			"type": ["string", "null"]
		},
		"scriptId": {
			"type": ["integer", "string", "null"]
		},
		"metadata": {
			"type": "object"
		},
		"albumName": {
			"type": ["string", "null"]
		},
		"recordings": {
			"type": "array",
			"minItems": 1,
			"items": {
				"type": "object",
				"required": ["corpusCodeId", "duration", "prompt", "hypothesis", "audioFiles"],
				"properties": {
					"corpusCodeId": {
						"type": "integer"
					},
					"duration": {
						"type": "number"
					},
					"prompt": {
						"type": ["string", "null"]
					},
					"hypothesis": {
						"type": ["string", "null"]
					},
					"audioFiles": {
						"type": "array",
						"minItems": 1,
						"items": {
							"type": "object",
							"required": ["filePath", "trackId", "audioSpec", "audioDataLocation", "stats"],
							"properties": {
								"filePath" : {
									"type": "string"
								},
								"trackId": {
									"type": "integer"
								},
								"audioSpec": {
									"type": "object"
								},
								"audioDataLocation": {
									"type": "object"
								},
								"stats": {
									"type": ["object", "null"]
								}
							}
						}
					}
				}
			}
		},
	}
}


class AudioCheckingLoadConfigSchema(Schema):
	task_id = fields.Integer(dump_to="taskId")
	name = fields.String()
	task_type = fields.String(dump_to="taskType")
	loadable_recording_platforms = fields.Nested("LoadRecordingPlatformSchema", dump_to="recordingPlatforms", many=True)


class LoadTrackSchema(Schema):
	track_id = fields.Integer(dump_to="trackId")
	name = fields.String()
	track_index = fields.Integer(dump_to="trackIndex")


class LoadCorpusCodeSchema(Schema):
	corpus_code_id = fields.Integer(dump_to="corpusCodeId")
	code = fields.String()
	is_scripted = fields.Boolean(dump_to="isScripted")
	regex = fields.String()


class LoadPerformanceMetaCategorySchema(Schema):
	performance_meta_category_id = fields.Integer(dump_to="performanceMetaCategoryId")
	extractor = fields.Dict()


class LoadRecordingPlatformSchema(Schema):
	task_id = fields.Integer(dump_to="taskId")
	recording_platform_id = fields.Integer(dump_to="recordingPlatformId")
	loader = fields.Dict()
	completed_performances = fields.Method("get_completed_performances", dump_to="completedPerformances")
	incomplete_performances = fields.Method("get_incomplete_performances", dump_to="incompletePerformances")
	tracks = fields.Nested(LoadTrackSchema, many=True)
	corpus_codes = fields.Nested(LoadCorpusCodeSchema, many=True, dump_to="corpusCodes")
	loadable_performance_meta_categories = fields.Nested(LoadPerformanceMetaCategorySchema, many=True, dump_to="performanceMetaCategories")

	def get_completed_performances(self, obj):
		"""
		Returns a list of completed performance names.
		"""
		completed = []

		if obj.loader["name"] != AudioCheckingLoaders.UNSTRUCTURED:
			for performance in obj.performances:
				if not performance.incomplete:
					completed.append(performance.name)

		return completed

	def get_incomplete_performances(self, obj):
		"""
		Returns a list of incomplete performances.
		Example:
		[
			{
				"rawPieceId": 1,
				"name": "ExamplePerformance",
				"existingFiles": [
					"/path/to/audio/file/1",
					"/path/to/audio/file/2",
					"/path/to/audio/file/3",
					...
				]
			},
			...
		]
		"""

		incomplete = []
		for performance in obj.performances:
			
			# if performance is incomplete
			if obj.loader["name"] == AudioCheckingLoaders.UNSTRUCTURED or performance.incomplete:
				
				# get list of existing filenames
				existing_files = []
				for recording in performance.recordings:
					for audio_file in recording.audio_files:
						existing_files.append(audio_file.file_path)

				incomplete.append({
					"rawPieceId": performance.raw_piece_id,
					"name": performance.name,
					"existingFiles": existing_files,
				})
		return incomplete


def validate_load_performance_data(data):
	"""
	Validates the load data.
	"""
	jsonschema.validate(data, PERFORMANCE_DATA_SCHEMA)
