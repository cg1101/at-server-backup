
from flask import request, abort, session, jsonify

import db.model as m
from db.db import SS
from app.api import api, caps, validate_input as v, get_text as _
from app.i18n import get_text as _
from . import api_1_0 as bp

_name = __file__.split('/')[-1].split('.')[0]

@bp.route(_name + '/', methods=['GET'])
@api
@caps()
def get_tag_sets():
	'''
	returns a list of tag sets
	'''
	tagSets = m.TagSet.query.order_by(m.TagSet.tagSetId).all()
	return jsonify({
		'tagSets': m.TagSet.dump(tagSets),
	})

@bp.route(_name + '/<int:tagSetId>', methods=['GET'])
@api
@caps()
def get_tag_set(tagSetId):
	'''
	returns specified tag set
	'''
	tagSet = m.TagSet.query.get(tagSetId)
	if not tagSet:
		abort(404)
	return jsonify({
		'tagSet': m.TagSet.dump(tagSet),
	})

@bp.route(_name + '/<int:tagSetId>/tags/', methods=['POST'])
@api
@caps()
def create_tag():
	'''
	creates a new tag
	'''
	try:
		if request.headers.get('Content-Type', '') == 'application/json':
			data = json.loads(request.data)
		else:
			data = s.load(request.values).data
	except Exception, e:
		raise RuntimeError, _('error parsing parameters: {0}').format(e)

	if not data.has_key('name'):
		raise RuntimeError, _('must provide parameter \'{0}\'').format('name')
	elif not isinstance(data['name'], basestring):
		raise RuntimeError, _('parameter \'{0}\' must be {1}').format('name', 'string')
	elif not data['name'].strip():
		raise RuntimeError, _('parameter \'{0}\' must not be blank').format('name')
	if m.ErrorType.query.filter_by(name=data['name']).count() > 0:
		raise RuntimeError, _('name \'{0}\' is already in use').format(data['name'])

	if not data.has_key('errorClassId'):
		raise RuntimeError, _('must provide parameter \'{0}\'').format('errorClassId')
	elif not isinstance(data['errorClassId'], int):
		raise RuntimeError, _('parameter \'{0}\' must be {1}').format('errorClassId', 'int')
	if not m.ErrorClass.get(data['errorClassId']):
		raise RuntimeError, _('ErrorClass #{0} not found').format(data['errorClassId'])


	if data.has_key('errorTypeId'):
		del data['errorTypeId']

	tag = m.Tag(**data)
	SS.add(tag)
	_tag = m.ErrorType.query.filter_by(
			errorClassId=errorType.errorClassId).filter_by(
			name=errorType.name).one()
	assert tag is _tag
	return jsonify({
		'status': _('new tag {0} successfully created').format(tag.name),
		'errorType': m.Tag.dump(tag),
	})

@bp.route(_name + '<int:tagSetId>/tags/<int:tagId>', methods=['PUT'])
@api
@caps()
def update_tag(tagSetId, tagId):
	'''
	updates tag settings
	'''
	return jsonify({
		'tag': {},
	})
