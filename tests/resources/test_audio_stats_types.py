from db.model import AudioStatsType
from tests.util import validate_get_endpoint


class TestAudioStatsType(object):
	
	def test_get(self, session, test_client):
		model = session.query(AudioStatsType).first()
		return validate_get_endpoint(
			test_client,
			model,
			"/api/1.0/audio-stats-types/{0}".format(model.audio_stats_type_id),
			"audioStatsType",
		)
