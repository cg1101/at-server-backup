
import datetime
import random

from sqlalchemy import and_, select, func

from app.util import Converter
from app.i18n import get_text as _
from db.db import SS
import db.model as m

class MyFilter(object):
	ON = 'on'
	AFTER = 'after'
	BEFORE = 'before'

	EQUALS = '='
	NOT_EQUALS = '!='
	GREATER_THAN = '>'
	LESS_THAN = '<'

	ANY = 'any'
	FIRST = 'first'
	MOST_RECENT = 'mostrecent'
	MOST_RECENT_MODIFIED = 'mostrecentmodified'

	TRUE = 'true'
	FALSE = 'false'

	TEXT = 'text'
	REGEX = 'regex'

	_allow_override = False
	_filter_funcs = {}

	@classmethod
	def register(cls, func):
		func_name = func.__name__
		prefix = 'filter_'
		if not func_name.startswith(prefix):
			raise ValueError('filter function name must start with \'{}\''.format(prefix))

		filter_type = func_name[len(prefix):].upper()
		key = filter_type.lower().replace('_', '')

		if cls._filter_funcs.has_key(key) and not cls._allow_override:
			raise RuntimeError('filter key \'{}\' has been registered already'.format(key))
		cls._filter_funcs[key] = func

	@classmethod
	def run(cls, filter, task):
		func = cls._filter_funcs.get(filter.filterType, None)
		if func is None:
			raise RuntimeError('unsupported filter type \'{}\''.format(filter.filterType))
		pieces = [p.data for p in filter.pieces]
		rs = func(task, *pieces)
		if not isinstance(rs, set):
			rs = set(rs)
		return rs



# SOURCE_TAG
@MyFilter.register
def filter_source_tag(task, tagId):
	if tagId == MyFilter.ANY:
		tagId = None
		cond = m.RawPiece.rawText.contains('tagid=')
	else:
		try:
			tagId == int(tagId)
		except:
			raise ValueError(_('invalid tag id: {}').format(tagId))
		cond = m.RawPiece.rawText.contains('tagid="%s"' % tagId)

	q = SS.query(m.RawPiece.rawPieceId
		).filter(m.RawPiece.taskId==task.taskId
		).filter(cond)

	return set([r.rawPieceId for r in q.all()])


# ALLOCATION_CONTEXT
@MyFilter.register
def filter_allocation_context(task, text):
	cond = m.RawPiece.allocationContext == text

	q = SS.query(m.RawPiece.rawPieceId
		).filter(m.RawPiece.taskId==task.taskId
		).filter(cond)

	return set([r.rawPieceId for r in q.all()])


# TRANSCRIBED
@MyFilter.register
def filter_transcribed(task, transcribedOption):
	if transcribedOption == MyFilter.TRUE:
		cond = m.RawPiece.isNew.isnot(True)
	elif transcribedOption == MyFilter.FALSE:
		cond = m.RawPiece.isNew.is_(True)
	else:
		raise ValueError(_('invalid value of transcribed option {}').format(transcribedOption))

	q = SS.query(m.RawPiece.rawPieceId
		).filter(m.RawPiece.taskId==task.taskId
		).filter(cond)

	return set([r.rawPieceId for r in q.all()])


# LOAD
@MyFilter.register
def filter_load(task, loadOption, loadId):
	try:
		loadId = int(loadId)
	except:
		raise ValueError(_('invalid load id: {}').format(loadId))

	if loadOption == MyFilter.EQUALS:
		cond = m.RawPiece.loadId==loadId
	elif loadOption == MyFilter.NOT_EQUALS:
		cond = m.RawPiece.loadId!=loadId
	elif loadOption == MyFilter.LESS_THAN:
		cond = m.RawPiece.loadId<loadId
	elif loadOption == MyFilter.GREATER_THAN:
		cond = m.RawPiece.loadId>loadId
	else:
		raise ValueError(_('invalid load option: {}').format(loadOption))

	q = SS.query(m.RawPiece.rawPieceId
		).filter(m.RawPiece.taskId==task.taskId
		).filter(cond)

	return set([r.rawPieceId for r in q.all()])


# SOURCE_WORD_COUNT
@MyFilter.register
def filter_source_word_count(task, wordCountOption, words):
	try:
		words = int(words)
	except:
		raise ValueError(_('invalid word count: {}').format(words))
	if wordCountOption == MyFilter.EQUALS:
		cond = m.RawPiece.words == words
	elif wordCountOption == MyFilter.GREATER_THAN:
		cond = m.RawPiece.words > words
	elif wordCountOption == MyFilter.LESS_THAN:
		cond = m.RawPiece.words < words
	else:
		raise ValueError(_('invalid word count option: {}').format(words))

	q = SS.query(m.RawPiece.rawPieceId
		).filter(m.RawPiece.taskId==task.taskId
		).filter(cond)

	return set([r.rawPieceId for r in q.all()])


# RAW_TEXT
@MyFilter.register
def filter_raw_text(task, text, searchType=MyFilter.TEXT):
	if searchType == MyFilter.TEXT:
		func_ok = lambda (s): s.find(text) >= 0
	elif searchType == MyFilter.REGEX:
		try:
			pattern = re.compile(text)
		except:
			raise ValueError(_('invalid regular expression: {}').format(text))
		func_ok = lambda (s): pattern.search(s)
	else:
		raise ValueError(_('invalid search type: {}').format(searchType))

	def check(t):
		try:
			extractText = Converter.asExtract(t)
			return func_ok(extractText)
		except:
			return False

	q = SS.query(m.RawPiece.rawPieceId, m.RawPiece.rawText
		).filter(m.RawPiece.taskId==task.taskId)

	return set([r.rawPieceId for r in q.all() if check(r.rawText)])


# DATE_SINGLE
@MyFilter.register
def filter_date_single(task, workOption, dateOption, date):
	try:
		date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
	except ValueError, e:
		raise ValueError(_('invalid date value: {}').format(date))
	# TODO: use tz should be used
	startTime = datetime.datetime(date.year, date.month, date.day)
	endTime = startTime + datetime.timedelta(days=1)
	inner = SS.query(m.WorkEntry.rawPieceId, m.WorkEntry.entryId, m.WorkEntry.created
		).distinct(m.WorkEntry.rawPieceId
		).filter(m.WorkEntry.taskId==task.taskId)
	if workOption == MyFilter.ANY:
		pass
	elif workOption == MyFilter.FIRST:
		inner = inner.order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created)
	elif workOption == MyFilter.MOST_RECENT:
		inner = inner.order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())
	elif workOption == MyFilter.MOST_RECENT_MODIFIED:
		inner = inner.filter_by(m.WorkEntry.modifiesTranscription
			).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())
	else:
		raise ValueError(_('invalid work option: {}').format(workOption))
	sub_q = inner.subquery('sub_q')
	if dateOption == MyFilter.ON:
		cond = and_(sub_q.c.created >= startTime, sub_q.c.created < endTime)
	elif dateOption == MyFilter.BEFORE:
		cond = sub_q.c.created < startTime
	elif dateOption == MyFilter.AFTER:
		cond = sub_q.c.created >= endTime
	else:
		raise ValueError(_('invalid date option: {}').format(dateOption))
	q = SS.query(sub_q.c.rawPieceId
		).distinct(sub_q.c.rawPieceId
		).filter(cond)
	return set([r.rawPieceId for r in q.all()])


# DATE_INTERVAL
@MyFilter.register
def filter_date_interval(task, workOption, startDate, endDate):
	try:
		startDate = datetime.datetime.strptime(startDate, '%Y-%m-%d').date()
		startDate = datetime.datetime(startDate.year, startDate.month, startDate.day)
	except:
		raise ValueError(_('invalid start date: {}').format(startDate))
	try:
		endDate = datetime.datetime.strptime(endDate, '%Y-%m-%d').date()
		endDate = datetime.datetime(endDate.year, endDate.month, endDate.day)
	except:
		raise ValueError(_('invalid end date: {}').format(endDate))

	inner = SS.query(m.WorkEntry.rawPieceId, m.WorkEntry.entryId, m.WorkEntry.created
		).distinct(m.WorkEntry.rawPieceId
		).filter(m.WorkEntry.taskId==task.taskId)

	if workOption == MyFilter.ANY:
		pass
	elif workOption == MyFilter.FIRST:
		inner = inner.order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created)
	elif workOption == MyFilter.MOST_RECENT:
		inner = inner.order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())
	elif workOption == MyFilter.MOST_RECENT_MODIFIED:
		inner = inner.filter(m.WorkEntry.modifiesTranscription
			).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())
	else:
		raise ValueError(_('invalid work option: {}').format(workOption))

	sub_q = inner.subquery('sub_q')
	q = SS.query(sub_q.c.rawPieceId
		).filter(and_(sub_q.c.created>=startDate, sub_q.c.created<=endDate))

	return set([r.rawPieceId for r in q.all()])


# TEXT
@MyFilter.register
def filter_text(task, text, searchType=MyFilter.TEXT):
	if searchType == MyFilter.TEXT:
		pass
	elif searchType == MyFilter.REGEX:
		try:
			pattern = re.compile(text)
		except:
			raise ValueError(_('invalid regular expression: {}').format(text))

	def check(t):
		try:
			extractText = Converter.asExtract(t)
			return func_ok(extractText)
		except:
			return False

	q = SS.query(m.WorkEntry.rawPieceId, m.WorkEntry.result
		).distinct(m.WorkEntry.rawPieceId
		).filter(m.WorkEntry.taskId==task.taskId
		).filter(m.WorkEntry.modifiesTranscription
		).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())

	return set([r.rawPieceId for r in q.all() if check(r.result)])


# USER
@MyFilter.register
def filter_user(task, workOption, userId):
	try:
		userId = int(userId)
	except:
		raise ValueError(_('invalid user id: {}').format(userId))
	# TODO: check user is working on this task?
	inner = SS.query(m.WorkEntry.rawPieceId.label('rawPieceId'),
			m.WorkEntry.userId.label('userId')
		).distinct(m.WorkEntry.rawPieceId
		).filter(m.WorkEntry.taskId==task.taskId)
	if workOption == MyFilter.ANY:
		inner = inner.filter(m.WorkEntry.userId==userId)
	elif workOption == MyFilter.FIRST:
		inner = inner.order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created)
	elif workOption == MyFilter.MOST_RECENT:
		inner = inner.order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())
	elif workOption == MyFilter.MOST_RECENT_MODIFIED:
		inner = inner.filter(m.WorkEntry.modifiesTranscription.is_(True)
			).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())
	else:
		raise ValueError(_('invalid work option: {}').format(workOption))
	sub_q = inner.subquery('sub_q')
	q = SS.query(sub_q.c.rawPieceId
		).distinct(sub_q.c.rawPieceId
		).filter(sub_q.c.userId==userId)
	return set([r.rawPieceId for r in q.all()])


# TAG
@MyFilter.register
def filter_tag(task, tagId):
	if tagId == MyFilter.ANY:
		tagId = None
		key_string = 'tagid='
	else:
		try:
			tagId == int(tagId)
		except:
			raise ValueError(_('invalid tag id: {}').format(tagId))
		key_string = 'tagid="{}"'.format(tagId)

	q = SS.query(m.WorkEntry.rawPieceId, m.WorkEntry.result
		).distinct(m.WorkEntry.rawPieceId
		).filter(m.WorkEntry.taskId==task.taskId
		).filter(m.WorkEntry.modifiesTranscription
		).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())

	return set([r.rawPieceId for r in q.all() if r.result.find(key_string) > 0])


# RESULT_WORD_COUNT
@MyFilter.register
def filter_word_count(task, wordCountOption, words):
	try:
		words = int(words)
	except:
		raise ValueError(_('invalid words: {}').format(words))

	def count_words(t):
		extractText = Converter.asExtract(t)
		return len(extractText.split())

	if wordCountOption == MyFilter.EQUALS:
		func_ok = lambda (t): count_words(t) == words
	elif wordCountOption == MyFilter.GREATER_THAN:
		func_ok = lambda (t): count_words(t) > words
	elif wordCountOption == MyFilter.LESS_THAN:
		func_ok = lambda (t): count_words(t) < words

	q = SS.query(m.WorkEntry.rawPieceId, m.WorkEntry.result
		).distinct(m.WorkEntry.rawPieceId
		).filter(m.WorkEntry.taskId==task.taskId
		).filter(m.WorkEntry.modifiesTranscription
		).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())

	return set([r.rawPieceId for r in q.all() if func_ok(r.result)])


# WORD_COUNT_GAP
@MyFilter.register
def filter_word_count_gap(task, wordCountOption, gap):
	try:
		percentage = int(gap.rstrip('%')) / 100.0
	except:
		raise ValueError(_('invalid word count gap: {}').format(gap))

	def count_words(t):
		extractText = Converter.asExtract(t)
		return len(extractText.split())

	def calculate_gap(t, words):
		wc = count_words(t)
		return float(max(wc, words)) / min(wc, words) - 1

	if wordCountOption == MyFilter.EQUALS:
		func_op = lambda t: calculated == gap
	elif wordCountOption == MyFilter.LESS_THAN:
		func_op = lambda calculated, gap: calculated < gap
	elif wordCountOption == MyFilter.GREATER_THAN:
		func_op = lambda calculated, gap: calculated > gap

	def check(t, words):
		try:
			calculated = calculated_gap(t, words)
			return func_op(calculated, gap)
		except ZeroDivisionError:
			return True

	q = SS.query(m.WorkEntry.rawPieceId, m.WorkEntry.result
		).distinct(m.WorkEntry.rawPieceId
		).filter(m.WorkEntry.taskId==task.taskId
		).filter(m.WorkEntry.modifiesTranscription
		).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())
	sub_q = q.subquery('sub_q')
	sel_stmt = select([sub_q.c.rawPieceId, sub_q.c.result, m.RawPiece.words],
		from_obj=sub_q.join(m.RawPiece))
	return set([r.rawPieceId for r in SS.bind.execute(sel_stmt)
		if check(r.result, r.words)])

# LABEL
@MyFilter.register
def filter_label(task, labelId):
	if labelId == MyFilter.ANY:
		labelId = None
	else:
		try:
			labelId = int(labelId)
		except:
			raise ValueError(_('invalid label id: {}').format(labelId))

	inner = SS.query(m.WorkEntry.rawPieceId.label('rawPieceId'),
		m.WorkEntry.entryId.label('entryId')
		).distinct(m.WorkEntry.rawPieceId
		).filter(m.WorkEntry.taskId==task.taskId
		).filter(m.WorkEntry.modifiesTranscription
		).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())

	sub_q = inner.subquery('sub_q')
	q = sub_q.join(m.AppliedLabel, sub_q.c.entryId==m.AppliedLabel.entryId)
	if labelId != None:
		q = q.where(m.AppliedLabel==labelId)

	sel_stmt = select(q.c, distinct=True, from_obj=q)
	return set([r.rawPieceId for r in SS.bind.execute(sel_stmt)])


# QA_ERROR_SEVERITY
@MyFilter.register
def filter_qa_severity(task, isMoreThan, score, isCorrect):
	try:
		assert isMoreThan in (MyFilter.TRUE, MyFilter.FALSE)
	except:
		raise ValueError(_('invalid option value: {}').format(isMoreThan))
	else:
		isMoreThan = isMoreThan == MyFilter.TRUE
	try:
		assert isCorrect in (MyFilter.TRUE, MyFilter.FALSE)
	except:
		raise ValueError(_('invalid option value: {}').format(isCorrect))
	else:
		isCorrect = isCorrect == MyFilter.TRUE
	try:
		score = float(score)
	except:
		raise ValueError(_('invalid score value: {}').format(score))

	if isMoreThan:
		if isCorrect:
			predicate = lambda qaErrorSum: qaErrorSum == None or (1 - qaErrorSum) > score
		else:
			predicate = lambda qaErrorSum: qaErrorSum > score
	else:
		if correct:
			predicate = lambda qaErrorSum: 1 - (qaErrorSum or 0) < score
		else:
			predicate = lambda qaErrorSum: qaErrorSum == None or qaErrorSum < score

	# latest QA result
	q1 = SS.query(m.WorkEntry.entryId, m.WorkEntry.qaedEntryId, m.WorkEntry.rawPieceId
		).distinct(m.WorkEntry.qaedEntryId
		).filter(m.WorkEntry.taskId==task.taskId
		).filter(m.WorkEntry.workType==m.WorkType.QA
		).order_by(m.WorkEntry.qaedEntryId, m.WorkEntry.created.desc())

	sub_q = q1.subquery('sub_q')

	stmt = SS.query(m.AppliedError.entryId,
		func.sum(m.AppliedError.severity).label('qaErrorSum')
		).group_by(m.AppliedError.entryId).subquery()

	q = SS.query(sub_q.rawPieceId, stmt.c.qaErrorSum
		).join(stmt, stmt.c.entryId==sub_q.c.entryId)

	return set([r.rawPieceId for r in q.all() if predicate(r.qaErrorSum)])


# QA_ERROR_TYPE
@MyFilter.register
def filter_qa_error_type(task, errorTypeId):
	try:
		errorTypeId = int(erorrTypeId)
	except:
		raise ValueError(_('invalid error type id: {}').format(errorTypeId))

	taskErrorType = m.TaskErrorType.query.get((task.taskId, errorTypeId))
	if not taskErrorType:
		return set()

	# latest QA result
	inner = SS.query(m.WorkEntry.entryId, m.WorkEntry.qaedEntryId,
			m.WorkEntry.rawPieceId
		).distinct(m.WorkEntry.qaedEntryId
		).filter(m.WorkEntry.taskId==task.taskId
		).filter(m.WorkEntry.workType==m.WorkType.QA
		).order_by(m.WorkEntry.qaedEntryId, m.WorkEntry.created.desc())

	sub_q = inner.subquery('sub_q')

	q = SS.query(sub_q.c.rawPieceId
		).distinct(sub_q.c.rawPieceId
		).join(m.AppliedError, m.AppliedError.entryId==sub_q.c.entryId
		).filter(m.AppliedError.errorTypeId==errorTypeId)

	return set([r.rawPieceId for r in q.all()])

# QA_ERROR_CLASS
@MyFilter.register
def filter_qa_error_class(task, errorClassId):
	try:
		errorClassId = int(errorClassId)
	except:
		raise ValueError(_('invalid error class id: {}').format(errorClassId))
	# latest QA result
	inner = SS.query(m.WorkEntry.entryId, m.WorkEntry.qaedEntryId,
			m.WorkEntry.rawPieceId
		).distinct(m.WorkEntry.qaedEntryId
		).filter(m.WorkEntry.taskId==task.taskId
		).filter(m.WorkEntry.workType==m.WorkType.QA
		).order_by(m.WorkEntry.qaedEntryId, m.WorkEntry.created.desc())
	sub_q = inner.subquery('sub_q')
	q = SS.query(sub_q.c.rawPieceId
		).distinct(sub_q.c.rawPieceId
		).join(m.AppliedError, m.AppliedError.entryId==sub_q.c.entryId
		).filter(m.AppliedError.errorTypeId.in_(
			SS.query(m.ErrorType.errorTypeId
				).filter(m.ErrorType.errorClassId==errorClassId)))
	return set([r.rawPieceId for r in q.all()])

# PP_GROUP
@MyFilter.register
def filter_pp_group(task, groupId):
	if groupId == MyFilter.ANY:
		cond = m.RawPiece.groupId.isnot(None)
	else:
		try:
			groupId = int(groupId)
		except:
			raise ValueError(_('invalid group id: {}').format(groupId))
		cond = m.RawPiece.groupId == groupId

	q = SS.query(m.RawPiece.rawPieceId
		).filter(m.RawPiece.taskId==task.taskId
		).filter(cond)

	return set([r.rawPieceId for r in q.all()])

# CUSTOM_GROUP
@MyFilter.register
def filter_custom_group(task, groupId):
	q = SS.query(m.CustomUtteranceGroupMember.rawPieceId
		).distinct(m.CustomUtteranceGroupMember.rawPieceId
		).join(m.CustomUtteranceGroup
		).filter(m.CustomUtteranceGroup.taskId==task.taskId)

	if groupId == MyFilter.ANY:
		pass
	else:
		try:
			groupId == int(groupId)
		except:
			raise ValueError(_('invalid group id: {}').format(groupId))
		q = q.filter(m.CustomUtteranceGroup.groupId==groupId)

	return set([r.rawPieceId for r in q.all()])


# SUB_TASK_WORK
@MyFilter.register
def filter_sub_task_work(task, workOption, subTaskId):
	try:
		subTaskId = int(subTaskId)
	except:
		raise ValueError(_('invalid sub task id: {}').format(subTaskId))

	subTask = m.SubTask.query.get(subTaskId)
	if not subTask or subTask.taskId != task.taskId:
		return set()

	inner = SS.query(m.WorkEntry.rawPieceId, m.WorkEntry.subTaskId
		).distinct(m.WorkEntry.rawPieceId
		).filter(m.WorkEntry.taskId==task.taskId)

	if workOption == MyFilter.ANY:
		inner = inner.filter(m.WorkEntry.subTaskId == subTaskId)
	elif workOption == MyFilter.FIRST:
		inner = inner.order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created)
	elif workOption == MyFilter.MOST_RECENT:
		inner = inner.order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())
	elif workOption == MyFilter.MOST_RECENT_MODIFIED:
		inner = inner.filter(m.WorkEntry.modifiesTranscription.is_(True)
			).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())

	sub_q = inner.subquery('sub_q')
	sel_stmt = select([sub_q.c.rawPieceId], distinct=True, from_obj=sub_q
		).where(sub_q.c.subTaskId==subTaskId)

	return set([r.rawPieceId for r in SS.bind.execute(sel_stmt)])

# SUB_TASK_BATCHING
@MyFilter.register
def filter_sub_task_batching(task, subTaskId):
	if subTaskId == MyFilter.ANY:
		q1 = SS.query(m.PageMember.rawPieceId
			).distinct(m.PageMember.rawPieceId
			).filter(m.PageMember.taskId==task.taskId
			).filter(m.PageMember.rawPieceId.isnot(None))

		q2 = SS.query(m.WorkEntry.rawPieceId
			).distinct(m.WorkEntry.rawPieceId
			).filter(m.WorkEntry.entryId.in_(
				SS.query(m.PageMember.workEntryId
				).filter(m.PageMember.taskId==task.taskId
				).filter(m.PageMember.workEntryId.isnot(None))))
		q = q1.union(q2)
	else:
		try:
			subTaskId = int(subTaskId)
		except:
			raise ValueError(_('invalid sub task id'.format(subTaskId)))

		subTask = m.SubTask.query.get(subTaskId)
		if not subTask or subTaskId != task.taskId:
			return set()

		if subTask.workType in (m.WorkType.WORK, m.WorkType.REWORK):
			q = SS.query(m.PageMember.rawPieceId
				).distinct(m.PageMember.rawPieceId
				).filter(m.PageMember.taskId==task.taskId
				).filter(m.PageMember.subTaskId==subTaskId)
		elif subTask.workType in (m.WorkType.QA):
			q = SS.query(m.WorkEntry.rawPieceId
				).distinct(m.WorkEntry.rawPieceId
				).filter(m.WorkEntry.entryId.in_(
					SS.query(m.PageMember.workEntryId
					).filter(m.PageMember.taskId==task.taskId
					).filter(m.PageMember.subTaskId==subTaskId)))

	return [r.rawPieceId for r in q.all()]


# WORK_TYPE_WORK
@MyFilter.register
def filter_work_type_work(task, workOption, workTypeId):
	try:
		workTypeId = int(workTypeId)
	except:
		raise ValueError(_('invalid work type id: {}').format(workTypeId))

	inner = SS.query(m.WorkEntry.rawPieceId, m.WorkEntry.workTypeId
		).distinct(m.WorkEntry.rawPieceId
		).filter(m.WorkEntry.taskId==task.taskId)

	if workOption == MyFilter.ANY:
		inner = inner.filter(m.WorkEntry.workTypeId==workTypeId)

	elif workOption == MyFilter.MOST_RECENT:
		inner = inner.order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())

	elif workOption == MyFilter.MOST_RECENT_MODIFIED:
		inner = inner.filter(m.WorkEntry.modifiesTranscription
			).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())

	sub_q = inner.subquery('sub_q')
	sel_stmt = select([sub_q.c.rawPieceId], from_obj=sub_q
		).where(sub_q.c.workTypeId==workTypeId)
	return set([r.rawPieceId for r in SS.bind.execute(sel_stmt)])


# WORK_TYPE_BATCHING
@MyFilter.register
def filter_work_type_batching(task, workTypeId):

	workType = m.WorkType.query.get(workTypeId)
	if not workType:
		raise ValueError(_('invalid work type id: {}').format(workTypeId))

	if workType.name in (m.WorkType.WORK, m.WorkType.REWORK):
		q = SS.query(m.PageMember.rawPieceId
			).distinct(m.PageMember.rawPieceId
			).filter(m.PageMember.taskId==task.taskId
			).filter(m.PageMember.workType==workType.name)
	elif workType.name == m.WorkType.QA:
		q = SS.query(m.WorkEntry.rawPieceId
			).distinct(m.WorkEntry.rawPieceId
			).filter(m.WorkEntry.taskId==task.taskId
			).filter(m.WorkEntry.entryId.in_(SS.query(m.PageMember.workEntryId
				).filter(m.PageMember.taskId==task.taskId
				).filter(m.PageMember.workType==m.WorkType.QA)))
	else:
		return set()
	return set([r.rawPieceId for r in q.all()])

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
		task = m.Task.query.get(taskId)
		if taskId is None:
			raise ValueError(_('must specify taskId'))

		filters = {
			True: [],  # inclusive
			False: [], # exclusive
		}
		for f in selection.filters:
			filters[f.isInclusive].append(f)
		if len(filters[True]):
			rs = set()
		else:
			rs = set([r.rawPieceId for r in SS.query(m.RawPiece.rawPieceId
				).filter(m.RawPiece.taskId==taskId)])
		for f in filters[True]:
			result = MyFilter.run(f, task)
			rs |= result
		for f in filters[False]:
			result = MyFilter.run(f, task)
			rs -= result
		rs = sorted(rs)
		if selection.limit != None:
			limit = min(selection.limit, len(rs))
			rs = random.sample(rs, limit)
		return rs
for key, value in Selector.FILTER_TYPES.iteritems():
	setattr(Selector, key, value)
del key, value
