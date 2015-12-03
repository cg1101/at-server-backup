
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

COOKIE_SECRET = '01342dfa/12340af/afds'

class CookieError(Exception):
	def __init__(self, message):
		Exception.__init__(self)
		self.message = message

def decode_cookies(cookies):
	data = None
	try:
		encrypted = cookies['appen'].encode('utf8')
		ctav = base64.urlsafe_b64decode(encrypted)
		if len(ctav) < AES.block_size:
			raise CookieError, 'cookie currupted'
		init_vec, cipher_text = ctav[:AES.block_size], ctav[AES.block_size:]
		secret = COOKIE_SECRET
		if len(cipher_text) % AES.block_size:
			raise CookieError, 'cookie currupted'
		key = hashlib.md5(secret).digest()
		decryptor = AES.new(key, AES.MODE_CBC, init_vec)
		compressed = decryptor.decrypt(cipher_text)
		decompressed = zlib.decompress(compressed)
		if not decompressed.startswith('Cookie'):
			raise CookieError, 'cookie malformed'
		pickled = decompressed[len('Cookie'):]
		(data, timeout) = cPickle.loads(pickled)
		if timeout and timeout < time.time():
			raise CookieError, 'cookie expired'
		if not data.get('REMOTE_USER_ID'):
			raise CookieError, 'cookie invalid'
		data.setdefault('CAPABILITIES', set())
	except Exception, e:
		# log this error and continue
		pass
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

		user_dict = decode_cookies(request.cookies)
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
				_('Could not verify your access level for requested URL.\nYou have to login with proper credentials')}))
			return response(environ, start_response)

		url = self.authentication_url + '?r=' + \
			urllib.quote(base64.b64encode(request.url))

		return redirect(url, code=303)(environ, start_response)
