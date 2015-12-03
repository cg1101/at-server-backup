
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
	SQLALCHEMY_COMMIT_ON_TEARDOWN = True
	FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
	FLASKY_MAIL_SENDER = 'Flasky Admin <flasky@example.com>'
	FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
	@staticmethod
	def init_app(app):
		pass

class DevelopmentConfig(Config):
	DEBUG = True
	MAIL_SERVER = 'smtp.googlemail.com'
	MAIL_PORT = 587
	MAIL_USE_TLS = True
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
	AUTHENTICATION_LOGIN_URL = 'http://localhost:8080'
	AUTHENTICATION_LOGOUT_URL = 'http://localhost:8080/logout'
	SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
		'postgresql://localhost/atdb'

class TestingConfig(Config):
	TESTING = True
	AUTHENTICATION_LOGIN_URL = 'http://localhost:8080'
	AUTHENTICATION_LOGOUT_URL = 'http://localhost:8080/logout'
	SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
		'postgresql://localhost/at_test'

class ProductionConfig(Config):
	AUTHENTICATION_LOGIN_URL = 'http://appenonline.appen.com.au'
	AUTHENTICATION_LOGOUT_URL = 'http://appenonline.appen.com.au/logout'
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
		'postgresql://dbserver/appentext'

config = {
	'development': DevelopmentConfig,
	'testing': TestingConfig,
	'production': ProductionConfig,
	'default': DevelopmentConfig,
}
