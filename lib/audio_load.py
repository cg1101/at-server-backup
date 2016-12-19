import jsonschema

from marshmallow import Schema, fields


UTTERANCES_DATA_SCHEMA = {
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


class LoadConfigSchema(Schema):
	task_id = fields.Integer(dump_to="taskId")
	loader = fields.Function(lambda obj: obj.loader.name)
	config = fields.Dict()
	loaded_files = fields.Method("get_loaded_files", dump_to="loadedFiles")

	def get_loaded_files(self, obj):
		return []	# FIXME


def validate_load_utterance_data(data):
	jsonschema.validate(data, UTTERANCES_DATA_SCHEMA)
