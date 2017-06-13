from db import database as db
from db.model import (
	AudioCheckingChangeMethod,
	BatchingMode,
	Loader,
	RecordingPlatformType,
	TaskType,
	WorkType
)
from db.schema import t_database_settings


models = [

	# audio checking change methods
	AudioCheckingChangeMethod(name=AudioCheckingChangeMethod.ADMIN),
	AudioCheckingChangeMethod(name=AudioCheckingChangeMethod.WORK_PAGE),
	AudioCheckingChangeMethod(name=AudioCheckingChangeMethod.PERFORMANCE_SEARCH_PAGE),

	# batching modes
	BatchingMode(name=BatchingMode.NONE, requires_context=False),
	BatchingMode(name=BatchingMode.PERFORMANCE, requires_context=True),
	BatchingMode(name=BatchingMode.FILE, requires_context=True),
	BatchingMode(name=BatchingMode.CUSTOM_CONTEXT, requires_context=True),
	BatchingMode(name=BatchingMode.ALLOCATION_CONTEXT, requires_context=False),
	BatchingMode(name=BatchingMode.FOLDER, requires_context=True),

	# loaders
	Loader(name=Loader.STORAGE),
	Loader(name=Loader.LINKED),
	Loader(name=Loader.UNSTRUCTURED, all_performances_incomplete=True),
	Loader(name=Loader.STANDARD, all_performances_incomplete=False),
	Loader(name=Loader.AMR_SCRIPTED, all_performances_incomplete=False, metadata_sources=["Log File"]),
	Loader(name=Loader.AMR_CONVERSATIONAL, all_performances_incomplete=False),
	Loader(name=Loader.APPEN_TELEPHONY_SCRIPTED, all_performances_incomplete=False),
	Loader(name=Loader.APPEN_TELEPHONY_CONVERSATIONAL, all_performances_incomplete=False, metadata_sources=["Log File"]),

	# recording platform types
	RecordingPlatformType(name=RecordingPlatformType.UNSPECIFIED),
	RecordingPlatformType(name=RecordingPlatformType.SONY_MOBILE_RECORDER),
	RecordingPlatformType(name=RecordingPlatformType.APPEN_MOBILE_RECORDER),
	RecordingPlatformType(name=RecordingPlatformType.TELEPHONY),

	# task types
	TaskType(name=TaskType.TRANSLATION),
	TaskType(name=TaskType.TEXT_COLLECTION),
	TaskType(name=TaskType.MARKUP),
	TaskType(name=TaskType.TRANSCRIPTION),
	TaskType(name=TaskType.AUDIO_CHECKING),

	# work types
	WorkType(name=WorkType.WORK, modifies_transcription=True),
	WorkType(name=WorkType.QA, modifies_transcription=False),
	WorkType(name=WorkType.REWORK, modifies_transcription=True),
	WorkType(name=WorkType.SECOND_PASS_WORK, modifies_transcription=True),
	WorkType(name=WorkType.SECOND_PASS_REWORK, modifies_transcription=True),
]


def seed_db():
	"""
	Seeds the database.
	"""
	# get database settings
	settings = db.session.execute(t_database_settings.select()).fetchone()

	if settings and settings.seeded:
		raise RuntimeError("Database has already been seeded.")
	
	# add seed models
	for model in models:
		db.session.add(model)

	# indicate that the database has been seeded
	if settings:
		db.session.execute(t_database_settings.update().values(seeded=True))
	else:
		db.session.execute(t_database_settings.insert().values(seeded=True))

	db.session.commit()
