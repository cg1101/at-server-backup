#!/usr/bin/env python

import logging
import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, backref, synonym, deferred, column_property, object_session
from sqlalchemy.sql import case, text, func
from marshmallow import Schema, fields
import pytz

from . import database, mode
from .db import SS
from lib import DurationField, utcnow
from lib.metadata_validation import process_received_metadata, resolve_new_metadata
from schema import *

log = logging.getLogger(__name__)


# model mixin classes

class ImportMixin:
	"""
	Adds extra functionality for models created
	during audio import.
	"""

	@classmethod
	def from_import(cls, data, *args, **kwargs):
		"""
		Parses the validated import data and returns
		the created model.
		"""
		raise NotImplementedError


class MetaCategoryMixin:
	"""
	Adds extra functionality for metadata categories.
	"""

	@property
	def meta_category_id(self):
		"""
		An alias for the category ID.
		"""
		raise NotImplementedError


class MetaEntityMixin:
	"""
	Adds extra functionality for models that store metadata.
	"""

	# the corresponding meta value model class
	MetaValueModel = None
	
	@property
	def meta_values(self):
		"""
		An SQLAlchemy relationship to the meta values.
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

	def add_meta_change_request(self, meta_category, new_value):
		"""
		Adds a new meta value change request.
		"""
		raise NotImplementedError


class MetaValueMixin:
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


def set_schema(cls, schema_class):
	if not issubclass(schema_class, Schema):
		raise TypeError('schema must be subclass of Schema')
	cls._schema_class = schema_class


def dump(cls, obj, extra=None, only=(), exclude=(), prefix=u'',
		strict=False, context=None, load_only=(), **kwargs):
	if cls._schema_class is None:
		raise RuntimeError('schema class not found for {0}'\
			.format(cls.__name__))
	s = cls._schema_class(extra=extra, only=only, exclude=exclude,
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

Base._schema_class = None
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
class WorkType(Base):
	WORK = 'Work'
	QA = 'QA'
	REWORK = 'Rework'
	SECOND_PASS_WORK = '2ndPass_work'
	SECOND_PASS_REWORK = '2ndPass_rework'
	__table__ = t_worktypes

class WorkTypeSchema(Schema):
	class Meta:
		fields = ('workTypeId', 'name', 'description', 'modifiesTranscription')

# Batch
class Batch(Base):
	__table__ = t_batches
	user = relationship('User', foreign_keys=[t_batches.c.userId])
	userName = association_proxy('user', 'userName')
	pages = relationship('Page', order_by='Page.pageIndex',
		cascade='all, delete-orphan')
	task = relationship('Task')
	subTask = relationship('SubTask')

	@property
	def isExpired(self):
		if self.leaseExpires is None:
			return False
		else:
			return self.leaseExpires <= datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

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

	def expire(self):
		"""
		Expires the lease on the batch.
		"""
		if self.userId:
			log.debug("revoking batch {0}, owned by {1}".format(self.batchId, self.userId))
			self.log_event("revoked")
			self.reset_ownership()
			self.increase_priority()

		else:
			log.debug("batch {0} is not owned by anyone".format(self.batchId))

	def reset_ownership(self):
		"""
		Resets the ownership of the batch.
		"""
		self.userId = None
		self.leaseGranted = None
		self.leaseExpires = None
		self.checkedOut = False

	def increase_priority(self, increase_by=1):
		"""
		Increases the batch priority.
		"""
		self.priority += increase_by

	def log_event(self, event):
		"""
		Adds an event to the batch log.
		"""
		query = t_batchhistory.insert({
			"batchId": self.batchId,
			"userId": self.userId,
			"event": event,
		})
		SS.execute(query)


class BatchSchema(Schema):
	user = fields.Method('get_user')
	def get_user(self, obj):
		s = UserSchema(only=['userId', 'userName'])
		return s.dump(obj.user).data if obj.user else None
	pages = fields.Nested('PageSchema', many=True)
	class Meta:
		fields = ('batchId', 'taskId', 'subTaskId', 'userId', 'userName', 'user', 'priority', 'onHold', 'leaseGranted', 'leaseExpires', 'notUserId', 'workIntervalId', 'checkedOut', 'pages')
		# ordered = True

# BathchingMode
class BatchingMode(Base):
	NONE = 'None'
	SESSION = 'Session'
	RECORDING = 'Recording'
	LONG_RECORDING = 'Long Recordings'
	CUSTOM_CONTEXT = 'Custom Context'
	ALLOCATION_CONTEXT = 'Allocation Context'
	__table__ = t_batchingmodes

class BatchingModeSchema(Schema):
	class Meta:
		fields = ('modeId', 'name', 'description', 'requiresContext')
		ordered = True

# CalculatedPayment
class CalculatedPayment(Base):
	__table__ = t_calculatedpayments
	user = relationship('User')
	userName = association_proxy('user', 'userName')

class CalculatedPaymentSchema(Schema):
	class Meta:
		fields = ('calculatedPaymentId', 'payrollId', 'workIntervalId', 'userId', 'userName', 'taskId', 'subTaskId', 'itemCount', 'unitCount', 'qaedItemCount', 'qaedUnitCount', 'accuracy', 'originalAmount', 'amount', 'receipt', 'updated')
		ordered = True
		# skip_missing = True

# CustomUtteranceGroup
class CustomUtteranceGroup(Base):
	__table__ = t_customutterancegroups
	_members = relationship('CustomUtteranceGroupMember', cascade='all, delete-orphan')
	rawPieces = association_proxy('_members', 'rawPiece')
	selection = relationship('UtteranceSelection')

class CustomUtteranceGroupSchema(Schema):
	rawPieces = fields.Nested('RawPieceSchema', many=True)
	class Meta:
		fields = ('groupId', 'name', 'taskId', 'created', 'utterances', 'selectionId')
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
		fields = ('labelId', 'name', 'description', 'shortcutKey', 'extract', 'labelGroupId', 'labelSetId')
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

# Load
class Load(Base):
	__table__ = t_loads
	rawPieces = relationship('RawPiece', order_by='RawPiece.rawPieceId', viewonly=True)
	_createdByUser = relationship('User')

class LoadSchema(Schema):
	createdBy = fields.Method('get_created_by')
	def get_created_by(self, obj):
		s = UserSchema(only=['userId', 'userName'])
		return s.dump(obj._createdByUser).data
	class Meta:
		fields = ('loadId', 'createdBy', 'createdAt', 'taskId')

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
		cascade='all, delete-orphan'
		)
	memberEntries = relationship('PageMemberEntry', cascade='all, delete-orphan')

class PageSchema(Schema):
	members = fields.Method('get_members')
	def get_members(self, obj):
		_sd = {
			WorkType.WORK: WorkTypePageMemberSchema(),
			WorkType.QA: QaTypePageMemberSchema(),
			WorkType.REWORK: ReworkTypePageMemberSchema(),
		}
		result = []
		for m in obj.members:
			s = _sd[m.workType]
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
	batch = relationship('Batch', primaryjoin='PageMember.batchId==Batch.batchId', foreign_keys='Batch.batchId', uselist=False)

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
	rawPiece = fields.Nested('RawPieceSchema', only=['rawPieceId', 'rawText', 'hypothesis', 'words'])
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
		if self.batch.task.taskType == TaskType.TRANSLATION and s.lookAhead > 0:
			rs = RawPiece.query.filter(
				(RawPiece.taskId==s.taskId) &
				(RawPiece.allocationContext==self.rawPiece.allocationContext) &
				(RawPiece.rawPieceId > self.rawPiece.rawPieceId)
			).order_by(RawPiece.rawPieceId).all()[:s.lookAhead]
		else:
			rs = []
		return rs
	def _get_look_behind(self):
		s = self.batch.subTask
		if self.batch.task.taskType == TaskType.TRANSLATION and s.lookBehind > 0:
			rs = RawPiece.query.filter(
				(RawPiece.taskId==s.taskId) &
				(RawPiece.allocationContext==self.rawPiece.allocationContext) &
				(RawPiece.rawPieceId < self.rawPiece.rawPieceId)
			).order_by(RawPiece.rawPieceId.desc()).all()[:s.lookBehind]
		else:
			rs = []
		return reversed(rs)
	saved = property(_get_saved)
	lookAhead = property(_get_look_ahead)
	lookBehind = property(_get_look_behind)

class QaTypePageMemberSchema(PageMemberSchema):
	rawPiece = fields.Nested('RawPieceSchema', only=['rawPieceId', 'rawText', 'hypothesis', 'words'])
	qaedEntry = fields.Method('get_qaed_entry')
	saved = fields.Method('get_saved')
	lookAhead = fields.Nested('RawPieceSchema', many=True, only=['rawPieceId', 'rawText'])
	lookBehind = fields.Nested('RawPieceSchema', many=True, only=['rawPieceId', 'rawText'])
	def get_qaed_entry(self, obj):
		s = WorkEntrySchema()
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
			).filter((WorkEntry.rawPieceId==self.rawPieceId) & WorkEntry.modifiesTranscription &(WorkEntry.batchId!=self.batchId)
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
	latestEdition = property(_get_latest_edition)
	saved = property(_get_saved)

class ReworkTypePageMemberSchema(PageMemberSchema):
	rawPiece = fields.Nested('RawPieceSchema', only=['rawPieceId', 'rawText', 'hypothesis', 'words'])
	saved = fields.Method('get_saved')
	latestEdition = fields.Method('get_latest_edition')
	def get_saved(self, obj):
		if obj.saved == None:
			return None
		assert obj.saved.workType == WorkType.REWORK
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
	class Meta:
		additional = ('rawPiece', 'latestEdition', 'saved')
		ordered = True
		# skip_missing = True

# # PaymentClass

# PaymentType
class PaymentType(Base):
	__table__ = t_ao_payment_types

class PaymentTypeSchema(Schema):
	class Meta:
		fields = ('paymentTypeId', 'name', 'created')

# Payroll
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
class RawPiece(Base):
	__table__ = t_rawpieces

class RawPieceSchema(Schema):
	class Meta:
		fields = ('rawPieceId', 'taskId', 'rawText', 'assemblyContext', 'allocationContext', 'hypothesis', 'words')
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

# SubTask
class SubTask(Base):
	POLICY_NO_LIMIT = 'nolimit'
	POLICY_ONE_ONLY = 'oneonly'
	__table__ = t_subtasks
	task = relationship('Task')
	taskTypeId = association_proxy('task', 'taskTypeId')
	taskType = association_proxy('task', 'taskType')
	_batchingMode = relationship('BatchingMode')
	batchingMode = association_proxy('_batchingMode', 'name')
	_workType = relationship('WorkType')
	workType = association_proxy('_workType', 'name')
	qaConfig = relationship('QaConfig', primaryjoin='SubTask.subTaskId==QaConfig.workSubTaskId',
		uselist=False)
	@property
	def currentRate(self):
		return SubTaskRate.query.filter_by(subTaskId=self.subTaskId
			).filter(SubTaskRate.validFrom<=func.now()
			).order_by(SubTaskRate.validFrom.desc()
			).first()

class SubTaskSchema(Schema):
	class Meta:
		fields = ('subTaskId', 'name',
			'workTypeId', 'workType',
			'taskId', 'taskTypeId', 'taskType',
			'maxPageSize', 'dstDir', 'modeId',
			'defaultLeaseLife',
			'getPolicy', 'expiryPolicy',
			'allowPageSkip', 'allowEditing', 'allowAbandon', 'allowCheckout',
			'lookAhead', 'lookBehind',
			'instructionPage', 'useQaHistory',
			'isSecondPassQa', 'needDynamicTagSet')
		ordered = True
		# skip_missing = True

# SubTaskContentEvent
class SubTaskContentEvent(Base):
	__table__ = t_reworkcontenthistory
	amount = synonym('itemCount')
	populating = synonym('isAdding')

class SubTaskContentEventSchema(Schema):
	class Meta:
		fields = ('subTaskId', 'selectionId', 'itemCount', 'isAdding', 'tProcessedAt', 'operator')
		ordered = True

# SubTaskMetric
class SubTaskMetric(Base):
	__table__ = t_subtaskmetrics

class SubTaskMetricSchema(Schema):
	class Meta:
		fields = ('metricId', 'userId', 'workIntervalId', 'subTaskId', 'itemCount',
			'unitCount', 'workRate', 'accuracy', 'lastUpdated')
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
		fields = ('subTaskRateId', 'subTaskId', 'taskId', 'rateId', 'rateName', 'standardValue', 'targetAccuracy', 'validFrom', 'multiplier', 'updatedBy', 'updatedAt')
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
	pass

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

class FootnoteTagSchema(TagSchema):
	pass

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


# Task
class Task(Base):
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
	@property
	def displayName(self):
		return '{0} - {1}'.format(self.taskId, self.name)

class TaskSchema(Schema):
	tagSet = fields.Nested('TagSetSchema')
	labelSet = fields.Nested('LabelSetSchema')
	migratedBy = fields.Method('get_migrated_by')
	def get_migrated_by(self, obj):
		s = UserSchema(only=['userId', 'userName'])
		return s.dump(obj._migratedByUser).data
	class Meta:
		fields = ('taskId', 'name', 'projectId', 'taskTypeId', 'taskType', 'status', 'srcDir', 'lastStatusChange', 'tagSetId', 'labelSetId', 'migrated', 'migratedBy')
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

class TaskSupervisorSchema(Schema):
	class Meta:
		fields = ('taskId', 'userId', 'userName', 'receivesFeedback', 'informLoads')
		ordered = True

# TaskType
class TaskType(Base):
	TRANSLATION = 'translation'
	TEXT_COLLECTION = 'text collection'
	MARUP = 'markup'
	__table__ = t_tasktypes

class TaskTypeSchema(Schema):
	class Meta:
		fields = ('taskTypeId', 'name', 'description')

# TaskWorker
class TaskWorker(Base):
	__table__ = t_taskusers
	user = relationship('User')
	userName = association_proxy('user', 'userName')

class TaskWorkerSchema(Schema):
	class Meta:
		fields = ('taskId', 'subTaskId', 'userId', 'userName', 'isNew', 'removed', 'paymentFactor', 'hasReadInstructions')
		ordered = True

# TrackingEvent
class TrackingEvent(Base):
	__table__ = t_tracking_events

class TrackingEventSchema(Schema):
	class Meta:
		fields = ('eventId', 'eventType', 'tTriggeredAt', 'hostIp', 'details')

# User
class User(Base):
	__table__ = j_users
	userId = column_property(t_users.c.userId, t_ao_users.c.userId)
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

# UtteranceSelection
class UtteranceSelection(Base):
	ACTION_BATCH = 'batch'
	ACTION_CUSTOM = 'custom'
	ACTION_PP = 'pp'
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
	__table__ = j_workentries
	__mapper_args__ = {
		'polymorphic_on': j_workentries.c.workType,
		'polymorphic_identity': 'generic',
	}
	user = relationship('User')
	userName = association_proxy('user', 'userName')
	rawPiece = relationship('RawPiece')

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

# RecordingPlatformType
class RecordingPlatformType(Base):
	__table__ = t_recording_platform_types

	# constants
	UNSPECIFIED = "Unspecified"
	SONY_MOBILE_RECORDER = "Sony Mobile Recorder"
	APPEN_MOBILE_RECORDER = "Appen Mobile Recorder"

	# column synonyms
	recording_platform_id = synonym("recordingPlatformId")


class RecordingPlatformTypeSerialiser(Schema):
	class Meta:
		fields = ("recordingPlatformTypeId", "name")


# RecordingPlatform
class RecordingPlatform(Base):
	__table__ = t_recording_platforms

	# relationships
	audio_collection = relationship("AudioCollection", backref="recording_platforms")
	audio_importer = relationship("AudioImporter")

	# synonyms
	recording_platform_id = synonym("recordingPlatformId")
	audio_collection_id = synonym("audioCollectionId")
	audio_importer_id = synonym("audioImporterId")
	recording_platform_id = synonym("recordingPlatformId")
	storage_location = synonym("storageLocation")

	@property
	def importable_performance_meta_categories(self):
		"""
		Meta categories that are populated during audio import.
		"""
		return [meta_category for meta_category in self.performance_meta_categories if meta_category.extractor]


class RecordingPlatformSchema(Schema):
	audioImporter = fields.Nested("AudioImporterSchema", attribute="audio_importer")
	class Meta:
		additional = ("recordingPlatformId", "storageLocation", "index", "name", "masterHypothesisFile", "masterScriptFile", "config")

# AudioCollectionStatusLog
class AudioCollectionStatusLog(Base):
	__table__ = t_audio_collection_status_log

	# column synonyms
	log_entry_id = synonym("logEntryId")
	audio_collection_id = synonym("audioCollectionId")
	from_audio_collection_status_id = synonym("fromAudioCollectionStatusId")
	to_audio_collection_status_id = synonym("toAudioCollectionStatusId")
	changed_by = synonym("changedBy")
	changed_at = synonym("changedAt")


class AudioCollectionStatusLogSchema(Schema):
	class Meta:
		fields = ("logEntryId", "audioCollectionId", "fromAudioCollectionStatusId", "toAudioCollectionStatusId", "changedBy", "changedAt")

# AudioCollectionStatus
class AudioCollectionStatus(Base):
	__table__ = t_audio_collection_statuses

	# constants
	OPEN = "Open"
	CLOSED = "Closed"
	ARCHIVED = "Archived"

	# synonyms
	audio_collection_status_id = synonym("audioCollectionStatusId")


class AudioCollectionStatusSchema(Schema):
	class Meta:
		fields = ("audioCollectionStatusId", "name")

# AudioCollectionSupervisor
class AudioCollectionSupervisor(Base):
	__table__ = t_audio_collection_supervisors

	# column synonyms
	audio_collection_id = synonym("audioCollectionId")
	user_id = synonym("userId")


class AudioCollectionSupervisorSchema(Schema):
	class Meta:
		fields = ("audioCollectionId", "userId")

# AudioCollection
class AudioCollection(Base):
	__table__ = t_audio_collections

	# relationships
	project = relationship("Project", backref="audio_collections")

	# synonyms
	audio_collection_id = synonym("audioCollectionId")
	project_id = synonym("projectId")
	audio_collection_status_id = synonym("audioCollectionStatusId")
	archive_file = synonym("archiveFile")

	@property
	def importable(self):
		return bool(self.importable_recording_platforms)

	@property
	def importable_recording_platforms(self):
		return [rp for rp in self.recording_platforms if rp.audio_importer]


class AudioCollectionSchema(Schema):
	class Meta:
		fields = ("audioCollectionId", "projectId", "name", "key", "config", "audioCollectionStatusId", "defaultAudioSpec", "masterScriptFile", "masterHypothesisFile", "archiveFile")

# AudioFile
class AudioFile(Base, ImportMixin):
	__table__ = t_audio_files

	# relationships
	recording = relationship("Recording", backref="audio_files")
	track = relationship("Track")
	audio_collection = relationship("AudioCollection", backref="audio_files")
	recording_platform = relationship("RecordingPlatform", backref="audio_files")

	# synonyms
	audio_file_id = synonym("audioFileId")
	recording_id = synonym("recordingId")
	audio_collection_id = synonym("audioCollectionId")
	recording_platform_id = synonym("recordingPlatformId")
	track_id = synonym("trackId")
	file_path = synonym("filePath")
	audio_spec = synonym("audioSpec")
	audio_data_location = synonym("audioDataLocation")

	@classmethod
	def from_import(cls, data, recording):
		track = Track.query.get(data["trackId"])

		if track.recording_platform != recording.recording_platform:
			raise ValueError("Track {0} does not belong to recording platform {1}".format(track.track_id, recording.recording_platform.recording_platform_id))

		audio_file = AudioFile(
			recording=recording,
			audio_collection=recording.audio_collection,
			recording_platform=recording.recording_platform,
			track=track,
			file_path=data["filePath"],
			audio_spec=data["audioSpec"],
			audio_data_location=data["audioDataLocation"],
			duration=DurationField().deserialize(data["duration"]),
			stats=data["stats"]
		)

		return audio_file


class AudioFileSchema(Schema):
	class Meta:
		fields = ("audioFileId", "recordingId", "trackId", "filePath", "audioSpec", "audioDataLocation", "duration", "stats")

# AudioImporter
class AudioImporter(Base):
	__table__ = t_audio_importers

	# constants
	UNSTRUCTURED = "Unstructured"
	STANDARD = "Standard"
	AMR_SCRIPTED = "Appen Mobile Recorder - Scripted"
	AMR_CONVERSATIONAL = "Appen Mobile Recorder - Conversational"
	APPEN_TELEPHONY_SCRIPTED = "Appen Telephony - Scripted"
	APPEN_TELEPHONY_CONVERSATIONAL = "Appen Telephony - Conversational"

	# synonyms
	audio_importer_id = synonym("audioImporterId")
	all_performances_incomplete = synonym("allPerformancesIncomplete")


class AudioImporterSchema(Schema):
	class Meta:
		fields = ("audioImporterId", "name")

# SpeakerMetaCategory
class SpeakerMetaCategory(Base):
	__table__ = t_speaker_meta_categories

	# column synonyms
	speaker_meta_category_id = synonym("speakerMetaCategoryId")
	audio_collection_id = synonym("audioCollectionId")


class SpeakerMetaCategorySchema(Schema):
	class Meta:
		fields = ("speakerMetaCategoryId", "audioCollectionId", "name", "key", "validator")

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
	audio_collection_id = synonym("audioCollectionId")


class SpeakerSchema(Schema):
	class Meta:
		fields = ("speakerId", "audioCollectionId", "identifier")

# AlbumMetaCategory
class AlbumMetaCategory(Base):
	__table__ = t_album_meta_categories

	# column synonyms
	album_meta_category_id = synonym("albumMetaCategoryId")
	audio_collection_id = synonym("audioCollectionId")


class AlbumMetaCategorySchema(Schema):
	class Meta:
		fields = ("albumMetaCategoryId", "audioCollectionId", "name", "key", "validator")

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

	# synonyms
	album_id = synonym("albumId")
	audio_collection_id = synonym("audioCollectionId")
	speaker_id = synonym("speakerId")


class AlbumSchema(Schema):
	class Meta:
		fields = ("albumId", "audioCollectionId", "speakerId")

# PerformanceMetaCategory
class PerformanceMetaCategory(Base, MetaCategoryMixin):
	__table__ = t_performance_meta_categories

	# relationships
	recording_platform = relationship("RecordingPlatform", backref="performance_meta_categories")

	# synonyms
	performance_meta_category_id = synonym("performanceMetaCategoryId")
	audio_collection_id = synonym("audioCollectionId")

	@property
	def meta_category_id(self):
		return self.performance_meta_category_id


class PerformanceMetaCategorySchema(Schema):
	class Meta:
		fields = ("performanceMetaCategoryId", "name", "extractor", "validator")

# PerformanceMetaValue
class PerformanceMetaValue(Base, MetaValueMixin):
	__table__ = t_performance_meta_values

	# relationships
	meta_entity = relationship("Performance", backref="meta_values")
	meta_category = relationship("PerformanceMetaCategory")

	# synonyms
	performance_meta_value_id = synonym("performanceMetaValueId")
	performance_meta_category_id = synonym("performanceMetaCategoryId")
	performance_id = synonym("performanceId")


class PerformanceMetaValueSchema(Schema):
	class Meta:
		fields = ("performanceMetaValueId", "performanceMetaCategoryId", "performanceId", "value")

# Performance
class Performance(Base, ImportMixin, MetaEntityMixin):
	__table__ = t_performances

	# relationships
	album = relationship("Album", backref="performances")
	audio_collection = relationship("AudioCollection", backref="performances")
	recording_platform = relationship("RecordingPlatform", backref="performances")

	# synonyms
	performance_id = synonym("performanceId")
	audio_collection_id = synonym("audioCollectionId")
	album_id = synonym("albumId")
	recording_platform_id = synonym("recordingPlatformId")
	script_id = synonym("scriptId")
	imported_at = synonym("importedAt")

	MetaValueModel = PerformanceMetaValue

	@property
	def incomplete(self):
		"""
		Placeholder for audio importing. To be
		replaced when queue functionality and 
		incomplete performance importing is 
		added.
		"""
		return False  # FIXME

	@classmethod
	def from_import(cls, data, recording_platform):

		# if adding new data to an existing performance
		if data["performanceId"]:
			performance = cls.query.get(data["performanceId"])

			if performance.recording_platform != recording_platform:
				raise ValueError("Performance {0} does not belong to recording platform {1}".format(performance.performance_id, recording_platform.record_platform_id))

		# adding a new performance
		else:
			performance = cls(
				audio_collection=recording_platform.audio_collection,
				recording_platform=recording_platform,
				name=data["name"],
				script_id=data["scriptId"],
				imported_at=utcnow()
			)

			meta_values = process_received_metadata(data["metadata"], recording_platform.performance_meta_categories)
			resolve_new_metadata(performance, meta_values)

		# add new recordings
		for recording_data in data["recordings"]:
			recording = Recording.from_import(recording_data, performance)
			performance.recordings.append(recording)
		
		return performance


class PerformanceSchema(Schema):
	class Meta:
		fields = ("performanceId", "audioCollectionId", "albumId", "recordingPlatformId", "scriptId", "key", "importedAt")

# RecordingMetaCategory
class RecordingMetaCategory(Base):
	__table__ = t_recording_meta_categories

	# column synonyms
	recording_meta_category_id = synonym("recordingMetaCategoryId")
	audio_collection_id = synonym("audioCollectionId")


class RecordingMetaCategorySchema(Schema):
	class Meta:
		fields = ("recordingMetaCategoryId", "audioCollectionId", "name", "key", "validator")

# RecordingMetaValue
class RecordingMetaValue(Base):
	__table__ = t_recording_meta_values

	# column synonyms
	recording_meta_value_id = synonym("recordingMetaValueId")
	recording_meta_category_id = synonym("recordingMetaCategoryId")
	recording_id = synonym("recordingId")


class RecordingMetaValueSchema(Schema):
	class Meta:
		fields = ("recordingMetaValueId", "recordingMetaCategoryId", "recordingId", "value")

# Recording
class Recording(Base, ImportMixin):
	__table__ = t_recordings

	# relationships
	audio_collection = relationship("AudioCollection", backref="recordings")
	recording_platform = relationship("RecordingPlatform", backref="recordings")
	performance = relationship("Performance", backref="recordings")
	corpus_code = relationship("CorpusCode", backref="recordings")

	# synonyms
	recording_id = synonym("recordingId")
	audio_collection_id = synonym("audioCollectionId")
	performance_id = synonym("performanceId")
	corpus_code_id = synonym("corpusCodeId")

	@classmethod
	def from_import(cls, data, performance):
		corpus_code = CorpusCode.query.get(data["corpusCodeId"])

		if corpus_code.recording_platform != performance.recording_platform:
			raise ValueError("Corpus Code {0} does not belong to recording platform {1}".format(corpus_code.corpus_code_id, performance.recording_platform.record_platform_id))

		recording = cls(
			audio_collection=performance.audio_collection,
			recording_platform=performance.recording_platform,
			performance=performance,
			corpus_code=corpus_code,
			prompt=data["prompt"],
			hypothesis=data["hypothesis"]
		)
		
		for audio_file_data in data["audioFiles"]:
			audio_file = AudioFile.from_import(audio_file_data, recording)
			recording.audio_files.append(audio_file)
		
		return recording


class RecordingSchema(Schema):
	class Meta:
		fields = ("recordingId", "audioCollectionId", "performanceId", "corpusCodeId", "prompt", "hypothesis")

# CorpusCode
class CorpusCode(Base):
	__table__ = t_corpus_codes

	# relationships
	recording_platform = relationship("RecordingPlatform", backref="corpus_codes")

	# synonyms
	corpus_code_id = synonym("corpusCodeId")
	audio_collection_id = synonym("audioCollectionId")
	requires_cutup = synonym("requiresCutup")
	corpus_code_group_id = synonym("corpusCodeGroupId")

class CorpusCodeSchema(Schema):
	class Meta:
		fields = ("corpusCodeId", "code", "requiresCutup", "included", "regex")

# Track
class Track(Base):
	__table__ = t_tracks

	# relationships
	recording_platform = relationship("RecordingPlatform", backref="tracks")

	# synonyms
	track_id = synonym("trackId")
	recording_platform_id = synonym("recordingPlatformId")
	track_index = synonym("trackIndex")

class TrackSchema(Schema):
	class Meta:
		fields = ("trackId", "name", "trackIndex")


#
# Define model class and its schema (if needed) above
#

__all__ = list(set(locals().keys()) - _names)

for schema_name in [i for i in __all__ if i.endswith('Schema')]:
	klass_name = schema_name[:-6]
	assert klass_name
	klass = locals()[klass_name]
	schema = locals()[schema_name]
	klass.set_schema(schema)
