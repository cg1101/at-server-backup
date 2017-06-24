class Loaders(object):
	
	# transcription loaders
	STORAGE = "Storage"
	LINKED = "Linked"

	# audio checking loaders
	UNSTRUCTURED = "Unstructured"
	STANDARD = "Standard"
	AMR_SCRIPTED = "Appen Mobile Recorder - Scripted"
	AMR_CONVERSATIONAL = "Appen Mobile Recorder - Conversational"
	APPEN_TELEPHONY_SCRIPTED = "Appen Telephony - Scripted"
	APPEN_TELEPHONY_CONVERSATIONAL = "Appen Telephony - Conversational"


def get_available_loaders(task_type=None, recording_platform_type=None):
	"""
	Returns the available loaders.
	"""
	from db.model import RecordingPlatformType, TaskType

	if task_type == TaskType.TRANSCRIPTION:
		return (
			Loaders.STORAGE,
			Loaders.LINKED,
		)

	if recording_platform_type == RecordingPlatformType.APPEN_MOBILE_RECORDER:
		return (
			Loaders.AMR_SCRIPTED,
			Loaders.AMR_CONVERSATIONAL,
		)

	if recording_platform_type == RecordingPlatformType.TELEPHONY:
		return (
			Loaders.APPEN_TELEPHONY_SCRIPTED,
			Loaders.APPEN_TELEPHONY_CONVERSATIONAL,
		)


def get_loader_metadata_sources(name):
	"""
	Returns the metadata sources available for
	the loader.
	"""

	if name == Loaders.AMR_SCRIPTED:
		return ["Log File"]

	if name == Loaders.APPEN_TELEPHONY_CONVERSATIONAL:
		return ["Log File"]
	
	return []


__all__ = [
	"Loaders",
	"get_available_loaders",
	"get_loader_metadata_sources",
]
