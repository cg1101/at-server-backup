
from flask.ext.sqlalchemy import SQLAlchemy

from .schema import metadata

database = SQLAlchemy(metadata=metadata)
