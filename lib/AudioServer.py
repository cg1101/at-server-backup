# TODO use lr_utilities version when migrated to Python3

import json
import os
import requests

from itsdangerous import URLSafeSerializer


class AudioServer(object):
	
	STATUS_URL = "https://audio.appen.com/api/v1/status"
	API_BASE_URL = "https://audio.appen.com/api/v1"

	@classmethod
	def is_online(cls):
		response = requests.get(cls.STATUS_URL)
		return response.status_code == 200

	def __init__(self, secret_key):
		self.secret_key = secret_key

	def get_url(self, prefix, audio_spec, audio_data_location, file_path, start_at=None, end_at=None):
		"""
		Returns the audio server URL.
		"""
		json_dict = {
			"audioSpec": audio_spec,
			"audioDataLocation": audio_data_location,
			"filePath": file_path,
		}
		
		if start_at is not None:
			json_dict.update({"startAt": start_at.total_seconds()})
		
		if end_at is not None:
			json_dict.update({"endAt": end_at.total_seconds()})

		json_string = json.dumps(json_dict)
		data = URLSafeSerializer(self.secret_key).dumps(json_string)
		return os.path.join(self.API_BASE_URL, prefix, data)

	def get_mp3_url(self, *args, **kwargs):
		"""
		Returns an MP3 URL.
		"""
		return self.get_url("mp3", *args, **kwargs)
	
	def get_ogg_url(self, *args, **kwargs):
		"""
		Returns an Ogg URL.
		"""
		return self.get_url("ogg", *args, **kwargs)


class AudioStageServer(AudioServer):
	STATUS_URL = "https://audio-stage.appen.com/api/v1/status"
	API_BASE_URL = "https://audio-stage.appen.com/api/v1"


class AudioDevServer(AudioServer):
	STATUS_URL = "http://localhost:5001/api/v1/status"
	API_BASE_URL = "http://localhost:5001/api/v1"


__all__ = ["AudioServer", "AudioStageServer", "AudioDevServer"]
