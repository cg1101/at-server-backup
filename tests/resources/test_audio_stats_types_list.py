from db.model import AudioStatsType
from tests.util import validate_get_list_endpoint


class TestAudioStatsTypesList(object):
	
	def test_get(self, session, test_client):
		return validate_get_list_endpoint(
			test_client,
			session.query(AudioStatsType).all(),
			"/api/1.0/audio-stats-types",
			"audioStatsTypes",
		)
