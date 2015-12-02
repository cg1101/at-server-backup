
import types

from flask import request, abort, session, jsonify

import db.model as m
from db.db import SS
from app.api import api, caps, validate_input as v
from app.i18n import get_text as _

from . import api_1_0 as bp

_name = __file__.split('/')[-1].split('.')[0]

@bp.route(_name + '/', methods=['GET'])
@api
@caps()
def get_label_sets():
	'''
	returns a list of label sets
	'''
	labelSets = m.LabelSet.query.order_by(m.LabelSet.labelSetId).all()
	s = m.LabelSetSchema()
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
		abort(404)
	s = m.LabelSetSchema()
	return jsonify({
		'labelSet': m.LabelSet.dump(labelSet),
	})

def validate_label_name(data, key, value, labelSetId, labelId):
	if not isinstance(value, basestring):
		raise ValueError, _('expected {0}, got {1}').format(
			types.StringType.__name__, type(value).__name__)
	elif not value.strip():
		raise ValueError, _('parameter \'{0}\' must not be blank').format(key)
	if m.LabelGroup.query.filter_by(labelSetId=labelSetId
			).filter_by(name=value
			).filter(m.Label.labelId!=labelId).count() > 0:
		raise ValueError, _('{0} \'{1}\' is already in use').format(key, value)
	return value


def validate_label_extract(date, key, value, labelSet, labelId):
	if not isinstance(value, basestring):
		raise ValueError, _('expected {0}, got {1}').format(
			types.StringType.__name__, type(value).__name__)
	elif not value.strip():
		raise ValueError, _('parameter \'{0}\' must not be blank').format(key)
	if m.LabelGroup.query.filter_by(labelSetId=labelSetId
			).filter_by(name=value
			).filter(m.Label.labelId!=labelId).count() > 0:
		raise ValueError, _('{0} \'{1}\' is already in use').format(key, value)
	return value

def validate_label_shortcut_key():
	pass

def validate_label_extract():
	pass

def validate_label_group_id(labelSetId, labelGroupId):
	if labelId != None:
		labelGroup = m.LabelGroup.get(labelGroupId)
		if labelGroup.labelSetId != labelSetId:
			raise ValueError, _('label group {0} not found in label set {1}').format(labelGroupId, labelSetId)

@bp.route(_name + '/<int:labelSetId>/labels/', methods=['POST'])
@api
@caps()
def create_label(labelSetId):
	'''
	creates a new label
	'''
	labelSet = m.LabelSet.get(labelSetId)
	if not labelSet:
		abort(404)

	data = v([
		('name', True, None, validate_label_name, (labelSetId, None), ()),
		('description', False, None, None, (), ()),
		('shortcutKey', False, None, None, (), ()),
		('extract', True, None, validate_label_extract, (labelSetId, None), ()),
		('labelGroupId', True, None, validate_label_group_id, (labelSetId, None), ()),
	])
	label = m.Label(**data)
	SS.add(label)
	_label = m.Label.query.filter_by(
			labelSetId=labelSetId).filter_by(
			name=label.name).one()
	assert label is _label

	s = m.LabelSchema()
	return jsonify({
		'status': _('new label {0} successfully created').format(label.name),
		'label': m.Label.dump(label),
	})


@bp.route(_name + '/<int:labelSetId>/labels/<int:labelId>', methods=['PUT'])
@api
@caps()
def update_label(labelSetId, labelId):
	'''
	updates label settings
	'''
	return jsonify({
		'label': {},
	})


def validate_group_name(data, key, value, labelSetId, labelGroupId):
	import types
	if not isinstance(value, basestring):
		raise ValueError, _('expected {0}, got {1}').format(
			types.StringType.__name__, type(value).__name__)
	elif not value.strip():
		raise ValueError, _('parameter \'{0}\' must not be blank').format(key)
	if m.LabelGroup.query.filter_by(labelSetId=labelSetId
			).filter_by(name=value
			).filter(m.LabelGroup.labelGroupId!=labelGroupId).count() > 0:
		raise ValueError, _('{0} \'{1}\' is already in use').format(key, value)
	return value


@bp.route(_name + '/<int:labelSetId>/labelgroups/', methods=['POST'])
@api
@caps()
def create_label_group(labelSetId):
	'''
	creates a new label group
	'''
	labelSet = m.LabelSet.query.get(labelSetId)
	if not labelSet:
		abort(404)

	data = v([
		('name', True, None, validate_group_name, (labelSetId, None), ()),
		('dropDownDisplay', False, False, (True, False, None), (), ()),
		('isMandatory', False, False, (True, False, None), (), ()),
	])
	labelGroup = m.LabelGroup(labelSetId=labelSetId, **data)
	SS.add(labelGroup)
	_labelGroup = m.LabelGroup.query.filter_by(
			labelSetId=labelSetId).filter_by(
			name=labelGroup.name).one()
	assert labelGroup is _labelGroup
	return jsonify({
		'status': _('new label group {0} successfully created').format(labelGroup.name),
		'labelGroup': m.LabelGroup.dump(labelGroup),
	})


@bp.route(_name + '/<int:labelSetId>/labelgroups/<int:labelGroupId>', methods=['PUT'])
@api
@caps()
def update_label_group(labelSetId, labelGroupId):
	'''
	updates label group settings
	'''
	labelGroup = m.LabelGroup.query.get(labelGroupId)
	if not labelGroup or labelGroup.labelSetId != labelSetId:
		abort(404);

	data = v([
		('name', False, None, validate_group_name, (labelSetId, labelGroupId), ()),
		('dropDownDisplay', False, None, (True, False), (), ()),
		('isMandatory', False, None, (True, False), (), ()),
	])
	for k in data:
		if getattr(labelGroup, k) != data[k]:
			setattr(labelGroup, k, data[k]);

	s = m.LabelGroupSchema()
	return jsonify({
		'status': _('label group {0} was updated').format(labelGroup.name),
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
		abort(404);

	for i in labelGroup.labels:
		i.labelGroup = None
	name = labelGroup.name
	SS().delete(labelGroup)
	return jsonify({
		'status': _('label group {} has been deleted').format(name),
	})

