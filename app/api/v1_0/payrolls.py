
import json

from flask import request, session, jsonify

import db.model as m
from db.db import SS
from app.api import api, caps, MyForm, Field, validators
from app.i18n import get_text as _
from . import api_1_0 as bp, InvalidUsage

_name = __file__.split('/')[-1].split('.')[0]


@bp.route(_name + '/', methods=['GET'])
@api
@caps()
def get_payrolls():
	payrolls = m.Payroll.query.order_by(m.Payroll.payrollId).all()
	return jsonify(payrolls=m.Payroll.dump(payrolls))
