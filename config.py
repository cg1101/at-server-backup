
import logging
import os

from LRUtilities.Api import (
	AudioServerApi,
	AudioServerStageApi,
	AudioServerDevApi,
	ProjectDbApi,
	ProjectDbStageApi,
	ProjectDbDevApi
)


class Config:
	ENV = None
	SECRET_KEY = os.environ['SECRET_KEY']
	APPEN_API_SECRET_KEY = os.environ['APPEN_API_SECRET_KEY']

	SSO_COOKIE_NAME = os.environ.get('SSO_COOKIE_NAME', '').strip()

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
	USE_PDB_API = bool(os.environ.get(
			'USE_PDB_API', '').strip())
	LOG_LEVEL = logging.INFO
	AUDIO_SERVER_API_SECRET = None
	AUDIO_SERVER_API_CLS = None
	ADMIN_APPEN_ID = os.environ.get("ADMIN_APPEN_ID")
	SEED_MIGRATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "seeds"))

	@staticmethod
	def init_app(app):
		pass


class DevelopmentConfig(Config):
	DEBUG = True
	ENV = "dev"
	LOG_LEVEL = logging.DEBUG
	AUDIO_SERVER_API_SECRET = "secret"
	AUDIO_SERVER_API_CLS = AudioServerDevApi
	PDB_API_CLS = ProjectDbDevApi


class TestingConfig(Config):
	TESTING = True
	ENV = "test"
	AUDIO_SERVER_API_CLS = AudioServerDevApi
	PDB_API_CLS = ProjectDbDevApi


class AwsConfig(Config):
	AUDIO_SERVER_API_SECRET = os.environ.get("AUDIO_SERVER_API_SECRET")


class QaConfig(AwsConfig):
	DEBUG = True
	ENV = "qa"
	LOG_LEVEL = logging.DEBUG
	AUDIO_SERVER_API_CLS = AudioServerStageApi
	PDB_API_CLS = ProjectDbStageApi


class StageConfig(AwsConfig):
	DEBUG = True
	ENV = "stage"
	LOG_LEVEL = logging.DEBUG
	AUDIO_SERVER_API_CLS = AudioServerStageApi
	PDB_API_CLS = ProjectDbStageApi


class ProductionConfig(AwsConfig):
	ENV = "prod"
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	AUDIO_SERVER_API_CLS = AudioServerApi
	PDB_API_CLS = ProjectDbApi


config = {
	'development': DevelopmentConfig,
	'testing': TestingConfig,
	'qa': QaConfig,
	'stage': StageConfig,
	'production': ProductionConfig,
	'default': DevelopmentConfig,
}
