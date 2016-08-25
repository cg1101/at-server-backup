
import datetime

from sqlalchmey import and_, select, func

from app.util import Converter
from db.db import SS
import db.model as m

class MyFilter(object):
	ON = 'on'
	BEFORE = 'before'
	AFTER = 'after'

	EQUALS = '='
	NOT_EQUALS = '!='
	GREATER_THAN = '>'
	LESS_THAN = '<'

	FIRST = 'first'
	ANY = 'any'
	MOST_RECENT = 'mostrecent'
	MOST_RECENT_MODIFIED = 'mostrecentmodified'

	TRUE = 'true'
	FALSE = 'false'

	TEXT = 'text'
	REGEX = 'regex'


# SOURCE_TAG
def filter_source_tag(task, tagId):
	if tagId == MyFilter.ANY:
		tagId = None
		cond = m.RawPiece.rawText.contains('tagid=')
	else:
		try:
			tagId == int(tagId)
		except:
			raise ValueError('invalid tag id: {}'.format(tagId))
		cond = m.RawPiece.rawText.contains('tagid="{}"'.format(tagId))

	q = SS.query(m.RawPiece.rawPieceId
		).filter(m.RawPiece.taskId==task.taskId
		).filter(cond)

	return set([r.rawPieceId for r in q.all()])


# RAW_TEXT
def filter_raw_text(task, text, searchType=MyFilter.TEXT):

	if searchType == MyFilter.TEXT:
		func_ok = lambda (s): s.find(text) >= 0
	elif searchType == MyFilter.REGEX:
		try:
			pattern = re.compile(text)
		except:
			raise ValueError('invalid regular expression: {}'.format(text))
		func_ok = lambda (s): pattern.search(s)
	else:
		raise ValueError('invalid search type: {}'.format(searchType))

	def check(t):
		try:
			extractText = Converter.asExtract(t)
			return func_ok(extractText)
		except:
			return False

	q = SS.query(m.RawPiece.rawPieceId, m.RawPiece.rawText
		).filter(m.RawPiece.taskId==task.taskId)

	return set([r.rawPieceId for r in q.all() if check(r.rawText)])


# ALLOCATION_CONTEXT
def filter_allocation_context(task, text):
	cond = m.RawPiece.allocationContext == text

	q = SS.query(m.RawPiece.rawPieceId
		).filter(m.RawPiece.taskId==task.taskId
		).filter(cond)

	return set([r.rawPieceId for r in q.all()])


# TRANSCRIBED
def filter_transcribed(task, transcribedOption):
	if transcribedOption == MyFilter.TRUE:
		cond = m.RawPiece.isNew.isnot(True)
	elif transcribedOption == MyFilter.FALSE:
		cond = m.RawPiece.isNew.is_(True)

	q = SS.query(m.RawPiece.rawPieceId
		).filter(m.RawPiece.taskId==task.taskId
		).filter(cond)

	return set([r.rawPieceId for r in q.all()])


# LOAD
def filter_load(task, loadOption, loadId):
	try:
		loadId = int(loadId)
	except:
		raise ValueError('invalid load id: {}'.format(loadId))

	if loadOption == MyFilter.EQUALS:
		cond = m.RawPiece.loadId==loadId
	elif loadOption == MyFilter.NOT_EQUALS:
		cond = m.RawPiece.loadId!=loadId
	elif loadOption == MyFilter.LESS_THAN:
		cond = m.RawPiece.loadId<loadId
	elif loadOption == MyFilter.GREATER_THAN:
		cond = m.RawPiece.loadId>loadId
	else:
		raise ValueError('invalid load option: {}'.format(loadOption))

	q = SS.query(m.RawPiece.rawPieceId
		).filter(m.RawPiece.taskId==task.taskId
		).filter(cond)

	return set([r.rawPieceId for r in q.all()])


# SOURCE_WORD_COUNT
def filter_word_count(task, wordCountOption, words):
	try:
		words = int(words)
	except:
		raise ValueError('invalid word count: {}'.format(words))
	if wordCountOption == MyFilter.EQUALS:
		cond = m.RawPiece.words == words
	elif wordCountOption == MyFilter.GREATER_THAN:
		cond = m.RawPiece.words > words
	elif wordCountOption == MyFilter.LESS_THAN:
		cond = m.RawPiece.words < words
	else:
		raise ValueError('invalid word count option: {}'.format(words))

	q = SS.query(m.RawPiece.rawPieceId
		).filter(m.RawPiece.taskId==task.taskId
		).filter(cond)

	return set([r.rawPieceId for r in q.all()])



# DATE_SINGLE
def filter_date_single(task, workOption, dateOption, date):
	try:
		date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
	except ValueError, e:
		raise ValueError('invalid date value: {}'.format(date))

	# TODO: use tz should be used
	startTime = datetime.datetime(date.year, d.month, d.day)
	endTime = startTime + datetime.timedelta(days=1)

	if dateOption == MyFilter.ON:
		cond = and_(m.WorkEntry.created >= startTime, m.WorkEntry.created < endTime)
	elif dateOption == MyFilter.BEFORE:
		cond = m.WorkEntry.created < startTime
	elif dateOption == MyFilter.AFTER:
		cond = m.WorkEntry.created >= endTime
	else:
		raise ValueError('invalid date option: {}'.format(dateOption))
	
	q = SS.query(m.WorkEntry.rawPieceId
		).distinct(m.WorkEntry.rawPieceId
		).filter(m.WorkEntry.taskId==task.taskId
		).filter(cond)

	# utterances first worked on
	if workOption == MyFilter.FIRST:
		q = q.order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created)

		# cursor.execute('''
		# 	SELECT rawPieceId
		# 	FROM
		# 		(SELECT DISTINCT ON (rawPieceId) *
		# 		FROM workentries
		# 		WHERE taskID = %s
		# 		ORDER BY rawPieceId, created ASC) h
		# 	WHERE %s
		# ''' %(taskID, ' AND '.join(constraints)))

	# utterances worked on at any point
	elif workOption == MyFilter.ANY:
		pass
		# constraints.append('taskID = %s' %taskID)
		# cursor.execute('''
		# 	SELECT DISTINCT rawPieceId
		# 	FROM workentries
		# 	WHERE %s
		# ''' %' AND '.join(constraints))

	# utterances worked on most recently
	elif workOption == MyFilter.MOST_RECENT:
		q = q.order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())

		# cursor.execute('''
		# 	SELECT rawPieceId
		# 	FROM 
		# 		(SELECT DISTINCT ON (rawPieceId) *
		# 		FROM workentries
		# 		WHERE taskID = %s
		# 		ORDER BY rawPieceId, created DESC) h
		# 	WHERE %s
		# ''' %(taskID, ' AND '.join(constraints)))

	# utterances modified most recently
	elif workOption == MyFilter.MOST_RECENT_MODIFIED:
		q = q.filter_by(m.WorkEntry.modifiesTranscription
			).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())
		# cursor.execute('''
		# 	SELECT rawPieceId
		# 	FROM
		# 		(SELECT DISTINCT ON (rawPieceId) *
		# 		FROM workentries
		# 		WHERE
		# 			taskID = %s AND
		# 			workTypeID IN (SELECT workTypeID FROM workTypes WHERE modifiesTranscription)
		# 		ORDER BY rawPieceId, created DESC) h
		# 	WHERE %s 
		# ''' %(taskID, ' AND '.join(constraints)))
	
	else:
		raise ValueError('invalid work option: {}'.format(workOption))

	return set([r.rawPieceId for r in q.all()])


# DATE_INTERVAL
def filter_date_interval(task, workOption, startDate, endDate):
	try:
		startDate = datetime.datetime.strptime(startDate, '%Y-%m-%d').date()
		startDate = datetime.datetime(startDate.year, startDate.month, startDate.day)
	except:
		raise ValueError('invalid start date: {}'.format(startDate))
	try:
		endDate = datetime.datetime.strptime(endDate, '%Y-%m-%d').date()
		endDate = datetime.datetime(endDate.year, endDate.month, endDate.day)
	except:
		raise ValueError('invalid end date: {}'.format(endDate))

	q = SS.query(m.WorkEntry.rawPieceId
		).distinct(m.WorkEntry.rawPieceId
		).filter(m.WorkEntry.taskId==task.taskId
		).filter(and_(m.WorkEntry.created>=startDate, m.WorkEntry.created<=endDate))

	# utterances first worked on
	if workOption == MyFilter.FIRST:
		q = q.order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created)
		# cursor.execute('''
		# 	SELECT rawPieceId
		# 	FROM
		# 		(SELECT DISTINCT ON (rawPieceId) *
		# 		FROM workentries
		# 		WHERE taskID = %s
		# 		ORDER BY rawPieceId, created ASC) h
		# 	WHERE
		# 		created >= %s AND
		# 		created <= %s
		# ''', (taskID, startDate, endDate))

	# utterances worked on at any point
	elif workOption == MyFilter.ANY:
		pass
		# cursor.execute('''
		# 	SELECT DISTINCT rawPieceId
		# 	FROM workentries
		# 	WHERE
		# 		taskID = %s AND
		# 		created >= %s AND
		# 		created <= %s
		# ''', (taskID, startDate, endDate))

	# utterances worked on most recently
	elif workOption == MyFilter.MOST_RECENT:
		q = q.order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())
		# cursor.execute('''
		# 	SELECT rawPieceId
		# 	FROM 
		# 		(SELECT DISTINCT ON (rawPieceId) *
		# 		FROM workentries
		# 		WHERE taskID = %s
		# 		ORDER BY rawPieceId, created DESC) h
		# 	WHERE
		# 		created >= %s AND
		# 		created <= %s
		# ''', (taskID, startDate, endDate))

	# utterances modified most recently
	elif workOption == MyFilter.MOST_RECENT_MODIFIED:
		q = q.filter(m.WorkEntry.modifiesTranscription
			).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())
		# cursor.execute('''
		# 	SELECT rawPieceId
		# 	FROM
		# 		(SELECT DISTINCT ON (rawPieceId) *
		# 		FROM workentries
		# 		WHERE
		# 			taskID = %s AND
		# 			workTypeID IN (SELECT workTypeID FROM workTypes WHERE modifiesTranscription)
		# 		ORDER BY rawPieceId, created DESC) h
		# 	WHERE 
		# 		created >= %s AND
		# 		created <= %s
		# ''', (taskID, startDate, endDate))
	
	else:
		raise ValueError('invalid work option: {}'.format(workOption))

	return set([r.rawPieceId for r in q.all()])


# TEXT
def filter_text(task, text, searchType=MyFilter.TEXT):
	if searchType == MyFilter.TEXT:
		pass
	elif searchType == MyFilter.REGEX:
		try:
			pattern = re.compile(text)
		except:
			raise ValueError('invalid regular expression: {}'.format(text))

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
def filter_user(task, workOption, userId):
	try:
		userId = int(userId)
	except:
		raise ValueError('invalid user id: {}'.format(userId))
	# TODO: check user is working on this task?
	inner = SS.query(m.WorkEntry.rawPieceId.label('rawPieceId'),
			m.WorkEntry.userId.label('userId')
		).distinct(m.WorkEntry.rawPieceId
		).filter(m.WorkEntry.taskId==task.taskId)
	if workOption == MyFilter.ANY:
		inner = inner.filter(m.WorkEntry.userId==userId)
		# cursor.execute("""
		# 	SELECT DISTINCT rawpieceid
		# 	FROM workentries
		# 	WHERE
		# 		taskID = %s AND
		# 		userID = %s
		# """, (taskID, userID))
	elif workOption == MyFilter.FIRST:
		inner = inner.order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created)
		# cursor.execute("""
		# 	SELECT rawpieceid
		# 	FROM
		# 		(SELECT DISTINCT ON (rawpieceid) *
		# 		FROM workentries
		# 		WHERE taskID = %s
		# 		ORDER BY rawpieceid, created ASC) h
		# 	WHERE userID = %s
		# """, (taskID, userID))
	elif workOption == MyFilter.MOST_RECENT:
		inner = inner.order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())
		# cursor.execute("""
		# 	SELECT rawpieceid
		# 	FROM
		# 		(SELECT DISTINCT ON (rawpieceid) *
		# 		FROM workentries
		# 		WHERE taskID = %s
		# 		ORDER BY rawpieceid, created DESC) h
		# 	WHERE userID = %s
		# """, (taskID, userID))
	elif workOption == MyFilter.MOST_RECENT_MODIFIED:
		inner = inner.filter(m.WorkEntry.modifiesTranscription.is_(True)
			).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())
		# cursor.execute("""
		# 	SELECT rawpieceid
		# 	FROM
		# 		(SELECT DISTINCT ON (rawpieceid) *
		# 		FROM workentries
		# 		WHERE
		# 			taskID = %s AND
		# 			workTypeID IN (SELECT workTypeID FROM workTypes WHERE modifiesTranscription)
		# 		ORDER BY rawpieceid, created DESC) h
		# 	WHERE userID = %s
		# """, (taskID, userID))
	else:
		raise ValueError('invalid work option: {}'.format(workOption))

	sub_q = inner.subquery('sub_q')
	sel_stmt = select([sub_q.c.rawPieceId], distinct=True,
		from_obj=sub_q).where(sub_q.c.userId==userId)
	return set([r.rawPieceId for r in SS.bind.execute(sel_stmt)])


# TAG
def filter_tag(task, tagId):
	if tagId == MyFilter.ANY:
		tagId = None
		key_string = 'tagid='
	else:
		try:
			tagId == int(tagId)
		except:
			raise ValueError('invalid tag id: {}'.format(tagId))
		key_string = 'tagid="{}"'.format(tagId)

	q = SS.query(m.WorkEntry.rawPieceId, m.WorkEntry.result
		).distinct(m.WorkEntry.rawPieceId
		).filter(m.WorkEntry.taskId==task.taskId
		).filter(m.WorkEntry.modifiesTranscription
		).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())

	return set([r.rawPieceId for r in q.all() if r.result.find(key_string) > 0])


# RESULT_WORD_COUNT
def filter_word_count(task, wordCountOption, words):
	try:
		words = int(words)
	except:
		raise ValueError('invalid words: {}'.format(words))

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
def filter_word_count_gap(task, wordCountOption, gap):
	try:
		percentage = int(gap.rstrip('%')) / 100.0
	except:
		raise ValueError('invalid word count gap: {}'.format(gap))

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
def filter_label(task, labelId):
	if labelId == MyFilter.ANY:
		labelId = None
	else:
		try:
			labelId = int(labelId)
		except:
			raise ValueError('invalid label id: {}'.format(labelId))

	inner = SS.query(m.WorkEntry.rawPieceId, m.WorkEntry.entryId
		).distinct(m.WorkEntry.rawPieceId
		).filter(m.WorkEntry.taskId==task.taskId
		).filter(m.WorkEntry.modifiesTranscription
		).order_by(m.WorkEntry.rawPieceId, m.WorkEntry.created.desc())

	sub_q = inner.subquery('sub_q')
	q = sub_q.join(m.AppliedLabel, sub_q.c.entryId==m.AppliedLabel.entryId)
	if labelId != None:
		q = q.where(m.AppliedLabel==labelId)

	sel_stmt = select(q.c.rawPieceId, distinct=True, from_obj=q)
	return set([r.rawPieceId for r in SS.bind.execute(sel_stmt)])


# QA_ERROR_SEVERITY
def filter_qa_severity(task, isMoreThan, score, isCorrect):
	try:
		assert isMoreThan in (MyFilter.TRUE, MyFilter.FALSE)
	except:
		raise ValueError('invalid option value: {}'.format(isMoreThan))
	else:
		isMoreThan = isMoreThan == MyFilter.TRUE
	try:
		assert isCorrect in (MyFilter.TRUE, MyFilter.FALSE)
	except:
		raise ValueError('invalid option value: {}'.format(isCorrect))
	else:
		isCorrect = isCorrect == MyFilter.TRUE
	try:
		score = float(score)
	except:
		raise ValueError('invalid score value: {}'.format(score))
	
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
def filter_qa_error_type(task, errorTypeId):
	try:
		errorTypeId = int(erorrTypeId)
	except:
		raise ValueError('invalid error type id: {}'.format(errorTypeId))

	taskErrorType = m.TaskErrorType.query.get((task.taskId, errorTypeId))
	if not taskErrorType:
		return set()

	# latest QA result
	q1 = SS.query(m.WorkEntry.entryId, m.WorkEntry.qaedEntryId,
			m.WorkEntry.rawPieceId
		).distinct(m.WorkEntry.qaedEntryId
		).filter(m.WorkEntry.taskId==task.taskId
		).filter(m.WorkEntry.workType==m.WorkType.QA
		).order_by(m.WorkEntry.qaedEntryId, m.WorkEntry.created.desc())

	sub_q = q1.subquery('sub_q')

	q = SS.query(sub_q.c.rawPieceId
		).distinct(sub_q.c.rawPieceId
		).join(m.AppliedError, m.AppliedError.entryId==sub_q.c.entryId
		).filter(m.AppliedError.errorTypeId==errorTypeId)

	return set([r.rawPieceId for r in q.all()])

# QA_ERROR_CLASS
def filter_qa_error_class(task, errorClassId):
	try:
		errorClassId = int(errorClassId)
	except:
		raise ValueError('invalid error class id: {}'.format(errorClassId))
	# latest QA result
	q1 = SS.query(m.WorkEntry.entryId, m.WorkEntry.qaedEntryId,
			m.WorkEntry.rawPieceId
		).distinct(m.WorkEntry.qaedEntryId
		).filter(m.WorkEntry.taskId==task.taskId
		).filter(m.WorkEntry.workType==m.WorkType.QA
		).order_by(m.WorkEntry.qaedEntryId, m.WorkEntry.created.desc())
	sub_q = q1.subquery('sub_q')
	q = SS.query(sub_q.c.rawPieceId
		).distinct(sub_q.c.rawPieceId
		).join(m.AppliedError, m.AppliedError.entryId==sub_q.c.entryId
		).filter(m.AppliedError.errorTypeId.in_(
			SS.query(m.ErrorType.errorTypeId
				).filter(m.ErrorType.errorClassId==errorClassId)))
	return set([r.rawPieceId for r in q.all()])

# PP_GROUP
def filter_pp_group(task, groupId):
	if groupId == MyFilter.ANY:
		cond = m.RawPiece.groupId.isnot(None)
	else:
		try:
			groupId = int(groupId)
		except:
			raise ValueError('invalid group id: {}'.format(groupId))
		cond = m.RawPiece.groupId == groupId

	q = SS.query(m.RawPiece.rawPieceId
		).filter(m.RawPiece.taskId==task.taskId
		).filter(cond)

	return set([r.rawPieceId for r in q.all()])

# CUSTOM_GROUP
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
			raise ValueError('invalid group id: {}'.format(groupId))
		q = q.filter(m.CustomUtteranceGroup.groupId==groupId)

	return set([r.rawPieceId for r in q.all()])


# SUB_TASK_WORK
def filter_sub_task_work(task, workOption, subTaskId):
	try:
		subTaskId = int(subTaskId)
	except:
		raise ValueError('invalid sub task id: {}'.format(subTaskId))

	subTask = m.SubTask.query.get(subTaskId)
	if not subTask or subTask.taskId != task.taskId:
		return set()

	inner == SS.query(m.WorkEntry.rawPieceId, m.WorkEntry.subTaskId
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

	return [r.rawPieceId for r in SS.bind.execute(sel_stmt)]

# SUB_TASK_BATCHING
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
			raise ValueError('invalid sub task id'.format(subTaskId))
		
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
def filter_work_type_work(task, workOption, workTypeId):
	try:
		workTypeId = int(workTypeId)
	except:
		raise ValueError('invalid work type id: {}'.format(workTypeId))

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
	sel_stmt = select(sub_q.c.rawPieceId, from_obj=sub_q
		).where(sub_q.c.workTypeId==workTypeId)
	return set([r.rawPieceId for r in SS.bind.execute(sel_stmt)])


# WORK_TYPE_BATCHING
def filter_work_type_batching(task, workTypeId):

	workType = m.WorkType.query.get(workTypeId)
	if not workType:
		raise ValueError('invalid work type id: {}'.format(workTypeId))

	if workType.name in (m.WorkType.WORK, m.WorkType.REWORK):
		q = SS.query(m.PageMember.rawPieceId
			).distinct(m.PageMember.rawPieceId
			).filter(m.PageMember.taskId==task.taskId
			).filter(m.PageMember.workType==workType.name)
	elif workType.name == m.WorkType.QA:
		q = SS.query(m.WorkEntry.rawPieceId
			).distinct(m.WorkEntry.rawPieceId
			).filter(.WorkEntry.taskId==task.taskId
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
		if taskId is None:
			raise ValueError('must specify taskId')
		limit = min(selection.limit, 5)
		rs = [r.rawPieceId for r in SS.query(m.RawPiece.rawPieceId
			).filter_by(taskId=taskId
			).order_by(m.RawPiece.rawPieceId
			).all()[:limit]]
		return rs
for key, value in Selector.FILTER_TYPES.iteritems():
	setattr(Selector, key, value)
del key, value
