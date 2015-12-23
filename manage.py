#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import os

from app import create_app
from flask.ext.script import Manager

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
# migrate = Migrate(app, db)

# def make_shell_context():
# 	return dict(app=app, db=db, User=User, Role=Role)
# manager.add_command('shell', Shell(make_context=make_shell_context))
# manager.add_command('db', MigrateCommand)

@manager.command
def list():
	for rule in app.url_map.iter_rules():
		print(str(rule), 'methods:', ','.join(rule.methods), '->', rule.endpoint)


if __name__ == "__main__":
	manager.run()
