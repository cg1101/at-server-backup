from flask import jsonify

from . import api_1_0 as bp
from app.api import api, caps
from db.model import AudioImporter


@bp.route("audioimporters")
@api
@caps()
def get_audio_importers():
	audio_importers = AudioImporter.query.all()
	return jsonify({"audioImporters": AudioImporter.dump(audio_importers)})
