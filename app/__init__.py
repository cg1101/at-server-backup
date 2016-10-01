#!/usr/bin/env python

import re

import requests
import sqlalchemy.orm.exc
from flask import Flask, session, request, after_this_request,\
		redirect, jsonify, make_response, url_for, current_app
from flask_oauthlib.client import OAuth
from flask_cors import CORS

from config import config
from db.model import User
from db.db import SS
from db import database as db
import auth
from .i18n import get_text as _
import app.util as util

def create_app(config_name):
	app = Flask(__name__)
	app.config.from_object(config[config_name])
	config[config_name].init_app(app)
	db.init_app(app)
	CORS(app, resources={'/api/1.0/*': {'origins': '*'}})

	public_url_patterns = map(re.compile, [
		'/static/',
		'/favicon.ico',
		'/edm',
		'/webservices',
		'/logout',
		'/authorization_response',
		'/api/1.0/status',
		'/api/1.0/audiocollections/\d+/importconfig',
		'/api/1.0/audiocollections/\d+/import',
	])
	json_url_patterns = map(re.compile, [
		'/api'
	])

	from app.api import api_1_0
	from app.edm import edm
	# from app.webservices import webservices
	from app.views import views
	app.register_blueprint(api_1_0, url_prefix='/api/1.0/')
	app.register_blueprint(edm, url_prefix='/edm')
	# app.register_blueprint(webservices, url_prefix='/webservices')
	app.register_blueprint(views, url_prefix='')

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
		# no need to authenticate
		for p in public_url_patterns:
			if p.match(request.path):
				return None

		# authenticate by cookie
		cookie = request.cookies.get(current_app.config['APP_COOKIE_NAME'])
		if cookie or True:
			secret = current_app.config['APP_COOKIE_SECRET']
			try:
				user_dict = auth.decode_cookie(cookie, secret)
			except:
				user_dict = None
			# # TODO: remove following statement to re-enable authentication
			# user_dict = {'REMOTE_USER_ID':699}

			if user_dict:
				user = User.query.get(user_dict['REMOTE_USER_ID'])
				session['current_user'] = user
				return None
		# 	else:
		# 		# cookie corrupted or expired
		# 		pass
		# else:
		# 	# cookie not found
		# 	pass

		# authenticate by header
		try:
			authorization_info = request.headers.get('authorization', None)
			globalId, token = authorization_info.split('~', 1)
			result = util.go.check_token_for_user(globalId)
			# result = {
			# 	'token': token,
			# 	'expires_at': 'something',
			# 	'appen_id': 15517,
			# 	'app_id': 'appen_global'
			# }
			if result and token == result['token']:
				try:
					user = User.query.filter(User.globalId==globalId).one()
					session['current_user'] = user
					return None
				except NoResultFound:
					result = util.edm.get_user(globalId)
					if result:
						data = dict(
							familyName=result['family_name'],
							givenName=result['given_name'],
							emailAddress=result['primary_email_email_address'],
							globalId=globalId,
						)
						user = User(**data)
						SS.add(user)
						SS.flush()
						SS.commit()
						session['current_user'] = user
						return None
		except:
			pass

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
	def clear_current_user(resp):
		session['current_user'] = None
		return resp

	@app.route('/whoami')
	def who_am_i():
		me = session['current_user']
		return jsonify(
			user=User.dump(me, use='full'),
			runtimeEnvironment={
				'tiger': util.tiger.get_url_root(),
				'edm': util.edm.get_url_root(),
				'go': util.go.get_url_root(),
			}
		)

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
			return make_response(_('error getting access token: {}').format(e), 500)

		if resp is None:
			return make_response(_(
				'You need to grant access to continue, error: {}').format(
				request.args['error']), 400)

		# get user info from Go
		try:
			token = resp['access_token']
		except:
			return make_response(_('error loading access token {}').format(resp), 500)

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
			me = User.query.filter(User.emailAddress==email).one()
		except sqlalchemy.orm.exc.NoResultFound:
			SS.rollback()
			# add user
			try:
				me = User(emailAddress=email,
					familyName=userInfo['extra']['last_name'],
					givenName=userInfo['extra']['first_name'],
					globalId=userInfo['extra']['global_id']
				)
				SS.add(me)
				SS.flush()
			except Exception, e:
				SS.rollback()
				# current_app.logger.error('error creating new user: {}'.format(e))
				return make_response(_('error creating new user {}').format(email), 500)

		data = {
			'REMOTE_USER_ID': me.userId,
			'REMOTE_USER_NAME': me.userName,
			'CAPABILITIES': ['admin']
		}
		value = auth.encode_cookie(data,
			current_app.config['APP_COOKIE_SECRET'], timeout=0)
		response = redirect(location=original_url)
		response.set_cookie(current_app.config['APP_COOKIE_NAME'], value)
		return response

	@app.errorhandler(404)
	def default_hander(exc):
		if request.path.startswith('/static'):
			return make_response(
				_('Sorry, the resource you have requested for is not found'),
				404)
		if request.path.startswith('/api/'):
			return make_response(jsonify(error='requested url not found'),
				404, {})
		# TODO: only redirect valid urls
		return redirect('/#%s' % request.path)

	return app
