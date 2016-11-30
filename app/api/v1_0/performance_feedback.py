import logging

from flask import jsonify, request

from . import api_1_0 as bp
from app.api import Field, InvalidUsage, MyForm, api, caps, get_model, validators
from db import database as db
from db.model import PerformanceFeedbackEntry

log = logging.getLogger(__name__)


@bp.route("performancefeedback/<int:performance_feedback_entry_id>", methods=["DELETE"])
@api
@caps()
@get_model(PerformanceFeedbackEntry)
def delete_performance_feedback_entry(entry):
	db.session.delete(entry)
	db.session.commit()
	return jsonify(success=True)
