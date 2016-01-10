#!/usr/bin/env python

import os

from flask import Flask, session, request, send_file, after_this_request,\
		redirect, jsonify, make_response

from config import config
from db.model import User
from db.db import SS
from .i18n import get_text as _
from .auth import MyAuthMiddleWare

def create_app(config_name):
	app = Flask(__name__)
	app.config.from_object(config[config_name])
	config[config_name].init_app(app)

	app.wsgi_app = MyAuthMiddleWare(app.wsgi_app,
		app.config['AUTHENTICATION_LOGIN_URL'],
		public_prefixes=['/static/', '/webservices', '/logout'],
		json_prefixes=['/api/'],
	)

	from app.api import api_1_0
	from app.webservices import webservices
	from app.views import views
	app.register_blueprint(api_1_0, url_prefix='/api/1.0/')
	app.register_blueprint(webservices, url_prefix='/webservices')
	app.register_blueprint(views, url_prefix='')

	@app.before_request
	def get_current_user():
		data = request.environ.get('myauthmiddleware', None)
		if not data:
			user = User.query.get(699)
		else:
			user = User.query.get(data['REMOTE_USER_ID'])
		session['current_user'] = user

	@app.after_request
	def clear_current_user(resp):
		session['current_user'] = None
		return resp

	@app.teardown_request
	def terminate_transaction(exception):
		if exception is None:
			SS.commit()
		else:
			SS.rollback()
		SS.remove()

	@app.route('/logout')
	def logout():
		@after_this_request
		def clear_cookie(response):
			response.delete_cookie('appen')
			return response
		if request.is_xhr:
			return jsonify({'url': app.config['AUTHENTICATION_LOGOUT_URL']})
		return redirect(app.config['AUTHENTICATION_LOGOUT_URL'])

	@app.route('/logout2')
	def logout2():
		@after_this_request
		def clear_cookie(response):
			response.delete_cookie('appen')
			return response
		return jsonify({'url': app.config['AUTHENTICATION_LOGOUT_URL']})

	@app.errorhandler(404)
	def default_hander(exc):
		if request.path.startswith('/static'):
			return make_response(
				_('Sorry, the resource you have requested for is not found'),
				404)
		# TODO: only redirect valid urls
		return redirect('/#%s' % request.path)

	return app
