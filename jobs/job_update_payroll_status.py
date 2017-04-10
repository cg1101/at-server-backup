
import logging
import cStringIO
import traceback

from db.db import SS
import db.model as m
from app.util.agent import ao
from app.util import CountryRatioLookupTable


log = logging.getLogger(__name__)


class SubTaskHelper(object):
	def __init__(self, subTaskId):
		subTask = m.SubTask.query.get(subTaskId)
		if not subTask:
			raise ValueError('sub task {0} not found'.format(subTaskId))
		self.subTask = subTask
		self.worker_by_id = {}
		for i in m.TaskWorker.query.filter(m.TaskWorker.subTaskId==subTaskId).all():
			self.worker_by_id[i.userId] = i
		self.pay_rate_history = m.SubTaskRate.query.\
			filter(m.SubTaskRate.subTaskId==subTaskId).\
			order_by(m.SubTaskRate.validFrom.desc()).all()
	def load_unpaid_events(self):
		# TODO: load words in this query
		subTaskId = self.subTask.subTaskId
		unpaid_events = m.PayableEvent.query.\
			filter(m.PayableEvent.subTaskId==subTaskId).\
			filter(m.PayableEvent.calculatedPaymentId==None).\
			filter(m.PayableEvent.batchId.notin_(
				SS.query(m.Batch.batchId).\
				filter(m.Batch.subTaskId==subTaskId))).\
			all()
		return unpaid_events
	def get_interval(self, moment):
		intervals = self.subTask.workIntervals
		if not len(intervals):
			raise RuntimeError('work interals not found for sub task {0}'.\
					format(self.subTask.subTaskId))
		if moment < intervals[0].startTime:
			raise RuntimeError('earlier than the first work interval')
		for next_interval in intervals:
			if moment >= next_interval.startTime and\
				(next_interval.endTime is None or\
					moment < next_interval.endTime):
				return next_interval
		raise RuntimeError('later than the last work interval')
	def iter_unpaid_events_by_interval(self):
		events_by_interval_id = {}
		for event in self.load_unpaid_events():
			try:
				interval = self.get_interval(event.created)
				events_by_interval_id.setdefault(interval.workIntervalId, {}
					).setdefault(event.userId, []).append(event)
			except RuntimeError, e:
				log.error('no interval found for event {}'.format(event.eventId))
				# found payable event with no receiving work interval
				raise
		for i in self.subTask.workIntervals:
			events = events_by_interval_id.get(i.workIntervalId, {})
			if events:
				yield (i, events)
	def iter_payable_items(self):
		for interval, events_by_user_id in self.iter_unpaid_events_by_interval():
			if interval.status != m.WorkInterval.STATUS_FINISHED:
				continue
			for userId, events in events_by_user_id.iteritems():
				yield (interval, userId, events)
	def get_units(self, rawPieceId):
		return m.RawPiece.query.get(rawPieceId).words
	def get_qa_result(self, interval, userId):
		return {
			'qaedItemCount': 0,
			'qaedUnitCount': 0,
			'accuracy': 1.0,
		}
	def get_pay_rate(self, moment):
		for rate in self.pay_rate_history:
			if rate.validFrom <= moment:
				return rate
		return None
	def get_payment_factor(self, userId):
		worker = self.worker_by_id[userId]
		return worker.paymentFactor
	def adjust_by_accuracy(self, rate, accuracy, amount):
		return amount
	def calculate_payment(self, payrollId):
		payments = []
		for interval, userId, events in self.iter_payable_items():
			qa = self.get_qa_result(interval, userId)
			paymentFactor = self.get_payment_factor(userId)
			itemCount = len(events)
			unitCount = 0
			totalAmount = 0.0
			for event in events:
				rate = self.get_pay_rate(event.created)
				if not rate:
					continue
				units = self.get_units(event.rawPieceId)
				unitCount += units
				full_amount = (units if self.subTask.payByUnit else 1) *\
					rate.multiplier *\
					paymentFactor
				real_amount = self.adjust_by_accuracy(rate, qa['accuracy'], full_amount)
				totalAmount += real_amount

			# add bonus if configured
			if self.subTask.bonus != None and self.subTask.bonus > 0:
				totalAmount *= (1.0 + self.subTask.bonus)

			# adjust amount according to country ratio if required
			if self.subTask.useWorkRate:
				user = m.User.query.get(userId)
				try:
					ratio = CountryRatioLookupTable.get_ratio(user.countryId)
				except:
					# user.countryId is null
					raise
				totalAmount *= ratio

			cp = m.CalculatedPayment(payrollId=payrollId,
				workIntervalId=interval.workIntervalId,
				userId=userId,
				taskId=self.subTask.taskId,
				subTaskId=self.subTask.subTaskId,
				itemCount=itemCount,
				unitCount=unitCount,
				qaedItemCount=qa['qaedItemCount'],
				qaedUnitCount=qa['qaedUnitCount'],
				accuracy=qa['accuracy'],
				amount=totalAmount,
				originalAmount=totalAmount,
				receipt=None,
				#updated=False,
			)
			SS.add(cp)
			SS.flush()
			for event in events:
				event.calculatedPaymentId = cp.calculatedPaymentId
			payments.append(cp)
		return payments


def update_payroll_status(task, payrollId):
	for subTask in task.subTasks:
		SubTaskHelper(subTask.subTaskId).calculate_payment(payrollId)


def main(taskId=None):
	logging.basicConfig(level=logging.DEBUG)
	if taskId is None:
		tasks = m.Task.query.filter(m.Task.status.notin_([
				m.Task.STATUS_ARCHIVED, m.Task.STATUS_CLOSED,
				m.Task.STATUS_FINISHED])).all()
	else:
		task = m.Task.query.get(taskId)
		if not task:
			raise ValueError('task {0} not found'.format(taskId))
		tasks = [task]

	payroll_data = ao.get_payroll()

	# print 'payroll to use for payment submission:\n{}'.format(payroll_data)

	payrollId = payroll_data['payrollId']
	payroll = m.BasicPayroll.query.get(payrollId)
	if not payroll:
		payroll = m.BasicPayroll(payrollId=payrollId)
		SS.add(payroll)

	for task in tasks:
		try:
			update_payroll_status(task, payrollId)
		except:
			log.info('task {} failed'.format(task.taskId))
			out = cStringIO.StringIO()
			traceback.print_exc(file=out)
			log.error(out.getvalue())
			SS.rollback()
			# break
		else:
			log.info('task {} succeeded'.format(task.taskId))
			# SS.commit()
			pass
	SS.commit()

	# find all CalculatedPayment entries and send them as package
	payments = m.CalculatedPayment.query.filter(
		m.CalculatedPayment.receipt.is_(None)).filter(
		m.CalculatedPayment.payrollId==payrollId).all()
	# print 'payments to submit: ', len(payments)
	receipts = ao.send_payments(payments)
	# print receipts
	for cp in payments:
		cp.receipt = receipts.get(cp.calculatedPaymentId, None)
	SS.commit()
