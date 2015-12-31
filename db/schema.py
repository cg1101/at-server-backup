
from sqlalchemy import *
from sqlalchemy.dialects.postgresql import *
from sqlalchemy import event

from mytypes import JsonString, MutableDict

metadata = MetaData()
#metadata = MetaData(naming_convention={
#        "ix": 'ix_%(column_0_label)s',
#        "uq": "uq_%(table_name)s_%(column_0_name)s",
#        "ck": "ck_%(table_name)s_%(constraint_name)s",
#        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
#        "pk": "pk_%(table_name)s",
#})

event.listen(metadata, 'before_create', DDL('CREATE SCHEMA IF NOT EXISTS q'))

# Level 000

t_pdb_projects = Table('pdb_projects', metadata,
	Column('project_id', Integer, primary_key=True, autoincrement=False, key=u'projectId', doc=''),
	Column('name', Text, nullable=False, unique=True, key=u'name', doc=''),
)

t_pdb_tasks = Table('pdb_tasks', metadata,
	Column('task_id', Integer, primary_key=True, autoincrement=False, key=u'taskId', doc=''),
	Column('project_id', Integer, ForeignKey('pdb_projects.projectId'), nullable=False, key=u'projectId', doc=''),
	Column('work_area', Text, key=u'workArea', doc=''),
	Column('name', Text, key=u'name', doc=''),
)

t_ao_payment_classes = Table('ao_payment_classes', metadata,
	Column('paymentclassid', Integer, primary_key=True, autoincrement=False, key=u'paymentClassId', doc=''),
	Column('name', Text, nullable=False, unique=True, key=u'name', doc=''),
	Column('created', TIMESTAMP(timezone=True), server_default=text('now()'), key=u'created', doc='')
)

t_ao_payment_types = Table('ao_payment_types', metadata,
	Column('paymenttypeid', Integer, primary_key=True, autoincrement=False, key=u'paymentTypeId', doc=''),
	Column('name', Text, nullable=False, unique=True, key=u'name', doc=''),
	Column('created', TIMESTAMP(timezone=True), server_default=text('now()'), key=u'created', doc='')
)

t_ao_payrolls = Table('ao_payrolls', metadata,
	Column('payrollid', Integer, primary_key=True, autoincrement=False, key=u'payrollId', doc=''),
	Column('startdate', Date, nullable=False, key=u'startDate', doc=''),
	Column('enddate', Date, nullable=False, key=u'endDate', doc=''),
)

t_ao_users = Table('ao_users', metadata,
	Column('userid', Integer, primary_key=True, autoincrement=False, key=u'userId', doc=''),
	Column('emailaddress', Text, nullable=False, key=u'emailAddress', doc=''),
	Column('active', Text, nullable=False, server_default=text('TRUE'), key=u'isActive', doc=''),
	Column('familyname', Text, key=u'familyName', doc=''),
	Column('givenname', Text, key=u'givenName', doc=''),
)

# t_ao_countries = Table('ao_countries', metadata,
# 	Column('country_id', Integer, primary_key=True, autoincrement=False, key=u'countryId', doc=''),
# 	Column('name', Text, nullable=False, unique=True, key=u'name', doc=''),
# 	Column('iso2', VARCHAR(2), nullable=False, unique=True, key=u'iso2', doc=''),
# 	Column('iso3', VARCHAR(3), nullable=False, unique=True, key=u'iso3', doc=''),
# )

# t_ao_languages = Table('ao_languages', metadata,
# 	Column('language_id', Integer, primary_key=True, autoincrement=False, key=u'languageId', doc=''),
# 	Column('name', Text, nullable=False, unique=True, key=u'name', doc=''),
# 	Column('iso3', VARCHAR(3), nullable=False, unique=True, key=u'iso3', doc=''),
# 	Column('ltr', Boolean, nullable=False, server_default=text('TRUE'), key=u'ltr', doc=''),
# )


# Level 010


t_batchingmodes =  Table('batchingmodes', metadata,
	Column(u'modeid', INTEGER, primary_key=True, nullable=False, key=u'modeId', doc=''),
	Column(u'name', TEXT, nullable=False, unique=True, key=u'name', doc=''),
	Column(u'description', TEXT, key=u'description', doc=''),
	Column(u'requirescontext', BOOLEAN, nullable=False, server_default=text(u'true'), key=u'requiresContext', doc=''),
)


t_errorclasses =  Table('errorclasses', metadata,
	Column(u'errorclassid', INTEGER, primary_key=True, nullable=False, key=u'errorClassId', doc=''),
	Column(u'name', TEXT, nullable=False, unique=True, key=u'name', doc=''),
)


t_filehandlers =  Table('filehandlers', metadata,
	Column(u'handlerid', INTEGER, primary_key=True, nullable=False, key=u'handlerId', doc=''),
	Column(u'name', TEXT, nullable=False, unique=True, key=u'name', doc=''),
	Column(u'description', TEXT, key=u'description', doc=''),
)


t_jobs =  Table('jobs', metadata,
	Column(u'jobid', INTEGER, primary_key=True, nullable=False, key=u'jobId', doc=''),
	Column(u'added', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'added', doc=''),
	Column(u'started', TIMESTAMP(timezone=False), key=u'started', doc=''),
	Column(u'completed', TIMESTAMP(timezone=False), key=u'completed', doc=''),
	Column(u'failed', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'failed', doc=''),
	Column(u'isnew', BOOLEAN, nullable=False, server_default=text(u'true'), key=u'isNew', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'pid', INTEGER, key=u'pid', doc=''),
)


t_labelsets =  Table('labelsets', metadata,
	Column(u'labelsetid', INTEGER, primary_key=True, nullable=False, key=u'labelSetId', doc=''),
	Column(u'created', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'created', doc=''),
)


t_rates =  Table('rates', metadata,
	Column(u'rateid', INTEGER, primary_key=True, nullable=False, key=u'rateId', doc=''),
	Column(u'name', TEXT, nullable=False, unique=True, key=u'name', doc=''),
	Column(u'centsperutt', DOUBLE_PRECISION, nullable=False, key=u'standardValue', doc=''),
	Column(u'maxcentsperutt', DOUBLE_PRECISION, nullable=False, key=u'maxValue', doc=''),
	Column(u'targetaccuracy', DOUBLE_PRECISION, nullable=False, key=u'targetAccuracy', doc=''),
	CheckConstraint('targetaccuracy>=0 AND targetaccuracy<=1'),
)


t_tagimagepreviews =  Table('tagimagepreviews', metadata,
	Column(u'previewid', INTEGER, primary_key=True, nullable=False, key=u'previewId', doc=''),
	Column(u'image', LargeBinary, nullable=False, key=u'image', doc=''),
	Column(u'created', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'created', doc=''),
)


t_tagsets =  Table('tagsets', metadata,
	Column(u'tagsetid', INTEGER, primary_key=True, nullable=False, key=u'tagSetId', doc=''),
	Column(u'created', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'created', doc=''),
	Column(u'lastupdated', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'lastUpdated', doc=''),
)


t_tasktypes =  Table('tasktypes', metadata,
	Column(u'tasktypeid', INTEGER, primary_key=True, nullable=False, key=u'taskTypeId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'description', TEXT, key=u'description', doc=''),
)


t_taskreporttypes =  Table('taskreporttypes', metadata,
	Column(u'reporttypeid', INTEGER, primary_key=True, nullable=False, key=u'reportTypeId', doc=''),
	Column(u'name', TEXT, nullable=False, unique=True, key=u'name', doc=''),
	Column(u'isstandard', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'isStandard', doc=''),
	Column(u'restrictusersallowed', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'restrictUsersAllowed', doc=''),
)


t_worktypes =  Table('worktypes', metadata,
	Column(u'worktypeid', INTEGER, primary_key=True, nullable=False, key=u'workTypeId', doc=''),
	Column(u'name', TEXT, nullable=False, unique=True, key=u'name', doc=''),
	Column(u'description', TEXT, key=u'description', doc=''),
	Column(u'modifiestranscription', BOOLEAN, nullable=False, key=u'modifiesTranscription', doc=''),
)


# Level 020

t_errortypes =  Table('errortypes', metadata,
	Column(u'errortypeid', INTEGER, primary_key=True, nullable=False, key=u'errorTypeId', doc=''),
	Column(u'name', TEXT, nullable=False, unique=True, key=u'name', doc=''),
	Column(u'errorclassid', INTEGER, nullable=False, key=u'errorClassId', doc=''),
	Column(u'defaultseverity', DOUBLE_PRECISION, nullable=False, key=u'defaultSeverity', doc=''),
	Column(u'isstandard', BOOLEAN, nullable=False, server_default=text(u'true'), key=u'isStandard', doc=''),
	ForeignKeyConstraint([u'errorClassId'], [u'errorclasses.errorClassId']),
	CheckConstraint('defaultseverity >= 0 AND defaultseverity <= 1'),
)


t_filehandleroptions =  Table('filehandleroptions', metadata,
	Column(u'optionid', INTEGER, primary_key=True, nullable=False, key=u'optionId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'label', TEXT, key=u'label', doc=''),
	Column(u'handlerid', INTEGER, nullable=False, key=u'handlerId', doc=''),
	Column(u'datatype', TEXT, nullable=False, key=u'dataType', doc=''),
	Column(u'widgettype', TEXT, key=u'widgetType', doc=''),
 	Column(u'params', MutableDict.as_mutable(JsonString), key=u'params', doc=''),
 	UniqueConstraint(u'name', u'handlerId'),
	ForeignKeyConstraint([u'handlerId'], [u'filehandlers.handlerId']),
)


t_labelgroups =  Table('labelgroups', metadata,
	Column(u'labelgroupid', INTEGER, primary_key=True, nullable=False, key=u'labelGroupId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'ismandatory', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'isMandatory', doc=''),
	Column(u'labelsetid', INTEGER, nullable=False, key=u'labelSetId', doc=''),
	Column(u'dropdowndisplay', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'dropDownDisplay', doc=''),
	UniqueConstraint(u'labelSetId', u'name'),
	ForeignKeyConstraint([u'labelSetId'], [u'labelsets.labelSetId']),
)


t_ratedetails =  Table('ratedetails', metadata,
	Column(u'rateid', INTEGER, nullable=False, key=u'rateId', doc=''),
	Column(u'centsperutt', DOUBLE_PRECISION, nullable=False, key=u'value', doc=''),
	Column(u'accuracy', DOUBLE_PRECISION, nullable=False, key=u'accuracy', doc=''),
	UniqueConstraint(u'rateId', u'accuracy'),
	PrimaryKeyConstraint(u'rateId', u'accuracy'),
	ForeignKeyConstraint([u'rateId'], [u'rates.rateId']),
	CheckConstraint('accuracy>=0 AND accuracy<=1'),
)


t_tags =  Table('tags', metadata,
	Column(u'tagid', INTEGER, primary_key=True, nullable=False, key=u'tagId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'tagsetid', INTEGER, nullable=False, key=u'tagSetId', doc=''),
	Column(u'tagtype', TEXT, nullable=False, key=u'tagType', doc=''),
	Column(u'colour', TEXT, key=u'color', doc=''),
	Column(u'isforeground', BOOLEAN, key=u'isForeground', doc=''),
	Column(u'image', LargeBinary, key=u'image', doc=''),
	Column(u'extractstart', TEXT, nullable=False, key=u'extractStart', doc=''),
	Column(u'extractend', TEXT, key=u'extractEnd', doc=''),
	Column(u'shortcutkey', CHAR(length=1), key=u'shortcutKey', doc=''),
	Column(u'enabled', BOOLEAN, nullable=False, server_default=text(u'true'), key=u'enabled', doc=''),
	Column(u'surround', BOOLEAN, nullable=False, key=u'surround', doc=''),
	Column(u'extend', BOOLEAN, nullable=False, key=u'extend', doc=''),
	Column(u'split', BOOLEAN, nullable=False, key=u'split', doc=''),
	Column(u'tooltip', TEXT, key=u'tooltip', doc=''),
	Column(u'description', TEXT, key=u'description', doc=''),
	Column(u'isdynamic', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'isDynamic', doc=''),
	UniqueConstraint(u'tagSetId', u'name'),
	UniqueConstraint(u'color', u'isForeground', u'tagSetId'),
	ForeignKeyConstraint([u'tagSetId'], [u'tagsets.tagSetId']),
	CheckConstraint("shortcutkey IS NULL OR shortcutkey <> ' '"),
)


# Level 030


t_labels =  Table('labels', metadata,
	Column(u'labelid', INTEGER, primary_key=True, nullable=False, key=u'labelId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'description', TEXT, key=u'description', doc=''),
	Column(u'hotkey', CHAR(length=1), key=u'shortcutKey', doc=''),
	Column(u'extract', TEXT, nullable=False, key=u'extract', doc=''),
	Column(u'labelgroupid', INTEGER, key=u'labelGroupId', doc=''),
	Column(u'labelsetid', INTEGER, nullable=False, key=u'labelSetId', doc=''),
	UniqueConstraint(u'labelSetId', u'extract'),
	UniqueConstraint(u'labelSetId', u'name'),
	UniqueConstraint(u'labelSetId', u'shortcutKey'),
	ForeignKeyConstraint([u'labelGroupId'], [u'labelgroups.labelGroupId']),
	ForeignKeyConstraint([u'labelSetId'], [u'labelsets.labelSetId']),
	CheckConstraint("hotkey<>' '"),
)
Index('labelsbylabelgroupid', t_labels.c.labelGroupId, unique=False)


# Level 100

t_payrolls =  Table('payrolls', metadata,
	Column(u'payrollid', INTEGER, primary_key=True, autoincrement=False, nullable=False, key=u'payrollId', doc=''),
	Column(u'updatedpayments', TIMESTAMP(timezone=False), key=u'updatedPayments', doc=''),
)


t_paymentclasses =  Table('paymentclasses', metadata,
	Column(u'paymentclassid', INTEGER, key=u'paymentClassId', doc=''),
)


t_paymenttypes =  Table('paymenttypes', metadata,
	Column(u'paymenttypeid', INTEGER, primary_key=True, autoincrement=False, nullable=False, key=u'paymentTypeId', doc=''),
)


t_projects =  Table('projects', metadata,
	Column(u'projectid', INTEGER, primary_key=True, autoincrement=False, nullable=False, key=u'projectId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'description', TEXT, key=u'description', doc=''),
	Column(u'created', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'created', doc=''),
	Column(u'migratedby', INTEGER, nullable=False, key=u'migratedBy', doc=''),
	ForeignKeyConstraint([u'migratedBy'], [u'users.userId']),
)


t_users =  Table('users', metadata,
	Column(u'userid', INTEGER, primary_key=True, autoincrement=False, nullable=False, key=u'userId', doc=''),
)


# Level 110


t_calculateduserpayrates =  Table('calculateduserpayrates', metadata,
	Column(u'rateid', INTEGER, nullable=False, key=u'rateId', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userId', doc=''),
	Column(u'hourlyrate', DOUBLE_PRECISION, nullable=False, key=u'hourlyRate', doc=''),
	Column(u't', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u't', doc=''),
	Column(u'changerid', INTEGER, nullable=False, key=u'changerId', doc=''),
	ForeignKeyConstraint([u'changerId'], [u'users.userId']),
	ForeignKeyConstraint([u'rateId'], [u'rates.rateId']),
	ForeignKeyConstraint([u'userId'], [u'users.userId']),
)


t_tasks =  Table('tasks', metadata,
	Column(u'taskid', INTEGER, primary_key=True, autoincrement=False, nullable=False, key=u'taskId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'projectid', INTEGER, nullable=False, key=u'projectId', doc=''),
	Column(u'tasktypeid', INTEGER, nullable=False, key=u'taskTypeId', doc=''),
	Column(u'status', TEXT, nullable=False, server_default=text(u"'active'::text"), key=u'status', doc=''),
	Column(u'src_dir', CHAR(length=3), nullable=False, server_default=text(u"'ltr'::bpchar"), key=u'srcDir', doc=''),
	Column(u'laststatuschange', TIMESTAMP(timezone=False), key=u'lastStatusChange', doc=''),
	Column(u'tagsetid', INTEGER, key=u'tagSetId', doc=''),
	Column(u'labelsetid', INTEGER, key=u'labelSetId', doc=''),
	Column(u'migrated', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'migrated', doc=''),
	Column(u'migratedby', INTEGER, key=u'migratedBy', doc=''),
	Column(u'handlerid', INTEGER, key=u'handlerId', doc=''),
	ForeignKeyConstraint([u'labelSetId'], [u'labelsets.labelSetId']),
	ForeignKeyConstraint([u'taskTypeId'], [u'tasktypes.taskTypeId']),
	ForeignKeyConstraint([u'projectId'], [u'projects.projectId']),
	ForeignKeyConstraint([u'tagSetId'], [u'tagsets.tagSetId']),
	ForeignKeyConstraint([u'handlerId'], [u'filehandlers.handlerId']),
	ForeignKeyConstraint([u'migratedBy'], [u'users.userId']),
	CheckConstraint("src_dir=ANY(ARRAY['ltr','rtl'])"),
	CheckConstraint("status=ANY(ARRAY['active','disabled','finished','closed','archived'])"),
)
Index('projectsmigratedby', t_tasks.c.migratedBy, unique=False)


t_tracking_events =  Table('tracking_events', metadata,
	Column(u'eventid', INTEGER, primary_key=True, nullable=False, key=u'eventId', doc=''),
	Column(u'eventtype', TEXT, nullable=False, key=u'eventType', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userId', doc=''),
	Column(u't_triggered_at', TIMESTAMP(timezone=True), key=u'tTriggeredAt', doc=''),
	Column(u'hostip', INET(), key=u'hostIp', doc=''),
	Column(u'details', MutableDict.as_mutable(JsonString), nullable=False, key=u'details', doc=''),
)


# Level 120


t_costperutterance =  Table('costperutterance', metadata,
	Column(u'taskid', INTEGER, primary_key=True, nullable=False, key=u'taskId', doc=''),
	Column(u'cutofftime', TIMESTAMP(timezone=False), nullable=False, key=u'cutOffTime', doc=''),
	Column(u'itemsdone', INTEGER, nullable=False, key=u'itemCount', doc=''),
	Column(u'unitsdone', INTEGER, nullable=False, key=u'unitCount', doc=''),
	Column(u'payrollid', INTEGER, primary_key=True, nullable=False, key=u'payrollId', doc=''),
	Column(u'amount', DOUBLE_PRECISION, nullable=False, key=u'paymentSubtotal', doc=''),
	ForeignKeyConstraint([u'payrollId'], [u'payrolls.payrollId']),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
)
Index('costperutterancebytaskid', t_costperutterance.c.taskId, unique=False)


t_loads =  Table('loads', metadata,
	Column(u'loadid', INTEGER, primary_key=True, nullable=False, key=u'loadId', doc=''),
	Column(u'createdby', INTEGER, nullable=False, key=u'createdBy', doc=''),
	Column(u'createdat', TIMESTAMP(timezone=True), nullable=False, server_default=text(u'now()'), key=u'createdAt', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	UniqueConstraint(u'loadId', u'taskId'),
	ForeignKeyConstraint([u'createdBy'], [u'users.userId']),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
)


t_otherpayments =  Table('otherpayments', metadata,
	Column(u'otherpaymentid', INTEGER, primary_key=True, nullable=False, key=u'otherPaymentId', doc=''),
	Column(u'payrollid', INTEGER, nullable=False, key=u'payrollId', doc=''),
	Column(u'identifier', TEXT, nullable=False, unique=True, key=u'identifier', doc=''),
	Column(u'paymenttypeid', INTEGER, nullable=False, key=u'paymentTypeId', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userId', doc=''),
	Column(u'amount', INTEGER, nullable=False, key=u'amount', doc=''),
	Column(u'added', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'added', doc=''),
	ForeignKeyConstraint([u'paymentTypeId'], [u'paymenttypes.paymentTypeId']),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
	ForeignKeyConstraint([u'payrollId'], [u'payrolls.payrollId']),
	ForeignKeyConstraint([u'userId'], [u'users.userId']),
)
Index('otherpaymentsbypayrollid', t_otherpayments.c.payrollId, unique=False)
Index('otherpaymentsbytaskid', t_otherpayments.c.taskId, unique=False)


t_overallqaprogresscache =  Table('overallqaprogresscache', metadata,
	Column(u'taskid', INTEGER, primary_key=True, nullable=False, key=u'taskId', doc=''),
	Column(u'endtime', TIMESTAMP(timezone=False), key=u'endTime', doc=''),
	Column(u'remaining', INTEGER, nullable=False, key=u'remaining', doc=''),
	Column(u'lastupdated', TIMESTAMP(timezone=False), nullable=False, key=u'lastUpdated', doc=''),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
)


t_overalltrprogresscache =  Table('overalltrprogresscache', metadata,
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'itemcount', INTEGER, nullable=False, key=u'itemCount', doc=''),
	Column(u'wordcount', INTEGER, nullable=False, key=u'wordCount', doc=''),
	Column(u'newitems', INTEGER, nullable=False, key=u'newItems', doc=''),
	Column(u'finished', INTEGER, nullable=False, key=u'finished', doc=''),
	Column(u'finishedlastweek', INTEGER, nullable=False, key=u'finishedLastWeek', doc=''),
	Column(u'lastupdated', TIMESTAMP(timezone=False), nullable=False, key=u'lastUpdated', doc=''),
	Column(u'overallaccuracy', DOUBLE_PRECISION, key=u'overallAccuracy', doc=''),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
)


t_overallworkprogresscache =  Table('overallworkprogresscache', metadata,
	Column(u'taskid', INTEGER, primary_key=True, nullable=False, key=u'taskId', doc=''),
	Column(u'total', INTEGER, nullable=False, key=u'total', doc=''),
	Column(u'newutts', INTEGER, nullable=False, key=u'newUtts', doc=''),
	Column(u'transcribed', INTEGER, nullable=False, key=u'transcribed', doc=''),
	Column(u'transcribedlastweek', INTEGER, nullable=False, key=u'transcribedLastWeek', doc=''),
	Column(u'lastupdated', TIMESTAMP(timezone=False), nullable=False, key=u'lastUpdated', doc=''),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
)


t_streams =  Table('streams', metadata,
	Column(u'streamid', INTEGER, primary_key=True, nullable=False, key=u'streamId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'created', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'created', doc=''),
	Column(u'open', BOOLEAN, nullable=False, server_default=text(u'true'), key=u'open', doc=''),
	UniqueConstraint(u'taskId', u'name'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
)


t_subtasks =  Table('subtasks', metadata,
	Column(u'subtaskid', INTEGER, primary_key=True, nullable=False, key=u'subTaskId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'worktypeid', INTEGER, nullable=False, key=u'workTypeId', doc=''),
	Column(u'maximumpagesize', INTEGER, nullable=False, server_default=text(u'20'), key=u'maxPageSize', doc=''),
	Column(u'dst_dir', CHAR(length=3), nullable=False, server_default=text(u"'ltr'::bpchar"), key=u'dstDir', doc=''),
	Column(u'modeid', INTEGER, nullable=False, server_default=text(u'1'), key=u'modeId', doc=''),
	Column(u'getpolicy', TEXT, server_default=text(u"'nolimit'::text"), key=u'getPolicy', doc=''),
	Column(u'expirypolicy', TEXT, server_default=text(u"'noextend'::text"), key=u'expiryPolicy', doc=''),
	Column(u'allowpageskip', BOOLEAN, server_default=text(u'true'), key=u'allowPageSkip', doc=''),
	Column(u'needitemcontext', BOOLEAN, server_default=text(u'false'), key=u'needItemContext', doc=''),
	Column(u'allowediting', BOOLEAN, server_default=text(u'true'), key=u'allowEditing', doc=''),
	Column(u'allowabandon', BOOLEAN, server_default=text(u'false'), key=u'allowAbandon', doc=''),
	Column(u'lookahead', INTEGER, nullable=False, server_default=text(u'0'), key=u'lookAhead', doc=''),
	Column(u'lookbehind', INTEGER, nullable=False, server_default=text(u'0'), key=u'lookBehind', doc=''),
	Column(u'allowcheckout', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'allowCheckout', doc=''),
	Column(u'is2ndpassqa', BOOLEAN, key=u'isSecondPassQa', doc=''),
	Column(u'defaultleaselife', INTERVAL(precision=None), server_default=text(u"'7 days'::interval"), key=u'defaultLeaseLife', doc=''),
	Column(u'needdynamictagset', BOOLEAN, server_default=text(u'false'), key=u'needDynamicTagSet', doc=''),
	Column(u'instructionspage', TEXT, key=u'instructionPage', doc=''),
	Column(u'useqahistory', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'useQaHistory', doc=''),
	Column(u'meanamount', DOUBLE_PRECISION, key=u'meanAmount', doc=''),
	Column(u'maxamount', INTEGER, key=u'maxAmount', doc=''),
	Column(u'accuracy', DOUBLE_PRECISION, key=u'accuracy', doc=''),
	Column(u'maxworkrate', DOUBLE_PRECISION, key=u'maxWorkRate', doc=''),
	Column(u'medianworkrate', DOUBLE_PRECISION, key=u'medianWorkRate', doc=''),
	Column(u'hidelabels', BOOLEAN, server_default=text(u'false'), key=u'hideLabels', doc=''),
	Column(u'validators', TEXT, key=u'validators', doc=''),
	UniqueConstraint(u'taskId', u'workTypeId', u'name'),
	UniqueConstraint(u'taskId', u'subTaskId'),
	ForeignKeyConstraint([u'workTypeId'], [u'worktypes.workTypeId']),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
	ForeignKeyConstraint([u'modeId'], [u'batchingmodes.modeId']),
	CheckConstraint("dst_dir=ANY(ARRAY['ltr','rtl'])"),
	CheckConstraint("getpolicy=ANY(ARRAY['nolimit','oneonly'])"),
)
Index('subtasksbytaskid', t_subtasks.c.taskId, unique=False)


t_taskerrortypes =  Table('taskerrortypes', metadata,
	Column(u'taskid', INTEGER, primary_key=True, nullable=False, key=u'taskId', doc=''),
	Column(u'errortypeid', INTEGER, primary_key=True, nullable=False, key=u'errorTypeId', doc=''),
	Column(u'severity', DOUBLE_PRECISION, nullable=False, server_default=text(u'1'), key=u'severity', doc=''),
	Column(u'disabled', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'disabled', doc=''),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
	ForeignKeyConstraint([u'errorTypeId'], [u'errortypes.errorTypeId']),
	CheckConstraint('severity>=0 AND severity<=1'),
)


t_taskreports =  Table('taskreports', metadata,
	Column(u'taskreportid', INTEGER, primary_key=True, nullable=False, key=u'taskReportId', doc=''),
	Column(u'reporttypeid', INTEGER, nullable=False, key=u'reportTypeId', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'filename', TEXT, key=u'filename', doc=''),
	Column(u'title', TEXT, key=u'title', doc=''),
	Column(u'usergroupid', INTEGER, key=u'userGroupId', doc=''),
	ForeignKeyConstraint([u'reportTypeId'], [u'taskreporttypes.reportTypeId']),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
)
Index('taskreportsbytaskid', t_taskreports.c.taskId, unique=False)


t_tasksupervisors =  Table('tasksupervisors', metadata,
	Column(u'taskid', INTEGER, primary_key=True, nullable=False, key=u'taskId', doc=''),
	Column(u'userid', INTEGER, primary_key=True, nullable=False, key=u'userId', doc=''),
	Column(u'receivesfeedback', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'receivesFeedback', doc=''),
	Column(u'informloads', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'informLoads', doc=''),
	ForeignKeyConstraint([u'userId'], [u'users.userId']),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
)


# Level 130

t_dailysubtasktotals =  Table('dailysubtasktotals', metadata,
	Column(u'totalid', INTEGER, primary_key=True, nullable=False, key=u'totalId', doc=''),
	Column(u'totaldate', DATE(), nullable=False, key=u'totalDate', doc=''),
	Column(u'subtaskid', INTEGER, nullable=False, key=u'subTaskId', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userId', doc=''),
	Column(u'amount', INTEGER, nullable=False, key=u'amount', doc=''),
	Column(u'words', INTEGER, key=u'words', doc=''),
	UniqueConstraint(u'totalDate', u'subTaskId', u'userId'),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId']),
	ForeignKeyConstraint([u'userId'], [u'users.userId']),
)
Index('dailysubtasktotalsbysubtaskid', t_dailysubtasktotals.c.subTaskId, unique=False)
Index('dailysubtasktotalsbyuserid', t_dailysubtasktotals.c.userId, unique=False)
Index('dailysubtasktotalsbytotaldate', t_dailysubtasktotals.c.totalDate, unique=False)


t_defaultqaconfiguration =  Table('defaultqaconfiguration', metadata,
	Column(u'worksubtaskid', INTEGER, primary_key=True, nullable=False, key=u'workSubTaskId', doc=''),
	Column(u'qasubtaskid', INTEGER, nullable=False, key=u'qaSubTaskId', doc=''),
	Column(u'samplingerror', DOUBLE_PRECISION, nullable=False, key=u'samplingError', doc=''),
	Column(u'defaultexpectedaccuracy', DOUBLE_PRECISION, nullable=False, key=u'defaultExpectedAccuracy', doc=''),
	Column(u'confidenceinterval', DOUBLE_PRECISION, nullable=False, key=u'confidenceInterval', doc=''),
	Column(u'reworksubtaskid', INTEGER, key=u'reworkSubTaskId', doc=''),
	Column(u'accuracythreshold', DOUBLE_PRECISION, key=u'accuracyThreshold', doc=''),
	Column(u'populaterework', BOOLEAN, server_default=text(u'false'), key=u'populateRework', doc=''),
	Column(u'updatedby', INTEGER, nullable=False, key=u'updatedBy', doc=''),
	ForeignKeyConstraint([u'workSubTaskId'], [u'subtasks.subTaskId']),
	ForeignKeyConstraint([u'qaSubTaskId'], [u'subtasks.subTaskId']),
	CheckConstraint('accuracythreshold <= defaultexpectedaccuracy AND accuracythreshold > 0 AND accuracythreshold < 1'),
	CheckConstraint('confidenceinterval >= 0.9 AND confidenceinterval < 1'),
	CheckConstraint('defaultexpectedaccuracy > 0 AND defaultexpectedaccuracy < 1'),
	CheckConstraint('samplingerror > 0 AND samplingerror <= 0.1'),
)


t_qaconfigurationentries =  Table('qaconfigurationentries', metadata,
	Column(u'entryid', INTEGER, primary_key=True, nullable=False, key=u'entryId', doc=''),
	Column(u'worksubtaskid', INTEGER, nullable=False, key=u'workSubTaskId', doc=''),
	Column(u'orderindex', INTEGER, nullable=False, key=u'orderIndex', doc=''),
	Column(u'qasubtaskid', INTEGER, nullable=False, key=u'qaSubTaskId', doc=''),
	Column(u'samplingerror', DOUBLE_PRECISION, nullable=False, key=u'samplingError', doc=''),
	Column(u'defaultexpectedaccuracy', DOUBLE_PRECISION, nullable=False, key=u'defaultExpectedAccuracy', doc=''),
	Column(u'confidenceinterval', DOUBLE_PRECISION, nullable=False, key=u'confidenceInterval', doc=''),
	UniqueConstraint('workSubTaskId', u'orderIndex'),
	ForeignKeyConstraint([u'qaSubTaskId'], [u'subtasks.subTaskId']),
	ForeignKeyConstraint([u'workSubTaskId'], [u'subtasks.subTaskId']),
	CheckConstraint('confidenceinterval >= 0.9 AND confidenceinterval < 1'),
	CheckConstraint('defaultexpectedaccuracy > 0 AND defaultexpectedaccuracy < 1'),
	CheckConstraint('orderindex>=0'),
	CheckConstraint('samplingerror > 0 AND samplingerror <= 0.1'),
)


t_subtaskrates =  Table('subtaskrates', metadata,
	Column(u'subtaskrateid', INTEGER, primary_key=True, nullable=False, key=u'subTaskRateId', doc=''),
	Column(u'subtaskid', INTEGER, nullable=False, key=u'subTaskId', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'rateid', INTEGER, nullable=False, key=u'rateId', doc=''),
	Column(u'validfrom', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'validFrom', doc=''),
	Column(u'multiplier', DOUBLE_PRECISION, nullable=False, server_default=text(u'1'), key=u'multiplier', doc=''),
	Column(u'updatedby', INTEGER, nullable=False, key=u'updatedBy', doc=''),
	Column(u'updatedat', TIMESTAMP(timezone=False), server_default=text(u'now()'), key=u'updatedAt', doc=''),
	ForeignKeyConstraint([u'rateId'], [u'rates.rateId']),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId']),
)


t_taskusers =  Table('taskusers', metadata,
	Column(u'userid', INTEGER, primary_key=True, nullable=False, key=u'userId', doc=''),
	Column(u'taskid', INTEGER, primary_key=True, nullable=False, key=u'taskId', doc=''),
	Column(u'subtaskid', INTEGER, primary_key=True, nullable=False, key=u'subTaskId', doc=''),
	Column(u'isnew', BOOLEAN, nullable=False, server_default=text(u'true'), key=u'isNew', doc=''),
	Column(u'removed', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'removed', doc=''),
	Column(u'paymentfactor', DOUBLE_PRECISION, nullable=False, server_default=text(u'1'), key=u'paymentFactor', doc=''),
	Column(u'hasreadinstructions', BOOLEAN, nullable=False, server_default=text(u'FALSE'), key=u'hasReadInstructions', doc=''),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
	ForeignKeyConstraint([u'userId'], [u'users.userId']),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId']),
)


t_utteranceselections =  Table('utteranceselections', metadata,
	Column(u'selectionid', INTEGER, primary_key=True, nullable=False, key=u'selectionId', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userId', doc=''),
	Column(u'limitrestriction', INTEGER, key=u'limit', doc=''),
	Column(u'selected', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'selected', doc=''),
	Column(u'action', TEXT, key=u'action', doc=''),
	Column(u'subtaskid', INTEGER, key=u'subTaskId', doc=''),
	Column(u'name', TEXT, key=u'name', doc=''),
	Column(u'processed', TIMESTAMP(timezone=False), key=u'processed', doc=''),
	Column(u'random', BOOLEAN, server_default=text(u'false'), key=u'random', doc=''),
	ForeignKeyConstraint([u'userId'], [u'users.userId']),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId']),
)


t_workintervals =  Table('workintervals', metadata,
	Column(u'workintervalid', INTEGER, primary_key=True, nullable=False, key=u'workIntervalId', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'subtaskid', INTEGER, nullable=False, key=u'subTaskId', doc=''),
	Column(u'starttime', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'startTime', doc=''),
	Column(u'endtime', TIMESTAMP(timezone=False), key=u'endTime', doc=''),
	Column(u'intervalstatus', TEXT, nullable=False, server_default=text(u"'current'::text"), key=u'status', doc=''),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId']),
	ForeignKeyConstraint([u'taskId', u'subTaskId'], [u'subtasks.taskId', u'subtasks.subTaskId'], name=u'workintervals_taskid_fkey1'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
	CheckConstraint("intervalstatus=ANY(ARRAY['current','addingfinalchecks','checking','finished'])"),
)


# Level 140

t_batches =  Table('batches', metadata,
	Column(u'batchid', INTEGER, primary_key=True, nullable=False, key=u'batchId', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'subtaskid', INTEGER, nullable=False, key=u'subTaskId', doc=''),
	Column(u'userid', INTEGER, key=u'userId', doc=''),
	Column(u'priority', INTEGER, nullable=False, server_default=text(u'5'), key=u'priority', doc=''),
	Column(u'onhold', BOOLEAN, server_default=text(u'false'), key=u'onHold', doc=''),
	Column(u'leasegranted', TIMESTAMP(timezone=False), key=u'leaseGranted', doc=''),
	Column(u'leaseexpires', TIMESTAMP(timezone=False), key=u'leaseExpires', doc=''),
	Column(u'notuserid', INTEGER, key=u'notUserId', doc=''),
	Column(u'workintervalid', INTEGER, key=u'workIntervalId', doc=''),
	Column(u'checkedout', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'checkedOut', doc=''),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId']),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
	ForeignKeyConstraint([u'userId'], [u'users.userId']),
	ForeignKeyConstraint([u'notUserId'], [u'users.userId']),
)
Index('batchesbysubtaskid', t_batches.c.subTaskId, unique=False)
Index('batchesbytaskid', t_batches.c.taskId, unique=False)
Index('batchesbyuserid', t_batches.c.userId, unique=False)


t_calculatedpayments =  Table('calculatedpayments', metadata,
	Column(u'calculatedpaymentid', INTEGER, primary_key=True, nullable=False, key=u'calculatedPaymentId', doc=''),
	Column(u'payrollid', INTEGER, nullable=False, key=u'payrollId', doc=''),
	Column(u'workintervalid', INTEGER, nullable=False, key=u'workIntervalId', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userId', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'subtaskid', INTEGER, nullable=False, key=u'subTaskId', doc=''),
	Column(u'units', INTEGER, nullable=False, key=u'units', doc=''),
	Column(u'unitsqaed', INTEGER, nullable=False, key=u'qaedUnits', doc=''),
	Column(u'accuracy', DOUBLE_PRECISION, nullable=False, key=u'accuracy', doc=''),
	Column(u'originalamount', INTEGER, nullable=False, key=u'originalAmount', doc=''),
	Column(u'amount', INTEGER, nullable=False, key=u'amount', doc=''),
	Column(u'receipt', TEXT, key=u'receipt', doc=''),
	Column(u'updated', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'updated', doc=''),
	Column(u'items', INTEGER, nullable=False, key=u'items', doc=''),
	Column(u'itemsqaed', INTEGER, nullable=False, key=u'qaedItems', doc=''),
	ForeignKeyConstraint([u'userId'], [u'users.userId']),
	ForeignKeyConstraint([u'workIntervalId'], [u'workintervals.workIntervalId']),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId']),
	ForeignKeyConstraint([u'payrollId'], [u'payrolls.payrollId']),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
)


t_customutterancegroups =  Table('customutterancegroups', metadata,
	Column(u'groupid', INTEGER, primary_key=True, nullable=False, key=u'groupId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'created', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'created', doc=''),
	Column(u'utterances', INTEGER, nullable=False, key=u'utterances', doc=''),
	Column(u'selectionid', INTEGER, nullable=False, key=u'selectionId', doc=''),
	UniqueConstraint(u'taskId', u'name'),
	ForeignKeyConstraint([u'selectionId'], [u'utteranceselections.selectionId']),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
)


t_postprocessingutterancegroups =  Table('postprocessingutterancegroups', metadata,
	Column(u'groupid', INTEGER, primary_key=True, nullable=False, key=u'groupId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'streamid', INTEGER, key=u'streamId', doc=''),
	Column(u'created', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'created', doc=''),
	Column(u'utterances', INTEGER, nullable=False, key=u'utterances', doc=''),
	Column(u'selectionid', INTEGER, nullable=False, key=u'selectionId', doc=''),
	UniqueConstraint(u'taskId', u'name'),
	ForeignKeyConstraint([u'selectionId'], [u'utteranceselections.selectionId']),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
)


t_reworkcontenthistory =  Table('reworkcontenthistory', metadata,
	Column(u'eventid', INTEGER, primary_key=True, key=u'eventId', doc=''),
	Column(u'subtaskid', INTEGER, nullable=False, key=u'subTaskId', doc=''),
	Column(u'selectionid', INTEGER, key=u'selectionId', doc=''),
	Column(u'amount', INTEGER, nullable=False, key=u'itemCount', doc=''),
	Column(u'populating', BOOLEAN, server_default=text(u'true'), key=u'isAdding', doc=''),
	Column(u't_processed_at', TIMESTAMP(timezone=True), key=u'tProcessedAt', doc=''),
	Column(u'operator', INTEGER, key=u'operator', doc=''),
	ForeignKeyConstraint([u'selectionId'], [u'utteranceselections.selectionId']),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId']),
	CheckConstraint('populating AND selectionid IS NOT NULL OR NOT populating AND selectionid IS NULL'),
)
Index('reworkcontenthistorybysubtaskid', t_reworkcontenthistory.c.subTaskId, unique=False)


t_subtaskmetrics =  Table('subtaskmetrics', metadata,
	Column(u'metricid', INTEGER, primary_key=True, nullable=False, key=u'metricId', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userId', doc=''),
	Column(u'workintervalid', INTEGER, key=u'workIntervalId', doc=''),
	Column(u'subtaskid', INTEGER, key=u'subTaskId', doc=''),
	Column(u'amount', INTEGER, key=u'amount', doc=''),
	Column(u'words', INTEGER, key=u'words', doc=''),
	Column(u'workrate', DOUBLE_PRECISION, key=u'workRate', doc=''),
	Column(u'accuracy', DOUBLE_PRECISION, key=u'accuracy', doc=''),
	Column(u'lastupdated', TIMESTAMP(timezone=False), key=u'lastUpdated', doc=''),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId']),
	ForeignKeyConstraint([u'userId'], [u'users.userId']),
	ForeignKeyConstraint([u'workIntervalId'], [u'workintervals.workIntervalId']),
	CheckConstraint('workintervalid IS NOT NULL AND subtaskid IS NULL OR workintervalid IS NULL AND subtaskid IS NOT NULL'),
)
Index('subtaskmetricsbysubtaskid', t_subtaskmetrics.c.subTaskId, unique=False)
Index('subtaskmetricsbyuserid', t_subtaskmetrics.c.userId, unique=False)
Index('subtaskmetricsbyworkintervalid', t_subtaskmetrics.c.workIntervalId, unique=False)


t_userworkstats =  Table('userworkstats', metadata,
	Column(u'workintervalid', INTEGER, nullable=False, key=u'workintervalid', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskid', doc=''),
	Column(u'subtaskid', INTEGER, nullable=False, key=u'subtaskid', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userid', doc=''),
	Column(u'items', INTEGER, nullable=False, key=u'items', doc=''),
	Column(u'itemsqaed', INTEGER, nullable=False, key=u'itemsqaed', doc=''),
	Column(u'units', INTEGER, nullable=False, key=u'units', doc=''),
	Column(u'unitsqaed', INTEGER, nullable=False, key=u'unitsqaed', doc=''),
	Column(u'accuracy', DOUBLE_PRECISION, nullable=False, key=u'accuracy', doc=''),
	ForeignKeyConstraint([u'userid'], [u'users.userId']),
	ForeignKeyConstraint([u'workintervalid'], [u'workintervals.workIntervalId']),
)


t_utteranceselectionfilters =  Table('utteranceselectionfilters', metadata,
	Column(u'filterid', INTEGER, primary_key=True, nullable=False, key=u'filterId', doc=''),
	Column(u'selectionid', INTEGER, nullable=False, key=u'selectionId', doc=''),
	Column(u'include', BOOLEAN, nullable=False, key=u'isInclusive', doc=''),
	Column(u'description', TEXT, nullable=False, key=u'description', doc=''),
	Column(u'filtertype', TEXT, nullable=False, key=u'filterType', doc=''),
	Column(u'mandatory', BOOLEAN, nullable=False, key=u'isMandatory', doc=''),
	ForeignKeyConstraint([u'selectionId'], [u'utteranceselections.selectionId']),
)


# Level 150


t_abnormalusage =  Table('abnormalusage', metadata,
	Column(u'metricid', INTEGER, nullable=False, key=u'metricId', doc=''),
	Column(u'tagid', INTEGER, key=u'tagId', doc=''),
	Column(u'labelid', INTEGER, key=u'labelId', doc=''),
	Column(u'degree', INTEGER, nullable=False, key=u'degree', doc=''),
	ForeignKeyConstraint([u'labelId'], [u'labels.labelId']),
	ForeignKeyConstraint([u'metricId'], [u'subtaskmetrics.metricId']),
	ForeignKeyConstraint([u'tagId'], [u'tags.tagId']),
	CheckConstraint('tagid IS NOT NULL AND labelid IS NULL OR tagid IS NULL AND labelid IS NOT NULL'),
	CheckConstraint('degree <> 0'),
)
Index('abnormalusagebymetricid', t_abnormalusage.c.metricId, unique=False)


t_batchhistory =  Table('batchhistory', metadata,
	Column(u'batchid', INTEGER, nullable=False, key=u'batchId', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userId', doc=''),
	Column(u'event', TEXT, nullable=False, key=u'event', doc=''),
	Column(u'when', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'when', doc=''),
	ForeignKeyConstraint([u'userId'], [u'users.userId']),
	CheckConstraint("event=ANY(ARRAY['assigned','abandoned','submitted','revoked'])")
)
Index('batchhistorybyuserid', t_batchhistory.c.userId, unique=False)


t_customutterancegroupmembers =  Table('customutterancegroupmembers', metadata,
	Column(u'groupid', INTEGER, nullable=False, key=u'groupId', doc=''),
	Column(u'rawpieceid', INTEGER, nullable=False, key=u'rawPieceId', doc=''),
	PrimaryKeyConstraint(u'groupId', u'rawPieceId'),
	ForeignKeyConstraint([u'groupId'], [u'customutterancegroups.groupId']),
	ForeignKeyConstraint([u'rawPieceId'], [u'rawpieces.rawPieceId']),
)
Index('customutterancegroupmember_by_rawpieceid', t_customutterancegroupmembers.c.rawPieceId, unique=False)


t_pages =  Table('pages', metadata,
	Column(u'pageid', INTEGER, primary_key=True, nullable=False, key=u'pageId', doc=''),
	Column(u'batchid', INTEGER, nullable=False, key=u'batchId', doc=''),
	Column(u'pageindex', INTEGER, nullable=False, key=u'pageIndex', doc=''),
	UniqueConstraint(u'batchId', u'pageIndex'),
	ForeignKeyConstraint([u'batchId'], [u'batches.batchId']),
	CheckConstraint('pageindex>=0'),
)
Index('pagesbybatchid', t_pages.c.batchId, unique=False)


t_rawpieces =  Table('rawpieces', metadata,
	Column(u'rawpieceid', INTEGER, primary_key=True, nullable=False, key=u'rawPieceId', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'rawtext', TEXT, nullable=False, key=u'rawText', doc=''),
	Column(u'assemblycontext', TEXT, nullable=False, server_default=text(u"''::text"), key=u'assemblyContext', doc=''),
	Column(u'allocationcontext', TEXT, nullable=False, server_default=text(u"''::text"), key=u'allocationContext', doc=''),
	Column(u'meta', TEXT, key=u'meta', doc=''),
	Column(u'isnew', BOOLEAN, nullable=False, server_default=text(u'true'), key=u'isNew', doc=''),
	Column(u'hypothesis', TEXT, key=u'hypothesis', doc=''),
	Column(u'words', INTEGER, server_default=text(u'0'), key=u'words', doc=''),
	Column(u'groupid', INTEGER, key=u'groupId', doc=''),
	Column(u'loadid', INTEGER, nullable=False, key=u'loadId', doc=''),
	UniqueConstraint(u'taskId', u'assemblyContext'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
	ForeignKeyConstraint([u'groupId'], [u'postprocessingutterancegroups.groupId']),
	ForeignKeyConstraint([u'taskId', u'loadId'], [u'loads.taskId', u'loads.loadId']),
)
Index('rawpieces_taskid', t_rawpieces.c.taskId, unique=False)
Index('rawpieces_loadid', t_rawpieces.c.loadId, unique=False)
Index('rawpieces_groupid', t_rawpieces.c.groupId, unique=False)


t_subtaskmetricerrors =  Table('subtaskmetricerrors', metadata,
	Column(u'metricid', INTEGER, primary_key=True, nullable=False, key=u'metricId', doc=''),
	Column(u'errortypeid', INTEGER, primary_key=True, nullable=False, key=u'errorTypeId', doc=''),
	Column(u'occurences', INTEGER, nullable=False, key=u'occurences', doc=''),
	ForeignKeyConstraint([u'errorTypeId'], [u'errortypes.errorTypeId']),
	ForeignKeyConstraint([u'metricId'], [u'subtaskmetrics.metricId']),
)
Index('subtaskmetricerrorsbymetricid', t_subtaskmetricerrors.c.metricId, unique=False)


t_utteranceselectionfilterpieces =  Table('utteranceselectionfilterpieces', metadata,
	Column(u'filterid', INTEGER, primary_key=True, nullable=False, key=u'filterId', doc=''),
	Column(u'pieceindex', INTEGER, primary_key=True, autoincrement=False, nullable=False, key=u'index', doc=''),
	Column(u'data', TEXT, nullable=False, key=u'data', doc=''),
	ForeignKeyConstraint([u'filterId'], [u'utteranceselectionfilters.filterId']),
)


# Level 160


t_batchcheckincache =  Table('batchcheckincache', metadata,
	Column(u'batchid', INTEGER, nullable=False, key=u'batchId', doc=''),
	Column(u'rawpieceid', INTEGER, nullable=False, key=u'rawPieceId', doc=''),
	Column(u'result', TEXT, nullable=False, key=u'result', doc=''),
	Column(u'pageid', INTEGER, nullable=False, key=u'pageId', doc=''),
	UniqueConstraint(u'batchId', u'rawPieceId'),
)
Index('checkindatabybatchid', t_batchcheckincache.c.batchId, unique=False)
Index('checkindatabyrawpiecehid', t_batchcheckincache.c.rawPieceId, unique=False)


t_utteranceselectioncache =  Table('utteranceselectioncache', metadata,
	Column(u'selectionid', INTEGER, primary_key=True, nullable=False, key=u'selectionId', doc=''),
	Column(u'rawpieceid', INTEGER, primary_key=True, nullable=False, key=u'rawPieceId', doc=''),
	ForeignKeyConstraint([u'rawPieceId'], [u'rawpieces.rawPieceId']),
	ForeignKeyConstraint([u'selectionId'], [u'utteranceselections.selectionId']),
)
Index('idx_utteranceselectioncache_rawpieceid', t_utteranceselectioncache.c.rawPieceId, unique=False)


t_workentries =  Table('workentries', metadata,
	Column(u'entryid', INTEGER, primary_key=True, nullable=False, key=u'entryId', doc=''),
	Column(u'created', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'created', doc=''),
	Column(u'result', TEXT, key=u'result', doc=''),
	Column(u'rawpieceid', INTEGER, nullable=False, key=u'rawPieceId', doc=''),
	Column(u'batchid', INTEGER, nullable=False, key=u'batchId', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'subtaskid', INTEGER, nullable=False, key=u'subTaskId', doc=''),
	Column(u'worktypeid', INTEGER, nullable=False, key=u'workTypeId', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userId', doc=''),
	Column(u'notes', TEXT, key=u'notes', doc=''),
	Column(u'qaeduserid', INTEGER, key=u'qaedUserId', doc=''),
	Column(u'qaedentryid', INTEGER, key=u'qaedEntryId', doc=''),
	Column(u'pageid', INTEGER, nullable=False, key=u'pageId', doc=''),
	ForeignKeyConstraint([u'rawPieceId'], [u'rawpieces.rawPieceId']),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId']),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
	ForeignKeyConstraint([u'workTypeId'], [u'worktypes.workTypeId']),
	ForeignKeyConstraint([u'userId'], [u'users.userId']),
)
Index('workentriesbypageid', t_workentries.c.pageId, unique=False)
Index('workentriesbyqaedentryid', t_workentries.c.qaedEntryId, unique=False)
Index('workentriesbyrawpieceid', t_workentries.c.rawPieceId, unique=False)
Index('workentriesbysubtaskid', t_workentries.c.subTaskId, unique=False)
Index('workentriesbytaskid', t_workentries.c.taskId, unique=False)
Index('workentriesbybatchid', t_workentries.c.batchId, unique=False)
Index('workentriesbyuserid', t_workentries.c.userId, unique=False)


# Level 170


t_pagemembers =  Table('pagemembers', metadata,
	Column(u'pageid', INTEGER, primary_key=True, nullable=False, key=u'pageId', doc=''),
	Column(u'memberindex', INTEGER, primary_key=True, autoincrement=False, nullable=False, key=u'memberIndex', doc=''),
	Column(u'rawpieceid', INTEGER, key=u'rawPieceId', doc=''),
	Column(u'workentryid', INTEGER, key=u'workEntryId', doc=''),
	ForeignKeyConstraint([u'pageId'], [u'pages.pageId']),
	ForeignKeyConstraint([u'rawPieceId'], [u'rawpieces.rawPieceId']),
	ForeignKeyConstraint([u'workEntryId'], [u'workentries.entryId']),
	CheckConstraint('rawpieceid IS NOT NULL AND workentryid IS NULL OR rawpieceid IS NULL AND workentryid IS NOT NULL'),
)
Index('pagememberbyrawpiecid', t_pagemembers.c.rawPieceId, unique=False)


t_payableevents =  Table('payableevents', metadata,
	Column(u'eventid', INTEGER, primary_key=True, nullable=False, key=u'eventId', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userId', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'subtaskid', INTEGER, nullable=False, key=u'subTaskId', doc=''),
	Column(u'created', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'created', doc=''),
	Column(u'batchid', INTEGER, nullable=False, key=u'batchId', doc=''),
	Column(u'pageid', INTEGER, nullable=False, key=u'pageId', doc=''),
	Column(u'rawpieceid', INTEGER, key=u'rawPieceId', doc=''),
	Column(u'workentryid', INTEGER, key=u'workEntryId', doc=''),
	Column(u'calculatedpaymentid', INTEGER, key=u'calculatedPaymentId', doc=''),
	Column(u'localconnection', BOOLEAN, key=u'localConnection', doc=''),
	Column(u'ipaddress', CIDR(), key=u'ipAddress', doc=''),
	Column(u'ratio', DOUBLE_PRECISION, nullable=False, server_default=text(u'1.0'), key=u'ratio', doc=''),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId']),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId']),
	ForeignKeyConstraint([u'calculatedPaymentId'], [u'calculatedpayments.calculatedPaymentId']),
	ForeignKeyConstraint([u'userId'], [u'users.userId']),
)
Index('payableeventsbycalculatedpaymentid', t_payableevents.c.calculatedPaymentId, unique=False)
Index('payableeventsbypageid', t_payableevents.c.pageId, unique=False)
Index('payableeventsbyrawpieceid', t_payableevents.c.rawPieceId, unique=False)
Index('payableeventsbysubtaskid', t_payableevents.c.subTaskId, unique=False)
Index('payableeventsbybatchid', t_payableevents.c.batchId, unique=False)
Index('payableeventsbytaskid', t_payableevents.c.taskId, unique=False)
Index('payableeventsbyuserid', t_payableevents.c.userId, unique=False)
Index('payableeventsbyworkentryid', t_payableevents.c.workEntryId, unique=False)


t_workentryerrors =  Table('workentryerrors', metadata,
	Column(u'entryid', INTEGER, primary_key=True, nullable=False, key=u'entryId', doc=''),
	Column(u'errortypeid', INTEGER, primary_key=True, nullable=False, key=u'errorTypeId', doc=''),
	Column(u'severity', DOUBLE_PRECISION, nullable=False, key=u'severity', doc=''),
	ForeignKeyConstraint([u'entryId'], [u'workentries.entryId']),
	ForeignKeyConstraint([u'errorTypeId'], [u'errortypes.errorTypeId']),
	CheckConstraint('severity>=0 AND severity<=1'),
)
Index('workentryerrorsbyentryid', t_workentryerrors.c.entryId, unique=False)


t_workentrylabels =  Table('workentrylabels', metadata,
	Column(u'entryid', INTEGER, primary_key=True, nullable=False, key=u'entryId', doc=''),
	Column(u'labelid', INTEGER, primary_key=True, nullable=False, key=u'labelId', doc=''),
	ForeignKeyConstraint([u'entryId'], [u'workentries.entryId']),
	ForeignKeyConstraint([u'labelId'], [u'labels.labelId']),
)
Index('workentrylabelsbyentryid', t_workentrylabels.c.entryId, unique=False)
Index('workentrylabelsbylabelid', t_workentrylabels.c.labelId, unique=False)


# Level 200

t_pools =  Table('pools', metadata,
	Column(u'pool_id', INTEGER, primary_key=True, nullable=False, key=u'poolId', doc=''),
	Column(u'name', TEXT, nullable=False, unique=True, key=u'name', doc=''),
	Column(u'meta', MutableDict.as_mutable(JsonString), nullable=False, key=u'meta', doc=''),
	Column(u'task_type_id', INTEGER, nullable=False, key=u'taskTypeId', doc=''),
	Column(u'auto_scoring', BOOLEAN, nullable=False, server_default=text('FALSE'), key=u'autoScoring', doc=''),
	Column(u'tag_set_id', INTEGER, key=u'tagSetId', doc=''),
	ForeignKeyConstraint([u'taskTypeId'], [u'tasktypes.taskTypeId']),
	ForeignKeyConstraint([u'tagSetId'], [u'tagsets.tagSetId']),
	schema='q',
)


t_questions =  Table('questions', metadata,
	Column(u'question_id', INTEGER, primary_key=True, nullable=False, key=u'questionId', doc=''),
	Column(u'pool_id', INTEGER, nullable=False, key=u'poolId', doc=''),
	Column(u'respondent_data', MutableDict.as_mutable(JsonString), nullable=False, server_default=text(u"'{}'::text"), key=u'respondentData', doc=''),
	Column(u'scorer_data', MutableDict.as_mutable(JsonString), nullable=False, server_default=text(u"'{}'::text"), key=u'scorerData', doc=''),
	Column(u'auto_scoring', BOOLEAN, nullable=False, server_default=text('FALSE'), key=u'autoScoring', doc=''),
	Column(u'point', DOUBLE_PRECISION, nullable=False, server_default=text('1.0'), key=u'point', doc=''),
	Column(u'type', TEXT, nullable=False, server_default=text(u"'text'::bpchar"), key=u'type', doc=''),
	ForeignKeyConstraint([u'poolId'], [u'q.pools.poolId']),
	schema='q',
)


t_tests =  Table('tests', metadata,
	Column(u'test_id', INTEGER, primary_key=True, nullable=False, key=u'testId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'description', TEXT, key=u'description', doc=''),
	Column(u'instruction_page', TEXT, key=u'instructionPage', doc=''),
	Column(u'requirement', MutableDict.as_mutable(JsonString), nullable=False, server_default=text(u"'{}'::text"), key=u'requirement', doc=''),
	Column(u'time_limit', INTERVAL(precision=None), nullable=False, server_default=text(u"'02:00:00'::interval"), key=u'timeLimit', doc=''),
	Column(u'tag_set_id', INTEGER, key=u'tagSetId', doc=''),
	Column(u'passing_score', DOUBLE_PRECISION, nullable=False, key=u'passingScore', doc=''),
	Column(u'test_type', TEXT, server_default=text(u"'static'::bpchar"), key=u'testType', doc=''),
	Column(u'size', INTEGER, key=u'size', doc=''),
	Column(u'enabled', BOOLEAN, nullable=False, server_default=text('TRUE'), key=u'isEnabled', doc=''),
	Column(u'task_type_id', INTEGER, nullable=False, key=u'taskTypeId', doc=''),
	Column(u'pool_id', INTEGER, nullable=False, key=u'poolId', doc=''),
	Column(u'message_success', TEXT, key=u'messageSuccess', doc=''),
	Column(u'message_failure', TEXT, key=u'messageFailure', doc=''),
	ForeignKeyConstraint([u'tagSetId'], [u'tagsets.tagSetId']),
	ForeignKeyConstraint([u'taskTypeId'], [u'tasktypes.taskTypeId']),
	ForeignKeyConstraint([u'poolId'], [u'q.pools.poolId']),
	schema='q',
)


t_answer_sheets =  Table('answer_sheets', metadata,
	Column(u'sheet_id', INTEGER, primary_key=True, nullable=False, key=u'sheetId', doc=''),
	Column(u'test_id', INTEGER, nullable=False, key=u'testId', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userId', doc=''),
	Column(u'n_times', INTEGER, nullable=False, key=u'nTimes', doc=''),
	Column(u't_started_at', TIMESTAMP(timezone=True), nullable=False, server_default=text(u'now()'), key=u'tStartedAt', doc=''),
	Column(u't_expires_by', TIMESTAMP(timezone=True), nullable=False, key=u'tExpiresBy', doc=''),
	Column(u't_expired_at', TIMESTAMP(timezone=True), key=u'tExpiredAt', doc=''),
	Column(u't_finished_at', TIMESTAMP(timezone=True), key=u'tFinishedAt', doc=''),
	Column(u'score', DOUBLE_PRECISION, key=u'score', doc=''),
	Column(u'comment', TEXT, key=u'comment', doc=''),
	Column(u'more_attempts', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'moreAttempts', doc=''),
	UniqueConstraint(u'testId', u'userId', u'nTimes'),
	ForeignKeyConstraint([u'testId'], [u'q.tests.testId']),
	schema='q',
)
Index(u'answer_sheet_by_testid', t_answer_sheets.c.testId, unique=False)
Index(u'answer_sheet_by_testid_userid', t_answer_sheets.c.testId, t_answer_sheets.c.userId, unique=False)
Index(u'answer_sheet_by_userid', t_answer_sheets.c.userId, unique=False)



t_sheet_entries =  Table('sheet_entries', metadata,
	Column(u'sheet_entry_id', INTEGER, primary_key=True, nullable=False, key=u'sheetEntryId', doc=''),
	Column(u'sheet_id', INTEGER, nullable=False, key=u'sheetId', doc=''),
	Column(u'index', INTEGER, nullable=False, key=u'index', doc=''),
	Column(u'question_id', INTEGER, nullable=False, key=u'questionId', doc=''),
	Column(u'answer_id', INTEGER, key=u'answerId', doc=''),
	Column(u'marking_id', INTEGER, key=u'markingId', doc=''),
	ForeignKeyConstraint([u'sheetId'], [u'q.answer_sheets.sheetId']),
	ForeignKeyConstraint([u'questionId'], [u'q.questions.questionId']),
	schema='q',
)


t_answers =  Table('answers', metadata,
	Column(u'answer_id', INTEGER, primary_key=True, nullable=False, key=u'answerId', doc=''),
	Column(u'sheet_entry_id', INTEGER, nullable=False, key=u'sheetEntryId', doc=''),
	Column(u'answer', TEXT, nullable=False, key=u'answer', doc=''),
	Column(u't_created_at', TIMESTAMP(timezone=True), nullable=False, server_default=text(u'now()'), key=u'tCreatedAt', doc=''),
	ForeignKeyConstraint([u'sheetEntryId'], [t_sheet_entries.c.sheetEntryId]),
	schema='q',
)
Index('answer_by_sheet_entry_id', t_answers.c.sheetEntryId, unique=False)


t_markings =  Table('markings', metadata,
	Column(u'marking_id', INTEGER, primary_key=True, nullable=False, key=u'markingId', doc=''),
	Column(u'sheet_entry_id', INTEGER, nullable=False, key=u'sheetEntryId', doc=''),
	Column(u't_created_at', TIMESTAMP(timezone=True), nullable=False, server_default=text(u'now()'), key=u'tCreatedAt', doc=''),
	Column(u'scorer_id', INTEGER, primary_key=True, autoincrement=False, nullable=False, key=u'scorerId', doc=''),
	Column(u'score', DOUBLE_PRECISION, nullable=False, key=u'score', doc=''),
	Column(u'comment', TEXT, key=u'comment', doc=''),
	ForeignKeyConstraint([u'sheetEntryId'], [u'q.sheet_entries.sheetEntryId']),
	ForeignKeyConstraint([u'scorerId'], [u'users.userId']),
	schema='q',
)
Index('marking_by_sheet_entry_id', t_markings.c.sheetEntryId, unique=False)


j_users = join(t_users, t_ao_users, t_users.c.userId == t_ao_users.c.userId)

j_pagemembers = select([t_batches.c.batchId, t_batches.c.userId, t_subtasks.c.subTaskId,
	t_worktypes.c.name.label('workType'), t_subtasks.c.taskId, t_pagemembers]).select_from(
	join(t_batches, t_subtasks).join(t_worktypes).join(t_pages).join(t_pagemembers)).alias('j_pm')

j_workentries = select([t_worktypes.c.name.label('workType'), t_worktypes.c.modifiesTranscription, t_workentries]).select_from(
	join(t_workentries, t_worktypes)).alias('j_we')

__all__ = [name for name in locals().keys() if name.startswith('t_')]
__all__.insert(0, 'metadata')
__all__.append('j_users')
__all__.append('j_pagemembers')
__all__.append('j_workentries')
