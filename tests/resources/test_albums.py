from db.model import Album
from tests.util import validate_delete_endpoint


class TestAlbums(object):
	
	def test_delete(self, sample_data, session, test_client):
		album = Album(
			task_id=sample_data.task_id_1,
			name="test album",
		)
		session.add(album)
		session.commit()

		validate_delete_endpoint(
			test_client,
			session,
			album, 
			"/api/1.0/albums/{0}".format(album.album_id),
		)
