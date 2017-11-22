from db.model import Project
from tests.util import validate_get_list_endpoint


class TestProjectsList(object):
	
	def test_get(self, session, test_client):
		validate_get_list_endpoint(
			test_client,
			session.query(Project).all(),
			"/api/1.0/projects/",
			"projects",
		)
