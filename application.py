import os

from app import create_app

application = create_app(os.environ.get('APPLICATION_CONFIG', 'development'))
