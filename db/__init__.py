
import sys

from flask.ext.sqlalchemy import SQLAlchemy

from .schema import metadata

mode = 'app' if sys.modules.has_key('app') else 'shell'

database = SQLAlchemy(metadata=metadata)
