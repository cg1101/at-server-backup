
from flask import request, abort, session, jsonify

import db.model as m
from db.db import SS
from app.api import api, caps, MyForm, Field, validators
from app.i18n import get_text as _
from . import api_1_0 as bp, InvalidUsage

_name = __file__.split('/')[-1].split('.')[0]


@bp.route(_name + '/', methods=['GET'])
@api
@caps()
def get_label_sets():
	'''
	returns a list of label sets
	'''
	labelSets = m.LabelSet.query.order_by(m.LabelSet.labelSetId).all()
	return jsonify({
		'labelSets': m.LabelSet.dump(labelSets),
	})


@bp.route(_name + '/<int:labelSetId>', methods=['GET'])
@api
@caps()
def get_label_set(labelSetId):
	'''
	returns specified label set
	'''
	labelSet = m.LabelSet.query.get(labelSetId)
	if not labelSet:
		raise InvalidUsage(_('label set {0} not found').format(labelSetId), 404)
	return jsonify({
		'labelSet': m.LabelSet.dump(labelSet),
	})


def check_label_name_uniqueness(data, key, name, labelSetId, labelId):
	if m.Label.query.filter_by(labelSetId=labelSetId
			).filter_by(name=name
			).filter(m.Label.labelId!=labelId).count() > 0:
		raise ValueError, _('name \'{0}\' is already in use').format(name)


def check_label_extract_uniqueness(data, key, extract, labelSetId, labelId):
	if m.Label.query.filter_by(labelSetId=labelSetId
			).filter_by(extract=extract
			).filter(m.Label.labelId!=labelId).count() > 0:
		raise ValueError, _('extract \'{0}\' is already in use').format(extract)


def check_label_shortcut_key_non_space(data, key, shortcutKey):
	if shortcutKey == ' ':
		raise ValueError, _('shortcut key must not be space')


def check_label_shortcut_key_uniqueness(data, key, shortcutKey, labelSetId, labelId):
	if shortcutKey is not None:
		if m.Label.query.filter_by(labelSetId=labelSetId
				).filter_by(shortcutKey=shortcutKey
				).filter(m.Label.labelId!=labelId).count() > 0:
			raise ValueError, _('shortcut key \'{0}\' is already in use').format(shortcutKey)


def check_label_group_existence(data, key, labelGroupId, labelSetId):
	if labelGroupId is not None:
		g = m.LabelGroup.query.get(labelGroupId)
		if not g:
			raise ValueError, _('label group {0} not found').format(labelGroupId)
		if g.labelSetId != labelSetId:
				raise ValueError, _('label group {0} does not belong to label set {1}'
				).format(labelGroupId, labelSetId)


@bp.route(_name + '/<int:labelSetId>/labels/', methods=['POST'])
@api
@caps()
def create_label(labelSetId):
	'''
	creates a new label
	'''
	labelSet = m.LabelSet.query.get(labelSetId)
	if not labelSet:
		raise InvalidUsage(_('label set {0} not found').format(labelSetId), 404)

	data = MyForm(
		Field('name', is_mandatory=True, validators=[
			(check_label_name_uniqueness, (labelSetId, None)),
		]),
		Field('description'),
		Field('shortcutKey', validators=[
			(validators.is_string, (), dict(length=1)),
			check_label_shortcut_key_non_space,
			(check_label_shortcut_key_uniqueness, (labelSetId, None)),
		]),
		Field('extract', is_mandatory=True, validators=[
			validators.non_blank,
			(check_label_extract_uniqueness, (labelSetId, None)),
		]),
		Field('labelGroupId', validators=[
			(check_label_group_existence, (labelSetId,)),
		]),
	).get_data()

	label = m.Label(**data)
	SS.add(label)
	SS.flush()
	return jsonify({
		'message': _('created label {0} successfully').format(label.name),
		'label': m.Label.dump(label),
	})


@bp.route(_name + '/<int:labelSetId>/labels/<int:labelId>', methods=['PUT'])
@api
@caps()
def update_label(labelSetId, labelId):
	'''
	updates label settings
	'''
	labelSet = m.LabelSet.query.get(labelSetId)
	if not labelSet:
		raise InvalidUsage(_('label set {0} not found').format(labelSetId), 404)
	label = m.Label.query.get(labelId)
	if not label or label.labelSetId != labelSetId:
		raise InvalidUsage(_('label {0} not found').format(lableId), 404)

	data = MyForm(
		Field('name', validators=[
			(check_label_name_uniqueness, (labelSetId, labelId)),
		]),
		Field('description'),
		Field('shortcutKey', validators=[
			(validators.is_string, (), dict(length=1)),
			check_label_shortcut_key_non_space,
			(check_label_shortcut_key_uniqueness, (labelSetId, labelId)),
		]),
		Field('extract', validators=[
			validators.non_blank,
			(check_label_extract_uniqueness, (labelSetId, labelId)),
		]),
		Field('labelGroupId', validators=[
			(check_label_group_existence, (labelSetId,)),
		]),
	).get_data()
	# data['labelSetId'] = labelSetId

	for key in data.keys():
		value = data[key]
		if getattr(label, key) != value:
			setattr(label, key, value)
		else:
			del data[key]
	SS.flush()
	return jsonify({
		'message': _('updated label {0} successfully').format(labelId),
		'updatedFields': data.keys(),
		'label': m.Label.dump(label),
	})


def check_label_group_name_uniqueness(data, key, name, labelSetId, labelGroupId):
	if m.LabelGroup.query.filter_by(labelSetId=labelSetId
			).filter_by(name=name
			).filter(m.LabelGroup.labelGroupId!=labelGroupId).count() > 0:
		raise ValueError, _('name \'{0}\' is already in use').format(name)


@bp.route(_name + '/<int:labelSetId>/labelgroups/', methods=['POST'])
@api
@caps()
def create_label_group(labelSetId):
	'''
	creates a new label group
	'''
	labelSet = m.LabelSet.query.get(labelSetId)
	if not labelSet:
		raise InvalidUsage(_('label set {0} not found').format(labelSetId), 404)

	data = MyForm(
		Field('name', is_mandatory=True, validators=[
			validators.is_string,
			(check_label_group_name_uniqueness, (labelSetId, None)),
		]),
		Field('dropDownDisplay', default=False, validators=[
			validators.is_bool,
		]),
		Field('isMandatory', default=False, validators=[
			validators.is_bool,
		]),
	).get_data()
	labelGroup = m.LabelGroup(**data)
	SS.add(labelGroup)
	SS.flush()
	return jsonify({
		'message': _('created label group {0} successfully').format(labelGroup.name),
		'labelGroup': m.LabelGroup.dump(labelGroup),
	})


@bp.route(_name + '/<int:labelSetId>/labelgroups/<int:labelGroupId>', methods=['PUT'])
@api
@caps()
def update_label_group(labelSetId, labelGroupId):
	'''
	updates label group settings
	'''
	labelSet = m.LabelSet.query.get(labelSetId)
	if not labelSet:
		raise InvalidUsage(_('label set {0} not found').format(labelSetId), 404)
	labelGroup = m.LabelGroup.query.get(labelGroupId)
	if not labelGroup or labelGroup.labelSetId != labelSetId:
		raise InvalidUsage(_('label group {0} not found').format(labelGroupId), 404);

	data = MyForm(
		Field('name', is_mandatory=True, validators=[
			validators.is_string,
			(check_label_group_name_uniqueness, (labelSetId, None)),
		]),
		Field('dropDownDisplay', validators=[validators.is_bool,]),
		Field('isMandatory', validators=[validators.is_bool,]),
	).get_data()


	for key in data.keys():
		value = data[key]
		if getattr(labelGroup, key) != value:
			setattr(labelGroup, key, value)
		else:
			del data[key]
	SS.flush()
	return jsonify({
		'message': _('updated label group {0} successfully').format(labelGroup.name),
		'labelGroup': m.LabelGroup.dump(labelGroup),
	})


@bp.route(_name + '/<int:labelSetId>/labelgroups/<int:labelGroupId>', methods=['DELETE'])
@api
@caps()
def delete_label_group(labelSetId, labelGroupId):
	'''
	deletes specified label group
	'''
	labelGroup = m.LabelGroup.query.get(labelGroupId);
	if not labelGroup or labelGroup.labelSetId != labelSetId:
		raise InvalidUsage(_('label group {0} not found').format(labelGroupId), 404)

	for i in labelGroup.labels:
		i.labelGroup = None
	name = labelGroup.name
	SS().delete(labelGroup)
	return jsonify({
		'message': _('deleted label group {0} sucessfully').format(name),
	})

