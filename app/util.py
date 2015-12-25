
from collections import OrderedDict

from app.i18n import get_text as _
import db.model as m
from db.db import SS

def split_by_size(seq, size):
	if not size >= 1:
		raise ValueError('size must be greater than or equal to 1')
	return [seq[offset:offset+size] for offset in [i for i in
		range(0, len(seq), size)]]


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
			b = Batch(taskId=subTask.taskId,
				subTaskId=subTask.subTaskId, priority=priority)
			for pageIndex, page_load in enumerate(split_by_size(
					batch_load, subTask.maxPageSize)):
				p = Page(pageIndex=pageIndex)
				b.pages.append(p)
				for memberIndex, rawPiece in enumerate(page_load):
					member = m.PageMember(memberIndex=memberIndex)
					p.member.rawPiecedId = rawPiece.rawPieceId
					p.members.append(member)
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
