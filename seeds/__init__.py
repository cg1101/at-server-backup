from db import database as db
from db.model import AudioCollectionStatus, AudioImporter, TaskType
from db.schema import t_database_settings


models = [

	# audio collection statuses
	AudioCollectionStatus(name=AudioCollectionStatus.OPEN),
	AudioCollectionStatus(name=AudioCollectionStatus.CLOSED),
	AudioCollectionStatus(name=AudioCollectionStatus.ARCHIVED),

	# audio importers
	AudioImporter(name=AudioImporter.UNSTRUCTURED, all_performances_incomplete=True),
	AudioImporter(name=AudioImporter.STANDARD),
	AudioImporter(name=AudioImporter.AMR_SCRIPTED, metadata_sources=["Log File"]),
	AudioImporter(name=AudioImporter.AMR_CONVERSATIONAL),
	AudioImporter(name=AudioImporter.APPEN_TELEPHONY_SCRIPTED),
	AudioImporter(name=AudioImporter.APPEN_TELEPHONY_CONVERSATIONAL),

	# task types
	TaskType(name=TaskType.TRANSLATION),
	TaskType(name=TaskType.TEXT_COLLECTION),
	TaskType(name=TaskType.MARKUP),
	TaskType(name=TaskType.TRANSCRIPTION),
	TaskType(name=TaskType.AUDIO_CHECKING),
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
