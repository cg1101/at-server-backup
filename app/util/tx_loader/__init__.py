
from collections import OrderedDict

import db.model as m
from db.db import SS

from app.util import Batcher
from TextParser import TxParser

from tx import iter_utts

class TxLoader(object):
	def __init__(self, taskId):
		task = m.Task.query.get(taskId)
		if not task:
			raise ValueError('task {0} not found'.format(taskId))
		if task.tagSetId is None:
			tags = []
		else:
			tags = m.Tag.query.filter(m.Tag.tagSetId==task.tagSetId).all()
		if task.labelSetId is None:
			labels = []
		else:
			labels = m.Label.query.filter(m.Label.labelSetId==task.labelSetId).all()
		self.taskId = taskId
		self.task = task
		self.tags = tags
		self.labels = labels
		self.tx_parser = TxParser(tags)
	def load_raw_piece_ids(self):
		self.id2key = {}
		self.key2id = {}
		q = SS.query(m.RawPiece.rawPieceId, m.RawPiece.assemblyContext
			).filter(m.RawPiece.taskId==self.taskId)
		for rawPieceId, assemblyContext in q.all():
			self.id2key[rawPieceId] = assemblyContext
			self.key2id[assemblyContext] = rawPieceId
	def load_utts(self, filepath):
		return [utt for utt in iter_utts(filepath)]
	def get_utt_info(self, utt):
		assemblyContext = utt['FILE']
		try:
			rawPieceId = self.key2id[assemblyContext]
		except Exception, e:
			print ('id2key', self.id2key)
			print ('key2id', self.key2id)
			print ('error', e)
			raise RuntimeError('invalid item key {}'.format(assemblyContext))
		return rawPieceId, assemblyContext
	def get_applied_labels(self, utt):
		labelIds = []
		return labelIds
	def load_tx_file(self, filespec, srcSubTask, fakeUser, dstSubTask):
		self.load_raw_piece_ids()
		utts = iter_utts(filespec)
		rawPieceIds = OrderedDict()

		# create fake work entries
		for utt in utts:
			rawPieceId, assemblyContext = self.get_utt_info(utt)
			labelIds = self.get_applied_labels(utt)
			result = self.tx_parser.parse(utt['TRANSCRIPTION'])
			rawPieceIds[rawPieceId] = rawPieceId
			entry = m.WorkEntry(
					rawPieceId=rawPieceId,
					taskId=self.taskId,
					result=result,
					subTaskId=srcSubTask.subTaskId,
					batchId=-1,
					pageId=-1,
					workTypeId=srcSubTask.workTypeId,
					userId=fakeUser.userId,
			)
			SS.add(entry)
			SS.flush()
			for labelId in labelIds:
				label = m.AppliedLabel(entryId=entry.entryId, labelId=labelId)
				SS.add(label)
		rawPieceIds = list(rawPieceIds.keys())

		# populate destination rework sub task
		batches = Batcher.batch(dstSubTask, rawPieceIds)
		for batch in batches:
			SS.add(batch)

		return {
			'itemCount': len(rawPieceIds),
			'batches': batches,
		}
