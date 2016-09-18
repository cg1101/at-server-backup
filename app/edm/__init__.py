
from flask import Blueprint

edm = Blueprint('edm', __name__, template_folder='../templates')

import handlers
