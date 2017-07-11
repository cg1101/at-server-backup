#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from LRUtilities.FlaskExtensions import SeedMigrate, SeedMigrateCommand
from application import application as app
from db import database as db

manager = Manager(app)
migrate = Migrate(app, db)
seed_migrate = SeedMigrate(app, db)

manager.add_command('db', MigrateCommand)
manager.add_command("seed", SeedMigrateCommand)

# def make_shell_context():
# 	return dict(app=app, db=db, User=User, Role=Role)
# manager.add_command('shell', Shell(make_context=make_shell_context))


def clean_docstring(docstring):
	"""
	Removes leading whitespace (indentation) from
	a docstring.
	"""
	return re.sub("\n\s+", "\n", docstring)


@manager.option("-d", "--detailed", action="store_true", default=False)
def list(detailed=False):

	for rule in app.url_map.iter_rules():

		if detailed:
			divider = "-----------------------"
			fn = app.view_functions[rule.endpoint]
			docstring = (fn.__doc__ or "No description available").strip()
			module = fn.__module__
			name = fn.func_name
			fmt = "{0}\n{1} {2}\n{3}\n\nEndpoint: {4}\n  Module: {5}\nFunction: {6}\n"

			print(fmt.format(
				divider,
				",".join(rule.methods),
				str(rule),
				clean_docstring(docstring),
				rule.endpoint,
				module,
				name,
			))

		else:
			print("{0} methods: {1} -> {2}".format(str(rule), ",".join(rule.methods), rule.endpoint))


if __name__ == '__main__':
	manager.run()
