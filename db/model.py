#!/usr/bin/env python

_names = set(locals().keys())

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, backref, synonym, deferred, column_property, object_session
from sqlalchemy.sql import case, text, func
from marshmallow import Schema, fields

from db import SS
from schema import *

class MyBase(object):
	_schema_class = None
	@classmethod
	def set_schema(cls, schema_class):
		if not issubclass(schema_class, Schema):
			raise TypeError, 'schema class must be subclass of {}'.format(
				Schema.__name__)
		cls._schema_class = schema_class
	@classmethod
	def dump(cls, obj, extra=None, only=(), exclude=(), prefix=u'',
			strict=False, context=None, load_only=(), **kwargs):
		if cls._schema_class is None:
			raise RuntimeError, 'schema class not found for {0}'.format(cls.__name__)
		s = cls._schema_class(extra=extra, only=only, exclude=exclude,
				prefix=prefix, strict=strict, context=context)
		if isinstance(obj, list):
			many = True
		else:
			many = False
		marshal_result = s.dump(obj, many=many, **kwargs)
		return marshal_result.data


def _(**kwargs):
	return kwargs

def _make_model(input):
	modelClassName, bases, modelClassDict, schemaClassDict = input
	modelClass = type(modelClassName, bases, modelClassDict)
	globals()[modelClassName] = modelClass
	__all__.append(modelClassName)
	schemaClassName = modelClassName + 'Schema'
	schemaClass = type(schemaClassName, (Schema,), schemaClassDict)
	globals()[schemaClassName] = schemaClass
	__all__.append(schemaClassName)

def _meta(**kwargs):
	return type('Meta', (), kwargs)

_names = set(locals().keys()) - _names

Base = declarative_base(cls=MyBase, metadata=metadata)
Base.query = SS.query_property()


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
	pages = relationship('Page', order_by='Page.pageIndex')
	task = relationship('Task')
	subTask = relationship('SubTask')

class BatchSchema(Schema):
	pages = fields.Nested('PageSchema', many=True)
	class Meta:
		fields = ('batchId', 'taskId', 'subTaskId', 'userId', 'userName', 'priority', 'onHold', 'leaseGranted', 'leaseExpires', 'notUserId', 'workIntervalId', 'checkedOut', 'pages')
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
		fields = ('calculatedPaymentId', 'payrollId', 'workIntervalId', 'userId', 'userName', 'taskId', 'subTaskId', 'items', 'units', 'qaedItems', 'qaedUnits', 'accuracy', 'originalAmount', 'amount', 'receipt', 'updated')
		ordered = True
		# skip_missing = True

# CustomUtteranceGroup
class CustomUtteranceGroup(Base):
	__table__ = t_customutterancegroups
	_members = relationship('CustomUtteranceGroupMember')
	rawPieces = association_proxy('_members', 'rawPiece')

class CustomUtteranceGroupSchema(Schema):
	rawPieces = fields.Nested('RawPieceSchema', many=True)
	class Meta:
		fields = ('groupId', 'name', 'taskId', 'created', 'utterances', 'selectionId', 'rawPieces')
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

# Page
class Page(Base):
	__table__ = t_pages
	members = relationship('PageMember',
		primaryjoin="Page.pageId == PageMember.pageId", order_by='PageMember.memberIndex',
		cascade='all, delete-orphan')
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
# # PaymentType
# # Payroll

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

# SelectionFilter
class SelectionFilter(Base):
	__table__ = t_utteranceselectionfilters
	pieces = relationship('SelectionFilterPiece', order_by='SelectionFilterPiece.index')

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

class SubTaskContentEventSchema(Schema):
	class Meta:
		fields = ('subTaskId', 'selectionId', 'amount', 'populating', 'tProcessedAt', 'operator')
		ordered = True

# SubTaskMetric
class SubTaskMetric(Base):
	__table__ = t_subtaskmetrics

class SubTaskMetricSchema(Schema):
	class Meta:
		fields = ('metricId', 'userId', 'workIntervalId', 'subTaskId', 'amount',
			'words', 'workRate', 'accuracy', 'lastUpdated')
		ordered = True

# SubTaskRate
class SubTaskRate(Base):
	__table__ = t_subtaskrates
	rate = relationship('Rate')
	rateName = association_proxy('rate', 'name')

class SubTaskRateSchema(Schema):
	class Meta:
		fields = ('subTaskRateId', 'subTaskId', 'taskId', 'rateId', 'rateName', 'validFrom', 'multiplier', 'updatedBy', 'updatedAt')
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

class SpanTagSchema(TagSchema):
	class Meta:
		additional = ('color', 'isForeground', 'surround', 'extend', 'split')

class SpanBTag(Tag):
	__mapper_args__ = {
		'polymorphic_identity': Tag.EMBEDDABLE,
	}

class SpanBTagSchema(TagSchema):
	pass

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
	__table__ = t_utteranceselections
	user = relationship('User')
	userName = association_proxy('user', 'userName')
	filters = relationship('SelectionFilter', order_by='SelectionFilter.filterId')

class UtteranceSelectionSchema(Schema):
	filters = fields.Nested('SelectionFilterSchema', many=True)
	class Meta:
		fields = ('selectionId', 'taskId', 'userId', 'userName', 'limit', 'selected', 'action', 'subTaskId', 'name', 'processed', 'random', 'filters')
		ordered = True
		# skip_missing = True

# WorkEntry
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

class WorkTypeEntrySchema(WorkEntrySchema):
	class Meta:
		additional = ()
		ordered = True

class QaTypeEntry(WorkEntry):
	__mapper_args__ = {
		'polymorphic_identity': WorkType.QA,
	}
	appliedErrors = relationship('AppliedError')

class QaTypeEntrySchema(WorkEntrySchema):
	class Meta:
		additional = ()
		ordered = True

class ReworkTypeEntry(WorkEntry):
	__mapper_args__ = {
		'polymorphic_identity': WorkType.REWORK,
	}
	appliedLabels = relationship('AppliedLabel')

class ReworkTypeEntrySchema(WorkEntrySchema):
	class Meta:
		additional = ()
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

__all__ = list(set(locals().keys()) - _names)

for schema_name in [i for i in __all__ if i.endswith('Schema')]:
	klass_name = schema_name[:-6]
	assert klass_name
	klass = locals()[klass_name]
	schema = locals()[schema_name]
	klass.set_schema(schema)
