#!/usr/bin/env python

import os

from flask import Flask, session, request, send_file

from config import config
from db.model import User
from db.db import SS

# app = Flask(__name__)

# from .db import SS
# @app.teardown_appcontext
# def shutdown_session(exception=None):
# 	SS.remove()

def create_app(config_name):
	app = Flask(__name__)
	app.config.from_object(config[config_name])
	config[config_name].init_app(app)

	from app.api import api_1_0
	from app.webservices import webservices
	# app.register_blueprint(api_1_0, url_prefix='/api/1.0')
	app.register_blueprint(api_1_0, url_prefix='/')
	app.register_blueprint(webservices, url_prefix='/webservices')

	@app.before_request
	def get_current_user():
		print '\033[1;32mApp.before_request()\n' + '='* 30
		# if request.headers.get('Content-Type', '') == 'application/json':
		# 	print request.get_json()
		print '\033[1;32mget json returns\033[0m', request.get_json()
		print 'set up current user in session'

		me = User.query.get(699)
		session['current_user'] = me
		if request.method in ('POST', 'PUT'):
			print 'headers is', request.headers
			print 'is JSON request', request.headers.get('Content-Type', '') == 'application/json'
			print 'form is', request.form
			print 'args', request.args
			print 'values', request.values
			print 'data', request.data
			#print 'json', request.json

	@app.after_request
	def clear_current_user(resp):
		session['current_user'] = None
		return resp

	@app.teardown_request
	def terminate_transaction(exception):
		if exception is not None:
			app.logger.info('\033[1;31mFailed\033[0m ===> rollback')
			SS.rollback()

	dot = os.path.dirname(__file__)

	@app.route('/')
	def index():
		return send_file(os.path.join(dot, 'index.html'))

	return app
