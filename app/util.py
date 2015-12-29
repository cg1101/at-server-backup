
import cStringIO
import gzip
from collections import OrderedDict

from app.i18n import get_text as _
import db.model as m
from db.db import SS


def split_by_size(seq, size):
	if not size >= 1:
		raise ValueError('size must be greater than or equal to 1')
	return [seq[offset:offset+size] for offset in range(0, len(seq), size)]


class _batcher(object):
	@staticmethod
	def _create_work_batches(subTask, rawPieces, priority):
		partitions = []
		if subTask.batchingMode == m.BatchingMode.NONE:
			partitions.append(rawPieces[:])
		elif subTaks.batchingMode == m.BatchingMode.ALLOCATION_CONTEXT:
			loads = OrderedDict()
			for i in rawPieces:
				loads.setdefault(i.allocationContext, []).append(i)
			partitions.extend(loads.values())
		else:
			raise RuntimeError(_('unsupported batching mode {0}'
				).format(subTask.batchingMode))
		batches = []
		for batch_load in partitions:
			b = m.Batch(taskId=subTask.taskId,
				subTaskId=subTask.subTaskId, priority=priority)
			for pageIndex, page_load in enumerate(split_by_size(
					batch_load, subTask.maxPageSize)):
				p = m.Page(pageIndex=pageIndex)
				b.pages.append(p)
				for memberIndex, rawPiece in enumerate(page_load):
					memberEntry = m.PageMemberEntry(memberIndex=memberIndex)
					memberEntry.rawPieceId = rawPiece.rawPieceId
					p.memberEntries.append(memberEntry)
			batches.append(b)
		return batches

	@staticmethod
	def _create_qa_batches(subTask, workEntries, priority):
		raise NotImplementedError

	@staticmethod
	def _create_rework_batches(subTask, rawPieceIds, priority):
		raise NotImplementedError


class Batcher(object):
	@staticmethod
	def batch(subTask, things, priority=5):
		if subTask.workType == m.WorkType.WORK:
			return _batcher._create_work_batches(subTask, things, priority)
		elif subTask.workType == m.WorkType.QA:
			return _batcher._create_qa_batches(subTask, things, priority)
		elif subTask.workType == m.WorkType.REWORK:
			return _batcher._create_rework_batches(subTask, things, priority)
		else:
			raise RuntimeError(_('work type not supported {0}'
				).format(subTask.workType))


class Loader(object):
	@staticmethod
	def load(handler, task, dataFile, **options):
		# TODO: implement this
		rawPieces = []
		for i in range(10):
			rawPiece = m.RawPiece()
			rawPiece.rawText = 'raw text #' + str(i)
			rawPiece.words = i
			rawPiece.hypothesis = 'this is hypothesis of ' + str(i)
			rawPiece.meta = None
			rawPieces.append(rawPiece)
		return rawPieces


class Selector(object):
	FILTER_TYPES = {
		'DATE_SINGLE': 'datesingle',
		'DATE_INTERVAL': 'dateinterval',
		'LABEL': 'label',
		'QA_ERROR_SEVERITY': 'qaseverity',
		'QA_ERROR_TYPE': 'qaerrortype',
		'QA_ERROR_CLASS': 'qaerrorclass',
		'SUB_TASK_WORK': 'subtaskwork',
		'SUB_TASK_BATCHING': 'subtaskbatching',
		'TAG': 'tag',
		'SOURCE_TAG': 'sourcetag',
		'TEXT': 'text',
		'RAW_TEXT': 'rawtext',
		'ALLOCATION_CONTEXT': 'allocationcontext',
		'TRANSCRIBED': 'transcribed',
		'USER': 'user',
		'WORK_TYPE_WORK': 'worktypework',
		'WORK_TYPE_BATCHING': 'worktypebatching',
		'PP_GROUP': 'ppgroup',
		'CUSTOM_GROUP': 'customgroup',
		'LOAD': 'load',
		'SOURCE_WORD_COUNT': 'sourcewordcount',
		'RESULT_WORD_COUNT': 'resultwordcount',
		'WORD_COUNT_GAP': 'wordcountgap',
	}
	@staticmethod
	def select(selection):
		# TODO: implemet this
		taskId = getattr(selection, 'taskId')
		if taskId is None:
			raise ValueError('must specify taskId')
		return [1,2,3]
for key, value in Selector.FILTER_TYPES.iteritems():
	setattr(Selector, key, value)
del key, value


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
		# TODO: implement this
		data = 'this is a piece of fake extract'
		if compress:
			sio = cStringIO.StringIO()
			with gzip.GzipFile(None, mode='w', compresslevel=9, fileobj=sio) as f:
				f.write(data)
			data = sio.getvalue()
		return data


class Warnings(dict):
	CRITICAL = 'Critical'
	NON_CRITICAL = 'Non-Critical'
	NOTES = 'Notes'
	def critical(self, message):
		self.setdefault(self.CRITICAL, []).append(message)
	def non_critical(self, message):
		self.setdefault(self.NON_CRITICAL, []).append(message)
	def notes(self, message):
		self.setdefault(self.NOTES, []).append(message)

