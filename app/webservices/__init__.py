
from functools import wraps

from flask import Blueprint, render_template, make_response

from app.api import InvalidUsage


webservices = Blueprint('webservices', __name__, template_folder='./xml')


def ws(template_xml):
	def rendering_customization_decorator(fn):
		@wraps(fn)
		def xml_responder(*args, **kwargs):
			try:
				result = fn(*args, **kwargs)
				template = template_xml
				status_code = 200
			except InvalidUsage, e:
				result = dict(error=str(e))
				template = 'error.xml'
				status_code = 400
			except Exception, e:
				result = dict(error=str(e))
				template = 'error.xml'
				status_code = 500
			resp = make_response(render_template(template, **result))
			resp.status_code = status_code
			resp.headers['Content-Type'] = 'text/xml'
			return resp
		return xml_responder
	return rendering_customization_decorator


import handlers
