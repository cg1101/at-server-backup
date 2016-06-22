
import os
import base64
import hashlib
import zlib
import cPickle
import time
import re
import json
import urllib
from Crypto.Cipher import AES

from flask import redirect, Response, Request

from i18n import get_text as _

COOKIE_SECRET = os.environ.get('APP_COOKIE_SECRET')
COOKIE_PREFIX = os.environ.get('APP_COOKIE_PREFIX')
COOKIE_NAME = os.environ.get('APP_COOKIE_NAME')

class CookieError(Exception):
	def __init__(self, message):
		Exception.__init__(self)
		self.message = message

def random_bytes(size):
	with open('/dev/urandom', 'rb') as f:
		return f.read(size)

def pad(s, block_size):
	extra = len(s) % block_size
	size = block_size - extra if extra else 0
	return s + ' ' * size

def encode_cookie(data, secret=COOKIE_SECRET, timeout=0):
	pickled = cPickle.dumps((data, timeout))
	compressed = zlib.compress(COOKIE_PREFIX + pickled)
	init_vec = random_bytes(AES.block_size)
	key = hashlib.md5(secret).digest()
	encryptor = AES.new(key, AES.MODE_CBC, init_vec)
	cipher_text = encryptor.encrypt(pad(compressed, AES.block_size))
	encrypted = base64.urlsafe_b64encode(init_vec + cipher_text)
	return encrypted

def decode_cookie(cookie, secret=COOKIE_SECRET):
	data = None
	try:
		encrypted = cookie.encode('utf8')
		ctav = base64.urlsafe_b64decode(encrypted)
		if len(ctav) < AES.block_size:
			raise CookieError('encryption blocks too short')
		init_vec, cipher_text = ctav[:AES.block_size], ctav[AES.block_size:]
		if len(cipher_text) % AES.block_size:
			raise CookieError('encryption blocks of bad size')
		key = hashlib.md5(secret).digest()
		decryptor = AES.new(key, AES.MODE_CBC, init_vec)
		compressed = decryptor.decrypt(cipher_text)
		decompressed = zlib.decompress(compressed)
		if not decompressed.startswith(COOKIE_PREFIX):
			raise CookieError('cookie malformed')
		pickled = decompressed[len(COOKIE_PREFIX):]
		(data, timeout) = cPickle.loads(pickled)
		if timeout and timeout < time.time():
			raise CookieError('cookie expired')
		if not data.get('REMOTE_USER_ID'):
			raise CookieError('cookie invalid')
		data.setdefault('CAPABILITIES', set())
	except CookieError, exc:
		# log this error and continue
		data = None
	except Exception, e:
		# log this error and continue
		data = None
	return data

class MyAuthMiddleWare(object):

	def __init__(self, app, authentication_url, public_prefixes=[],
			json_prefixes=[]): 
		self.app = app
		self.authentication_url = authentication_url
		self.public_prefixes = []
		self.json_prefixes = []
		for i in public_prefixes:
			self.public_prefixes.append(re.compile(i))
		for i in json_prefixes:
			self.json_prefixes.append(re.compile(i))

	def __call__(self, environ, start_response):
		request = Request(environ)

		for i in self.public_prefixes:
			if i.match(request.path):
				return self.app(environ, start_response)

		user_dict = decode_cookie(request.cookies.get(COOKIE_NAME, ''))
		if user_dict:
			environ['myauthmiddleware'] = user_dict
			return self.app(environ, start_response)

		is_json = False
		for i in self.json_prefixes:
			if i.match(request.path):
				is_json = True
			break
		else:
			is_json = (request.headers.get('HTTP-ACCEPT') or ''
					).find('application/json') >= 0
		if is_json:
			response = Response(mimetype='application/json')
			response.status_code = 401
			response.set_data(json.dumps({'error':
				_('authentication required to access requested url')}))
			return response(environ, start_response)

		url = self.authentication_url + '?r=' + \
			urllib.quote(base64.b64encode(request.url))

		return redirect(url, code=303)(environ, start_response)
