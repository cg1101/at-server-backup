
import logging
import cStringIO
import traceback

from sqlalchemy import func

from db.db import SS
import db.model as m


log = logging.getLogger(__name__)


def collapse_payable_events(task=None):
	q_keys = SS.query(m.PayableEvent.rawPieceId,
			m.PayableEvent.workEntryId, m.PayableEvent.batchId,
			m.PayableEvent.pageId
		).group_by(m.PayableEvent.rawPieceId,
			m.PayableEvent.workEntryId, m.PayableEvent.batchId,
			m.PayableEvent.pageId
		).having(func.count('*') > 1)
	for rawPieceId, workEntryId, batchId, pageId in q_keys.all():
		events = m.PayableEvent.query.filter(m.PayableEvent.rawPieceId==rawPieceId
			).filter(m.PayableEvent.workEntryId==workEntryId
			).filter(m.PayableEvent.batchId==batchId
			).filter(m.PayableEvent.pageId==pageId
			).order_by(m.PayableEvent.created
			).all()
		while events:
			ev = events.pop(0)
			# delete event if it is neither paid nor the latest
			if ev.calculatedPaymentId is None and events:
				SS.delete(ev)


def main(taskId=None):
	logging.basicConfig(level=logging.DEBUG)
	log.debug('collapsing payable events, taskId={}'.format(taskId))
	try:
		collapse_payable_events()
	except Exception, e:
		out = cStringIO.StringIO()
		traceback.print_exc(file=out)
		log.error(out.getvalue())
		SS.rollback()
	else:
		log.info('succeeded')
		SS.commit()
