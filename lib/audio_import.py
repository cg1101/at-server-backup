import jsonschema
import os

from marshmallow import Schema, fields


# for audio checking tasks
PERFORMANCE_DATA_SCHEMA = {
	"type": "object",
	"required": ["recordingPlatformId", "rawPieceId", "name", "scriptId", "recordings", "metadata"],
	"properties": {
		"recordingPlatformId": {
			"type": "integer"
		},
		"rawPieceId": {
			"type": ["integer", "null"]
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


class ImportConfigSchema(Schema):
	taskId = fields.Integer()
	name = fields.String()
	taskType = fields.String()
	recordingPlatforms = fields.Nested("ImportRecordingPlatformSchema", attribute="importable_recording_platforms", many=True)


class ImportTrackSchema(Schema):
	track_id = fields.Integer(dump_to="trackId")
	name = fields.String()
	track_index = fields.Integer(dump_to="trackIndex")


class ImportCorpusCodeSchema(Schema):
	corpus_code_id = fields.Integer(dump_to="corpusCodeId")
	code = fields.String()
	is_scripted = fields.Boolean(dump_to="isScripted")
	regex = fields.String()


class ImportPerformanceMetaCategorySchema(Schema):
	performance_meta_category_id = fields.Integer(dump_to="performanceMetaCategoryId")
	extractor = fields.Dict()


class ImportRecordingPlatformSchema(Schema):
	recordingPlatformId = fields.Integer()
	storageLocation = fields.String()
	masterHypothesisFile = fields.Dict()
	masterScriptFile = fields.Dict()
	importer = fields.Function(lambda obj: obj.audio_importer.name)
	config = fields.Dict()
	completedPerformances = fields.Method("get_completed_performances")
	incompletePerformances = fields.Method("get_incomplete_performances")
	tracks = fields.Nested(ImportTrackSchema, many=True)
	corpus_codes = fields.Nested(ImportCorpusCodeSchema, many=True, dump_to="corpusCodes")
	importable_performance_meta_categories = fields.Nested(ImportPerformanceMetaCategorySchema, many=True, dump_to="performanceMetaCategories")

	def get_completed_performances(self, obj):
		"""
		Returns a list of completed performance names.
		"""
		completed = []

		if not obj.audio_importer.all_performances_incomplete:
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
			if obj.audio_importer.all_performances_incomplete or performance.incomplete:
				
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


def validate_import_performance_data(data):
	"""
	Validates the import data.
	"""
	jsonschema.validate(data, PERFORMANCE_DATA_SCHEMA)
