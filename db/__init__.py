import os
import sys

from flask_sqlalchemy import SQLAlchemy

from .schema import metadata

if os.environ.get("FORCE_APP_MODE"):
	mode = "app"
else:
	mode = 'app' if sys.modules.has_key('app') else 'shell'

database = SQLAlchemy(metadata=metadata)
