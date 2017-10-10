
import os
import cStringIO
import gzip
import math

from sqlalchemy import select, join
from sqlalchemy.orm import aliased
from jinja2 import Environment, FileSystemLoader

from db.db import SS
from db.schema import t_workentries
import db.model as m
from app.util.converter import Converter


_dir = os.path.dirname(__file__)


def ts_to_interval(f):
	hour = int(f / 3600)
	minute = int((f % 3600) / 60)
	second = f % 60
	return '%2d:%02d:%09.6f' % (hour, minute, second)


class Extractor(object):
	EXTRACT = 'extract'
	TABULAR = 'tabular'
	HTML = 'html'
	XML = 'xml'
	TEXT = 'text'
	RAW_PIECE_ID = 'rawPieceId'
	ASSEMBLY_CONTEXT = 'assemblyContext'
	RAW_TEXT = 'rawText'
	RESULT = 'result'
	EMAIL = 'email'
	USER_NAME = 'userName'
	LABELS = 'labels'
	HYPOTHESIS = 'hypothesis'
	INTERVAL = 'interval'
	QA_ERRORS = 'qaErrors'

	MANDATORY_COLUMNS = {ASSEMBLY_CONTEXT, RESULT}
	OPTIONAL_COLUMNS = {RAW_PIECE_ID, RAW_TEXT, EMAIL, USER_NAME, LABELS, QA_ERRORS, HYPOTHESIS, INTERVAL}
	@staticmethod
	def extract(task, columns=[], fileFormat=EXTRACT, sourceFormat=TEXT,
			resultFormat=TEXT, groupIds=[], keepLineBreaks=False,
			withQaErrors=False, compress=True):

		columns = set(set(columns) & Extractor.OPTIONAL_COLUMNS |
			Extractor.MANDATORY_COLUMNS)

		tagById = {}
		tagSet = None
		tags = []
		if task.tagSetId != None:
			tagSet = m.TagSet.query.get(task.tagSetId)
			tags = tagSet.tags[:]
		for t in tags:
			tagById[t.tagId] = t

		labelLookUpTable = {}
		labels = []
		if task.labelSetId != None:
			labels = m.Label.query.filter_by(labelSetId=task.labelSetId).all()
		for l in labels:
			labelLookUpTable[l.labelId] = l.extract

		errorLookUpTable = {}
		taskErrorTypes = m.TaskErrorType.query.filter_by(taskId=task.taskId).all()
		for er in taskErrorTypes:
			errorLookUpTable[er.errorTypeId] = er.errorType

		def formatResult(entry):
			if entry is None:
				return ''
			if resultFormat == Extractor.XML:
				htmlDoc = Converter.htmlText2HtmlDoc(entry.result)
				xmlDoc = Converter.htmlDoc2XmlDoc(htmlDoc)
				return Converter.xmlDoc2XmlText(xmlDoc)
			elif resultFormat == Extractor.TEXT:
				htmlDoc = Converter.htmlText2HtmlDoc(entry.result)
				xmlDoc = Converter.htmlDoc2XmlDoc(htmlDoc)
				txt = Converter.xmlDoc2ExtractText(xmlDoc).rstrip('\r\n')
				if not keepLineBreaks:
					txt = ' '.join(txt.split())
				return txt
			return entry.result

		def formatSource(rawText):
			if sourceFormat == Extractor.XML:
				htmlDoc = Converter.htmlText2HtmlDoc(rawText)
				xmlDoc = Converter.htmlDoc2XmlDoc(htmlDoc)
				return Converter.xmlDoc2XmlText(xmlDoc)
			elif resultFormat == Extractor.TEXT:
				htmlDoc = Converter.htmlText2HtmlDoc(rawText)
				xmlDoc = Converter.htmlDoc2XmlDoc(htmlDoc)
				return Converter.xmlDoc2ExtractText(xmlDoc)
			return rawText

		def formatLabels(entry):
			if entry is None:
				return ''
			buf = []
			for l in entry.appliedLabels:
				t = labelLookUpTable.get(l.labelId, None)
				if t != None:
					buf.append(t)
			return ' '.join(buf)

		def formatQaErrors(qaErrors):
			return ' '.join(qaErrors)

		users = {}
		def formatUser(entry, field):
			if entry is None:
				return ''
			try:
				user = users.setdefault(entry.userId, entry.user)
				value = getattr(user, field, '')
			except:
				value = ''
			return value

		def formatInterval(rawPiece, format=None):
			try:
				buf = rawPiece.assemblyContext.split('_')
				start = ts_to_interval(float(buf[-3]))
				end = ts_to_interval(float(buf[-1]))
			except:
				start = end = ''
			if format == 'start':
				return start
			elif format == 'end':
				return end
			return start + ' ' + end

		def showColumn(column):
			return column in columns

		env = Environment(loader=FileSystemLoader(_dir, followlinks=True),
			trim_blocks=True, lstrip_blocks=True)
		env.filters['formatResult'] = formatResult
		env.filters['formatSource'] = formatSource
		env.filters['formatLabels'] = formatLabels
		env.filters['formatQaErrors'] = formatQaErrors
		env.filters['formatUser'] = formatUser
		env.filters['formatInterval'] = formatInterval

		if fileFormat == Extractor.EXTRACT:
			template = env.get_template('extract.template')
		elif fileFormat == Extractor.TABULAR:
			template = env.get_template('tabular.template')
		else:
			raise ValueError('invalid file format {}'.format(fileFormat))

		q_s = SS.query(m.SubTask.subTaskId
			).join(m.WorkType
			).filter(m.WorkType.modifiesTranscription
			).filter(m.SubTask.taskId==task.taskId)

		class _we(m.Base):
			__table__ = t_workentries

		_qwe = aliased(_we)

		q1 = SS.query(_we.entryId
			).distinct(_we.rawPieceId
			).order_by(_we.rawPieceId, _we.created.desc()
			).filter(_we.subTaskId.in_(q_s))

		if len(groupIds):
			# include rawPieces that members of selected groups
			q_r = SS.query(m.CustomUtteranceGroupMember.rawPieceId.distinct()
				).join(m.CustomUtteranceGroup
				).filter(m.CustomUtteranceGroup.taskId==task.taskId
				).filter(m.CustomUtteranceGroup.groupId.in_(groupIds))
			q1 = q1.filter(_we.rawPieceId.in_(q_r))

		hit = q1.subquery('hit')

		q2 = SS.query(hit.c.entryId)

		q_3 = SS.query(_qwe.entryId
			).distinct(_qwe.qaedEntryId
			).order_by(_qwe.qaedEntryId, _qwe.created.desc()
			).filter(_qwe.subTaskId.in_(
					SS.query(m.SubTask.subTaskId
						).join(m.WorkType
						).filter(m.WorkType.name=='QA'
						).filter(m.SubTask.taskId==task.taskId
					)
				)
			)
		qa = q_3.subquery('qa_result')

		q3 = SS.query(_we.rawPieceId.label('rawPieceId'),
				_we.entryId.label('entryId'),
				qa.c.entryId.label('qaEntryId')
			).outerjoin(qa, qa.c.qaedEntryId==_we.entryId
			).filter(_we.entryId.in_(q2))

		a = q3.subquery('rs')
		rs = SS.query(m.RawPiece, m.WorkEntry, a.c.qaEntryId
				).select_from(
					join(a, m.RawPiece, a.c.rawPieceId==m.RawPiece.rawPieceId
					).join(m.WorkEntry, a.c.entryId==m.WorkEntry.entryId)
				).all()

		def _get_qa_errors(qaEntryId):
			errors = []
			if qaEntryId is not None:
				for errorTypeId in SS.query(m.AppliedError.errorTypeId
						).filter(m.AppliedError.entryId==qaEntryId
						).all():
					t = errorLookUpTable.get(er.errorTypeId, None)
					if t != None:
						errors.append(t)
			return errors

		get_qa_errors = _get_qa_errors if withQaErrors else lambda qaEntryId: []

		items = []
		for rawPiece, entry, qaEntryId in rs:
			qaErrors = get_qa_errors(qaEntryId)
			items.append((rawPiece, entry, qaErrors))

		data = template.render(items=items, showColumn=showColumn).encode('utf-8')
		if compress:
			sio = cStringIO.StringIO()
			with gzip.GzipFile(None, mode='w', compresslevel=9, fileobj=sio) as f:
				f.write(data)
			data = sio.getvalue()
		return data

