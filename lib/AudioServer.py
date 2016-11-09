# TODO move to lr_utilities
import logging


log = logging.getLogger(__name__)


class AudioServer(object):
	"""
	Flask wrapper for the AudioServer API library.
	"""
	def __init__(self):
		self._api = None
		self.checked_status = False

	def init_app(self, app):
		"""
		Initializes the API from the app config.
		"""
		cls = app.config["AUDIO_SERVER_API_CLS"]
		secret = app.config["AUDIO_SERVER_API_SECRET"]
		log.debug("init with cls:{0}, secret:{1}".format(cls, secret))
		self._api = cls(secret)

	@property
	def api(self):
		"""
		Checks that the API has been initialized
		and is online.
		"""

		# check initialized
		if self._api is None:
			raise RuntimeError("AudioServer API has not been initialized")

		# check online
		if not self.checked_status:
			if not self._api.is_online():
				raise RuntimeError("AudioServer API is not online")

			self.checked_status = True

		return self._api


__all__ = ["AudioServer"]
