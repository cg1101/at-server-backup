# TODO use lr_utilities audio cutup service api lib for validation

import jsonschema
import logging

log = logging.getLogger(__name__)


MINIMA_CUTTING_SCHEMA = {
	"type": "object",
	"required": ["method", "options"],
	"properties": {
		"method": {
			"enum": ["Minima Cutting"]
		},
		"options": {
			"type": "object",
			"required": ["minSegmentLength", "maxSegmentLength"],
			"additionalProperties": False,
			"properties": {
				"minSegmentLength": {
					"type": "number",
					"minimum": 1,
				},
				"maxSegmentLength": {
					"type": "number",
					"minimum": 1,
				}
			}
		}
	}
}

SILENCE_DETECTION_SCHEMA = {
	"type": "object",
	"required": ["method", "options"],
	"properties": {
		"method": {
			"enum": ["Silence Detection"]
		},
		"options": {
			"type": "object",
			"required": ["maxSegmentLength", "minimumSilence", "energyMethod", "energyDelta"],
			"additionalProperties": False,
			"properties": {
				"minimumSilence": {
					"type": "number",
					"minimum": 0,
				},
				"maxSegmentLength": {
					"type": "number",
					"minimum": 1,
				},
				"energyDelta": {
					"type": "number"
				},
				"energyMethod": {
					"enum": ["minFrameEnergy", "maxFrameEnergy", "meanFrameEnergy", "medianFrameEnergy", "minRangeEnergy", "maxRangeEnergy"]
				}
			}
		}
	}
}


def get_validation_schema(method):
	"""
	Returns the corresponding JSON
	scheme for the given audio cutup
	method.
	"""
	
	if method == "Minima Cutting":
		return MINIMA_CUTTING_SCHEMA

	if method == "Silence Detection":
		return SILENCE_DETECTION_SCHEMA

	raise ValueError("Unknown audio cutup method: {0}".format(method))


def validate_audio_cutup_config(config):
	"""
	Validates audio cutup config.
	"""
	method = config.get("method")
	schema = get_validation_schema(method)
	jsonschema.validate(schema, config)
