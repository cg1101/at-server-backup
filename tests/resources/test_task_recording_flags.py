from db.model import RecordingFlag
from tests.util import validate_create_endpoint


class TestTaskRecordingFlags(object):
	
	def test_create(self, sample_data, session, test_client):
		data = {
			"name": "test flag",
			"severity": RecordingFlag.INFO,
		}

		validate_create_endpoint(
			test_client,
			session,
			"/api/1.0/tasks/{0}/recordingflags".format(sample_data.task_id_1),
			data,
			"recordingFlag",
			"recordingFlagId",
			RecordingFlag,
		)
