from db import database as db
from db.model import RecordingPlatformType
from tests import util


class TestRecoringPlatformTypeList(object):
	
	@util.get_list_endpoint(return_key="recordingPlatformTypes")
	def test_get(self):
		return (
			"/api/1.0/recording-platform-types",
			db.session.query(RecordingPlatformType).all()
		)
