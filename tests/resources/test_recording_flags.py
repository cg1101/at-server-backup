from db.model import RecordingFlag
from tests.util import validate_update_endpoint


class TestRecordingFlags(object):
	
	def test_update(self, sample_data, session, test_client):
		recording_flag = RecordingFlag(
			task_id=sample_data.task_id_1,
			name="before",
			severity=RecordingFlag.WARNING
		)
		session.add(recording_flag)
		session.commit()

		updates = {
			"name": "after",
			"severity": RecordingFlag.SEVERE,
		}

		updated_model = validate_update_endpoint(
			test_client,
			session,
			"/api/1.0/recordingflags/{0}".format(recording_flag.recording_flag_id),
			updates,
			"recordingFlag",
			"recordingFlagId",
			RecordingFlag,
		)

		assert updated_model.name == updates["name"]
		assert updated_model.severity == updates["severity"]
