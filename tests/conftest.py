import os
import pytest

from LRUtilities.FlaskExtensions import SeedMigrate
from app import create_app
from db import database as _db
from tests.sample_data import add_sample_data, keys as _sample_data


@pytest.fixture(scope="session")
def app(request):
	app = create_app("testing")
	ctx = app.app_context()
	ctx.push()
	request.addfinalizer(lambda: ctx.pop())
	return app


@pytest.fixture(scope="session")
def test_client(app):
	return app.test_client()


@pytest.fixture(scope="session")
def db(app, request):
	_db.init_app(app)

	# create schema
	_db.drop_all()
	_db.create_all()

	# seed database
	seed_migrate = SeedMigrate(app, _db)
	seed_migrate.update()

	# add sample data
	add_sample_data(_db.session)
	_db.session.commit()

	request.addfinalizer(lambda: _db.drop_all())
	return _db


@pytest.fixture(scope="session")
def sample_data():
	return _sample_data


@pytest.fixture(scope="function")
def session(db, request):
	connection = db.engine.connect()
	transaction = connection.begin()
	options=dict(bind=connection, binds={})
	session = db.create_scoped_session(options=options)

	def teardown():
		transaction.rollback()
		connection.close()
		session.remove()

	request.addfinalizer(teardown)
	return session
