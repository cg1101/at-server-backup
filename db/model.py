#!/usr/bin/env python

import logging
import datetime
import json
import time
import re
import os

from functools import wraps
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import relationship, backref, synonym, deferred, column_property, object_session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import case, text, func
from sqlalchemy.types import Integer, String
from marshmallow import Schema, fields
import pytz

from LRUtilities.Audio import AudioDataPointer, AudioSpec
from LRUtilities.Misc import random_key_string, since_epoch
from LRUtilities.Serialization import DurationField
from . import database, mode
from .db import SS
from .db import database as db
from .errors import *
from lib import GetConstantsMixin, utcnow, validator
from lib.audio_load import validate_load_performance_data, validate_load_utterance_data
from lib.loaders import get_loader_metadata_sources
from lib.metadata_validation import MetaValidator, MetaValue, process_received_metadata, resolve_new_metadata
from schema import *

log = logging.getLogger(__name__)


# model mixin classes

class ModelMixin(GetConstantsMixin):

	@classmethod
	def check_exists(cls, data, key, value):
		"""
		MyForm validator to check that the model
		exists. The value is assumed to be the
		primary key.
		"""
		if not cls.query.get(value):
			raise ValueError("{0} {1} does not exist".format(key, value))

	@classmethod
	def check_all_exists(cls, data, key, value):
		"""
		MyForm validator to check that all models
		in a list exist. Each item in value is assumed
		to be a primary key.
		"""
		for pk in value:
			cls.check_exists(data, key, pk)

	@classmethod
	def check_new_field_unique(cls, field, **context):
		"""
		Returns a MyForm validator for checking that
		a new field value is unique within the given
		context.
		"""

		def validator(data, key, value):

			constraints = {field: value}
			constraints.update(context)
			query = cls.query.filter_by(**constraints)

			if query.count():
				raise ValueError("{0} is already used".format(value))

		return validator

	def check_updated_field_unique(self, field, **context):
		"""
		Returns a MyForm validator for checking that
		the field being updated is unique within the
		given context.
		"""

		def validator(data, key, value):

			# build filtered query
			constraints = {field: value}
			constraints.update(context)
			query = self.query.filter_by(**constraints)

			# add pk constraint
			primary_key = inspect(self.__class__).primary_key

			# TODO support composite keys
			if len(primary_key) > 1:
				raise NotImplementedError

			primary_key = primary_key[0]
			query = query.filter(primary_key!=getattr(self, primary_key.name))

			if query.count():
				raise ValueError("{0} is already used".format(value))

		return validator

	@classmethod
	def get_list(cls, *ids):
		"""
		Returns a list of models, one for each
		id provided.
		"""
		models = []

		for id in ids:
			models.append(cls.query.get(id))

		return models

	def serialize(self):
		"""
		Serializes the model.
		"""
		return self.dump(self)


class LoadMixin(object):
	"""
	Adds extra functionality for models created
	during audio loading.
	"""

	@classmethod
	def from_load(cls, data, *args, **kwargs):
		"""
		Parses the validated load data and returns
		the created model.
		"""
		raise NotImplementedError


class MetaCategoryMixin(object):
	"""
	Adds extra functionality for metadata categories.
	"""

	@property
	def meta_category_id(self):
		"""
		An alias for the category ID.
		"""
		raise NotImplementedError

	@property
	def validator(self):
		"""
		The MetaValidator object for the stored spec.
		"""
		return MetaValidator.get_validator(self.validator_spec)

	@staticmethod
	def check_validator(data, key, value):
		"""
		MyForm validator to check a meta validator.
		"""
		MetaValidator.get_validator(value)


class MetaEntityMixin(object):
	"""
	Adds extra functionality for models that store metadata.
	"""

	# the corresponding meta value model class
	MetaValueModel = None
	MetaCategoryModel = None

	@property
	def meta_values(self):
		"""
		An SQLAlchemy relationship to the meta values.
		"""
		raise NotImplementedError

	@property
	def task(self):
		"""
		An SQLAlchemy relationship to the associated task.
		"""
		raise NotImplementedError

	@property
	def meta_entity_id(self):
		"""
		Returns the 'entityId' to be stored
		in the metadata change log info field.
		"""
		raise NotImplementedError

	def add_meta_value(self, meta_category, new_value):
		"""
		Adds a new meta value.
		"""
		if self.MetaValueModel is None:
			raise RuntimeError("MetaValueModel not set")

		self.meta_values.append(self.MetaValueModel(
			meta_category=meta_category,
			value=new_value
		))

	# TODO require user and change method
	def add_meta_change_request(self, meta_category, new_value):
		"""
		Adds a new meta value change request.
		"""
		raise NotImplementedError

	@staticmethod
	def get_change_log_type(model):
		"""
		Returns the 'type' to be stored in
		the metadata change log info field.
		"""
		if isinstance(model, Performance):
			return "performance"

		raise RuntimeError("unknown meta entity model: {0}".format(model))

	def add_change_log_entry(self, meta_category, old_value, new_value, user, change_method_name):
		"""
		Adds a new change log entry.
		"""

		info = {
			"type": self.get_change_log_type(self),
			"entityId": self.meta_entity_id,
			"categoryId": meta_category.meta_category_id,
			"oldValue": old_value,
			"newValue": new_value,
		}

		entry = MetadataChangeLogEntry(
			task=self.task,
			info=info,
			changer=user,
			change_method=AudioCheckingChangeMethod.from_name(change_method_name),
		)
		db.session.add(entry)

	@property
	def metadata_change_log_entries(self):
		"""
		Returns the related change log entries.
		"""

		type = self.get_change_log_type(self)
		entity_id = self.meta_entity_id
		query = MetadataChangeLogEntry.query\
			.filter(MetadataChangeLogEntry.info["type"].cast(String)==type)\
			.filter(MetadataChangeLogEntry.info["entityId"].cast(Integer)==entity_id)

		return query.all()


class MetaValueMixin(object):
	"""
	Adds extra functionality for metadata values.
	"""

	@property
	def meta_entity(self):
		"""
		An SQLAlchemy relationship to the meta entity.
		"""
		raise NotImplementedError

	@property
	def meta_category(self):
		"""
		An SQLAlchemy relationship to the meta category.
		"""
		raise NotImplementedError


class AddFeedbackMixin(object):
	"""
	Adds extra functionality for models that
	have feedback entries.
	"""

	FeedbackEntryModel = None
	FlagModel = None
	SelfRelationshipName = None

	def add_feedback(self, user, change_method, comment=None, flags=[]):
		change_method = AudioCheckingChangeMethod.from_name(change_method)
		flags = self.FlagModel.get_list(*flags)

		kwargs = dict(
			user=user,
			change_method=change_method,
			comment=comment,
		)
		kwargs.update({
			self.SelfRelationshipName: self,
		})

		entry = self.FeedbackEntryModel(**kwargs)
		entry.add_flags(flags)
		return entry


class FeedbackEntryMixin(object):
	"""
	Adds extra functionality for models that
	are feedback entries.
	The EntryFlagModel must have a relationship
	to the Flag model named 'flag'.
	"""

	EntryFlagModel = None

	@property
	def flags(self):
		return [entry_flag.flag for entry_flag in self.entry_flags]

	def add_flags(self, flags):
		for flag in flags:
			self.entry_flags.append(self.EntryFlagModel(flag=flag))


class FeedbackFlagMixin(object):
	"""
	Adds extra functionality for feedback
	flag models.
	"""

	FlagIdAttr = None

	@property
	def flag_id(self):
		return getattr(self, self.FlagIdAttr)


class NamedTypeMixin(object):
	"""
	Adds extra functionality for named type
	models.
	"""

	@classmethod
	def is_valid(cls, name):
		try:
			cls.from_name(name)
		except NoResultFound:
			return False

		return True
	
	@classmethod
	def from_name(cls, name):
		return cls.query.filter_by(name=name).one()


def set_schema(cls, schema_class, schema_key=None):
	if not issubclass(schema_class, Schema):
		raise TypeError('schema must be subclass of Schema')
	registry = cls.__dict__.get('_schema_registry', None)
	if registry is None:
		cls._schema_registry = {}
	cls._schema_registry[schema_key] = schema_class


def dump(cls, obj, use=None, extra=None, only=(), exclude=(),
		prefix=u'', strict=False, context=None, load_only=(), **kwargs):
	try:
		schema_class = cls._schema_registry.get(use, None)
	except:
		schema_class = None
	if schema_class is None:
		raise RuntimeError('schema class not found for {0}: key {1}'\
			.format(cls.__name__, use))
	s = schema_class(extra=extra, only=only, exclude=exclude,
			prefix=prefix, strict=strict, context=context)
	if isinstance(obj, list):
		many = True
	else:
		many = False
	marshal_result = s.dump(obj, many=many, **kwargs)
	return marshal_result.data

if mode == 'app':
	Base = database.Model
else:
	class MyBase(object):
		pass
	Base = declarative_base(cls=MyBase, metadata=metadata)
	Base.query = SS.query_property()

Base.set_schema = classmethod(set_schema)
Base.dump = classmethod(dump)


_names = set(locals().keys()) | {'_names'}


#
# Define model class and its schema (if needed) below
#
##########################################################################


# PdbProject
class PdbProject(Base):
	__table__ = t_pdb_projects

class PdbProjectSchema(Schema):
	class Meta:
		fields = ('projectId', 'name')


# # PdbTask
class PdbTask(Base):
	__table__ = t_pdb_tasks

class PdbTaskSchema(Schema):
	class Meta:
		fields = ('taskId', 'name', 'workArea', 'projectId')


# WorkType
class WorkType(Base, ModelMixin, NamedTypeMixin):
	__table__ = t_worktypes

	WORK = 'Work'
	QA = 'QA'
	REWORK = 'Rework'
	SECOND_PASS_WORK = '2ndPass_work'
	SECOND_PASS_REWORK = '2ndPass_rework'
	TRANSCRIPTION_SOURCE = "Transcription Source"

	# synonyms
	modifies_transcription = synonym("modifiesTranscription")
	work_type_id = synonym("workTypeId")

class WorkTypeSchema(Schema):
	class Meta:
		fields = ('workTypeId', 'name', 'description', 'modifiesTranscription', "workable")


# Batch
class Batch(Base):
	__table__ = t_batches
	user = relationship('User', foreign_keys=[t_batches.c.userId])
	userName = association_proxy('user', 'userName')
	qaedUser = relationship('User', foreign_keys=[t_batches.c.notUserId])
	qaedUserName = association_proxy('qaedUser', 'userName')
	pages = relationship('Page', order_by='Page.pageIndex',
		cascade='all, delete-orphan')
	task = relationship('Task')
	subTask = relationship('SubTask', backref="batches")

	# synonyms
	batch_id = synonym("batchId")
	user_id = synonym("userId")
	sub_task = synonym("subTask")
	sub_task_id = synonym("subTaskId")

	@property
	def qaedInterval(self):
		if self.workIntervalId is None:
			return None
		return WorkInterval.query.get(self.workIntervalId)

	@property
	def isExpired(self):
		if self.leaseExpires is None:
			return False
		else:
			now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
			return self.leaseExpires <= now

	@property
	def isFinished(self):
		if self.userId is None:
			return False
		for page in self.pages:
			for member in page.members:
				if not member.saved:
					return False
		return True

	@property
	def unfinishedCount(self):
		if self.userId is None:
			return sum([len(page.members) for page in self.pages])
		count = 0
		for page in self.pages:
			for member in page.members:
				if not member.saved:
					count += 1
		return count

	@property
	def itemCount(self):
		return sum([len(p.members) for p in self.pages])

	@property
	def unitCount(self):
		if self.subTask.workType in (WorkType.WORK, WorkType.REWORK):
			r = SS.query(func.sum(RawPiece.words)
				).join(PageMember
				).filter(PageMember.rawPieceId==RawPiece.rawPieceId
				).filter(PageMember.batchId==self.batchId).first()
			unitCount = r[0]
		elif self.subTask.workType == WorkType.QA:
			r = SS.query(func.sum(RawPiece.words)
				).filter(RawPiece.rawPieceId.in_(
					SS.query(WorkEntry.rawPieceId
						).join(PageMember, PageMember.workEntryId==WorkEntry.entryId
						).filter(PageMember.batchId==self.batchId)
					)
				).first()
			unitCount = r[0]
		else:
			r = SS.query(func.sum(RawPiece.words)
				).join(PageMember
				).filter(PageMember.rawPieceId==RawPiece.rawPieceId
				).filter(PageMember.batchId==self.batchId).first()
			unitCount = r[0]
		try:
			assert isinstance(unitCount, (int, long))
		except:
			unitCount = 0
		return unitCount

	def log_event(self, event, operatorId=None):
		if operatorId is None:
			operatorId = self.userId
		SS.execute(t_batchhistory.insert(dict(
			batchId=self.batchId,
			userId=operatorId,
			event=event,
		)))

	def reset_ownership(self):
		self.userId = None
		self.leaseGranted = None
		self.leaseExpires = None
		self.checkedOut = False
		self.set_progress(None)

	def increase_priority(self, increase_by=1):
		self.priority += increase_by

	def revoke(self, revoked_by):
		self.log_event('revoked', revoked_by)
		self.reset_ownership()
		self.increase_priority()

	def abandon(self):
		self.log_event('abandoned')
		self.reset_ownership()
		self.increase_priority()

	def unassign(self):
		self.userId = None
		self.leaseGranted = None
		self.leaseExpires = None
		self.set_progress(None)

	def submit(self, user, data=None):
		self.log_event('submitted')

		# audio checking tasks
		if self.task.is_type(TaskType.AUDIO_CHECKING):
			assert len(self.pages) == 1
			assert len(self.pages[0].memberEntries) == 1
			performance = Performance.query.get(self.pages[0].memberEntries[0].rawPieceId)
			performance.isNew = False
			performance.move_to(data["destination"], AudioCheckingChangeMethod.WORK_PAGE, user.user_id)
			db.session.commit()

		# other task types
		else:
			rawPieceIds = []
			for p in self.pages:
			# 	for member in p.members:
			# 		SS.delete(member)
				for memberEntry in p.memberEntries:
					if memberEntry.rawPieceId:
						rawPieceIds.append(memberEntry.rawPieceId)
					SS.delete(memberEntry)
				SS.delete(p)
			SS.delete(self)
			for rawPieceId in rawPieceIds:
				rawPiece = RawPiece.query.get(rawPieceId)
				rawPiece.isNew = False
			SS.flush()

	def delete(self, force=False):
		
		if not force and self.task.is_type(TaskType.AUDIO_CHECKING):
			raise AudioCheckingBatch

		# TODO deleting the batch (with the cascades)
		# does not work - think its due to the PageMember
		# relationship, which is based on a view, not
		# a table. Ideally try to use the cascades
		for page in self.pages:

			for page_member in page.memberEntries:
				db.session.delete(page_member)
			
			db.session.delete(page)
		
		db.session.delete(self)

	def set_progress(self, progress):
		self.progress = progress
		flag_modified(self, "progress")


class BatchSchema(Schema):
	user = fields.Method('get_user')
	def get_user(self, obj):
		s = UserSchema(only=['userId', 'userName'])
		return s.dump(obj.user).data if obj.user else None
	pages = fields.Method('get_pages')
	def get_pages(self, obj):
		s = PageSchema(context={'full': True})
		return s.dump(obj.pages, many=True).data
	name = fields.Method('get_name')
	def get_name(self, obj):
		return obj.name if obj.name is not None else 'b-%s' % obj.batchId
	qaedInterval = fields.Nested('WorkIntervalSchema')
	def get_work_type(self, obj):
		return obj.subTask.workType

	def get_info(self, obj):
		info = {}

		if obj.task.is_type(TaskType.AUDIO_CHECKING):
			page_member = obj.pages[0].members[0]
			performance = Performance.query.get(page_member.raw_piece_id)
			performance_name = performance.name or "Performance {0}".format(page_member.raw_piece_id)
			info.update({
				"rawPieceId": page_member.raw_piece_id,
				"performanceName": performance_name,
			})

		return info

	info = fields.Method("get_info")

	class Meta:
		fields = ('batchId', 'taskId', 'subTaskId', 'userId', 'userName',
			'user', 'priority', 'onHold', 'leaseGranted', 'leaseExpires',
			'notUserId', 'qaedUserName', 'workIntervalId',
			'qaedInterval', 'checkedOut', 'name', 'itemCount',
			'unitCount', "info", "progress")
		# ordered = True

class Batch_FullSchema(BatchSchema):
	def get_pages(self, obj):
		s = PageSchema(context={'full': True})
		return s.dump(obj.pages, many=True).data
	class Meta:
		fields = ('batchId', 'taskId', 'subTaskId', 'userId', 'userName', 'user',
			'priority', 'onHold', 'leaseGranted', 'leaseExpires', 'notUserId',
			'workIntervalId', 'checkedOut', 'name', 'itemCount', 'unitCount', 'pages',
			"info", "progress")

class Batch_BriefSchema(Schema):
	priority = fields.Integer()
	onHold = fields.Boolean()
	leaseExpires = fields.DateTime()
	class Meta:
		fields = ('batchId', 'priority', 'onHold', 'leaseExpires')


# BathchingMode
class BatchingMode(Base, ModelMixin):
	__table__ = t_batchingmodes

	# constants
	NONE = 'None'
	PERFORMANCE = 'Performance'
	FILE = 'File'
	CUSTOM_CONTEXT = 'Custom Context'
	ALLOCATION_CONTEXT = 'Allocation Context'
	FOLDER = "Folder"

	# synonyms
	requires_context = synonym("requiresContext")

class BatchingModeSchema(Schema):
	class Meta:
		fields = ('modeId', 'name', 'description', 'requiresContext')
		ordered = True

# CalculatedPayment
class CalculatedPayment(Base):
	__table__ = t_calculatedpayments
	user = relationship('User')
	userName = association_proxy('user', 'userName')
	subTask = relationship('SubTask')
	workInterval = relationship('WorkInterval')

class CalculatedPaymentSchema(Schema):
	class Meta:
		fields = ('calculatedPaymentId', 'payrollId', 'workIntervalId', 'userId', 'userName', 'taskId', 'subTaskId', 'itemCount', 'unitCount', 'qaedItemCount', 'qaedUnitCount', 'accuracy', 'originalAmount', 'amount', 'receipt', 'updated')
		ordered = True
		# skip_missing = True

class CalculatedPayment_PostageSchema(Schema):
	calculatedPaymentId = fields.Integer(dump_to='identifier')
	amount = fields.Integer()
	userId = fields.Integer(dump_to='userid')
	taskId = fields.Integer(dump_to='taskid')
	units = fields.Method('get_units')
	weekending = fields.Method('get_week_ending')
	details = fields.Method('get_details')
	targetrate = fields.Method('get_target_rate')
	accuracy = fields.Float()
	unitname = fields.Method('get_unit_name')
	def get_units(self, obj):
		return obj.unitCount if obj.subTask.payByUnit else obj.itemCount
	def get_week_ending(self, obj):
		return obj.workInterval.endTime.strftime('%Y-%m-%d')
	def get_details(self, obj):
		s = obj.subTask
		return 'GNX {} - {} ({})'.format(s.taskId, s.name, s.workType)
	def get_target_rate(self, obj):
		r = obj.subTask.currentRate
		return r.standardValue * r.multiplier
	def get_unit_name(self, obj):
		return 'units' if obj.subTask.payByUnit else 'items'

# CustomUtteranceGroup
class CustomUtteranceGroup(Base):
	__table__ = t_customutterancegroups
	_members = relationship('CustomUtteranceGroupMember', cascade='all, delete-orphan')
	rawPieces = association_proxy('_members', 'rawPiece')
	selection = relationship('UtteranceSelection')

class CustomUtteranceGroupSchema(Schema):
	rawPieces = fields.Nested('RawPieceSchema', many=True)
	selection = fields.Nested('UtteranceSelectionSchema')
	class Meta:
		fields = ('groupId', 'name', 'taskId', 'created', 'utterances', 'selectionId', 'selection')
		ordered = True

# CustomUtteranceGroupMember
class CustomUtteranceGroupMember(Base):
	__table__ = t_customutterancegroupmembers
	rawPiece = relationship('RawPiece', uselist=False)

class CustomUtteranceGroupMemberSchema(Schema):
	class Meta:
		fields = ('groupId', 'rawPieceId')

# DailySubtotal
class DailySubtotal(Base):
	__table__ = t_dailysubtasktotals
	date = synonym('totalDate')
	items = synonym('amount')
	units = synonym('words')
	user = relationship('User')
	userName = association_proxy('user', 'userName')

class DailySubtotalSchema(Schema):
	class Meta:
		fields = ('totalId', 'date', 'subTaskId', 'userId', 'userName', 'items', 'units')
		ordered = True

# ErrorClass
class ErrorClass(Base):
	__table__ = t_errorclasses

class ErrorClassSchema(Schema):
	class Meta:
		fields = ('errorClassId', 'name')

# ErrorType
class ErrorType(Base):
	__table__ = t_errortypes
	_errorClass = relationship('ErrorClass')
	errorClass = association_proxy('_errorClass', 'name')

class ErrorTypeSchema(Schema):
	class Meta:
		fields = ('errorTypeId', 'name', 'errorClassId', 'errorClass', 'defaultSeverity', 'isStandard')

# FileHandlerOption
class FileHandlerOption(Base):
	__table__ = t_filehandleroptions
	handler = relationship('FileHandler')

class FileHandlerOptionSchema(Schema):
	class Meta:
		fields = ('optionId', 'name', 'label', 'handlerId', 'dataType', 'widgetType', 'params')

# FileHandler
class FileHandler(Base):
	__table__ = t_filehandlers
	options = relationship('FileHandlerOption', order_by='FileHandlerOption.optionId')

class FileHandlerSchema(Schema):
	options = fields.Nested(FileHandlerOptionSchema, many=True)
	class Meta:
		fields = ('handlerId', 'name', 'description', 'options')

# Job
class Job(Base):
	__table__ = t_jobs

class JobSchema(Schema):
	class Meta:
		fields = ('jobId', 'added', 'started', 'completed', 'failed', 'isNew', 'name', 'pid')
		ordered = True
		# skip_missing = True

# Label
class Label(Base):
	__table__ = t_labels
	labelSet = relationship('LabelSet')
	labelGroup = relationship('LabelGroup')

class LabelSchema(Schema):
	class Meta:
		fields = ('labelId', 'name', 'description', 'shortcutKey', 'extract', 'labelGroupId', 'labelSetId', 'enabled')
		# skip_missing = True

# LabelGroup
class LabelGroup(Base):
	__table__ = t_labelgroups
	labelSet = relationship('LabelSet')
	labels = relationship('Label')

class LabelGroupSchema(Schema):
	labels = fields.Nested('LabelSchema', many=True)
	class Meta:
		additional = ('labelGroupId', 'name', 'isMandatory', 'labelSetId', 'dropDownDisplay')

# LabelSet
class LabelSet(Base):
	__table__ = t_labelsets
	labelGroups = relationship('LabelGroup', order_by='LabelGroup.labelGroupId')
	ungroupedLabels = relationship('Label', primaryjoin='and_(LabelSet.labelSetId == Label.labelSetId, Label.labelGroupId == None)')

class LabelSetSchema(Schema):
	labelGroups = fields.Nested('LabelGroupSchema', many=True)
	ungroupedLabels = fields.Nested('LabelSchema', many=True)
	class Meta:
		additional = ('labelSetId', 'created')

class LabelSet_SmartSchema(Schema):
	subTaskId = fields.Method('get_sub_task_id')
	def get_sub_task_id(self, obj):
		try:
			context = self.context
			if context is None or not isinstance(context, dict):
				raise ValueError
			subTaskId = context['subTaskId']
		except (ValueError, KeyError):
			raise RuntimeError('must provide sub task id in context')
		return subTaskId
	def get_shadowed_ids(self, obj):
		subTaskId = self.get_sub_task_id(obj)
		shadowed = set([i.labelId for i in SS.query(ShadowedLabel.labelId
			).filter(ShadowedLabel.subTaskId==subTaskId).all()])
		return shadowed
	labelGroups = fields.Method('get_label_groups')
	def get_label_groups(self, obj):
		shadowed = self.get_shadowed_ids(obj)
		data = []
		s = LabelGroupSchema()
		for labelGroup in obj.labelGroups:
			group_data = s.dump(labelGroup).data
			checked = []
			for label_data in group_data['labels']:
				if label_data['labelId'] not in shadowed:
					checked.append(label_data)
			if checked:
				group_data['labels'] = checked
				data.append(group_data)
		return data
	ungroupedLabels = fields.Method('get_ungrouped_labels')
	def get_ungrouped_labels(self, obj):
		shadowed = self.get_shadowed_ids(obj)
		data = []
		s = LabelSchema()
		for label in obj.ungroupedLabels:
			if label.labelId not in shadowed:
				data.append(s.dump(label).data)
		return data
	class Meta:
		additional = ('labelSetId', 'created')


# Load
class Load(Base):
	__table__ = t_loads

	# relationships
	rawPieces = relationship('RawPiece', order_by='RawPiece.rawPieceId', viewonly=True, backref="load")
	_createdByUser = relationship('User')
	task = relationship("Task")

	# synonyms
	raw_pieces = synonym("rawPieces")
	load_id = synonym("loadId")
	created_by = synonym("createdBy")

	@property
	def itemCount(self):
		return len(self.rawPieces)

	@property
	def unitCount(self):
		return sum([i.words for i in self.rawPieces])


class LoadSchema(Schema):
	createdBy = fields.Method('get_created_by')
	def get_created_by(self, obj):
		s = UserSchema(only=['userId', 'userName'])
		return s.dump(obj._createdByUser).data
	class Meta:
		fields = ('loadId', 'createdBy', 'createdAt', 'taskId')

class Load_FullSchema(LoadSchema):
	class Meta:
		fields = ('loadId', 'createdBy', 'createdAt', 'taskId', 'unitCount', 'itemCount')

# KeyExpansion
class KeyExpansion(Base):
	__table__ = t_task_key_expansions

class KeyExpansionSchema(Schema):
	key = synonym('char')
	class Meta:
		fields = ('expansionId', 'taskId', 'char', 'text')

# OtherPayment
class OtherPayment(Base):
	__table__ = t_otherpayments

class OtherPaymentSchema(Schema):
	class Meta:
		fields = ('otherPaymentId', 'payrollId', 'identifier', 'paymentTypeId',
			'taskId', 'userId', 'amount', 'added')

# Page
class Page(Base):
	__table__ = t_pages
	members = relationship('PageMember',
		primaryjoin='Page.pageId == PageMember.pageId', order_by='PageMember.memberIndex',
		cascade='all, delete-orphan',
		)
	memberEntries = relationship('PageMemberEntry', cascade='all, delete-orphan')

class PageSchema(Schema):
	members = fields.Method('get_members')
	def get_members(self, obj):
		try:
			full = self.context['full']
		except:
			full = False
		_sd = {
			WorkType.WORK: WorkTypePageMemberSchema,
			WorkType.QA: QaTypePageMemberSchema,
			WorkType.REWORK: ReworkTypePageMemberSchema,
		}
		result = []
		if obj.members:
			klass = _sd[obj.members[0].workType]
			if full:
				s = klass()
			else:
				s = klass(only=['pageId', 'memberIndex', 'rawPieceId', 'workEntryId'])
			for m in obj.members:
				result.append(s.dump(m).data)
		return result
	class Meta:
		fields = ('pageId', 'batchId', 'pageIndex', 'members')
		ordered = True

# PageMemberEntry
class PageMemberEntry(Base):
	__table__ = t_pagemembers
	__mapper_args__ = {
		'confirm_deleted_rows': False,
	}

class PageMemberEntrySchema(Schema):
	class Meta:
		fields = ('pageId', 'memberIndex', 'rawPieceId', 'workEntryId')

# PageMember
class PageMember(Base):
	__table__ = j_pagemembers
	__mapper_args__ = {
		'polymorphic_on': j_pagemembers.c.workType,
		'polymorphic_identity': 'generic',
	}

	# synonyms
	raw_piece_id = synonym("rawPieceId")

	# relationships
	batch = relationship('Batch', primaryjoin='PageMember.batchId==Batch.batchId', foreign_keys='Batch.batchId', uselist=False)
	sub_task = relationship("SubTask", primaryjoin="PageMember.subTaskId==SubTask.subTaskId", foreign_keys="SubTask.subTaskId", uselist=False)

class PageMemberSchema(Schema):
	pageId = fields.Integer()
	memberIndex = fields.Integer()
	class Meta:
		ordered = True
		# skip_missing = True

class WorkTypePageMember(PageMember):
	__mapper_args__ = {
		'polymorphic_identity': WorkType.WORK,
	}
	rawPiece = relationship('RawPiece')

	def _get_saved(self):
		if self.userId == None:
			return None
		rs = object_session(self).query(WorkEntry
			).filter((WorkEntry.batchId==self.batchId) & (WorkEntry.userId==self.userId) & (WorkEntry.rawPieceId==self.rawPieceId)
			).order_by(WorkEntry.rawPieceId).order_by(WorkEntry.created.desc()
			).distinct(WorkEntry.rawPieceId).all()
		if len(rs) == 0:
			return None
		elif len(rs) == 1:
			return rs[0]
		return None
	saved = property(_get_saved)

class WorkTypePageMemberSchema(PageMemberSchema):
	rawPiece = fields.Nested('RawPieceSchema', only=['rawPieceId', 'rawText', 'hypothesis', 'words', "extra"])
	saved = fields.Method('get_saved')
	def get_saved(self, obj):
		if obj.saved == None:
			return None
		assert obj.saved.workType == WorkType.WORK
		_sd = {
			WorkType.WORK: WorkTypeEntrySchema(exclude=['taskId', 'subTaskId', 'workTypeId', 'workType', 'notes']),
			WorkType.QA: QaTypeEntrySchema(),
			WorkType.REWORK: ReworkTypeEntrySchema(),
		}
		s = _sd[obj.saved.workType]
		return s.dump(obj.saved).data
	class Meta:
		additional = ('rawPiece', 'saved')
		ordered = True
		# skip_missing = True

class QaTypePageMember(PageMember):
	__mapper_args__ = {
		'polymorphic_identity': WorkType.QA,
	}
	rawPiece = relationship('RawPiece',
		secondary='join(WorkEntry, RawPiece, WorkEntry.rawPieceId == RawPiece.rawPieceId)',
		primaryjoin='and_(QaTypePageMember.workEntryId == WorkEntry.entryId, WorkEntry.rawPieceId == RawPiece.rawPieceId)',
		secondaryjoin='WorkEntry.rawPieceId == RawPiece.rawPieceId',
		uselist=False,
	)
	qaedEntry = relationship('WorkEntry',
		primaryjoin='QaTypePageMember.workEntryId == WorkEntry.entryId',
	)
	def _get_saved(self):
		if self.userId == None:
			return None
		rs = object_session(self).query(WorkEntry
			).filter((WorkEntry.batchId==self.batchId) & (WorkEntry.userId==self.userId) & (WorkEntry.qaedEntryId==self.workEntryId)
			).order_by(WorkEntry.qaedEntryId).order_by(WorkEntry.created.desc()
			).distinct(WorkEntry.qaedEntryId).all()
		if len(rs) == 0:
			return None
		elif len(rs) == 1:
			return rs[0]
		return None
	def _get_look_ahead(self):
		s = self.batch.subTask
		rs = []
		if s.lookAhead > 0:
			rs = RawPiece.query.filter(
				(RawPiece.taskId==s.taskId) &
				(RawPiece.allocationContext==self.rawPiece.allocationContext) &
				(RawPiece.rawPieceId > self.rawPiece.rawPieceId)
			).order_by(RawPiece.rawPieceId).all()[:s.lookAhead]
		return rs
	def _get_look_behind(self):
		s = self.batch.subTask
		rs = []
		if s.lookBehind > 0:
			rs = RawPiece.query.filter(
				(RawPiece.taskId==s.taskId) &
				(RawPiece.allocationContext==self.rawPiece.allocationContext) &
				(RawPiece.rawPieceId < self.rawPiece.rawPieceId)
			).order_by(RawPiece.rawPieceId.desc()).all()[:s.lookBehind]
		return reversed(rs)
	saved = property(_get_saved)
	lookAhead = property(_get_look_ahead)
	lookBehind = property(_get_look_behind)

class QaTypePageMemberSchema(PageMemberSchema):
	rawPiece = fields.Nested('RawPieceSchema', only=['rawPieceId', 'rawText', 'hypothesis', 'words', "extra"])
	qaedEntry = fields.Method('get_qaed_entry')
	saved = fields.Method('get_saved')
	lookAhead = fields.Nested('RawPieceSchema', many=True, only=['rawPieceId', 'rawText'])
	lookBehind = fields.Nested('RawPieceSchema', many=True, only=['rawPieceId', 'rawText'])
	def get_qaed_entry(self, obj):
		s = WorkEntrySchema()
		if obj.qaedEntry.workType == WorkType.WORK:
			s = WorkTypeEntrySchema()
		elif obj.qaedEntry.workType == WorkType.REWORK:
			s = ReworkTypeEntrySchema()
		return s.dump(obj.qaedEntry).data
	def get_saved(self, obj):
		if obj.saved == None:
			return None
		assert obj.saved.workType == WorkType.QA
		_sd = {
			WorkType.WORK: WorkTypeEntrySchema(),
			WorkType.QA: QaTypeEntrySchema(exclude=['taskId', 'subTaskId', 'workTypeId', 'workType', 'notes']),
			WorkType.REWORK: ReworkTypeEntrySchema(),
		}
		s = _sd[obj.saved.workType]
		return s.dump(obj.saved).data
	class Meta:
		additional = ('rawPiece', 'qaedEntry', 'saved', 'lookAhead', 'lookBehind')
		ordered = True
		# skip_missing = True

class ReworkTypePageMember(PageMember):
	__mapper_args__ = {
		'polymorphic_identity': WorkType.REWORK,
	}
	rawPiece = relationship('RawPiece')
	def _get_latest_edition(self):
		rs = object_session(self).query(WorkEntry
			).filter((WorkEntry.rawPieceId==self.rawPieceId) & WorkEntry.modifiesTranscription & (WorkEntry.batchId!=self.batchId)
			).order_by(WorkEntry.rawPieceId).order_by(WorkEntry.created.desc()
			).distinct(WorkEntry.rawPieceId).all()
		if len(rs) == 0:
			return None
		elif len(rs) == 1:
			return rs[0]
		return None
	def _get_saved(self):
		if self.userId == None:
			return None
		rs = object_session(self).query(WorkEntry
			).filter((WorkEntry.batchId==self.batchId) & (WorkEntry.userId==self.userId) & (WorkEntry.rawPieceId==self.rawPieceId)
			).order_by(WorkEntry.rawPieceId).order_by(WorkEntry.created.desc()
			).distinct(WorkEntry.rawPieceId).all()
		if len(rs) == 0:
			return None
		elif len(rs) == 1:
			return rs[0]
		return None
	def _get_qa(self):
		if self.latestEdition is None:
			return None
		rs = object_session(self).query(WorkEntry
			).filter(WorkEntry.qaedEntryId==self.latestEdition.entryId
			).order_by(WorkEntry.qaedEntryId, WorkEntry.created.desc()
			).distinct(WorkEntry.qaedEntryId).all()
		if len(rs) == 0:
			return None
		elif len(rs) == 1:
			return rs[0]
		return None
	latestEdition = property(_get_latest_edition)
	saved = property(_get_saved)
	qa = property(_get_qa)

class ReworkTypePageMemberSchema(PageMemberSchema):
	rawPiece = fields.Nested('RawPieceSchema', only=['rawPieceId', 'rawText', 'hypothesis', 'words', "extra"])
	saved = fields.Method('get_saved')
	qa = fields.Method('get_qa')
	latestEdition = fields.Method('get_latest_edition')
	def get_saved(self, obj):
		if obj.saved == None:
			return None
		assert obj.saved.workType == WorkType.REWORK, obj.saved
		_sd = {
			WorkType.WORK: WorkTypeEntrySchema(),
			WorkType.QA: QaTypeEntrySchema(),
			WorkType.REWORK: ReworkTypeEntrySchema(exclude=['taskId', 'subTaskId', 'workTypeId', 'workType', 'notes']),
		}
		s = _sd[obj.saved.workType]
		return s.dump(obj.saved).data
	def get_latest_edition(self, obj):
		if obj.latestEdition == None:
			return None
		_sd = {
			WorkType.WORK: WorkTypeEntrySchema(exclude=['taskId', 'subTaskId', 'workTypeId', 'workType', 'notes']),
			WorkType.QA: QaTypeEntrySchema(),
			WorkType.REWORK: ReworkTypeEntrySchema(exclude=['taskId', 'subTaskId', 'workTypeId', 'workType', 'notes']),
		}
		s = _sd[obj.latestEdition.workType]
		return s.dump(obj.latestEdition).data
	def get_qa(self, obj):
		if obj.qa == None:
			return None
		_sd = {
			WorkType.WORK: WorkTypeEntrySchema(exclude=['taskId', 'subTaskId', 'workTypeId', 'workType', 'notes']),
			WorkType.QA: QaTypeEntrySchema(),
			WorkType.REWORK: ReworkTypeEntrySchema(exclude=['taskId', 'subTaskId', 'workTypeId', 'workType', 'notes']),
		}
		s = _sd[obj.qa.workType]
		return s.dump(obj.qa).data
	class Meta:
		additional = ('rawPiece', 'latestEdition', 'saved', 'qa')
		ordered = True
		# skip_missing = True

class TranscriptionSourceTypePageMember(ReworkTypePageMember):
	__mapper_args__ = {
		'polymorphic_identity': WorkType.TRANSCRIPTION_SOURCE,
	}

class TranscriptionSourceTypePageMemberSchema(ReworkTypePageMemberSchema):
	pass

# # PaymentClass

# PaymentType
class PaymentType(Base):
	__table__ = t_ao_payment_types

class PaymentTypeSchema(Schema):
	class Meta:
		fields = ('paymentTypeId', 'name', 'created')

# Payroll
class BasicPayroll(Base):
	__table__ = t_payrolls

class Payroll(Base):
	__table__ = j_payrolls
	payrollId = column_property(t_payrolls.c.payrollId, t_ao_payrolls.c.payrollId)


class PayrollSchema(Schema):
	class Meta:
		fields = ('payrollId', 'updatedAt', 'startDate', 'endDate')

# PayableEvent
class PayableEvent(Base):
	__table__ = t_payableevents

class PayableEventSchema(Schema):
	class Meta:
		fields = ('eventId', 'userId', 'taskId', 'subTaskId', 'batchId', 'pageId',
			'rawPieceId', 'workEntryId', 'created', 'localConnection', 'ipAddress',
			'calculatedPaymentId', 'ratio')

# Project
class Project(Base):
	__table__ = t_projects
	_migratedByUser = relationship('User')

class ProjectSchema(Schema):
	migratedBy = fields.Method('get_migrated_by')
	def get_migrated_by(self, obj):
		s = UserSchema(only=['userId', 'userName'])
		return s.dump(obj._migratedByUser).data
	class Meta:
		fields = ('projectId', 'name', 'description', 'created', 'migratedBy')
		ordered = True

# QaConfig
class QaConfig(Base):
	__table__ = t_defaultqaconfiguration

class QaConfigSchema(Schema):
	class Meta:
		fields = ('workSubTaskId', 'qaSubTaskId',
			'samplingError', 'defaultExpectedAccuracy', 'confidenceInterval',
			'populateRework', 'reworkSubTaskId', 'accuracyThreshold', 'updatedBy')
		ordered = True

# Pool
class Pool(Base):
	__table__ = t_pools
	tagSet = relationship('TagSet')
	_taskType = relationship('TaskType')
	taskType = association_proxy('_taskType', 'name')
	questions = relationship('Question', order_by='Question.questionId')

class PoolSchema(Schema):
	tagSet = fields.Method('get_tag_set')
	def get_tag_set(self, obj):
		if isinstance(obj.tagSet, TagSet):
			s = TagSetSchema()
			return s.dump(obj.tagSet).data
		elif obj.tagSet == None:
			return None
		raise ValueError, 'invalid tagSet value'
	questions = fields.Nested('QuestionSchema', many=True)
	class Meta:
		fields = ('poolId', 'name', 'meta', 'taskTypeId', 'taskType', 'tagSet', 'autoScoring', 'questions')

# Question
class Question(Base):
	__table__ = t_questions

class SmartField(fields.Field):
	def _serialize(self, value, attr, obj):
		my_level = self.metadata.get('level', 0)
		current_level = self.context.get('level', 0)
		if current_level >= my_level:
			return value
		return None

class QuestionSchema(Schema):
	type = SmartField(level=1)
	poolId = SmartField(level=1)
	respondentData = SmartField(level=1)
	scorerData = SmartField(level=2)
	autoScoring = SmartField(level=2)
	point = SmartField(level=2)
	class Meta:
		fields = ('questionId', 'type', 'poolId', 'respondentData', 'scorerData', 'autoScoring', 'point')
		ordered = True
		# skip_missing = True

# Test
class Test(Base):
	__table__ = t_tests
	_taskType = relationship('TaskType')
	taskType = association_proxy('_taskType', 'name')
	tagSet = relationship('TagSet')

class TestSchema(Schema):
	passingScore = fields.Decimal(as_string=True)
	tagSet = fields.Nested('TagSetSchema')
	class Meta:
		fields = ('testId', 'name', 'description', 'testType',
			'taskTypeId', 'taskType', 'timeLimit', 'passingScore',
			'instructionPage', 'requirement', 'poolId', 'isEnabled',
			'size', 'messageSuccess', 'messageFailure')
		ordered = True
		# skip_missing = True

# Sheet
class Sheet(Base):
	__table__ = t_answer_sheets
	STATUS_FINISHED = 'finished'
	STATUS_EXPIRED = 'expired'
	STATUS_SHOULD_EXPIRE = 'should_expire'
	STATUS_ACTIVE = 'active'
	user = relationship('User', primaryjoin='Sheet.userId==User.userId',
			foreign_keys=[t_answer_sheets.c.userId])
	test = relationship('Test')
	shouldExpire = column_property(t_answer_sheets.c.tExpiresBy <= text('now()'))
	entries = relationship('SheetEntry', order_by='SheetEntry.index')
	@hybrid_property
	def status(self):
		if self.tFinishedAt != None:
			return self.STATUS_FINISHED
		elif self.tExpiredAt != None:
			return self.STATUS_EXPIRED
		elif self.shouldExpire:
			return self.STATUS_SHOULD_EXPIRE
		else:
			return self.STATUS_ACTIVE
	@status.expression
	def status(klass):
		return case(
			[(klass.tFinishedAt != None, 'finished'),],
			else_=case(
				[(klass.tExpiredAt != None, 'expired'),],
				else_=case(
					[(klass.shouldExpire, 'should_expire'),],
					else_='active'
				)
			)
		)


class SheetSchema(Schema):
	user = fields.Method('get_user')
	entries = fields.Nested('SheetEntrySchema', many=True)
	tStartedAt = fields.DateTime()
	tExpiresBy = fields.DateTime()
	tExpiredAt = fields.DateTime()
	tFinishedAt = fields.DateTime()
	def get_user(self, obj):
		s = UserSchema(only=['userId', 'userName'])
		return s.dump(obj.user).data
	class Meta:
		fields = ('sheetId', 'testId', 'user', 'nTimes', 'status',
			'tStartedAt', 'tExpiresBy', 'tExpiredAt', 'tFinishedAt',
			'score', 'comment', 'moreAttempts', 'entries')
		ordered = True


class SheetEntry(Base):
	__table__ = t_sheet_entries
	question = relationship('Question')


class SheetEntrySchema(Schema):
	question = fields.Nested('QuestionSchema')
	class Meta:
		fields = ('sheetEntryId', 'sheetId', 'index', 'question')


# Answer
class Answer(Base):
	__table__ = t_answers


class AnswerSchema(Schema):
	class Meta:
		fields = ('answerId', 'sheetEntryId', 'tCreatedAt', 'answer')
		ordered = True


# Marking
class Marking(Base):
	__table__ = t_markings
	scorer = relationship('User')


class MarkingSchema(Schema):
	scorer = fields.Method('get_scorer')
	def get_scorer(self, obj):
		s = UserSchema(only=['userId', 'userName'])
		return s.dump(obj.scorer).data
	class Meta:
		fields = ('markingId', 'sheetEntryId', 'scorer', 'score', 'comment', 'tCreatedAt')
		ordered = True
		# skip_missing = True


# Rate
class Rate(Base):
	__table__ = t_rates
	points = relationship('RatePoint', order_by='RatePoint.accuracy')

class RateSchema(Schema):
	details = fields.Method('get_details')
	def get_details(self, obj):
		details = sorted([(p.accuracy, p.value) for p in obj.points])
		if details:
			la, lv = details[0]
			if la > 0:
				details.insert(0, (0.0, lv))
		details.append((1.0, obj.maxValue))
		return details
	class Meta:
		additional = ('rateId', 'name', 'standardValue', 'maxValue', 'targetAccuracy')

# RatePoint
class RatePoint(Base):
	__table__ = t_ratedetails

class RatePointSchema(Schema):
	class Meta:
		fields = ('value', 'accuracy')

# RawPiece
class RawPiece(Base, ModelMixin):
	__table__ = t_rawpieces

	# relationships
	task = relationship("Task")

	# synonyms
	assembly_context = synonym("assemblyContext")
	load_id = synonym("loadId")

	__mapper_args__ = {
		"polymorphic_identity": None,
		"polymorphic_on": t_rawpieces.c.type
	}

class RawPieceSchema(Schema):
	extra = fields.Method("get_extra")

	def get_extra(self, obj):
		extra = {}
		if obj.task.task_type == TaskType.TRANSCRIPTION:
			extra.update({"audioUrl": obj.audio_url})

		return extra


	class Meta:
		additional = ('rawPieceId', 'taskId', 'rawText', 'assemblyContext', 'allocationContext', 'hypothesis', 'words', "extra")
		ordered = True



# SelectionCacheEntry
class SelectionCacheEntry(Base):
	__table__ = t_utteranceselectioncache

class SelectionCacheEntrySchema(Schema):
	class Meta:
		fields = ('selectionId', 'rawPieceId')

# SelectionFilter
class SelectionFilter(Base):
	__table__ = t_utteranceselectionfilters
	pieces = relationship('SelectionFilterPiece',
		order_by='SelectionFilterPiece.index',
		cascade='all, delete-orphan')

class SelectionFilterSchema(Schema):
	pieces = fields.Nested('SelectionFilterPieceSchema', many=True)
	class Meta:
		fields = ('filterId', 'selectionId', 'filterType', 'description', 'isInclusive', 'isMandatory', 'pieces')
		ordered = True

class SelectionFilterPiece(Base):
	__table__ = t_utteranceselectionfilterpieces

class SelectionFilterPieceSchema(Schema):
	class Meta:
		fields = ('index', 'data')
		ordered = True

# ShadowedLabel
class ShadowedLabel(Base):
	__table__ = t_shadowed_labels

# ShadowedTag
class ShadowedTag(Base):
	__table__ = t_shadowed_tags

# SubTask
class SubTask(Base, ModelMixin):
	POLICY_NO_LIMIT = 'nolimit'
	POLICY_ONE_ONLY = 'oneonly'

	__table__ = t_subtasks

	taskTypeId = association_proxy('task', 'taskTypeId')
	taskType = association_proxy('task', 'taskType')
	batchingMode = association_proxy('_batchingMode', 'name')
	workType = association_proxy('_workType', 'name')

	# relationships
	task = relationship('Task')
	_batchingMode = relationship('BatchingMode')
	_workType = relationship('WorkType')
	qaConfig = relationship('QaConfig',
		primaryjoin='SubTask.subTaskId==QaConfig.workSubTaskId',
		uselist=False)
	workIntervals = relationship('WorkInterval',
		primaryjoin='SubTask.subTaskId==WorkInterval.subTaskId',
		order_by='WorkInterval.startTime')

	# synonyms
	sub_task_id = synonym("subTaskId")
	task_id = synonym("taskId")
	work_type_id = synonym("workTypeId")

	@property
	def currentRate(self):
		return SubTaskRate.query.filter_by(subTaskId=self.subTaskId
			).filter(SubTaskRate.validFrom<=func.now()
			).order_by(SubTaskRate.validFrom.desc()
			).first()
	@property
	def payByUnit(self):
		if self.task.taskType == TaskType.TRANSLATION:
			return True
		return False
	@property
	def bonus(self):
		return self.currentRate.bonus if self.currentRate.bonus else None

	@classmethod
	def for_task(cls, task_id):
		"""
		Returns a MyForm validator to check that
		the sub task belongs to the given task.
		"""
		def validator(data, key, value):
			sub_task = cls.query.get(value)

			if sub_task.task_id != task_id:
				raise ValueError("sub task {0} does not belong to task {1}".format(value, task_id))

		return validator


class SubTaskSchema(Schema):
	enforce_checking_criteria = fields.Boolean(dump_to="enforceCheckingCriteria")

	class Meta:
		additional = ('subTaskId', 'name',
			'workTypeId', 'workType',
			'taskId', 'taskTypeId', 'taskType',
			'maxPageSize', 'dstDir', 'modeId',
			'defaultLeaseLife',
			'getPolicy', 'expiryPolicy',
			'allowPageSkip', 'allowEditing', 'allowAbandon', 'allowCheckout',
			'lookAhead', 'lookBehind',
			'instructionPage', 'useQaHistory',
			'isSecondPassQa', 'needDynamicTagSet', 'useWorkRate')
		ordered = True
		# skip_missing = True

# SubTaskContentEvent
class SubTaskContentEvent(Base):
	__table__ = t_reworkcontenthistory
	amount = synonym('itemCount')
	populating = synonym('isAdding')
	selection = relationship('UtteranceSelection')
	operatedBy = relationship('User',
		primaryjoin='SubTaskContentEvent.operator == User.userId',
		foreign_keys='User.userId',
		uselist=False,
	)
class SubTaskContentEventSchema(Schema):
	selection = fields.Nested('UtteranceSelectionSchema')
	operatedBy = fields.Method('get_operated_by')
	def get_operated_by(self, obj):
		if obj.operator is None:
			return None
		s = UserSchema(only=['userId', 'userName'])
		return s.dump(obj.operatedBy).data
	class Meta:
		fields = ('subTaskId', 'selectionId', 'selection', 'itemCount',
			'isAdding', 'tProcessedAt', 'operatedBy')
		ordered = True

# SubTaskMetric
class SubTaskMetric(Base):
	__table__ = t_subtaskmetrics
	abnormalUsageEntries = relationship('AbnormalUsageEntry')
	errorEntries = relationship('SubTaskMetricErrorEntry')

class SubTaskMetricSchema(Schema):
	errors = fields.Method('get_errors')
	def get_errors(self, obj):
		errors = {}
		for i in obj.errorEntries:
			errors[i.errorTypeId] = i.occurences
		return errors
	abnormalTags = fields.Method('get_abnormal_tags')
	def get_abnormal_tags(self, obj):
		abnormal_tags = {}
		for i in obj.abnormalUsageEntries:
			if i.tagId is not None:
				abnormal_tags[i.tagId] = i.degree
		return abnormal_tags
	abnormalLabels = fields.Method('get_abnormal_labels')
	def get_abnormal_labels(self, obj):
		abnormal_labels = {}
		for i in obj.abnormalUsageEntries:
			if i.labelId is not None:
				abnormal_labels[i.labelId] = i.degree
		return abnormal_labels
	class Meta:
		fields = ('metricId', 'userId', 'workIntervalId', 'subTaskId', 'itemCount',
			'unitCount', 'workRate', 'accuracy', 'lastUpdated',
			'errors', 'abnormalTags', 'abnormalLabels')
		ordered = True

# SubTaskRate
class SubTaskRate(Base):
	__table__ = t_subtaskrates
	rate = relationship('Rate')
	_updatedByUser = relationship('User',
		primaryjoin='SubTaskRate.updatedBy == User.userId',
		foreign_keys='User.userId',
		uselist=False,
	)
	rateName = association_proxy('rate', 'name')
	standardValue = association_proxy('rate', 'standardValue')
	targetAccuracy = association_proxy('rate', 'targetAccuracy')

class SubTaskRateSchema(Schema):
	updatedBy = fields.Method('get_updated_by')
	def get_updated_by(self, obj):
		s = UserSchema(only=['userId', 'userName'])
		return s.dump(obj._updatedByUser).data

	class Meta:
		fields = ('subTaskRateId', 'subTaskId', 'taskId', 'rateId', 'rateName', 'standardValue', 'targetAccuracy', 'validFrom', 'multiplier', 'bonus', 'updatedBy', 'updatedAt')
		ordered = True

# TagImage:
class TagImage(Base):
	__table__ = t_tagimagepreviews

class TagImageSchema(Schema):
	class Meta:
		fields = ('previewId', 'created')
		ordered = True

# Tag
class Tag(Base):
	EVENT = 'Event'
	NON_EMBEDDABLE = 'Span'
	EMBEDDABLE = 'SpanB'
	SUBSTITUTION = 'Substitution'
	ENTITY = 'Entity'
	FOOTNOTE = 'Footnote'
	TIMESTAMPED = "Timestamped"
	__table__ = t_tags
	__mapper_args__ = {
		'polymorphic_on': t_tags.c.tagType,
		'polymorphic_identity': 'generic',
		#'include_properties': [
		#	t_tags.c.tagId, t_tags.c.name, t_tags.c.tagSetId, t_tags.c.tagType,
		#	t_tags.c.extractStart, t_tags.c.extractEnd, t_tags.c.shortcutKey,
		#	t_tags.c.enabled, t_tags.c.tooltip, t_tags.c.description,
		#],
	}

class TagSchema(Schema):
	tagId = fields.Integer()
	name = fields.String()
	tagSetId = fields.Integer()
	tagType = fields.String()
	extractStart = fields.String()
	extractEnd = fields.String()
	shortcutKey = fields.String()
	enabled = fields.Boolean()
	tooltip = fields.String()
	description = fields.String()

class EventTag(Tag):
	__mapper_args__ = {
		'polymorphic_identity': Tag.EVENT,
	}

class EventTagSchema(TagSchema):
	imageUrl = fields.Method('get_image_url')
	def get_image_url(self, obj):
		return '/tagimages/{}.png'.format(obj.tagId)
	class Meta:
		additional = ('imageUrl',)

class SpanTag(Tag):
	__mapper_args__ = {
		'polymorphic_identity': Tag.NON_EMBEDDABLE,
		#'include_properties': [t_tags.c.color, t_tags.c.isForeground, t_tags.c.extend, t_tags.c.split],
	}
	@property
	def style(self):
		return '{}:{}'.format('color' if self.isForeground else 'background-color', self.color)

class SpanTagSchema(TagSchema):
	class Meta:
		additional = ('color', 'isForeground', 'surround', 'extend', 'split', 'style')

class SpanBTag(Tag):
	__mapper_args__ = {
		'polymorphic_identity': Tag.EMBEDDABLE,
	}
	@property
	def style(self):
		return '{}:{}'.format('color' if self.isForeground else 'background-color', self.color)

class SpanBTagSchema(TagSchema):
	class Meta:
		additional = ('color', 'isForeground', 'style')

class SubstitutionTag(Tag):
	__mapper_args__ = {
		'polymorphic_identity': Tag.SUBSTITUTION,
	}

class SubstitutionTagSchema(TagSchema):
	pass

class EntityTag(Tag):
	__mapper_args__ = {
		'polymorphic_identity': Tag.ENTITY,
	}

class EntityTagSchema(TagSchema):
	pass

class FootnoteTag(Tag):
	__mapper_args__ = {
		'polymorphic_identity': Tag.FOOTNOTE,
	}
	@property
	def style(self):
		return '{}:{}'.format('color' if self.isForeground else 'background-color', self.color)

class FootnoteTagSchema(TagSchema):
	class Meta:
		additional = ('color', 'isForeground', 'style')

class TimestampedTag(Tag):
	__mapper_args__ = {
		'polymorphic_identity': Tag.TIMESTAMPED,
	}

# TODO share with event tag
class TimestampedTagSchema(TagSchema):
	imageUrl = fields.Method('get_image_url')
	def get_image_url(self, obj):
		return '/tagimages/{}.png'.format(obj.tagId)
	class Meta:
		additional = ('imageUrl',)


# TagSet
class TagSet(Base):
	__table__ = t_tagsets
	tags = relationship('Tag', backref='tagSet')

class TagSetSchema(Schema):
	_sd = {
			Tag.EVENT: EventTagSchema(),
			Tag.NON_EMBEDDABLE: SpanTagSchema(),
			Tag.EMBEDDABLE: SpanBTagSchema(),
			Tag.SUBSTITUTION: SubstitutionTagSchema(),
			Tag.ENTITY: EntityTagSchema(),
			Tag.FOOTNOTE: FootnoteTagSchema(),
			Tag.TIMESTAMPED: TimestampedTagSchema(),
		}
	tags = fields.Method('get_tags')
	def get_tags(self, obj):
		result = []
		for t in obj.tags:
			s = self._sd[t.tagType]
			result.append(s.dump(t).data)
		return result
	class Meta:
		fields = ('tagSetId', 'created', 'lastUpdated', 'tags')
		ordered = True


class TagSet_SmartSchema(TagSetSchema):
	subTaskId = fields.Method('get_sub_task_id')
	def get_sub_task_id(self, obj):
		try:
			context = self.context
			if context is None or not isinstance(context, dict):
				raise ValueError
			subTaskId = context['subTaskId']
		except (ValueError, KeyError):
			raise RuntimeError('must provide sub task id in context')
		return subTaskId
	def get_tags(self, obj):
		subTaskId = self.get_sub_task_id(obj)
		shadowed = set([i.tagId for i in SS.query(ShadowedTag.tagId
				).filter(ShadowedTag.subTaskId==subTaskId).all()])
		result = []
		for t in obj.tags:
			if t.tagId in shadowed:
				continue
			s = self._sd[t.tagType]
			result.append(s.dump(t).data)
		return result
	class Meta:
		additional = ('subTaskId',)


# Task
class Task(Base, ModelMixin):
	STATUS_ACTIVE = 'active'
	STATUS_DISABLED = 'disabled'
	STATUS_FINISHED = 'finished'
	STATUS_CLOSED = 'closed'
	STATUS_ARCHIVED = 'archived'
	__table__ = t_tasks
	_migratedByUser = relationship('User')
	_taskType = relationship('TaskType')
	taskType = association_proxy('_taskType', 'name')
	tagSet = relationship('TagSet')
	labelSet = relationship('LabelSet')
	rawPieces = relationship('RawPiece', order_by='RawPiece.rawPieceId')
	supervisors = relationship('TaskSupervisor')
	taskErrorTypes = relationship('TaskErrorType')
	subTasks = relationship('SubTask', back_populates='task')
	expansions = relationship('KeyExpansion', order_by='KeyExpansion.char')

	# synonyms
	task_id = synonym("taskId")
	task_type = synonym("taskType")	# FIXME causes recursion error
	archive_info = synonym("archiveInfo")
	raw_pieces = synonym("rawPieces")
	audio_uploads = synonym("audioUploads")
	sub_tasks = synonym("subTasks")

	@classmethod
	def get_statuses(cls):
		return [
			cls.STATUS_ACTIVE,
			cls.STATUS_DISABLED,
			cls.STATUS_FINISHED,
			cls.STATUS_CLOSED,
			cls.STATUS_ARCHIVED
		]

	@classmethod
	def is_valid_status(cls, status):
		return status in cls.get_statuses()
	
	@property
	def displayName(self):
		return self.display_name

	@property
	def workers(self):
		return SS.query(User
			).filter(User.userId.in_(SS.query(TaskWorker.userId
				).filter(TaskWorker.taskId==self.taskId))
			).order_by(User.userName).all()

	def is_type(self, *task_types):
		return self.task_type in task_types

	@property
	def display_name(self):
		return "{0} - {1}".format(self.task_id, self.name)

	# FIXME update for transcription loading?
	@property
	def loadable(self):
		if not self.is_type(TaskType.AUDIO_CHECKING):
			raise RuntimeError

		return bool(self.loadable_recording_platforms)

	@property
	def loadable_recording_platforms(self):
		if not self.is_type(TaskType.AUDIO_CHECKING):
			raise RuntimeError

		return [rp for rp in self.recording_platforms if rp.loader]

	def get_load_sub_task(self):
		"""
		Gets the load sub task. Expects
		a single Work sub task.
		"""
		work_type = WorkType.from_name(WorkType.WORK)

		try:
			sub_task = SubTask.query.filter_by(
				task=self,
				work_type_id=work_type.work_type_id,
			).one()
		except SQLAlchemyError:
			raise RuntimeError("unable to find load sub task")

		return sub_task

	def load_transcription_data(self, data, load):
		"""
		Loads data into a transcription task.
		"""
		if not self.is_type(TaskType.TRANSCRIPTION):
			raise RuntimeError

		validate_load_utterance_data(data)
		assert data

		# create utterances
		utts = []
		for utt_data in data["utts"]:
			utt = Utterance.from_load(utt_data, self, load)
			utts.append(utt)

		# update performances
		for update_data in data["performanceUpdates"]:
			performance = Performance.query.get(update_data["rawPieceId"])
			performance.update_transcription_info(self.task_id, update_data)

		return utts

	def load_audio_checking_data(self, data, load):
		"""
		Loads data into an audio checking task.

		If loading for an existing performance, returns
		the Performance object, with newly added data.
		If loading for a new Performance, returns the
		Batch object containing the new performance.
		"""

		if not self.is_type(TaskType.AUDIO_CHECKING):
			raise RuntimeError

		# validate load data
		validate_load_performance_data(data)

		# if adding new data to an existing performance
		if data["rawPieceId"]:
			performance = Performance.query.get(data["rawPieceId"])

			if performance.task != self:
				raise ValueError("Performance {0} does not belong to task {1}".format(performance.raw_piece_id, self.task_id))

			performance.load_data(data)
			return performance

		# adding a new performance
		else:

			# get load sub task
			sub_task = self.get_load_sub_task()

			# create performance
			performance = Performance.from_load(data, self, load)

			# add batch to load sub task TODO move this to app.api...?
			from app.util import Batcher
			batches = Batcher.batch(sub_task, [performance])
			assert len(batches) == 1
			return batches[0]

	def update_config(self, updates):
		"""
		Updates the task config field.
		"""
		config = self.config or {}
		config.update(updates)
		self.config = config
		flag_modified(self, "config")

	def update_stats(self, updates):
		"""
		Updates the task stats field.
		"""
		stats = self.stats or {}
		stats.update(updates)
		self.stats = stats
		flag_modified(self, "stats")

	def set_loader(self, loader):
		self.loader = loader
		flag_modified(self, "loader")


class TaskSchema(Schema):
	tagSet = fields.Nested('TagSetSchema')
	labelSet = fields.Nested('LabelSetSchema')
	migratedBy = fields.Method('get_migrated_by')
	display_name = fields.String(dump_to="displayName")

	def get_migrated_by(self, obj):
		s = UserSchema(only=['userId', 'userName'])
		return s.dump(obj._migratedByUser).data

	class Meta:
		fields = ('taskId', 'name', 'projectId', 'taskTypeId',
			'taskType', 'status', 'srcDir', 'lastStatusChange',
			'tagSetId', 'labelSetId', 'migrated', 'migratedBy',
			'globalProjectId', 'config', "displayName")
		ordered = True


# TaskErrorType
class TaskErrorType(Base):
	__table__ = t_taskerrortypes
	_errorType = relationship('ErrorType')
	errorType = association_proxy('_errorType', 'name')
	errorClassId = association_proxy('_errorType', 'errorClassId')
	errorClass = association_proxy('_errorType', 'errorClass')
	defaultSeverity = association_proxy('_errorType', 'defaultSeverity')

class TaskErrorTypeSchema(Schema):
	class Meta:
		fields = ('taskId', 'errorTypeId', 'errorType', 'errorClassId', 'errorClass', 'severity', 'disabled', 'defaultSeverity')

# TaskPaymentRecord
class TaskPaymentRecord(Base):
	__table__ = t_costperutterance

class TaskPaymentRecordSchema(Schema):
	class Meta:
		fields = ('taskId', 'payrollId', 'cutOffTime', 'itemCount',
			'unitCount', 'paymentSubtotal')

# TaskSupervisor
class TaskSupervisor(Base):
	__table__ = t_tasksupervisors
	user = relationship('User')
	userName = association_proxy('user', 'userName')
	emailAddress = association_proxy('user', 'emailAddress')

class TaskSupervisorSchema(Schema):
	class Meta:
		fields = ('taskId', 'userId', 'userName', 'receivesFeedback', 'informLoads')
		ordered = True

# TaskType
class TaskType(Base, ModelMixin, NamedTypeMixin):
	__table__ = t_tasktypes
	
	# constants
	AUDIO_CHECKING = "Audio Checking"
	MARKUP = 'Markup'
	TEXT_COLLECTION = 'Text Collection'
	TRANSCRIPTION = "Transcription"
	TRANSLATION = 'Translation'

class TaskTypeSchema(Schema):
	class Meta:
		fields = ('taskTypeId', 'name', 'description')

# TaskWorker
class TaskWorker(Base):
	__table__ = t_taskusers
	user = relationship('User')
	userName = association_proxy('user', 'userName')
	countryId = association_proxy('user', 'countryId')

class TaskWorkerSchema(Schema):
	class Meta:
		fields = ('taskId', 'subTaskId', 'userId', 'userName', 'isNew', 'removed', 'paymentFactor', 'hasReadInstructions', 'countryId')
		ordered = True

# TrackingEvent
class TrackingEvent(Base):
	__table__ = t_tracking_events

class TrackingEventSchema(Schema):
	class Meta:
		fields = ('eventId', 'eventType', 'tTriggeredAt', 'hostIp', 'details')

# User
class User(Base, ModelMixin):
	PAYMENT_TYPE_INDEPENDENT_CONTRACTOR = 0
	PAYMENT_TYPE_W2_WORKER = 1
	PAYMENT_TYPE_CLIENT = 2
	PAYMENT_TYPE_INTERNAL = 3

	__table__ = t_users

	# synonyms
	globalId = synonym('userId')
	user_id = synonym("userId")
	global_id = synonym("globalId")
	appen_id = synonym("globalId")
	email_address = synonym("emailAddress")
	family_name = synonym("familyName")
	given_name = synonym("givenName")

	@hybrid_property
	def userName(self):
		if self.givenName == None or not self.givenName.strip():
			return 'User' + str(self.userId)
		return self.givenName.split()[0] + str(self.userId)
	@userName.expression
	def userName(klass):
		return case([
			(klass.givenName == None, 'User'),
			(klass.givenName.op('!~')(text(r"E'\\S'")), 'User'),
		], else_=func.substring(klass.givenName, text(r"E'(?:^\\s*)(\\S+)'"))).op('||')(klass.userId)

class UserSchema(Schema):
	class Meta:
		fields = ('userId', 'userName')

class User_FullSchema(Schema):
	caps = fields.Method('get_caps')
	def get_caps(self, obj):
		caps = getattr(obj, 'caps', [])
		return sorted(caps)
	class Meta:
		fields = ('userId', 'userName', 'emailAddress', 'familyName', 'givenName', 'globalId', 'caps')

# UtteranceSelection
class UtteranceSelection(Base):
	ACTION_BATCH = 'batch'
	ACTION_CUSTOM = 'custom'
	ACTION_PP = 'pp'
	ACTION_RECURRING = 'recurring'
	__table__ = t_utteranceselections
	user = relationship('User')
	userName = association_proxy('user', 'userName')
	filters = relationship('SelectionFilter',
		order_by='SelectionFilter.filterId',
		cascade='all, delete-orphan')

class UtteranceSelectionSchema(Schema):
	filters = fields.Nested('SelectionFilterSchema', many=True)
	class Meta:
		fields = ('selectionId', 'taskId', 'userId', 'userName', 'limit', 'selected', 'action', 'subTaskId', 'name', 'processed', 'random', 'filters')
		ordered = True
		# skip_missing = True

# WorkEntry
class BasicWorkEntry(Base):
	__table__ = t_workentries

class WorkEntry(Base):
	_P = re.compile(r'''tagid=(["'])(\d+)\1''')
	__table__ = j_workentries
	__mapper_args__ = {
		'polymorphic_on': j_workentries.c.workType,
		'polymorphic_identity': 'generic',
	}
	user = relationship('User')
	userName = association_proxy('user', 'userName')
	rawPiece = relationship('RawPiece')
	@property
	def utcTime(self):
		return self.created.astimezone(pytz.utc)
	@property
	def workDate(self):
		return self.utcTime.strftime('%Y-%m-%d')
	@property
	def timeSlotKey(self):
		return (self.workDate, self.utcTime.hour, self.utcTime.minute / 15)
	@property
	def tags(self):
		# TODO: improve current implementation to be more error-proof
		return [int(m.group(2)) for m in self._P.finditer(self.result or '')]

class WorkEntrySchema(Schema):
	entryId = fields.Integer()
	created = fields.DateTime()
	result = fields.String()
	batchId = fields.Integer()
	pageId = fields.Integer()
	rawPieceId = fields.Integer()
	taskId = fields.Integer()
	subTaskId = fields.Integer()
	workTypeId = fields.Integer()
	workType = fields.String()
	notes = fields.String()
	user = fields.Nested('UserSchema')
	class Meta:
		fields = ('entryId', 'created', 'result', 'user')
		ordered = True

class AppliedLabel(Base):
	__table__ = t_workentrylabels

class AppliedError(Base):
	__table__ = t_workentryerrors

class WorkTypeEntry(WorkEntry):
	__mapper_args__ = {
		'polymorphic_identity': WorkType.WORK,
	}
	appliedLabels = relationship('AppliedLabel')
	@property
	def labels(self):
		return [l.labelId for l in self.appliedLabels]

class WorkTypeEntrySchema(WorkEntrySchema):
	class Meta:
		additional = ('labels',)
		ordered = True

class QaTypeEntry(WorkEntry):
	__mapper_args__ = {
		'polymorphic_identity': WorkType.QA,
	}
	appliedErrors = relationship('AppliedError')
	@property
	def errors(self):
		return [e.errorTypeId for e in self.appliedErrors]
	@property
	def qaScore(self):
		return 1.0 - min(1, sum([e.severity for e in self.appliedErrors]))

class QaTypeEntrySchema(WorkEntrySchema):
	class Meta:
		additional = ('errors',)
		ordered = True

class ReworkTypeEntry(WorkEntry):
	__mapper_args__ = {
		'polymorphic_identity': WorkType.REWORK,
	}
	appliedLabels = relationship('AppliedLabel')
	@property
	def labels(self):
		return [l.labelId for l in self.appliedLabels]

class ReworkTypeEntrySchema(WorkEntrySchema):
	class Meta:
		additional = ('labels',)
		ordered = True

# WorkInterval
class WorkInterval(Base):
	STATUS_CURRENT = 'current'
	STATUS_ADDING_FINAL_CHECKS = 'addingfinalchecks'
	STATUS_CHECKING = 'checking'
	STATUS_FINISHED = 'finished'
	__table__ = t_workintervals
	intervalId = synonym('workIntervalId')

class WorkIntervalSchema(Schema):
	class Meta:
		fields = ('workIntervalId', 'taskId', 'subTaskId', 'status', 'startTime', 'endTime')
		ordered = True

# AbnormalUsageEntry
class AbnormalUsageEntry(Base):
	__table__ = t_abnormalusage

class AbnormalUsageEntrySchema(Schema):
	class Meta:
		fields = ('metricId', 'tagId', 'labelId', 'degree')

# SubTaskMetricErrorEntry
class SubTaskMetricErrorEntry(Base):
	__table__ = t_subtaskmetricerrors

class SubTaskMetricErrorEntrySchema(Schema):
	class Meta:
		fields = ('metricId', 'errorTypeId', 'occurrences')

##########################################################################

# SnsMessageRecord
class SnsMessageRecord(Base):
	__table__ = t_sns_message_records

# Country
class Country(Base):
	__table__ = t_countries

class CountrySchema(Schema):
	class Meta:
		fields = ('countryId', 'name', 'hourlyRate')

# Language
class Language(Base):
	__table__ = t_languages


# WritingScript
class WritingScript(Base):
	__table__ = t_writing_scripts

class WritingScriptSchema(Schema):
	class Meta:
		fields = ('scriptId', 'name', 'code', 'numericCode')

# Dialect
class Dialect(Base):
	__table__ = t_dialects
	script = relationship('WritingScript')
	langCode = synonym('iso639_3')
	countryCode = synonym('iso3166_3')
	@property
	def dir(self):
		return 'ltr' if self.ltr else 'rtl'

class DialectSchema(Schema):
	script = fields.Nested('WritingScriptSchema')
	class Meta:
		fields = ('dialectId', 'name', 'langCode', 'countryCode', 'dir',
			'romanizationScheme', 'scriptId', 'script')

class Rule(Base):
	__table__ = t_rules
	patterns = relationship('RulePattern', order_by='RulePattern.regexId')

class RuleSchema(Schema):
	patterns = fields.Nested('RulePatternSchema', many=True, exclude=('ruleId',))
	class Meta:
		fields = ('ruleId', 'name', 'type', 'description', 'alphabetId', 'patterns')

class RulePattern(Base):
	__table__ = t_rule_patterns

class RulePatternSchema(Schema):
	class Meta:
		fields = ('regexId', 'ruleId', 'search', 'replace')

class Alphabet(Base):
	__table__ = t_alphabets
	rules = relationship('Rule')
	graphemes = relationship('Grapheme')
	dialect = relationship('Dialect')
	current = synonym('isActive')
	manPageUrl = synonym('url')

class AlphabetSchema(Schema):
	rules = fields.Nested('RuleSchema', many=True, exclude=['alphabetId'])
	graphemes = fields.Nested('GraphemeSchema', many=True, exclude=['alphabetId'])
	dialect = fields.Nested('DialectSchema')
	class Meta(Schema):
		fields = ('alphabetId', 'name', 'dialect', 'isActive', 'url')

class Alphabet_FullSchema(AlphabetSchema):
	class Meta:
		fields = ('alphabetId', 'name', 'manPageUrl', 'current', 'dialectId',
			'dialect', 'graphemes', 'rules')

class Grapheme(Base):
	__table__ = t_graphemes

class GraphemeSchema(Schema):
	class Meta:
		fields = ('alphabetId', 'key', 'token')

##########################################################################

# RecordingPlatformType
class RecordingPlatformType(Base, ModelMixin):
	__table__ = t_recording_platform_types

	# constants
	UNSPECIFIED = "Unspecified"
	SONY_MOBILE_RECORDER = "Sony Mobile Recorder"
	APPEN_MOBILE_RECORDER = "Appen Mobile Recorder"
	TELEPHONY = "Telephony"

	# column synonyms
	recording_platform_id = synonym("recordingPlatformId")


class RecordingPlatformTypeSchema(Schema):
	class Meta:
		fields = ("recordingPlatformTypeId", "name")


# RecordingPlatform
class RecordingPlatform(Base, ModelMixin):
	__table__ = t_recording_platforms

	# constants
	MASTER_FILE_PARSERS = ["Simple", "Reading Script"]
	DEFAULT_AUDIO_QUALITY = {"name": "Standard Quality", "format": "ogg", "quality": 3}

	# relationships
	task = relationship("Task", backref="recording_platforms")
	recording_platform_type = relationship("RecordingPlatformType")
	selected_audio_stats_types = relationship("AudioStatsType", secondary=t_recording_platform_audio_stats_types)

	# synonyms
	recording_platform_id = synonym("recordingPlatformId")
	recording_platform_type_id = synonym("recordingPlatformTypeId")
	task_id = synonym("taskId")
	recording_platform_id = synonym("recordingPlatformId")
	audio_quality = synonym("audioQuality")

	@property
	def audio_stats_types(self):
		default_types = AudioStatsType.query.filter_by(is_default=True).all()
		return default_types + self.selected_audio_stats_types

	@property
	def loadable_performance_meta_categories(self):
		"""
		Meta categories that are populated during loading.
		"""
		return [meta_category for meta_category in self.performance_meta_categories if meta_category.extractor]

	@property
	def metadata_sources(self):
		"""
		Returns the metadata sources for the recording platform.
		This is the combination of the metadata sources of the
		associated loader (if any) and any custom metadata sources
		defined in the recording platform config.
		"""
		if self.loader and "name" in self.loader:
			return get_loader_metadata_sources(self.loader["name"])

		return []

	@property
	def spontaneous_corpus_codes(self):
		return [corpus_code for corpus_code in self.corpus_codes if not corpus_code.is_scripted]

	@property
	def scripted_corpus_codes(self):
		return [corpus_code for corpus_code in self.corpus_codes if corpus_code.is_scripted]

	def check_extractor(self, data, key, value):
		"""
		MyForm validator for checking that the metadata extractor
		is valid.
		"""
		if value is not None:

			if not "key" in value:
				raise ValueError("no key found")

			if not "source" in value:
				raise ValueError("no source found")

			if value["source"] not in self.metadata_sources:
				raise ValueError("{0} is an invalid source".format(value["source"]))

	@classmethod
	def is_valid_master_file(cls, data, key, value):
		"""
		MyForm validator for checking that the master file
		parser is valid.
		"""

		if value is not None:

			if not isinstance(value, dict):
				raise ValueError("invalid JSON format")

			if "parser" not in value:
				raise ValueError("missing parser")

			if "path" not in value:
				raise ValueError("missing path")

			if value["parser"] not in cls.MASTER_FILE_PARSERS:
				raise ValueError("invalid parser")

	@property
	def display_name(self):
		return "{0} - Recording Platform {1}".format(self.recording_platform_type.name, self.recording_platform_id)

	def move_performances(self, performances, destination, user_id, change_method):
		"""
		Moves performances to the destination sub task if allowed.
		Returns a three-item tuple:
		 1. list of performances successfully moved
		 2. list of performances already at the destination sub task
		 3. list of performances that can't be moved due to a missing transition
		 4. list of performances that are locked at the source
		"""

		if self.task_id != destination.task_id:
			raise RuntimeError

		at_destination = []		# already at the destination
		no_transition = []		# no transition exists
		locked = []				# performance is locked at source
		moved = []				# successfully moved

		for performance in performances:

			if performance.recording_platform != self:
				raise RuntimeError

			try:
				performance.move_to(destination.sub_task_id, change_method, user_id)

			except SelfTransition:
				at_destination.append(performance)

			except InvalidTransition:
				no_transition.append(performance)

			except LockedPerformance:
				locked.append(performance)

			else:
				moved.append(performance)

		return moved, at_destination, no_transition, locked

	def set_loader(self, loader):
		self.loader = loader
		flag_modified(self, "loader")

class RecordingPlatformSchema(Schema):
	metadata_sources = fields.Dict(dump_to="metadataSources")
	recording_platform_type = fields.Nested("RecordingPlatformTypeSchema", dump_to="recordingPlatformType")
	task = fields.Nested("TaskSchema", only=("taskId", "name", "displayName"))
	display_name = fields.String(dump_to="displayName")

	class Meta:
		additional = ("recordingPlatformId", "taskId", "audioQuality", "loader")


# AudioFile
class AudioFile(Base, LoadMixin):
	__table__ = t_audio_files

	# relationships
	recording = relationship("Recording", backref="audio_files")
	track = relationship("Track")
	recording_platform = relationship("RecordingPlatform", backref="audio_files")

	# synonyms
	audio_file_id = synonym("audioFileId")
	recording_id = synonym("recordingId")
	recording_platform_id = synonym("recordingPlatformId")
	track_id = synonym("trackId")
	file_path = synonym("filePath")
	audio_spec = synonym("audioSpec")
	audio_data_location = synonym("audioDataLocation")

	@classmethod
	def from_load(cls, data, recording):
		track = Track.query.get(data["trackId"])

		if track.recording_platform != recording.recording_platform:
			raise ValueError("Track {0} does not belong to recording platform {1}".format(track.track_id, recording.recording_platform.recording_platform_id))

		audio_file = AudioFile(
			recording=recording,
			recording_platform=recording.recording_platform,
			track=track,
			file_path=data["filePath"],
			audio_spec=data["audioSpec"],
			audio_data_location=data["audioDataLocation"],
			stats=data["stats"]
		)

		return audio_file

	@property
	def display_name(self):
		return "Audio File {0}".format(self.audio_file_id)

	@property
	def performance(self):
		return self.recording.performance

	@property
	def task(self):
		return self.performance.task

	@property
	def is_wav(self):
		return self.file_path.lower().endswith("wav")


class AudioFileSchema(Schema):
	task = fields.Nested("TaskSchema", only=("taskId", "displayName"))
	recording_platform = fields.Nested("RecordingPlatformSchema", dump_to="recordingPlatform", only=("recordingPlatformId", "display_name"))
	performance = fields.Nested("PerformanceSchema", only=("rawPieceId", "display_name"))
	recording = fields.Nested("RecordingSchema", only=("recordingId", "display_name"))
	display_name = fields.String(dump_to="displayName")
	track = fields.Nested("TrackSchema")

	class Meta:
		additional = ("audioFileId", "recordingId", "filePath", "audioSpec", "audioDataLocation", "stats")


# SpeakerMetaCategory
class SpeakerMetaCategory(Base):
	__table__ = t_speaker_meta_categories

	# column synonyms
	speaker_meta_category_id = synonym("speakerMetaCategoryId")
	task_id = synonym("taskId")
	validator_spec = synonym("validatorSpec")


class SpeakerMetaCategorySchema(Schema):
	class Meta:
		fields = ("speakerMetaCategoryId", "taskId", "name", "key", "validatorSpec")

# SpeakerMetaValue
class SpeakerMetaValue(Base):
	__table__ = t_speaker_meta_values

	# column synonyms
	speaker_meta_value_id = synonym("speakerMetaValueId")
	speaker_meta_category_id = synonym("speakerMetaCategoryId")
	speaker_id = synonym("speakerId")


class SpeakerMetaValueSchema(Schema):
	class Meta:
		fields = ("speakerMetaValueId", "speakerMetaCategoryId", "speakerId", "value")

# Speaker
class Speaker(Base):
	__table__ = t_speakers

	# synonyms
	speaker_id = synonym("speakerId")
	task_id = synonym("taskId")


class SpeakerSchema(Schema):
	class Meta:
		fields = ("speakerId", "taskId", "identifier")

# AlbumMetaCategory
class AlbumMetaCategory(Base):
	__table__ = t_album_meta_categories

	# column synonyms
	album_meta_category_id = synonym("albumMetaCategoryId")
	task_id = synonym("taskId")
	validator_spec = synonym("validatorSpec")


class AlbumMetaCategorySchema(Schema):
	class Meta:
		fields = ("albumMetaCategoryId", "taskId", "name", "key", "validatorSpec")

# AlbumMetaValue
class AlbumMetaValue(Base):
	__table__ = t_album_meta_values

	# column synonyms
	album_meta_value_id = synonym("albumMetaValueId")
	album_meta_category_id = synonym("albumMetaCategoryId")
	album_id = synonym("albumId")


class AlbumMetaValueSchema(Schema):
	class Meta:
		fields = ("albumMetaValueId", "albumMetaCategoryId", "albumId", "value")

# Album
class Album(Base):
	__table__ = t_albums

	# relationships
	task = relationship("Task", backref="albums")

	# synonyms
	album_id = synonym("albumId")
	task_id = synonym("taskId")
	speaker_id = synonym("speakerId")

	@property
	def display_name(self):
		return self.name or "Album {0}".format(self.album_id)

	@property
	def num_performances(self):
		return len(self.performances)


class AlbumSchema(Schema):
	album_id = fields.Integer(dump_to="albumId")
	speaker_id = fields.Integer(dump_to="speakerId")
	task = fields.Nested("TaskSchema", only=("taskId", "displayName"))
	display_name = fields.String(dump_to="displayName")
	performances = fields.Nested("PerformanceSchema", many=True, only=("rawPieceId", "display_name"))
	num_performances = fields.Integer(dump_to="numPerformances")


# PerformanceMetaCategory
class PerformanceMetaCategory(Base, ModelMixin, MetaCategoryMixin):
	__table__ = t_performance_meta_categories

	# relationships
	recording_platform = relationship("RecordingPlatform", backref="performance_meta_categories")

	# synonyms
	performance_meta_category_id = synonym("performanceMetaCategoryId")
	recording_platform_id = synonym("recordingPlatformId")
	validator_spec = synonym("validatorSpec")

	@property
	def meta_category_id(self):
		return self.performance_meta_category_id

	@classmethod
	def check_name_unique(cls, data, key, value, recording_platform):
		"""
		MyForm validator for checking that a new
		performance meta category name is unique
		for the	recording platform.
		"""
		if cls.query.filter_by(recording_platform=recording_platform, name=value).count():
			raise ValueError("{0} is already used".format(value))

	def check_other_name_unique(self, data, key, value):
		"""
		MyForm validator for checking that an
		existing performance meta category name
		is unique for the recording platform.
		"""
		query = self.query.filter(
			self.__class__.recording_platform_id==self.recording_platform_id,
			self.__class__.name==value,
			self.__class__.performance_meta_category_id!=self.performance_meta_category_id,
		)

		if query.count():
			raise ValueError("{0} is used by another performance meta category".format(value))


class PerformanceMetaCategorySchema(Schema):
	class Meta:
		fields = ("performanceMetaCategoryId", "name", "extractor", "validatorSpec")

# PerformanceMetaValue
class PerformanceMetaValue(Base, MetaValueMixin):
	__table__ = t_performance_meta_values

	# relationships
	meta_entity = relationship("Performance", backref="meta_values")
	meta_category = relationship("PerformanceMetaCategory")

	# synonyms
	performance_meta_value_id = synonym("performanceMetaValueId")
	performance_meta_category_id = synonym("performanceMetaCategoryId")
	raw_piece_id = synonym("rawPieceId")

	def satisfies(self, criteria_values):

		# enum
		if self.meta_category.validator_spec["type"] == "enum":
			return self.value["value"] in criteria_values

		# int with ranges
		if self.meta_category.validator_spec["type"] == "int" and "ranges" in self.meta_category.validator_spec:
			criteria_values = [json.loads(value) for value in criteria_values]

			for value in criteria_values:
				if "from" in value and self.value["value"] < value["from"]:
					continue

				if "to" in value and self.value["value"] > value["to"]:
					continue

				return True

			return False

		# other
		return self.value["value"] in criteria_values


class PerformanceMetaValueSchema(Schema):
	class Meta:
		fields = ("performanceMetaValueId", "rawPieceId", "performanceMetaCategoryId", "value")


class PerformanceFeedbackEntryFlag(Base, ModelMixin):
	__table__ = t_performance_feedback_flags

	# relationships
	flag = relationship("PerformanceFlag")
	entry = relationship("PerformanceFeedbackEntry", backref=backref("entry_flags", cascade="all, delete-orphan"))


# PerformanceFeedbackEntry
class PerformanceFeedbackEntry(Base, ModelMixin, FeedbackEntryMixin):
	__table__ = t_performance_feedback

	# relationships
	user = relationship("User")
	change_method = relationship("AudioCheckingChangeMethod")

	# synonyms
	performance_feedback_entry_id = synonym("performanceFeedbackEntryId")
	raw_piece_id = synonym("rawPieceId")
	user_id = synonym("userId")
	saved_at = synonym("savedAt")

	# mixin config
	EntryFlagModel = PerformanceFeedbackEntryFlag


class PerformanceFeedbackEntrySchema(Schema):
	user = fields.Nested("UserSchema")
	flags = fields.Nested("PerformanceFlagSchema", many=True)
	change_method = fields.Nested("AudioCheckingChangeMethodSchema", dump_to="changeMethod")

	class Meta:
		additional = ("performanceFeedbackEntryId", "rawPieceId", "comment", "savedAt")


# PerformanceFlag
class PerformanceFlag(Base, ModelMixin, FeedbackFlagMixin):
	__table__ = t_performance_flags

	FlagIdAttr = "performanceFlagId"

	# constants
	INFO = "Info"
	WARNING = "Warning"
	SEVERE = "Severe"

	# relationships
	task = relationship("Task", backref="performance_flags")

	# synonyms
	performance_flag_id = synonym("performanceFlagId")
	task_id = synonym("taskId")

	@classmethod
	def check_valid_severity(cls, data, key, value):
		"""
		MyForm validator for checking a valid
		severity.
		"""
		if value not in (cls.INFO, cls.WARNING, cls.SEVERE):
			raise ValueError("{0} is not a valid severity".format(value))

	@classmethod
	def check_new_name_unique(cls, task):
		"""
		Returns a MyForm validator for checking
		that a new performance flag name is unique
		for the task.
		"""
		return cls.check_new_field_unique("name", task=task)

	@validator
	def check_updated_name_unique(self):
		"""
		Returns a MyForm validator for checking
		that an existing performance flag name
		is unique for the task.
		"""
		return self.check_updated_field_unique("name", task=self.task)


class PerformanceFlagSchema(Schema):
	performance_flag_id = fields.Integer(dump_to="performanceFlagId")
	flag_id = fields.Integer(dump_to="flagId")
	name = fields.String()
	severity = fields.String()
	enabled = fields.Boolean()


# Performance
class Performance(RawPiece, LoadMixin, MetaEntityMixin, AddFeedbackMixin):
	__table__ = t_performances

	# relationships
	album = relationship("Album", backref="performances")
	recording_platform = relationship("RecordingPlatform", backref="performances")
	raw_piece = relationship("RawPiece")
	feedback_entries = relationship("PerformanceFeedbackEntry", backref="performance", order_by="PerformanceFeedbackEntry.savedAt")

	# synonyms
	raw_piece_id = synonym("rawPieceId")
	album_id = synonym("albumId")
	recording_platform_id = synonym("recordingPlatformId")
	script_id = synonym("scriptId")
	loaded_at = synonym("loadedAt")
	in_transcription = synonym("inTranscription")

	# associations
	task_id = association_proxy("raw_piece", "taskId")

	# mixin config
	MetaValueModel = PerformanceMetaValue
	MetaCategoryModel = PerformanceMetaCategory
	FeedbackEntryModel = PerformanceFeedbackEntry
	FlagModel = PerformanceFlag
	SelfRelationshipName = "performance"

	__mapper_args__ = {
		"polymorphic_identity": "performance",
	}

	@property
	def batch(self):
		page_member = PageMember.query.filter_by(raw_piece_id=self.raw_piece_id).one()
		return page_member.batch

	@property
	def sub_task(self):
		return self.batch.sub_task

	@property
	def current_feedback(self):
		if self.feedback_entries:
			return self.feedback_entries[-1]	# TODO check ordering

		return None

	@property
	def incomplete(self):
		"""
		Placeholder for audio loading. To be
		replaced when queue functionality and
		incomplete performance loading is
		added.
		"""
		return False  # FIXME

	@property
	def meta_entity_id(self):
		return self.raw_piece_id

	@property
	def display_name(self):
		return self.name or "Performance {0}".format(self.raw_piece_id)

	def load_data(self, data):
		"""
		Adds data for the performance from
		audio load.
		"""

		# add new recordings
		for recording_data in data["recordings"]:
			recording = Recording.from_load(recording_data, self)
			self.recordings.append(recording)

	@classmethod
	def from_load(cls, data, task, load):
		"""
		Creates a new performance during audio
		loading.
		"""

		recording_platform = RecordingPlatform.query.get(data["recordingPlatformId"])

		if recording_platform.task != task:
			raise RuntimeError
			
		kwargs = dict(
			task=task,
			load_id=load.load_id,
			assembly_context="{0}_{1}".format(data["name"], int(time.time())),	# TODO shouldnt be required
			recording_platform=recording_platform,
			name=data["name"],
			script_id=data["scriptId"],
			loaded_at=utcnow(),
			words=1,
		)

		# check if album needs to be located TODO handle missing album gracefully
		if recording_platform.loader.get("useAlbums"):
			album = Album.query.filter_by(task=task, name=data.get("albumName")).one()
			kwargs.update(dict(album=album))

		# create performance
		performance = cls(**kwargs)

		# add metadata
		meta_values = process_received_metadata(data["metadata"], recording_platform.performance_meta_categories)
		resolve_new_metadata(performance, meta_values, add_log_entries=False)

		# add load data
		performance.load_data(data)
		return performance

	def move_to(self, sub_task_id, change_method, user_id=None):
		"""
		Moves the performance batch to
		the given sub task.
		"""

		if self.sub_task.sub_task_id == sub_task_id:
			raise SelfTransition

		if not Transition.is_valid_transition(self.sub_task.sub_task_id, sub_task_id):
			raise InvalidTransition

		if self.locked:
			raise LockedPerformance

		sub_task = SubTask.query.get(sub_task_id)

		# add log entry
		kwargs = dict(
			performance=self,
			source=self.sub_task,
			destination=sub_task,
			change_method=AudioCheckingChangeMethod.from_name(change_method)
		)

		if user_id:
			kwargs.update(dict(user_id=user_id))

		entry = PerformanceTransitionLogEntry(**kwargs)
		db.session.add(entry)

		# remove current batch
		self.batch.delete(True)

		# add new batch
		from app.util import Batcher
		batches = Batcher.batch(sub_task, [self.raw_piece_id])
		assert len(batches) == 1
		db.session.add(batches[0])

	def lock(self):
		"""
		Locks the performance.
		"""
		self.locked = True

	def unlock(self):
		"""
		Unlocks the performance.
		"""
		if self.in_transcription:
			raise ValueError("unable to unlock performance loaded for transcription")
		
		self.locked = False

	def update_transcription_info(self, transcription_task_id, data):

		in_transcription = self.in_transcription or {}
		in_transcription.setdefault("tasks", []).append({
			"taskId": transcription_task_id,
			"audioFileCount": data["audioFileCount"],
			"uttCount": data["uttCount"],
			"loadedAt": since_epoch(datetime.datetime.utcnow()),
		})
		self.in_transcription = in_transcription
		flag_modified(self, "inTranscription")
		self.lock()
	
	def get_meta_value(self, meta_category_id):

		for meta_value in self.meta_values:
			if meta_value.meta_category.performance_meta_category_id == meta_category_id:
				return meta_value

		return None


class PerformanceSchema(Schema):
	batch = fields.Nested("BatchSchema", only=("batchId", "user"))
	current_feedback = fields.Nested("PerformanceFeedbackEntrySchema", dump_to="currentFeedback")
	recording_platform = fields.Nested("RecordingPlatformSchema", dump_to="recordingPlatform", only=("recording_platform_id", "display_name"))
	sub_task = fields.Nested("SubTaskSchema", dump_to="subTask", only=("subTaskId", "name"))
	task = fields.Nested("TaskSchema", only=("taskId", "name", "displayName"))
	task_id = fields.Integer(dump_to="taskId")
	display_name = fields.String(dump_to="displayName")
	album = fields.Nested("AlbumSchema", only=("albumId", "display_name", "num_performances"))
	in_transcription = fields.Dict(dump_to="inTranscription")
	locked = fields.Boolean()

	class Meta:
		additional = ("rawPieceId", "albumId", "name", "recordingPlatformId", "scriptId", "key", "loadedAt")


class Performance_FullSchema(PerformanceSchema):
	meta_values = fields.Method("get_meta_values", dump_to="metaValues")

	def get_meta_values(self, obj):
		values = {}

		for meta_value in obj.meta_values:
			values[meta_value.performance_meta_category_id] = meta_value.value

		return values


# RecordingMetaCategory
class RecordingMetaCategory(Base):
	__table__ = t_recording_meta_categories

	# column synonyms
	recording_meta_category_id = synonym("recordingMetaCategoryId")
	validator_spec = synonym("validatorSpec")


class RecordingMetaCategorySchema(Schema):
	recording_meta_category_id = fields.Integer(dump_to="recordingMetaCategoryId")
	validator_spec = fields.Dict(dump_to="validatorSpec")
	name = fields.String()
	key = fields.String()

# RecordingMetaValue
class RecordingMetaValue(Base):
	__table__ = t_recording_meta_values

	# column synonyms
	recording_meta_value_id = synonym("recordingMetaValueId")
	recording_meta_category_id = synonym("recordingMetaCategoryId")
	recording_id = synonym("recordingId")


class RecordingMetaValueSchema(Schema):
	recording_meta_value_id = fields.Integer(dump_to="recordingMetaValueId")
	recording_meta_category_id = fields.Integer(dump_to="recordingMetaCategoryId")
	recording_id = fields.Integer(dump_to="recordingId")
	value = fields.Dict()


# RecordingFlag
class RecordingFlag(Base, ModelMixin, FeedbackFlagMixin):
	__table__ = t_recording_flags

	FlagIdAttr = "recordingFlagId"

	# constants
	INFO = "Info"
	WARNING = "Warning"
	SEVERE = "Severe"

	# relationships
	task = relationship("Task", backref="recording_flags")

	# synonyms
	recording_flag_id = synonym("recordingFlagId")
	task_id = synonym("taskId")

	@classmethod
	def check_valid_severity(cls, data, key, value):
		"""
		MyForm validator for checking a valid
		severity.
		"""
		if value not in (cls.INFO, cls.WARNING, cls.SEVERE):
			raise ValueError("{0} is not a valid severity".format(value))

	@classmethod
	def check_new_name_unique(cls, task):
		"""
		Returns a MyForm validator for checking
		that a new recording flag name is unique
		for the task.
		"""
		return cls.check_new_field_unique("name", task=task)

	@validator
	def check_updated_name_unique(self):
		"""
		Returns a MyForm validator for checking
		that an existing recording flag name
		is unique for the task.
		"""
		return self.check_updated_field_unique("name", task=self.task)


class RecordingFlagSchema(Schema):
	recording_flag_id = fields.Integer(dump_to="recordingFlagId")
	flag_id = fields.Integer(dump_to="flagId")
	name = fields.String()
	severity = fields.String()
	enabled = fields.Boolean()


class RecordingFeedbackEntryFlag(Base, ModelMixin):
	__table__ = t_recording_feedback_flags

	# relationships
	flag = relationship("RecordingFlag")
	entry = relationship("RecordingFeedbackEntry", backref=backref("entry_flags", cascade="all, delete-orphan"))


# RecordingFeedbackEntry
class RecordingFeedbackEntry(Base, ModelMixin, FeedbackEntryMixin):
	__table__ = t_recording_feedback

	# relationships
	user = relationship("User")
	change_method = relationship("AudioCheckingChangeMethod")

	# synonyms
	recording_feedback_entry_id = synonym("recordingFeedbackEntryId")
	recording_id = synonym("recordingId")
	user_id = synonym("userId")
	saved_at = synonym("savedAt")

	# mixin config
	EntryFlagModel = RecordingFeedbackEntryFlag


class RecordingFeedbackEntrySchema(Schema):
	recording_feedback_entry_id = fields.Integer(dump_to="recordingFeedbackEntryId")
	recording_id = fields.Integer(dump_to="recordingId")
	comment = fields.String()
	user = fields.Nested("UserSchema")
	flags = fields.Nested("RecordingFlagSchema", many=True)
	change_method = fields.Nested("AudioCheckingChangeMethodSchema", dump_to="changeMethod")
	saved_at = fields.DateTime(dump_to="savedAt")


# Recording
class Recording(Base, ModelMixin, LoadMixin, AddFeedbackMixin):
	__table__ = t_recordings

	# relationships
	recording_platform = relationship("RecordingPlatform", backref="recordings")
	performance = relationship("Performance", backref="recordings")
	corpus_code = relationship("CorpusCode", backref="recordings")
	feedback_entries = relationship("RecordingFeedbackEntry", backref="recording", order_by="RecordingFeedbackEntry.savedAt")

	# synonyms
	recording_id = synonym("recordingId")
	raw_piece_id = synonym("rawPieceId")
	corpus_code_id = synonym("corpusCodeId")
	recording_platform_id = synonym("recordingPlatformId")

	# mixin config
	FeedbackEntryModel = RecordingFeedbackEntry
	FlagModel = RecordingFlag
	SelfRelationshipName = "recording"

	@classmethod
	def from_load(cls, data, performance):
		corpus_code = CorpusCode.query.get(data["corpusCodeId"])

		if corpus_code.recording_platform != performance.recording_platform:
			raise ValueError("Corpus Code {0} does not belong to recording platform {1}".format(
				corpus_code.corpus_code_id,
				performance.recording_platform.record_platform_id
			))

		recording = cls(
			recording_platform=performance.recording_platform,
			performance=performance,
			corpus_code=corpus_code,
			duration=DurationField().deserialize(data["duration"]),
			prompt=data["prompt"],
			hypothesis=data["hypothesis"]
		)

		for audio_file_data in data["audioFiles"]:
			audio_file = AudioFile.from_load(audio_file_data, recording)
			recording.audio_files.append(audio_file)

		return recording

	@property
	def current_feedback(self):
		if self.feedback_entries:
			return self.feedback_entries[-1]	# TODO check ordering

		return None

	@property
	def display_name(self):
		return self.corpus_code.code or "Recording {0}".format(self.recording_id)

	@property
	def task(self):
		return self.performance.task


class RecordingSchema(Schema):
	recording_id = fields.Integer(dump_to="recordingId")
	raw_piece_id = fields.Integer(dump_to="rawPieceId")
	recording_platform_id = fields.Integer(dump_to="recordingPlatformId")
	corpus_code = fields.Nested("CorpusCodeSchema", dump_to="corpusCode")
	prompt = fields.String()
	hypothesis = fields.String()
	duration = DurationField()
	current_feedback = fields.Nested("RecordingFeedbackEntrySchema", dump_to="currentFeedback")
	task = fields.Nested("TaskSchema", only=("taskId", "displayName"))
	recording_platform = fields.Nested("RecordingPlatformSchema", dump_to="recordingPlatform", only=("recordingPlatformId", "display_name"))
	performance = fields.Nested("PerformanceSchema", only=("rawPieceId", "display_name"))
	display_name = fields.String(dump_to="displayName")


# CorpusCode
class CorpusCode(Base, ModelMixin):
	__table__ = t_corpus_codes

	# constants
	NO_CODE = "No Code"
	SCRIPTED = "Scripted"
	SPONTANEOUS = "Spontaneous"

	# relationships
	recording_platform = relationship("RecordingPlatform", backref="corpus_codes")
	audio_checking_group = relationship("AudioCheckingGroup", backref="corpus_codes")

	# synonyms
	corpus_code_id = synonym("corpusCodeId")
	recording_platform_id = synonym("recordingPlatformId")
	is_scripted = synonym("isScripted")
	audio_checking_group_id = synonym("audioCheckingGroupId")

	@property
	def name(self):
		return self.code or self.NO_CODE

	@classmethod
	def check_new_code_unique(cls, recording_platform):
		"""
		Returns a MyForm validator for checking
		that a new code is unique for the recording
		platform.
		"""
		return cls.check_new_field_unique("code", recording_platform=recording_platform)

	@validator
	def check_updated_code_unique(self):
		"""
		Returns a MyForm validator for checking
		that an existing code is unique for the
		recording platform.
		"""
		return self.check_updated_field_unique("code", recording_platform=self.recording_platform)


class CorpusCodeSchema(Schema):
	corpus_code_id = fields.Integer(dump_to="corpusCodeId")
	is_scripted = fields.Boolean(dump_to="isScripted")
	audio_checking_group_id = fields.Integer(dump_to="audioCheckingGroupId")
	name = fields.String()
	code = fields.String()
	included = fields.Boolean()
	regex = fields.String()
	type = fields.Function(lambda obj: CorpusCode.SCRIPTED if obj.is_scripted else CorpusCode.SPONTANEOUS)


# Track
class Track(Base, ModelMixin, GetConstantsMixin):
	__table__ = t_tracks

	# constants
	ACTIVE = "Active"
	MUTED = "Muted"
	DISABLED = "Disabled"

	# relationships
	recording_platform = relationship("RecordingPlatform", backref="tracks")

	# synonyms
	track_id = synonym("trackId")
	recording_platform_id = synonym("recordingPlatformId")
	track_index = synonym("trackIndex")

	@classmethod
	def check_new_index_unique(cls, recording_platform):
		"""
		Returns a MyForm validator for checking
		that a new track index is unique for the
		recording platform.
		"""
		return cls.check_new_field_unique("track_index", recording_platform=recording_platform)

	@validator
	def check_updated_index_unique(self):
		"""
		Returns a MyForm validator for checking
		that an existing track index is unique
		for the recording platform.
		"""
		return self.check_updated_field_unique("track_index", recording_platform=self.recording_platform)

	@classmethod
	def check_new_name_unique(cls, recording_platform):
		"""
		Returns a MyForm validator for checking
		that a new track name is unique for the
		recording platform.
		"""
		return cls.check_new_field_unique("name", recording_platform=recording_platform)

	@validator
	def check_updated_name_unique(self):
		"""
		Returns a MyForm validator for checking
		that an existing track name is unique
		for the recording platform.
		"""
		return self.check_updated_field_unique("name", recording_platform=self.recording_platform)

	@classmethod
	def get_modes(cls):
		return [
			cls.ACTIVE,
			cls.MUTED,
			cls.DISABLED,
		]

	@classmethod
	def is_valid_mode(cls, mode=None, validator=False):
		
		if validator:
			
			def validator_fn(data, key, value):
				if not cls.is_valid_mode(value):
					raise ValueError("not a valid track mode: {0}".format(value))

			return validator_fn

		if mode:
			return mode in cls.get_modes()

		raise RuntimeError

	@property
	def display_name(self):
		return "{0}. {1}".format(self.track_index, self.name)

	@property
	def mode(self):
		if self.muted and self.disabled:
			return self.DISABLED

		if self.muted and not self.disabled:
			return self.MUTED

		if not self.muted and not self.disabled:
			return self.ACTIVE

		return "Unknown"

	def update_mode(self, mode):
	
		if mode == self.ACTIVE:
			self.muted = False
			self.disabled = False

		elif mode == self.MUTED:
			self.muted = True
			self.disabled = False

		elif mode == self.DISABLED:
			self.muted = True
			self.disabled = True

		else:
			raise RuntimeError("unhandled mode: {0}".format(mode))


class TrackSchema(Schema):
	track_id = fields.Integer(dump_to="trackId")
	track_index = fields.Integer(dump_to="trackIndex")
	name = fields.String()
	display_name = fields.String(dump_to="displayName")
	muted = fields.Boolean()
	disabled = fields.Boolean()
	mode = fields.String()


class AudioCheckingGroup(Base):
	__table__ = t_audio_checking_groups

	# relationships
	recording_platform = relationship("RecordingPlatform", backref="audio_checking_groups")

	# synonyms
	audio_checking_group_id = synonym("audioCheckingGroupId")
	recording_platform_id = synonym("recordingPlatformId")
	selection_size = synonym("selectionSize")

	@classmethod
	def check_name_unique(cls, data, key, value, recording_platform):
		"""
		MyForm validator for checking that a new
		group name is unique for the recording platform.
		"""
		if cls.query.filter_by(recording_platform=recording_platform, name=value).count():
			raise ValueError("{0} is already used".format(value))

	def check_other_name_unique(self, data, key, value):
		"""
		MyForm validator for checking that an
		existing group name is unique for the
		recording platform.
		"""
		query = self.query.filter(
			self.__class__.recording_platform_id==self.recording_platform_id,
			self.__class__.name==value,
			self.__class__.audio_checking_group_id!=self.audio_checking_group_id,
		)

		if query.count():
			raise ValueError("{0} is used by another group".format(value))

	def assign_corpus_codes(self, corpus_code_ids):
		"""
		Assigns the given corpus codes to this group.
		"""

		# unassign existing corpus codes
		assigned = CorpusCode.query.filter_by(audio_checking_group_id=self.audio_checking_group_id).all()
		for corpus_code in assigned:
			corpus_code.audio_checking_group_id = None

		# assign new corpus codes
		for corpus_code_id in corpus_code_ids:
			corpus_code = CorpusCode.query.get(corpus_code_id)
			corpus_code.audio_checking_group_id = self.audio_checking_group_id


class AudioCheckingGroupSchema(Schema):
	audio_checking_group_id = fields.Integer(dump_to="audioCheckingGroupId")
	recording_platform_id = fields.Integer(dump_to="recordingPlatformId")
	name = fields.String()
	selection_size = fields.Integer(dump_to="selectionSize")
	corpus_codes = fields.Nested("CorpusCodeSchema", many=True, dump_to="corpusCodes")


# AudioCheckingSection
class AudioCheckingSection(Base):
	__table__ = t_audio_checking_sections

	# relationships
	recording_platform = relationship("RecordingPlatform", backref="audio_checking_sections")

	# synonyms
	audio_checking_section_id = synonym("audioCheckingSectionId")
	recording_platform_id = synonym("recordingPlatformId")
	start_position = synonym("startPosition")
	end_position = synonym("endPosition")
	check_percentage = synonym("checkPercentage")


class AudioCheckingSectionSchema(Schema):
	audio_checking_section_id = fields.Integer(dump_to="audioCheckingSectionId")
	start_position = fields.Float(dump_to="startPosition")
	end_position = fields.Float(dump_to="endPosition")
	check_percentage = fields.Float(dump_to="checkPercentage")


# Transition
class Transition(Base, ModelMixin):
	__table__ = t_transitions

	# relationships
	task = relationship("Task", backref="transitions")
	source = relationship("SubTask", foreign_keys=[t_transitions.c.sourceId], backref="transitions")
	destination = relationship("SubTask", foreign_keys=[t_transitions.c.destinationId])

	# synonyms
	transition_id = synonym("transitionId")
	task_id = synonym("taskId")
	source_id = synonym("sourceId")
	destination_id = synonym("destinationId")

	@classmethod
	def is_valid_transition(cls, source_id, destination_id):
		"""
		Checks that the transition exists.
		"""
		return bool(cls.query.filter_by(
			source_id=source_id,
			destination_id=destination_id,
		).count())


class TransitionSchema(Schema):
	transition_id = fields.Integer(dump_to="transitionId")
	task_id = fields.Integer(dump_to="taskId")
	source = fields.Nested("SubTaskSchema", only=("subTaskId", "name", "workType"))
	destination = fields.Nested("SubTaskSchema", only=("subTaskId", "name", "workType"))


# AudioCheckingChangeMethod
class AudioCheckingChangeMethod(Base, ModelMixin):
	__table__ = t_audio_checking_change_methods

	# constants
	ADMIN = "Admin"
	PERFORMANCE_SEARCH_PAGE = "Performance Search Page"
	WORK_PAGE = "Work Page"

	@classmethod
	def is_valid(cls, data, key, value):
		"""
		MyForm validator for checking that the
		name is valid.
		"""
		if value not in (cls.ADMIN, cls.PERFORMANCE_SEARCH_PAGE, cls.WORK_PAGE):
			raise ValueError("{0} is not a valid change method".format(value))

	@classmethod
	def from_name(cls, name):
		return cls.query.filter_by(name=name).one()


class AudioCheckingChangeMethodSchema(Schema):
	class Meta:
		fields = ("changeMethodId", "name")


# Utterance
class Utterance(RawPiece):
	__table__ = t_utterances

	# relationships
	raw_piece = relationship("RawPiece")

	# synonyms
	raw_piece_id = synonym("rawPieceId")

	__mapper_args__ = {
		"polymorphic_identity": "utterance",
	}

	@classmethod
	def from_load(cls, data, task, load):
		"""
		Creates a new utterance during audio
		load.
		"""

		stored_data = data.get("data", {})
		stored_data.update({
			"audioSpec": data["audioSpec"],
			"audioDataPointer": data["audioDataPointer"],
			"filePath": data["filePath"],
		})

		# TODO shouldnt be required
		assembly_context_parts = [data["filePath"]]

		if "startAt" in data and data["startAt"] is not None:
			stored_data["startAt"] = data["startAt"]
			assembly_context_parts.append("from_%.3f" %data["startAt"])

		if "endAt" in data and data["endAt"] is not None:
			stored_data["endAt"] = data["endAt"]
			assembly_context_parts.append("to_%.3f" %data["endAt"])

		# create utterance
		utt = cls(
			task=task,
			load_id=load.load_id,
			assembly_context="_".join(assembly_context_parts),
			data=stored_data,
			hypothesis=data.get("hypothesis"),
			words=1,
		)

		return utt

	@property
	def audio_url(self):
		"""
		Returns the audio URL for the utterance.
		"""
		from app import audio_server
		audio_spec = self.data["audioSpec"]
		audio_data_pointer = self.data["audioDataPointer"]
		file_path = self.data["filePath"]
		start_at = self.data.get("startAt", None)
		end_at = self.data.get("endAt", None)

		if start_at is not None:
			start_at = datetime.timedelta(seconds=start_at)

		if end_at is not None:
			end_at = datetime.timedelta(seconds=end_at)

		url = audio_server.api.get_ogg_url(audio_spec, audio_data_pointer, file_path, start_at=start_at, end_at=end_at)
		return url


# PerformanceTransitionLogEntry
class PerformanceTransitionLogEntry(Base, ModelMixin):
	__table__ = t_performance_transition_log

	# relationships
	performance = relationship("Performance", backref="transition_log_entries")
	source = relationship("SubTask", foreign_keys=[t_performance_transition_log.c.sourceId])
	destination = relationship("SubTask", foreign_keys=[t_performance_transition_log.c.destinationId])
	user = relationship("User")
	change_method = relationship("AudioCheckingChangeMethod")

	# synonyms
	log_entry_id = synonym("logEntryId")
	raw_piece_id = synonym("rawPieceId")
	source_id = synonym("sourceId")
	destination_id = synonym("destinationId")
	user_id = synonym("userId")
	change_method_id = synonym("changeMethodId")
	moved_at = synonym("movedAt")

class PerformanceTransitionLogEntrySchema(Schema):
	log_entry_id = fields.Integer(dump_to="logEntryId")
	raw_piece_id = fields.Integer(dump_to="rawPieceId")
	source = fields.Nested("SubTaskSchema", only=("subTaskId", "name"))
	destination = fields.Nested("SubTaskSchema", only=("subTaskId", "name"))
	user = fields.Nested("UserSchema", only=("userId", "userName", "emailAddress"))
	change_method = fields.Nested("AudioCheckingChangeMethodSchema", dump_to="changeMethod")
	moved_at = fields.DateTime(dump_to="movedAt")


# MetadataChangeLogEntry
class MetadataChangeLogEntry(Base, ModelMixin):
	__table__ = t_metadata_change_log

	# constants
	TYPES = {
		"performance": Performance,
	}

	# relationships
	task = relationship("Task")
	change_method = relationship("AudioCheckingChangeMethod")
	changer = relationship("User")

	# synonyms
	log_entry_id = synonym("logEntryId")
	task_id = synonym("taskId")
	change_method_id = synonym("changeMethodId")
	changed_by = synonym("changedBy")
	changed_at = synonym("changedAt")

	@classmethod
	def get_type(cls, model):
		"""
		Returns the type string for
		the given model.
		"""
		for type, entity_cls in cls.TYPES.items():
			if isinstance(model, entity_cls):
				return type

		raise RuntimeError("unknown meta entity: {0}".format(model))

	@classmethod
	def get_entity_cls(cls, type):
		"""
		Returns the model cls from
		the type string.
		"""

		if type not in cls.TYPES:
			raise RuntimeError("unknown meta entity type: {0}".format(type))

		return cls.TYPES[type]

class MetadataChangeLogEntrySchema(Schema):
	log_entry_id = fields.Integer(dump_to="logEntryId")
	change_method = fields.Nested("AudioCheckingChangeMethodSchema", dump_to="changeMethod")
	changer = fields.Nested("UserSchema", only=("userId", "userName", "emailAddress"))
	changed_at = fields.DateTime(dump_to="changedAt")
	old_value = fields.Method("get_old_value", dump_to="oldValue")
	new_value = fields.Method("get_new_value", dump_to="newValue")
	meta_category = fields.Method("get_meta_category", dump_to="metaCategory")

	def get_old_value(self, obj):
		return obj.info["oldValue"]

	def get_new_value(self, obj):
		return obj.info["newValue"]

	def get_meta_category(self, obj):
		type = obj.info["type"]
		meta_entity_cls = obj.get_entity_cls(type)
		meta_category = meta_entity_cls.MetaCategoryModel.query.get(obj.info["categoryId"])
		return meta_category.serialize()


# ApiAccessPair
class ApiAccessPair(Base, ModelMixin):
	__table__ = t_api_access_pairs

	# relationships
	user = relationship("User")

	# synonyms
	api_access_pair_id = synonym("apiAccessPairId")
	user_id = synonym("userId")
	created_at = synonym("createdAt")

	@classmethod
	def is_unique(cls, key, secret):
		"""
		Checks if the key/secret combination
		is unique.
		"""
		query = cls.query.filter_by(key=key, secret=secret)
		return not bool(query.count())

	@classmethod
	def create(cls, user_id, description):
		"""
		Creates a new, unique, access pair.
		"""

		key = None
		secret = None

		# get unique pair
		while True:
			key = random_key_string(30)
			secret = random_key_string(30)
			if cls.is_unique(key, secret):
				break

		return cls(
			key=key,
			secret=secret,
			description=description,
			user_id=user_id,
		)

class ApiAccessPairSchema(Schema):
	api_access_pair_id = fields.Integer(dump_to="apiAccessPairId")
	key = fields.String()
	secret = fields.String()
	description = fields.String()
	user = fields.Nested("UserSchema", only=("userId", "userName", "emailAddress"))
	enabled = fields.Boolean()
	enabled_at = fields.DateTime()


# AudioStatsType
class AudioStatsType(Base, ModelMixin):
	__table__ = t_audio_stats_types

class AudioStatsTypeSchema(Schema):
	audio_stats_type_id = fields.Integer(dump_to="audioStatsTypeId")
	key = fields.String()
	name = fields.String()
	description = fields.String()
	is_default = fields.Boolean(dump_to="isDefault")


# AudioSandbox
class AudioSandbox(Base, ModelMixin):
	__table__ = t_audio_sandboxes

	# relationships
	user = relationship("User")

	@classmethod
	def check_new_name_unique(cls):
		"""
		Returns a MyForm validator for checking
		that a new sandbox name is unique.
		"""
		return cls.check_new_field_unique("name")

	@property
	def display_name(self):
		return self.name


class AudioSandboxSchema(Schema):
	audio_sandbox_id = fields.Integer(dump_to="audioSandboxId")
	name = fields.String()
	display_name = fields.String(dump_to="displayName")
	user = fields.Nested("UserSchema", only=("userId", "userName", "emailAddress"))
	created_at = fields.DateTime(dump_to="createdAt")


# AudioSandboxFile
class AudioSandboxFile(Base, ModelMixin):
	__table__ = t_audio_sandbox_files

	# relationships
	audio_sandbox = db.relationship("AudioSandbox", backref="files")

	@property
	def display_name(self):
		return "File {0}".format(self.audio_sandbox_file_id)

	@property
	def duration(self):
		return self.audio_spec_obj.get_duration(self.audio_data_pointer_obj.size)

	@property
	def audio_spec_obj(self):
		return AudioSpec(**self.audio_spec)

	@property
	def audio_data_pointer_obj(self):
		return AudioDataPointer(**self.audio_data_pointer)


class AudioSandboxFileSchema(Schema):
	audio_sandbox_file_id = fields.Integer(dump_to="audioSandboxFileId")
	display_name = fields.String(dump_to="displayName")
	file_path = fields.String(dump_to="filePath")
	audio_spec = fields.Dict(dump_to="audioSpec")
	audio_data_pointer = fields.Dict(dump_to="audioDataPointer")
	audio_sandbox = fields.Nested("AudioSandboxSchema", dump_to="audioSandbox", only=("audio_sandbox_id", "display_name"))
	data = fields.Dict()
	is_wav = fields.Boolean(dump_to="isWav")
	duration = DurationField()


class BatchRouter(Base, ModelMixin):
	__table__ = t_batch_router

	# relationships
	task = relationship("Task", backref="batch_routers")

	def add_sub_task_criteria(self, sub_task_id, criteria):
		sub_task = BatchRouterSubTask(
			sub_task_id=sub_task_id,
			criteria=criteria
		)
		self.sub_tasks.append(sub_task)

	def get_routed_sub_task(self, key):
		"""
		Given the batch key, return the destination
		sub task given the routing criteria
		"""
		
		# only works for linked loaders for now
		assert self.task.loader and self.task.loader["name"] == "Linked"

		# get session model
		session = Performance.query.get(key)

		for sub_task in self.sub_tasks:
			if self.is_match(session, sub_task.criteria):
				return sub_task.sub_task

		raise ValueError("session could not be routed to any sub task: {0}".format(session.raw_piece_id))

	def update_sub_task_criteria(self, data):
	
		def get_sub_task_id(key):
			match = re.match("^s(?P<subTaskId>\d+)$", key)
			sub_task_id = match.groupdict()["subTaskId"]
			return int(sub_task_id)
	
		for key, criteria in data.items():
			sub_task_id = get_sub_task_id(key)
			self.add_sub_task_criteria(sub_task_id, criteria)

	@classmethod
	def is_match(cls, session, criteria):
		
		if not criteria:
			return False

		for type, sub_criteria in criteria.items():
			
			if type == "metadataRestrictions":
				if cls.validate_metadata_restrictions(session, sub_criteria):
					return True

		return False

	@staticmethod
	def validate_metadata_restrictions(session, criteria):
		
		for category_key, criteria_values in criteria.items():

			if not criteria_values:
				continue

			criteria_values = criteria_values.values()
			category_id = int(category_key.lstrip("c"))
			meta_category = PerformanceMetaCategory.query.get(category_id)
			meta_value = session.get_meta_value(meta_category.performance_meta_category_id)

			if not meta_value:
				return False

			if not meta_value.satisfies(criteria_values):
				return False

		return True


class BatchRouterSchema(Schema):
	batch_router_id = fields.Integer(dump_to="batchRouterId")
	name = fields.String()
	task_id = fields.Integer(dump_to="taskId")
	enabled = fields.Boolean()
	sub_tasks = fields.Nested("BatchRouterSubTaskSchema", dump_to="subTasks", many=True)


class BatchRouterSubTask(Base, ModelMixin):
	__table__ = t_batch_router_sub_task

	# relationships
	router = relationship("BatchRouter", backref=backref("sub_tasks", cascade="all, delete-orphan"))
	sub_task = relationship("SubTask")


class BatchRouterSubTaskSchema(Schema):
	batch_router_sub_task_id = fields.Integer(dump_to="batchRouterSubTaskId")
	batch_router_id = fields.Integer(dump_to="batchRouterId")
	sub_task = fields.Nested("SubTaskSchema", only=("subTaskId", "workType", "name"), dump_to="subTask")
	criteria = fields.Dict()


#
# Define model class and its schema (if needed) above
#

__all__ = list(set(locals().keys()) - _names)

for schema_name in [i for i in __all__ if i.endswith('Schema')]:
	klass_name = schema_name[:-6]
	if klass_name.find('_') >= 0:
		klass_name, schema_key = klass_name.split('_', 1)
		schema_key = schema_key.lower()
	else:
		schema_key = ''
	assert klass_name
	klass = locals()[klass_name]
	schema = locals()[schema_name]
	klass.set_schema(schema, schema_key or None)
