import jsonschema

from marshmallow import Schema, fields


UTTERANCES_DATA_SCHEMA = {
	"type": "object",
	"required": ["utts"],
	"properties": {
		"performanceUpdates": {
			"type": "array",
			"items": {
				"type": "object",
				"required": ["rawPieceId", "subTaskId"],
				"properties": {
					"rawPieceId": {
						"type": "integer",
					},
					"subTaskId": {
						"type": "integer",
					}
				}
			}
		},
		"utts": {
			"type": "array",
			"minItems": 1,
			"items": {
				"type": "object",
				"required": ["filePath", "audioSpec", "audioDataPointer"],
				"properties": {
					"filePath": {
						"type": "string",
					},
					"audioSpec": {
						"type": "object",	# TODO check valid audio spec
					},
					"audioDataPointer": {
						"type": "object",	# TODO check valid audio data pointer
					},
					"hypothesis": {
						"type": ["string", "null"],
					},
					"startAt": {
						"type": ["number", "null"],
					},
					"endAt": {
						"type": ["number", "null"],
					},
				},
			}
		}
	}
}


class TranscriptionLoadConfigSchema(Schema):
	task_id = fields.Integer(dump_to="taskId")
	task_type = fields.String(dump_to="taskType")
	loader = fields.Function(lambda obj: obj.loader.name)
	config = fields.Dict()
	loaded_files = fields.Method("get_loaded_files", dump_to="loadedFiles")

	# TODO this is only required by storage loader - use end point instead
	def get_loaded_files(self, obj):
		"""
		Returns a list of previously loaded file paths.
		"""
		file_paths = set()

		for utt in obj.raw_pieces:
			file_path = utt.data.get("filePath")
			
			if file_path:
				file_paths.add(file_path)

		return list(file_paths)


def validate_load_utterance_data(data):
	jsonschema.validate(data, UTTERANCES_DATA_SCHEMA)
