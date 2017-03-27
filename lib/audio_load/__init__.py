import base64
import zlib

from .audio_checking import *
from .transcription import *


def decompress_load_data(data):
	"""
	Decompresses load data uploaded to the API.
	"""
	return zlib.decompress(base64.b64decode(data))
