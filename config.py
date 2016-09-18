
import os

class Config:
	SECRET_KEY = os.environ['SECRET_KEY']

	APP_COOKIE_NAME = os.environ['APP_COOKIE_NAME']
	APP_COOKIE_SECRET = os.environ['APP_COOKIE_SECRET']

	AUTHENTICATED_USER_INFO_URL = os.environ['AUTHENTICATED_USER_INFO_URL']
	AUTHENTICATION_LOGOUT_URL = os.environ['AUTHENTICATION_LOGOUT_URL']

	EDM_TOPICS = set([v for (k, v) in os.environ.iteritems()
		if k.startswith('EDM_TOPIC_') and bool(v)])

	OAUTH2_AUTHORIZATION_ENDPOINT = os.environ['OAUTH2_AUTHORIZATION_ENDPOINT']
	OAUTH2_TOKEN_ENDPOINT = os.environ['OAUTH2_TOKEN_ENDPOINT']
	OAUTH2_CLIENT_ID = os.environ['OAUTH2_CLIENT_ID']
	OAUTH2_CLIENT_SECRET = os.environ['OAUTH2_CLIENT_SECRET']

	SQLALCHEMY_COMMIT_ON_TEARDOWN = True
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	SQLALCHEMY_DATABASE_URI = (os.environ.get('DATABASE_URI')
			or 'postgresql://localhost/atdb')

	NON_ADMIN_REDIRECT_URL = (os.environ.get('NON_ADMIN_REDIRECT_URL')
			or 'http://appenonline.appen.com.au')

	SNS_AUTHENTICATE_REQUEST = bool(os.environ.get(
			'SNS_AUTHENTICATE_REQUEST', '').strip())

	@staticmethod
	def init_app(app):
		pass

class DevelopmentConfig(Config):
	DEBUG = True

class TestingConfig(Config):
	TESTING = True

class ProductionConfig(Config):
	SQLALCHEMY_TRACK_MODIFICATIONS = False

config = {
	'development': DevelopmentConfig,
	'testing': TestingConfig,
	'production': ProductionConfig,
	'default': DevelopmentConfig,
}
