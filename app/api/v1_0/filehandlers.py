
from flask import request, session, jsonify

import db.model as m
from db.db import SS
from app.api import api, caps
from app.i18n import get_text as _
from . import api_1_0 as bp

_name = __file__.split('/')[-1].split('.')[0]


@bp.route(_name + '/', methods=['GET'])
@api
@caps()
def get_file_handlers():
	handlers = m.FileHandler.query.order_by(m.FileHandler.handlerId).all()
	return jsonify({
		'fileHandlers': m.FileHandler.dump(handlers),
	})

