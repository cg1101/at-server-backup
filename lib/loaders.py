import re

from lib import GetConstantsMixin


class AudioCheckingLoaders(GetConstantsMixin):
	UNSTRUCTURED = "Unstructured"
	STANDARD = "Standard"
	AMR_SCRIPTED = "Appen Mobile Recorder - Scripted"
	AMR_CONVERSATIONAL = "Appen Mobile Recorder - Conversational"
	APPEN_TELEPHONY_SCRIPTED = "Appen Telephony - Scripted"
	APPEN_TELEPHONY_CONVERSATIONAL = "Appen Telephony - Conversational"


class TranscriptionLoaders(GetConstantsMixin):
	STORAGE = "Storage"
	LINKED = "Linked"


# TODO move to models
def get_available_loaders(task_type=None, recording_platform_type=None):
	"""
	Returns the available loaders.
	"""
	from db.model import RecordingPlatformType, TaskType

	if task_type == TaskType.TRANSCRIPTION:
		return (
			TranscriptionLoaders.STORAGE,
			TranscriptionLoaders.LINKED,
		)

	if recording_platform_type == RecordingPlatformType.APPEN_MOBILE_RECORDER:
		return (
			AudioCheckingLoaders.AMR_SCRIPTED,
			AudioCheckingLoaders.AMR_CONVERSATIONAL,
		)

	if recording_platform_type == RecordingPlatformType.TELEPHONY:
		return (
			AudioCheckingLoaders.APPEN_TELEPHONY_SCRIPTED,
			AudioCheckingLoaders.APPEN_TELEPHONY_CONVERSATIONAL,
		)


def get_loader_metadata_sources(name):
	"""
	Returns the metadata sources available for
	the loader.
	"""

	if name == AudioCheckingLoaders.AMR_SCRIPTED:
		return ["Log File"]

	if name == AudioCheckingLoaders.APPEN_TELEPHONY_CONVERSATIONAL:
		return ["Log File"]
	
	return []


__all__ = [
	"AudioCheckingLoaders",
	"TranscriptionLoaders",
	"get_available_loaders",
	"get_loader_metadata_sources",
]
