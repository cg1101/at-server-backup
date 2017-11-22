from db.model import Project
from tests.util import validate_get_endpoint


class TestProject(object):
	
	def test_get(self, session, test_client):
		model = session.query(Project).first()
		return validate_get_endpoint(
			test_client,
			model,
			"/api/1.0/projects/{0}".format(model.project_id),
			"project",
		)
