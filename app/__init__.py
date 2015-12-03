#!/usr/bin/env python

import os

from flask import Flask, session, request, send_file, after_this_request, redirect

from config import config
from db.model import User
from db.db import SS
from .auth import MyAuthMiddleWare

def create_app(config_name):
	app = Flask(__name__)
	app.config.from_object(config[config_name])
	config[config_name].init_app(app)

	app.wsgi_app = MyAuthMiddleWare(app.wsgi_app,
		app.config['AUTHENTICATION_LOGIN_URL'],
		public_prefixes=['/static/', '/logout'],
		json_prefixes=['/api/'],
	)

	from app.api import api_1_0
	from app.webservices import webservices
	# app.register_blueprint(api_1_0, url_prefix='/api/1.0')
	app.register_blueprint(api_1_0, url_prefix='/')
	app.register_blueprint(webservices, url_prefix='/webservices')

	@app.before_request
	def get_current_user():
		data = request.environ.get('myauthmiddleware', None)
		if not data:
			return
		user = User.query.get(data['REMOTE_USER_ID'])
		session['current_user'] = user

	@app.after_request
	def clear_current_user(resp):
		session['current_user'] = None
		return resp

	@app.teardown_request
	def terminate_transaction(exception):
		SS.remove()

	dot = os.path.dirname(__file__)

	@app.route('/')
	def index():
		return send_file(os.path.join(dot, 'index.html'))

	@app.route('/logout')
	def logout():
		@after_this_request
		def clear_cookie(response):
			response.delete_cookie('appen')
			return response
		return redirect(app.config['AUTHENTICATION_LOGOUT_URL'])

	return app
