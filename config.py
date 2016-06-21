
import os

class Config:
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
	SQLALCHEMY_COMMIT_ON_TEARDOWN = True
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	SQLALCHEMY_DATABASE_URI = (os.environ.get('DATABASE_URI')
			or 'postgresql://localhost/atdb')
	NON_ADMIN_REDIRECT_URL = (os.environ.get('NON_ADMIN_REDIRECT_URL')
			or 'http://appenonline.appen.com.au')
	AUTHENTICATION_LOGIN_URL = (os.environ.get('AUTHENTICATION_LOGIN_URL')
			or 'http://appenonline.appen.com.au')
	AUTHENTICATION_LOGOUT_URL = (os.environ.get('AUTHENTICATION_LOGOUT_URL')
			or 'http://appenonline.appen.com.au/logout')
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
