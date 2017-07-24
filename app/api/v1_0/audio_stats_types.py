from flask import jsonify

from . import api_1_0 as bp
from app.api import api, caps, get_model
from db.model import AudioStatsType


@bp.route("audio-stats-types", methods=["GET"])
@api
@caps()
def get_audio_stats_types():
	audio_stats_types = AudioStatsType.query.all()
	return jsonify({"audioStatsType": AudioStatsType.dump(audio_stats_types)})


@bp.route("audio-stats-types/<int:audio_stats_type_id>", methods=["GET"])
@api
@caps()
@get_model(AudioStatsType)
def get_audio_stats_type(audio_stats_type):
	return jsonify({"audioStatsType": AudioStatsType.dump(audio_stats_type)})
