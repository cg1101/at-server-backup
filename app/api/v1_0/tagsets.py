
from flask import request, session, jsonify
import sqlalchemy.orm

import db.model as m
from db.db import SS
from app.api import api, caps, MyForm, Field, validators
from app.i18n import get_text as _
from . import api_1_0 as bp, InvalidUsage

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
		raise InvalidUsage(_('tag set {0} not found').format(tagSetId), 404)
	return jsonify({
		'tagSet': m.TagSet.dump(tagSet),
	})


def check_tag_name_uniqueness(data, key, name, tagSetId, tagId):
	if m.Tag.query.filter_by(tagSetId=tagSetId
			).filter_by(name=name
			).filter(m.Tag.tagId!=tagId).count() > 0:
		raise ValueError, _('name \'{0}\' is already in use').format(name)


def check_extract_start_uniqueness(data, key, extractStart, tagSetId, tagId):
	if m.Tag.query.filter_by(tagSetId=tagSetId
			).filter_by(extractStart=extractStart
			).filter(m.Tag.tagId!=tagId).count() > 0:
		raise ValueError, _('extract start \'{0}\' is already in use').format(extractStart)


def check_tag_shortcut_key_non_space(data, key, shortcutKey):
	if shortcutKey == ' ':
		raise ValueError, _('shortcut key must not be space')


def check_tag_shortcut_key_uniqueness(data, key, shortcutKey, tagSetId, tagId):
	if shortcutKey is not None:
		if m.Tag.query.filter_by(tagSetId=tagSetId
				).filter_by(shortcutKey=shortcutKey
				).filter(m.Tag.tagId!=tagId).count() > 0:
			raise ValueError, _('shortcut key \'{0}\' is already in use').format(shortcutKey)


def normalize_is_foreground(data, key, isForeground):
	tagType = data.get('tagType')
	if tagType in (m.Tag.EMBEDDABLE, m.Tag.NON_EMBEDDABLE):
		return bool(isForeground)


def check_tag_extract_end_required(data, key, extractEnd):
	tagType = data.get('tagType')
	if tagType in (m.Tag.EMBEDDABLE,):
		if extractEnd is None or not extractEnd:
			raise ValueError, _('must be specified for {0} tag').format(tagType)


def check_tag_image_required(data, key, previewId, isUpdating):
	tagType = data.get('tagType')
	if tagType in (m.Tag.EVENT,) and not isUpdating:
		if previewId is None:
			raise ValueError, _('must be specified for {0} tag').format(tagType)


def check_tag_color_required(data, key, color):
	tagType = data.get('tagType')
	if tagType in (m.Tag.EMBEDDABLE, m.Tag.NON_EMBEDDABLE):
		if color is None:
			raise ValueError, _('must be specified for {0} tag').format(tagType)


def check_tag_color_uniqueness(data, key, color, tagSetId, tagId):
	isForeground = data.get('isForeground')
	if color is not None:
		if m.Tag.query.filter_by(tagSetId=tagSetId
				).filter_by(isForeground=isForeground
				).filter_by(color=color
				).filter(m.Tag.tagId!=tagId).count() > 0:
			raise ValueError, _('color \'{0}\' is already in use'.format(color))


def check_tag_image_existence(data, key, previewId):
	if previewId is not None:
		image = m.TagImage.query.get(previewId)
		if not image:
			raise ValueError, _('preview image {0} not found').format(previewId)


def load_tag_preview_image(data, key, value):
	previewId = data.get('previewId')
	if previewId is not None:
		image = m.TagImage.query.get(previewId)
		if image:
			return image.image


@bp.route(_name + '/<int:tagSetId>/tags/', methods=['POST'])
@api
@caps()
def create_tag(tagSetId):
	'''
	creates a new tag
	'''
	tagSet = m.TagSet.query.get(tagSetId)
	if not tagSet:
		raise InvalidUsage(_('tag set {0} not found').format(tagSetId), 404)

	data = MyForm(
		Field('name', is_mandatory=True, validators=[
			validators.non_blank,
			(check_tag_name_uniqueness, (tagSetId, None)),
		]),
		Field('tagType', is_mandatory=True, validators=[
			(validators.enum, (
				m.Tag.EVENT,
				m.Tag.NON_EMBEDDABLE,
				m.Tag.EMBEDDABLE,
				m.Tag.SUBSTITUTION,
				m.Tag.ENTITY,
				m.Tag.FOOTNOTE)),
		]),
		Field('extractStart', is_mandatory=True, validators=[
			validators.non_blank,
			(check_extract_start_uniqueness, (tagSetId, None)),
		]),
		Field('extractEnd', validators=[
			validators.is_string,
			check_tag_extract_end_required,
		]),
		Field('shortcutKey', validators=[
			(validators.is_string, (), dict(length=1)),
			check_tag_shortcut_key_non_space,
			(check_tag_shortcut_key_uniqueness, (tagSetId, None)),
		]),
		Field('enabled', default=True, validators=[
			validators.is_bool,
		]),
		Field('surround', is_mandatory=True, validators=[
			validators.is_bool,
		]),
		Field('extend', is_mandatory=True, validators=[
			validators.is_bool,
		]),
		Field('split', is_mandatory=True, validators=[
			validators.is_bool,
		]),
		Field('isDynamic', default=False, validators=[
			validators.is_bool,
		]),
		Field('description', validators=[
			validators.is_string,
		]),
		Field('tooltip', validators=[
			validators.is_string,
		]),
		Field('isForeground', is_mandatory=True, default=lambda: None,
			normalizer=normalize_is_foreground, validators=[
			validators.is_bool,
		]),
		Field('color', is_mandatory=True, default=lambda: None, validators=[
			check_tag_color_required,
			(check_tag_color_uniqueness, (tagSetId, None)),
		]),
		Field('previewId', is_mandatory=True, default=lambda: None, validators=[
			(check_tag_image_required, (False,)),
			check_tag_image_existence,
		]),
		Field('image', is_mandatory=True, default=lambda: None,
			normalizer=load_tag_preview_image
		),
	).get_data()
	del data['previewId']

	tag = m.Tag(**data)
	SS.add(tag)
	SS.flush()
	SS.commit()
	dbs = sqlalchemy.orm.sessionmaker(bind=SS.bind)()
	tag = dbs.query(m.Tag).get(tag.tagId)
	return jsonify({
		'message': _('created tag {0} successfully').format(tag.name),
		'tag': tag.dump(tag),
	})


@bp.route(_name + '/<int:tagSetId>/tags/<int:tagId>', methods=['PUT'])
@api
@caps()
def update_tag(tagSetId, tagId):
	'''
	updates tag settings
	'''
	tagSet = m.TagSet.query.get(tagSetId)
	if not tagSet:
		raise InvalidUsage(_('tag set {0} not found').format(tagSetId), 404)
	tag = m.Tag.query.get(tagId)
	if not tag or tag.tagSetId != tagSetId:
		raise InvalidUsage(_('tag {0} not found').format(tagId), 404)

	data = MyForm(
		Field('name', validators=[
			validators.non_blank,
			(check_tag_name_uniqueness, (tagSetId, tagId)),
		]),
		# tag type cannot be updated
		Field('tagType', is_mandatory=True, default=lambda: tag.tagType),
		Field('extractStart', validators=[
			validators.non_blank,
			(check_extract_start_uniqueness, (tagSetId, tagId)),
		]),
		Field('extractEnd', validators=[
			validators.is_string,
			check_tag_extract_end_required,
		]),
		Field('shortcutKey', validators=[
			(validators.is_string, (), dict(length=1)),
			check_tag_shortcut_key_non_space,
			(check_tag_shortcut_key_uniqueness, (tagSetId, tagId)),
		]),
		Field('enabled', validators=[
			validators.is_bool,
		]),
		Field('surround', validators=[
			validators.is_bool,
		]),
		Field('extend', validators=[
			validators.is_bool,
		]),
		Field('split', validators=[
			validators.is_bool,
		]),
		Field('isDynamic', validators=[
			validators.is_bool,
		]),
		Field('description', validators=[
			validators.is_string,
		]),
		Field('tooltip', validators=[
			validators.is_string,
		]),
		Field('isForeground', default=lambda: None,
			normalizer=normalize_is_foreground, validators=[
			validators.is_bool,
		]),
		Field('color', default=lambda: tag.color, validators=[
			check_tag_color_required,
			(check_tag_color_uniqueness, (tagSetId, tagId)),
		]),
		Field('previewId', default=lambda: None, validators=[
			(check_tag_image_required, (True,)),
			check_tag_image_existence,
		]),
		Field('image', default=lambda: None,
			normalizer=load_tag_preview_image
		),
	).get_data()
	if data['previewId'] is None:
		del data['image']
	del data['previewId']

	for key in data.keys():
		value = data[key]
		if getattr(tag, key) != value:
			setattr(tag, key, value)
		else:
			del data[key]
	SS.flush()
	return jsonify({
		'message': _('updated tag {0} successfully').format(tagId),
		'updatedFields': data.keys(),
		'tag': tag.dump(tag),
	})

