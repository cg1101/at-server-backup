
import datetime

from flask import request, abort, session

import db.model as m
from db.db import SS
from app.api import ajax, caps, get_text as _
from . import api_1_0 as bp

_name = __file__.split('/')[-1].split('.')[0]

@bp.route(_name + '/<int:sheetId>', methods=['GET'])
@ajax
@caps()
def get_sheet(sheetId):
	sheet = m.Sheet.query.get(sheetId)
	if not sheet:
		abort(404)
	return {
		'sheet': m.Sheet.dump(sheet, context={'level': 1}),
	}


@bp.route(_name + '/<int:sheetId>', methods=['DELETE'])
@ajax
@caps()
def submit_sheet(sheetId):
	sheet = m.Sheet.query.get(sheetId)
	if not sheet:
		abort(404)
	now = datetime.datetime.utcnow
	if sheet.tExpiresBy < now:
		sheet.tExpiredAt = now
		SS().flush()
		SS().commit()
		raise RuntimeError, 'answer sheet expired already'

	# check if all questions have been answered
	finished = all([entry.answerId != None for entry in sheet.entries])
	if not finished:
		raise RuntimeError, 'not finished'
	sheet.tFinished = now
	SS().flush()
	# score the sheet
	#if sheet.
	return {
		'message': 'submitted',
	}


@bp.route(_name + '/<int:sheetId>/answers/', methods=['POST'])
@ajax
@caps()
def submit_answer(sheetId):
	sheet = m.Sheet.query.get(sheetId)
	if not sheet:
		abort(404)
	# TODO:
	data = request.get_json()
	index = data['index']
	answer = m.Answer(**data)
	sheet.entries[index].answer = answer
	SS().flush()
	return {
		'answer': m.Answer.dump(answer),
	}


@bp.route(_name + '/<int:sheetId>/markings/', methods=['GET'])
@ajax
@caps()
def get_sheet_with_markings(sheetId):
	sheet = m.Sheet.query.get(sheetId)
	if not sheet:
		abort(404)
	return {
		'sheet': m.Sheet.dump(sheet, context={'level': 2})
	}


@bp.route(_name + '/<int:sheetId>/markings/', methods=['POST'])
@ajax
@caps()
def submit_marking(sheetId):
	sheet = m.Sheet.query.get(sheetId)
	if not sheet:
		abort(404)
	# TODO
	data = rquest.get_json()
	index = data['index']
	marking = m.Marking(**data)
	sheet.entries[index].marking = marking
	SS().flush()
	return {
		'message': 'blabh',
	}
