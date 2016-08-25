
import os
import cStringIO
import gzip

from sqlalchemy import select, join
from jinja2 import Environment, FileSystemLoader

from db.db import SS
import db.model as m
from app.util.converter import Converter


_dir = os.path.dirname(__file__)


class Extractor(object):
	EXTRACT = 'extract'
	TABULAR = 'tabular'
	HTML = 'html'
	XML = 'xml'
	TEXT = 'text'
	@staticmethod
	def extract(task, fileFormat=EXTRACT, sourceFormat=TEXT,
			resultFormat=TEXT, groupIds=[], keepLineBreaks=False,
			withQaErrors=False, compress=True):

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
				return Converter.xmlDoc2ExtractText(xmlDoc)
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

		def formatQaErrors(entry):
			if entry is None:
				return ''
			try:
				qaEntry = m.QaTypeEntry.query.filter_by(qaedEntryId=entry.entryId
					).order_by(m.QaTypeEntry.created.desc()).limit(1).one()
			except:
				return ''
			buf = []
			for er in entry.appliedErrors:
				t = errorLookUpTable.get(er.errorTypeId, None)
				if t != None:
					buf.append(t)
			return ' '.join(buf)

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

		env = Environment(loader=FileSystemLoader(_dir, followlinks=True),
			trim_blocks=True, lstrip_blocks=True)
		env.filters['formatResult'] = formatResult
		env.filters['formatSource'] = formatSource
		env.filters['formatLabels'] = formatLabels
		env.filters['formatQaErrors'] = formatQaErrors
		env.filters['formatUser'] = formatUser

		if fileFormat == Extractor.EXTRACT:
			template = env.get_template('extract.template')
		elif fileFormat == Extractor.TABULAR:
			template = env.get_template('tabular.template')
		else:
			raise ValueError('invalid file format {}'.format(fileFormat))

		if len(groupIds):
			# include rawPieces that members of selected groups
			q_r = SS.query(m.CustomUtteranceGroupMember.rawPieceId.distinct()
				).join(m.CustomUtteranceGroup
				).filter(m.CustomUtteranceGroup.taskId==task.taskId)
			q = SS.query(m.RawPiece, m.WorkEntry
				).filter(m.RawPiece.taskId==task.taskId
				).filter(m.RawPiece.rawPieceId.in_(q_r)
				).outerjoin(m.WorkEntry)
		else:
			# include rawPieces all have been worked on at least once
			q_s = select([m.SubTask.subTaskId]
				).select_from(join(m.SubTask, m.WorkType)
				).where(m.WorkType.modifiesTranscription
				).where(m.SubTask.taskId==task.taskId)
			q = SS.query(m.RawPiece, m.WorkEntry).distinct(m.WorkEntry.rawPieceId
				).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc()
				).filter(m.WorkEntry.rawPieceId==m.RawPiece.rawPieceId
				).filter(m.WorkEntry.taskId==task.taskId
				).filter(m.WorkEntry.subTaskId.in_(q_s))

		items = []
		for rawPiece, entry in q.all():
			items.append((rawPiece, entry))

		data = template.render(items=items).encode('utf-8')
		print data
		if compress:
			sio = cStringIO.StringIO()
			with gzip.GzipFile(None, mode='w', compresslevel=9, fileobj=sio) as f:
				f.write(data)
			data = sio.getvalue()
		return data

