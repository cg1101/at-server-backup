from db.model import RecordingPlatformType
from tests.util import validate_get_list_endpoint


class TestRecoringPlatformTypesList(object):
	
	def test_get(self, session, test_client):
		validate_get_list_endpoint(
			test_client,
			session.query(RecordingPlatformType).all(),
			"/api/1.0/recording-platform-types",
			"recordingPlatformTypes",
		)
