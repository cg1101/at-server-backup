
import datetime

from flask import request, session, jsonify
import pytz

import db.model as m
from db.db import SS
from app.api import api, caps, MyForm, Field, validators
from app.i18n import get_text as _
from . import api_1_0 as bp, InvalidUsage

_name = __file__.split('/')[-1].split('.')[0]


@bp.route(_name + '/<int:sheetId>', methods=['GET'])
@api
@caps()
def get_sheet(sheetId):
	sheet = m.Sheet.query.get(sheetId)
	if not sheet:
		raise InvalidUsage(_('sheet {0} not found').format(sheetId), 404)
	return jsonify({
		'sheet': m.Sheet.dump(sheet, context={'level': 1}),
	})


def mark_answer_sheet(sheet):
	# TODO: implement this
	return (True or False)


@bp.route(_name + '/<int:sheetId>', methods=['DELETE'])
@api
@caps()
def submit_sheet(sheetId):
	sheet = m.Sheet.query.get(sheetId)
	if not sheet:
		raise InvalidUsage(_('sheet {0} not found').format(sheetId), 404)

	me = session['current_user']
	if sheet.userId != me.userId:
		raise InvalidUsage(_('you are not the owner of sheet {0}').format(sheetId))

	now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

	if sheet.status == m.Sheet.STATUS_EXPIRED:
		raise InvalidUsage(_('sheet {0} has expired already').format(sheetId))
	elif sheet.status == m.Sheet.STATUS_FINISHED:
		raise InvalidUsage(_('sheet {0} is finished already').format(sheetId))
	elif sheet.status == m.Sheet.STATUS_SHOULD_EXPIRE:
		# if sheet.tExpiresBy < now:
		sheet.tExpiredAt = now
		SS.flush()
		SS.commit()
		raise InvalidUsage(_('sheet {0} has expired already').format(sheetId))

	finished = all([entry.answerId != None for entry in sheet.entries])
	if not finished:
		raise InvalidUsage(_('sheet {0} is not finished').format(sheetId))

	sheet.tFinishedAt = now
	SS.flush()

	# TODO: define autoScoring property on sheet
	autoScoring = all([i.question.autoScoring for i in sheet.entries])
	if autoScoring:
		passed = mark_answer_sheet(sheet)
		if passed:
			message = _(sheet.test.messageSuccess) or _('Congratulations, you passed!',
				'Your score is {0}.').format(sheet.score)
		else:
			message = _(sheet.test.messageFailure) or _('Sorry, you failed.',
				'Your score is {0}.').format(sheet.score)
	else:
		message = _('Thank you for taking the test!',
				'The translation supervisor will be marking your test in next 7-10 working days,',
				'and your result will then be available in AppenOnline.')

	return jsonify({
		'message': message,
	})


def check_sheet_entry_existence(data, key, sheetEntryId, sheetId):
	entry = m.SheetEntry.query.get(sheetEntryId)
	if not entry or entry.sheetId != sheetId:
		raise ValueError, _('sheet entry {0} not found').format(sheetEntryId)


def check_answer(data, key, answer):
	# TODO: implement this
	pass


@bp.route(_name + '/<int:sheetId>/answers/', methods=['POST'])
@api
@caps()
def submit_answer(sheetId):
	sheet = m.Sheet.query.get(sheetId)
	if not sheet:
		raise InvalidUsage(_('sheet {0} not found').format(sheetId), 404)

	now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
	if sheet.tExpiresBy < now:
		sheet.tExpiredAt = now
		SS.flush()
		SS.commit()
		raise InvalidUsage(_('sheet {0} has expired already').format(sheetId))

	me = session['current_user']
	if sheet.userId != me.userId:
		raise InvalidUsage(_('you are not the owner of sheet {0}').format(sheetId))

	data = MyForm(
		Field('sheetEntryId', is_mandatory=True, validators=[
			(check_sheet_entry_existence, (sheetId,)),
		]),
		Field('answer', is_mandatory=True, validators=[
			validators.is_string,
			check_answer,
		]),
	).get_data(with_view_args=False)

	answer = m.Answer(**data)
	SS.add(answer)
	SS.flush()
	assert answer.answerId

	# TODO: define relationship on SheetEntry
	entry = m.SheetEntry.query.get(data['sheetEntryId'])
	entry.answerId = answer.answerId

	return jsonify({
		'message': _('created answer {0} successfully').format(answer.answerId),
		'answer': m.Answer.dump(answer),
	})


@bp.route(_name + '/<int:sheetId>/markings/', methods=['GET'])
@api
@caps()
def get_sheet_with_markings(sheetId):
	sheet = m.Sheet.query.get(sheetId)
	if not sheet:
		raise InvalidUsage(_('sheet {0} not found').format(sheetId), 404)
	return jsonify({
		'sheet': m.Sheet.dump(sheet, context={'level': 2})
	})


def normalize_marking_data(data, key, value):
	sheetId = data['sheetId']
	sheet = m.Sheet.query.get(sheetId)
	if not isinstance(value, list):
		raise ValueError, _('must be an array of marking entries')
	if len(value) != len(sheet.entries):
		raise ValueError, _('incorrect numbers of markings submitted, expecting {0}, got {1}').format(len(sheet.entries), len(value))
	markings = []
	for i, md in enumerate(value):
		if not isinstance(md, dict):
			raise ValueError, _('invalid marking entry {0}').format(str(md))
		if 'score' not in md:
			raise ValueError, _('score not found in marking entry {0}').format(str(md))
		try:
			score = md.get('score')
			score = float(score)
		except:
			raise ValueError, _('invalid marking score \'{0}\'').format(md.get('score'))
		if score < 0 or score > 10:
			raise ValueError, _('marking score out of [0, 10]')
		comment = md.get('comment')
		if comment is not None:
			comment = str(comment)
		markings.append(dict(score=score, comment=comment))
	return markings


def calculate_sheet_score(data, key, value):
	import pprint
	pprint.pprint(data)
	score = 0.0
	for md in data['markings']:
		score += md['score']
	score = score * 10.0 / len(data['markings'])
	return score


@bp.route(_name + '/<int:sheetId>/markings/', methods=['POST'])
@api
@caps()
def submit_marking(sheetId):
	sheet = m.Sheet.query.get(sheetId)
	if not sheet:
		raise InvalidUsage(_('sheet {0} not found').format(sheetId), 404)

	# TODO: add policy check to enable/disable re-marking and/or marking of expired sheets

	data = MyForm(
		Field('moreAttempts', is_mandatory=True, validators=[
			validators.is_bool,
		]),
		Field('comment', validators=[
			validators.is_string,
		]),
		Field('markings', is_mandatory=True, normalizer=normalize_marking_data),
		Field('score', is_mandatory=True, default=0, normalizer=calculate_sheet_score),
	).get_data()

	# TODO: define relationship marking on SheetEntry

	me = session['current_user']
	markings = data.pop('markings')
	for entry, md in zip(sheet.entries, markings):
		marking = m.Marking(**md)
		marking.sheetEntryId = entry.sheetEntryId
		marking.scorerId = me.userId
		SS.add(marking)
		SS.flush()
		entry.markingId = marking.markingId

	for key in ['moreAttempts', 'comment', 'score']:
		setattr(sheet, key, data[key])

	return jsonify({
		'message': _('marked sheet {0} successfully').format(sheetId),
		'sheet': m.Sheet.dump(sheet),
	})

