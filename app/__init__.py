#!/usr/bin/env python

import datetime
import logging
import re

import requests
import jwt
from sqlalchemy.orm.exc import NoResultFound
from flask import Flask, session, request, after_this_request,\
		redirect, jsonify, make_response, url_for, current_app, g
from flask_oauthlib.client import OAuth
from flask_cors import CORS

from config import config
import db.model as m
from db.model import User
from db.db import SS
from db import database as db
import auth
from .i18n import get_text as _
import app.util as util

from LRUtilities.FlaskPlugins import AudioServer


class AuthError(Exception): pass

audio_server = AudioServer()


def create_app(config_name):
	app = Flask(__name__)
	app.config.from_object(config[config_name])
	config[config_name].init_app(app)
	db.init_app(app)
	audio_server.init_app(app)
	CORS(app, resources={'/api/1.0/*': {'origins': '*'}})

	logging.basicConfig(level=app.config["LOG_LEVEL"])

	public_url_patterns = map(re.compile, [
		'/static/',
		'/favicon.ico',
		'/edm',
		'/webservices',
		'/logout',
		'/authorization_response',
		'/health-check',
		"/api/1.0/status",
		"/api/1.0/get-token",
	])
	json_url_patterns = map(re.compile, [
		'/whoami',
		'/api'
	])

	from app.api import api_1_0
	from app.edm import edm
	from app.tagimages import tagimages
	from app.webservices import webservices
	from app.views import views
	app.register_blueprint(api_1_0, url_prefix='/api/1.0/')
	app.register_blueprint(edm, url_prefix='/edm')
	app.register_blueprint(tagimages, url_prefix='/tagimages')
	app.register_blueprint(webservices, url_prefix='/webservices')
	app.register_blueprint(views, url_prefix='')

	with app.app_context():
		from app.webservices.helpers import init_data
		init_data()

	oauth = OAuth()
	soteria = oauth.remote_app('soteria',
		base_url=None,
		request_token_url=None,
		access_token_url=app.config['OAUTH2_TOKEN_ENDPOINT'],
		authorize_url=app.config['OAUTH2_AUTHORIZATION_ENDPOINT'],
		consumer_key=app.config['OAUTH2_CLIENT_ID'],
		consumer_secret=app.config['OAUTH2_CLIENT_SECRET'],
		request_token_params={'scope': 'user', 'state': 'blah'},
	)

	@app.before_request
	def authenticate_request():
		# current_app.logger.debug('{} {}'.format(request.method, request.url))

		# do not authenticate public urls
		for p in public_url_patterns:
			if p.match(request.path):
				# current_app.logger.debug(\
				# 	'skip authencation for public url: {}'\
				# 	.format(request.url))
				return None

		# current_app.logger.debug('{} {}'.format(request.method, request.url))

		if not current_app.config['SSO_COOKIE_NAME']:
			check = lambda (x): True
		else:
			try:
				sso_cookie = request.cookies.get(current_app.config['SSO_COOKIE_NAME'])
				appenId = jwt.decode(sso_cookie, current_app.config['APPEN_API_SECRET_KEY'])['appen_id']
				check = lambda (x): appenId == int(x)
			except:
				check = lambda (x): False

		# authenticate by cookie
		try:
			cookie_name = current_app.config['APP_COOKIE_NAME']
			cookie = request.cookies.get(cookie_name)
			if not cookie:
				raise RuntimeError('cookie {} not found'\
					.format(cookie_name))

			secret = current_app.config['APP_COOKIE_SECRET']
			try:
				user_dict = auth.decode_cookie(cookie, secret)
				if not check(user_dict['REMOTE_USER_ID']):
					# current_app.logger.debug('gnx cookie stale')
					raise RuntimeError('gnx cookie is stale')
				user = m.User.query.get(user_dict['REMOTE_USER_ID'])
				session['current_user'] = user
				session['current_user_caps'] = user_dict['CAPABILITIES']
				session['current_user_type'] = user_dict['USER_TYPE']
				session['current_user_roles'] = user_dict['ROLES']
				return None
			except:
				raise RuntimeError('cookie corrupted or expired')

		except RuntimeError, e:
			# current_app.logger.debug('cookie authentication failed: {}'\
			# 	.format(e))
			pass

		# authenticate by header
		try:
			authorization_info = request.headers.get('authorization', None)
			# current_app.logger.debug('authorization header: {}'\
			# 	.format(authorization_info))
			if not authorization_info:
				raise RuntimeError('authorization header not found')
			try:
				globalId, token = authorization_info.split('~', 1)
			except:
				raise RuntimeError('unknown header format: {}'\
						.format(authorization_info))
			try:
				result = util.go.check_token_for_user(globalId)
				current_app.logger.debug('token info: {}'.format(result))
				# result = {
				# 	'token': token,
				# 	'expires_at': 'something',
				# 	'appen_id': 15517,
				# 	'app_id': 'appen_global'
				# }
			except RuntimeError, e:
				# token validation failed, return 500 to indicate server error
				return make_response(jsonify(error=\
					_('token validation failed: {}').format(e), ), 500)

			token_should_be = result.get('token', None)
			if token != token_should_be:
				raise RuntimeError(\
					'token validation failed: expecting {}, got {}'\
					.format(token_should_be, token))

			current_app.logger.debug('token validation passed, add user if necessary')
			try:
				user = m.User.query.filter(m.User.globalId==globalId).one()
				current_app.logger.debug('found local user {}'\
					.format(user.emailAddress))
			except NoResultFound:
				SS.rollback()
				current_app.logger.debug(\
					'user {} not found, get it from edm'.format(globalId))
				try:
					user = util.edm.make_new_user(globalId)
					SS.add(user)
					SS.flush()
					SS.commit()
				except Exception, e:
					SS.rollback()
					current_app.logger.error(\
						'failed to add user locally: {}'.format(e))
					return make_response(\
						jsonify(error=_('failed to add user {} locally'\
							).format(globalId), ), 500)
			# user exists locally
			# TODO: query tiger for roles to setup capabilities in cookie

			#
			# TODO: get user roles from global
			#
			try:
				result = util.tiger.get_user_roles(user.globalId)
				user_type = result['user']['role']
				roles = result['project_user_roles']
				caps = util.tiger.role2caps(user_type)
			except Exception, e:
				return make_response(_('error getting user roles {}').format(e), 500)

			session['current_user'] = user
			session['current_user_caps'] = caps
			session['current_user_type'] = user_type
			session['current_user_roles'] = roles
			g.update_cookie = True
			return None
		except RuntimeError, e:
			# current_app.logger.debug('header authentication failed: {}'.format(e))
			pass

		# authenticate by header (new method)
		try:
			check_appen_auth("x-appen-auth")

		# handle auth error
		except AuthError, e:
			current_app.logger.error("failed x-appen-auth authentication: {0}".format(e))
			pass

		# successfully authorised
		else:
			return None

		is_json = False
		for p in json_url_patterns:
			if p.match(request.path):
				is_json = True
				break
		else:
			is_json = (request.headers.get('HTTP-ACCEPT') or ''
					).find('application/json') >= 0
		if is_json:
			return make_response(jsonify(
				error=_('authentication required to access requested url'),
				authorizationUrl=app.config['AUTHENTICATION_LOGOUT_URL'],
			), 401)

		callback = url_for('authorization_response',
			r=request.url, _external=True)
		return soteria.authorize(callback=callback)

	@app.after_request
	def set_cookie_if_necessary(resp):
		if g.get('update_cookie', False):
			current_app.logger.debug('trying to set cookie as instructed')
			try:
				me = session['current_user']
				caps = session['current_user_caps']
				user_type = session['current_user_type']
				roles = session['current_user_roles']
				data = {
					'REMOTE_USER_ID': me.userId,
					'REMOTE_USER_NAME': me.userName,
					'CAPABILITIES': caps,
					'USER_TYPE': user_type,
					'ROLES': roles,
				}
				value = auth.encode_cookie(data,
					current_app.config['APP_COOKIE_SECRET'], timeout=0)
				resp.set_cookie(current_app.config['APP_COOKIE_NAME'], value)
			except Exception, e:
				current_app.logger.debug('error setting cookie {}'.format(e))
				pass
		session['current_user'] = None
		return resp

	@app.route('/whoami')
	def who_am_i():
		me = session['current_user']
		resp = jsonify(
			user=m.User.dump(me, use='full'),
			caps=session['current_user_caps'],
			userType=session['current_user_type'],
			roles=session['current_user_roles'],
			runtimeEnvironment={
				'tiger': util.tiger.get_url_root(),
				'edm': util.edm.get_url_root(),
				'go': util.go.get_url_root(),
			}
		)
		resp.headers['Cache-Control'] = 'max-age=0, must-revalidate'
		return resp

	@app.route('/logout')
	def logout():
		@after_this_request
		def clear_cookie(response):
			response.delete_cookie(current_app.config['APP_COOKIE_NAME'])
			return response
		return redirect(app.config['AUTHENTICATION_LOGOUT_URL'])

	@app.route('/authorization_response')
	def authorization_response():
		original_url = request.args['r']

		# retrieve the access_token using code from authorization grant
		try:
			resp = soteria.authorized_response()
		except Exception, e:
			return make_response(_(\
				'error getting access token: {}').format(e), 500)

		if resp is None:
			return make_response(_(\
				'You need to grant access to continue, error: {}').format(
				request.args.get('error')), 400)

		# get user info from Go
		try:
			token = resp['access_token']
		except:
			return make_response(_('error loading access token {}'\
				).format(resp), 500)

		try:
			userInfo = requests.get(app.config['AUTHENTICATED_USER_INFO_URL'],
				params={'oauth_token': token},
				headers={
					'Accept': 'application/vnd.edm.v1',
					'Content-Type': 'application/json'
				}).json()
			# current_app.logger.info('retrieved user info {}'.format(userInfo))
			email = userInfo['info']['email']
		except Exception, e:
			return make_response(_('error retrieving user info {}'
				).format(e), 500)

		#
		# search for user, if found, setup cookie
		try:
			me = m.User.query.filter(m.User.emailAddress==email).one()
		except NoResultFound:
			SS.rollback()
			# add user
			try:
				me = m.User(emailAddress=email,
					familyName=userInfo['extra']['last_name'],
					givenName=userInfo['extra']['first_name'],
					globalId=userInfo['extra']['global_id']
				)
				SS.add(me)
				SS.flush()
			except Exception, e:
				SS.rollback()
				current_app.logger.error('error creating new user: {}'.format(e))
				return make_response(_('error creating new user {}').format(email), 500)

		try:
			result = util.tiger.get_user_roles(me.globalId)
			user_type = result['user']['role']
			roles = result['project_user_roles']
			caps = util.tiger.role2caps(user_type)
		except Exception, e:
			if current_app.config.get('DEBUG'):
				user_type = util.tiger.SYS_ADMIN
				roles = {}
				caps = util.tiger.role2caps(user_type)
			else:
				return make_response(_('error getting user roles {}').format(e), 500)

		# indicate cookie should be updated
		session['current_user'] = me
		session['current_user_caps'] = caps
		session['current_user_type'] = user_type
		session['current_user_roles'] = roles
		g.update_cookie = True

		response = redirect(location=original_url)
		# data = {
		# 	'REMOTE_USER_ID': me.userId,
		# 	'REMOTE_USER_NAME': me.userName,
		# 	'CAPABILITIES': caps,
		# 	'USER_TYPE': user_type,
		# 	'ROLES': roles,
		# }
		# value = auth.encode_cookie(data,
		# 	current_app.config['APP_COOKIE_SECRET'], timeout=0)
		# response.set_cookie(current_app.config['APP_COOKIE_NAME'], value)
		return response

	@app.route('/health-check')
	def health_check():
		return make_response('OK', 200, {'Content-Type': 'text/plain'})

	# @app.errorhandler(404)
	# def default_hander(exc):
	# 	if request.path.startswith('/static'):
	# 		return make_response(
	# 			_('Sorry, the resource you have requested for is not found'),
	# 			404)
	# 	if request.path.startswith('/api/'):
	# 		return make_response(jsonify(error='requested url not found'),
	# 			404, {})
	# 	# TODO: only redirect valid urls
	# 	return redirect('/#%s' % request.path)

	return app


def check_appen_auth(header="authorization"):
	"""
	Decodes the token in the header and updates
	the session. Returns the User object for the
	logged in user.
	"""

	# extract token from header
	token = request.headers.get(header, None)
	if token is None:
		raise AuthError("No {0} header found".format(header))

	# decode token
	try:
		payload = jwt.decode(token, current_app.config["APPEN_API_SECRET_KEY"])
	except jwt.DecodeError, e:
		raise AuthError("Unable to decode token: {0}".format(unicode(e)))

	# check expected payload data
	expected_keys = ["appenId", "userType", "roles", "caps"]

	for key in expected_keys:
		if key not in payload:
			raise AuthError("Token payload missing: {0}".format(key))

	appen_id = payload["appenId"]

	# retrieve user
	try:
		user = User.query.filter_by(appen_id=appen_id).one()
	except NoResultFound:
		raise AuthError("User not found for appen id: {0}".format(appen_id))

	update_session(user, payload["caps"], payload["userType"], payload["roles"])

	return user


def get_user_info(appen_id):
	"""
	Retrieves user info from AppenGlobal.
	Returns a tuple of (user_type, roles, caps).
	"""
	result = util.tiger.get_user_roles(appen_id)
	user_type = result["user"]["role"]
	roles = result["project_user_roles"]
	caps = util.tiger.role2caps(user_type)
	return (user_type, roles, caps)


def create_access_token(appen_id, expires_after=datetime.timedelta(hours=2)):
	"""
	Returns an access token.
	"""

	user_type, roles, caps = get_user_info(appen_id)
	expires_at = datetime.datetime.utcnow() + expires_after

	# TODO standardise on snake case for payload keys
	# for consistency with cookie
	payload = {
		"appenId": appen_id,
		"userType": user_type,
		"roles": roles,
		"caps": caps,
	}

	payload.update({"exp" : expires_at})

	token = jwt.encode(payload, current_app.config["APPEN_API_SECRET_KEY"], algorithm="HS256")
	return token.decode(), expires_at


def update_session(user, caps, user_type, roles):
	session["current_user"] = user
	session["current_user_caps"] = caps
	session["current_user_type"] = user_type
	session["current_user_roles"] = roles

