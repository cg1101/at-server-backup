
from sqlalchemy import *
from sqlalchemy.dialects.postgresql import *
from sqlalchemy import event

from mytypes import JsonString, MutableDict

metadata = MetaData(naming_convention={
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
})

event.listen(metadata, 'before_create', DDL('CREATE SCHEMA IF NOT EXISTS q'))

# Level 000

t_pdb_projects = Table('pdb_projects', metadata,
	Column('project_id', Integer, primary_key=True, autoincrement=False, key='projectId'),
	Column('name', Text, nullable=False, unique=True, key='name'),
)

t_pdb_tasks = Table('pdb_tasks', metadata,
	Column('task_id', Integer, primary_key=True, autoincrement=False, key='taskId'),
	Column('project_id', Integer, ForeignKey('pdb_projects.projectId'), nullable=False, key='projectId'),
	Column('work_area', Text, key='workArea'),
	Column('name', Text, key='name'),
)

t_ao_payment_classes = Table('ao_payment_classes', metadata,
	Column('paymentclassid', Integer, primary_key=True, autoincrement=False, key='paymentClassId'),
	Column('name', Text, nullable=False, unique=True, key='name'),
	Column('created', TIMESTAMP(timezone=True), server_default=text('now()'), key='created')
)

t_ao_payment_types = Table('ao_payment_types', metadata,
	Column('paymenttypeid', Integer, primary_key=True, autoincrement=False, key='paymentTypeId'),
	Column('name', Text, nullable=False, unique=True, key='name'),
	Column('created', TIMESTAMP(timezone=True), server_default=text('now()'), key='created')
)

t_ao_payrolls = Table('ao_payrolls', metadata,
	Column('payrollid', Integer, primary_key=True, autoincrement=False, key='payrollId'),
	Column('startdate', Date, nullable=False, key='startDate'),
	Column('enddate', Date, nullable=False, key='endDate'),
)

t_ao_users = Table('ao_users', metadata,
	Column('userid', Integer, primary_key=True, autoincrement=False, key='userId'),
	Column('emailaddress', Text, nullable=False, key='emailAddress'),
	Column('active', Text, nullable=False, server_default=text('TRUE'), key='isActive'),
	Column('familyname', Text, key='familyName'),
	Column('givenname', Text, key='givenName'),
)

# t_ao_countries = Table('ao_countries', metadata,
# 	Column('country_id', Integer, primary_key=True, autoincrement=False, key='countryId'),
# 	Column('name', Text, nullable=False, unique=True, key='name'),
# 	Column('iso2', VARCHAR(2), nullable=False, unique=True, key='iso2'),
# 	Column('iso3', VARCHAR(3), nullable=False, unique=True, key='iso3'),
# )

# t_ao_languages = Table('ao_languages', metadata,
# 	Column('language_id', Integer, primary_key=True, autoincrement=False, key='languageId'),
# 	Column('name', Text, nullable=False, unique=True, key='name'),
# 	Column('iso3', VARCHAR(3), nullable=False, unique=True, key='iso3'),
# 	Column('ltr', Boolean, nullable=False, server_default=text('TRUE')),
# )


# Level 010


t_batchingmodes =  Table('batchingmodes', metadata,
	Column(u'modeid', INTEGER, primary_key=True, nullable=False, key=u'modeId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'description', TEXT, key=u'description', doc=''),
	Column(u'requirescontext', BOOLEAN, nullable=False, server_default=text(u'true'), key=u'requiresContext', doc=''),
)
Index(u'batchingmodes_name_key', t_batchingmodes.c.name, unique=True)


t_errorclasses =  Table('errorclasses', metadata,
	Column(u'errorclassid', INTEGER, primary_key=True, nullable=False, key=u'errorClassId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
)
Index(None, t_errorclasses.c.name, unique=True)


t_filehandlers =  Table('filehandlers', metadata,
	Column(u'handlerid', INTEGER, primary_key=True, nullable=False, key=u'handlerId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'description', TEXT, key=u'description', doc=''),
)
Index(None, t_filehandlers.c.name, unique=True)


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
#Index('jobs_pkey', t_jobs.c.jobid, unique=True)


t_labelsets =  Table('labelsets', metadata,
	Column(u'labelsetid', INTEGER, primary_key=True, nullable=False, key=u'labelSetId', doc=''),
	Column(u'created', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'created', doc=''),
)
#Index('labelsets_pkey', t_labelsets.c.labelsetid, unique=True)


t_rates =  Table('rates', metadata,
	Column(u'rateid', INTEGER, primary_key=True, nullable=False, key=u'rateId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'centsperutt', DOUBLE_PRECISION, nullable=False, key=u'standardValue', doc=''),
	Column(u'maxcentsperutt', DOUBLE_PRECISION, nullable=False, key=u'maxValue', doc=''),
	Column(u'targetaccuracy', DOUBLE_PRECISION, nullable=False, key=u'targetAccuracy', doc=''),
)
Index(None, t_rates.c.name, unique=True)


t_tagimagepreviews =  Table('tagimagepreviews', metadata,
	Column(u'previewid', INTEGER, primary_key=True, nullable=False, key=u'previewId', doc=''),
	Column(u'image', LargeBinary, nullable=False, key=u'image', doc=''),
	Column(u'created', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'created', doc=''),
)
#Index('tagimagepreviews_pkey', t_tagimagepreviews.c.previewid, unique=True)


t_tagsets =  Table('tagsets', metadata,
	Column(u'tagsetid', INTEGER, primary_key=True, nullable=False, key=u'tagSetId', doc=''),
	Column(u'created', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'created', doc=''),
	Column(u'lastupdated', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'lastUpdated', doc=''),
)
#Index('tagsets_pkey', t_tagsets.c.tagsetid, unique=True)


t_tasktypes =  Table('tasktypes', metadata,
	Column(u'tasktypeid', INTEGER, primary_key=True, nullable=False, key=u'taskTypeId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'description', TEXT, key=u'description', doc=''),
)
#Index('tasktypes_pkey', t_tasktypes.c.taskTypeId, unique=True)


t_taskreporttypes =  Table('taskreporttypes', metadata,
	Column(u'reporttypeid', INTEGER, primary_key=True, nullable=False, key=u'reportTypeId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'isstandard', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'isStandard', doc=''),
	Column(u'restrictusersallowed', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'restrictUsersAllowed', doc=''),
)
Index(u'taskreporttypes_name_key', t_taskreporttypes.c.name, unique=True)


t_worktypes =  Table('worktypes', metadata,
	Column(u'worktypeid', INTEGER, primary_key=True, nullable=False, key=u'workTypeId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'description', TEXT, key=u'description', doc=''),
	Column(u'modifiestranscription', BOOLEAN, nullable=False, key=u'modifiesTranscription', doc=''),
)
Index(None, t_worktypes.c.name, unique=True)


# Level 020

t_errortypes =  Table('errortypes', metadata,
	Column(u'errortypeid', INTEGER, primary_key=True, nullable=False, key=u'errorTypeId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'errorclassid', INTEGER, nullable=False, key=u'errorClassId', doc=''),
	Column(u'defaultseverity', DOUBLE_PRECISION, nullable=False, key=u'defaultSeverity', doc=''),
	Column(u'isstandard', BOOLEAN, nullable=False, server_default=text(u'true'), key=u'isStandard', doc=''),
	ForeignKeyConstraint([u'errorClassId'], [u'errorclasses.errorClassId'], name=u'errortypes_errorclassid_fkey'),
)
Index(None, t_errortypes.c.name, unique=True)


t_filehandleroptions =  Table('filehandleroptions', metadata,
	Column(u'optionid', INTEGER, primary_key=True, nullable=False, key=u'optionId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'label', TEXT, key=u'label', doc=''),
	Column(u'handlerid', INTEGER, nullable=False, key=u'handlerId', doc=''),
	Column(u'datatype', TEXT, nullable=False, key=u'dataType', doc=''),
	Column(u'widgettype', TEXT, key=u'widgetType', doc=''),
 	Column(u'params', MutableDict.as_mutable(JsonString), key=u'params', doc=''),
	ForeignKeyConstraint([u'handlerId'], [u'filehandlers.handlerId'], name=None),
)
Index(None, t_filehandleroptions.c.name, t_filehandleroptions.c.handlerId, unique=True)


t_labelgroups =  Table('labelgroups', metadata,
	Column(u'labelgroupid', INTEGER, primary_key=True, nullable=False, key=u'labelGroupId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'ismandatory', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'isMandatory', doc=''),
	Column(u'labelsetid', INTEGER, nullable=False, key=u'labelSetId', doc=''),
	Column(u'dropdowndisplay', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'dropDownDisplay', doc=''),
	ForeignKeyConstraint([u'labelSetId'], [u'labelsets.labelSetId'], name=u'labelgroups_labelsetid_fkey'),
)
Index(u'labelgroups_labelsetid_key', t_labelgroups.c.labelSetId, t_labelgroups.c.name, unique=True)


t_ratedetails =  Table('ratedetails', metadata,
	Column(u'rateid', INTEGER, nullable=False, key=u'rateId', doc=''),
	Column(u'centsperutt', DOUBLE_PRECISION, nullable=False, key=u'value', doc=''),
	Column(u'accuracy', DOUBLE_PRECISION, nullable=False, key=u'accuracy', doc=''),
	PrimaryKeyConstraint(u'rateId', u'accuracy'),
	ForeignKeyConstraint([u'rateId'], [u'rates.rateId'], name=u'ratedetails_rateid_fkey'),
)
Index(None, t_ratedetails.c.rateId, t_ratedetails.c.accuracy, unique=True)


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
	ForeignKeyConstraint([u'tagSetId'], [u'tagsets.tagSetId'], name=u'tags_tagsetid_fkey')
)
Index(None, t_tags.c.color, t_tags.c.isForeground, t_tags.c.tagSetId, unique=True)
Index(None, t_tags.c.tagSetId, t_tags.c.name, unique=True)


# Level 030


t_labels =  Table('labels', metadata,
	Column(u'labelid', INTEGER, primary_key=True, nullable=False, key=u'labelId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'description', TEXT, key=u'description', doc=''),
	Column(u'hotkey', CHAR(length=1), key=u'shortcutKey', doc=''),
	Column(u'extract', TEXT, nullable=False, key=u'extract', doc=''),
	Column(u'labelgroupid', INTEGER, key=u'labelGroupId', doc=''),
	Column(u'labelsetid', INTEGER, nullable=False, key=u'labelSetId', doc=''),
	ForeignKeyConstraint([u'labelGroupId'], [u'labelgroups.labelGroupId'], name=u'labels_labelgroupid_fkey'),
	ForeignKeyConstraint([u'labelSetId'], [u'labelsets.labelSetId'], name=u'labels_labelsetid_fkey'),
)
Index('ix_labels_labelsetid_key', t_labels.c.labelSetId, t_labels.c.extract, unique=True)
Index('ix_labels_labelsetid_key1', t_labels.c.labelSetId, t_labels.c.name, unique=True)
Index('ix_labels_labelsetid_key2', t_labels.c.labelSetId, t_labels.c.shortcutKey, unique=True)
Index(None, t_labels.c.labelGroupId, unique=False)


# Level 100

t_payrolls =  Table('payrolls', metadata,
	Column(u'payrollid', INTEGER, primary_key=True, autoincrement=False, nullable=False, key=u'payrollId', doc=''),
	Column(u'updatedpayments', TIMESTAMP(timezone=False), key=u'updatedPayments', doc=''),
)
#Index('payrolls_pkey', t_payrolls.c.payrollid, unique=True)


t_paymentclasses =  Table('paymentclasses', metadata,
	Column(u'paymentclassid', INTEGER, key=u'paymentClassId', doc=''),
)


t_paymenttypes =  Table('paymenttypes', metadata,
	Column(u'paymenttypeid', INTEGER, primary_key=True, autoincrement=False, nullable=False, key=u'paymentTypeId', doc=''),
)
#Index('paymenttypes_pkey', t_paymenttypes.c.paymenttypeid, unique=True)


t_projects =  Table('projects', metadata,
	Column(u'projectid', INTEGER, primary_key=True, autoincrement=False, nullable=False, key=u'projectId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'description', TEXT, key=u'description', doc=''),
	Column(u'created', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'created', doc=''),
	Column(u'migratedby', INTEGER, nullable=False, key=u'migratedBy', doc=''),
	ForeignKeyConstraint([u'migratedBy'], [u'users.userId'], name=u'projects_migratedby_fkey'),
)
#Index('projects_pkey', t_projects.c.projectid, unique=True)


t_users =  Table('users', metadata,
	Column(u'userid', INTEGER, primary_key=True, autoincrement=False, nullable=False, key=u'userId', doc=''),
)
#Index('users_pkey', t_users.c.userid, unique=True)


# Level 110


t_calculateduserpayrates =  Table('calculateduserpayrates', metadata,
	Column(u'rateid', INTEGER, nullable=False, key=u'rateId', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userId', doc=''),
	Column(u'hourlyrate', DOUBLE_PRECISION, nullable=False, key=u'hourlyRate', doc=''),
	Column(u't', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u't', doc=''),
	Column(u'changerid', INTEGER, nullable=False, key=u'changerId', doc=''),
	ForeignKeyConstraint([u'changerId'], [u'users.userId'], name=u'calculateduserpayrates_changerid_fkey'),
	ForeignKeyConstraint([u'rateId'], [u'rates.rateId'], name=u'calculateduserpayrates_rateid_fkey'),
	ForeignKeyConstraint([u'userId'], [u'users.userId'], name=u'calculateduserpayrates_userid_fkey'),
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
	ForeignKeyConstraint([u'labelSetId'], [u'labelsets.labelSetId'], name=u'tasks_labelsetid_fkey'),
	ForeignKeyConstraint([u'taskTypeId'], [u'tasktypes.taskTypeId'], name=u'tasks_tasktypeid_fkey'),
	ForeignKeyConstraint([u'projectId'], [u'projects.projectId'], name=u'tasks_projectid_fkey'),
	ForeignKeyConstraint([u'tagSetId'], [u'tagsets.tagSetId'], name=u'tasks_tagsetid_fkey'),
	ForeignKeyConstraint([u'handlerId'], [u'filehandlers.handlerId'], name=u'tasks_handlerid_fkey'),
	ForeignKeyConstraint([u'migratedBy'], [u'users.userId'], name=u'tasks_migratedby_fkey'),
)
#Index('tasks_pkey', t_tasks.c.taskid, unique=True)
Index(None, t_tasks.c.migratedBy)


t_tracking_events =  Table('tracking_events', metadata,
	Column(u'eventid', INTEGER, primary_key=True, nullable=False, key=u'eventId', doc=''),
	Column(u'eventtype', TEXT, nullable=False, key=u'eventType', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userId', doc=''),
	Column(u't_triggered_at', TIMESTAMP(timezone=True), key=u'tTriggeredAt', doc=''),
	Column(u'hostip', INET(), key=u'hostIp', doc=''),
	Column(u'details', TEXT, nullable=False, key=u'details', doc=''),
)


# Level 120


t_costperutterance =  Table('costperutterance', metadata,
	Column(u'taskid', INTEGER, primary_key=True, nullable=False, key=u'taskId', doc=''),
	Column(u'cutofftime', TIMESTAMP(timezone=False), nullable=False, key=u'cutOffTime', doc=''),
	Column(u'itemsdone', INTEGER, nullable=False, key=u'itemsDone', doc=''),
	Column(u'unitsdone', INTEGER, nullable=False, key=u'unitsDone', doc=''),
	Column(u'payrollid', INTEGER, primary_key=True, nullable=False, key=u'payrollId', doc=''),
	Column(u'amount', DOUBLE_PRECISION, nullable=False, key=u'amount', doc=''),
	ForeignKeyConstraint([u'payrollId'], [u'payrolls.payrollId'], name=u'costperutterance_payrollid_fkey'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'costperutterance_taskid_fkey'),
)
Index(u'costperutterancebytaskid', t_costperutterance.c.taskId, unique=False)


t_loads =  Table('loads', metadata,
	Column(u'loadid', INTEGER, primary_key=True, nullable=False, key=u'loadId', doc=''),
	Column(u'createdby', INTEGER, nullable=False, key=u'createdBy', doc=''),
	Column(u'createdat', TIMESTAMP(timezone=True), nullable=False, server_default=text(u'now()'), key=u'createdAt', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	ForeignKeyConstraint([u'createdBy'], [u'users.userId'], name=None),#u'tasksupervisors_userid_fkey'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=None),#u'tasksupervisors_taskid_fkey'),
)
#Index('loads_pkey', t_loads.c.loadId, unique=True)
Index('ix_loads_taskid_loadid', t_loads.c.loadId, t_loads.c.taskId, unique=True)


t_otherpayments =  Table('otherpayments', metadata,
	Column(u'otherpaymentid', INTEGER, primary_key=True, nullable=False, key=u'otherPaymentId', doc=''),
	Column(u'payrollid', INTEGER, nullable=False, key=u'payrollId', doc=''),
	Column(u'identifier', TEXT, nullable=False, key=u'identifier', doc=''),
	Column(u'paymenttypeid', INTEGER, nullable=False, key=u'paymentTypeId', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userId', doc=''),
	Column(u'amount', INTEGER, nullable=False, key=u'amount', doc=''),
	Column(u'added', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'added', doc=''),
	ForeignKeyConstraint([u'paymentTypeId'], [u'paymenttypes.paymentTypeId'], name=u'otherpayments_paymenttypeid_fkey'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'otherpayments_taskid_fkey'),
	ForeignKeyConstraint([u'payrollId'], [u'payrolls.payrollId'], name=u'otherpayments_payrollid_fkey'),
	ForeignKeyConstraint([u'userId'], [u'users.userId'], name=u'otherpayments_userid_fkey'),
)
Index(u'otherpayments_identifier_key', t_otherpayments.c.identifier, unique=True)
Index(u'otherpaymentsbypayrollid', t_otherpayments.c.payrollId, unique=False)
Index(u'otherpaymentsbytaskid', t_otherpayments.c.taskId, unique=False)


t_overallqaprogresscache =  Table('overallqaprogresscache', metadata,
	Column(u'taskid', INTEGER, primary_key=True, nullable=False, key=u'taskId', doc=''),
	Column(u'endtime', TIMESTAMP(timezone=False), key=u'endTime', doc=''),
	Column(u'remaining', INTEGER, nullable=False, key=u'remaining', doc=''),
	Column(u'lastupdated', TIMESTAMP(timezone=False), nullable=False, key=u'lastUpdated', doc=''),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'overallqaprogresscache_taskid_fkey'),
)
#Index('overallqaprogresscache_pkey', t_overallqaprogresscache.c.taskid, unique=True)


t_overalltrprogresscache =  Table('overalltrprogresscache', metadata,
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'itemcount', INTEGER, nullable=False, key=u'itemCount', doc=''),
	Column(u'wordcount', INTEGER, nullable=False, key=u'wordCount', doc=''),
	Column(u'newitems', INTEGER, nullable=False, key=u'newItems', doc=''),
	Column(u'finished', INTEGER, nullable=False, key=u'finished', doc=''),
	Column(u'finishedlastweek', INTEGER, nullable=False, key=u'finishedLastWeek', doc=''),
	Column(u'lastupdated', TIMESTAMP(timezone=False), nullable=False, key=u'lastUpdated', doc=''),
	Column(u'overallaccuracy', DOUBLE_PRECISION, key=u'overallAccuracy', doc=''),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'overalltrprogresscache_taskid_fkey'),
)


t_overallworkprogresscache =  Table('overallworkprogresscache', metadata,
	Column(u'taskid', INTEGER, primary_key=True, nullable=False, key=u'taskId', doc=''),
	Column(u'total', INTEGER, nullable=False, key=u'total', doc=''),
	Column(u'newutts', INTEGER, nullable=False, key=u'newUtts', doc=''),
	Column(u'transcribed', INTEGER, nullable=False, key=u'transcribed', doc=''),
	Column(u'transcribedlastweek', INTEGER, nullable=False, key=u'transcribedLastWeek', doc=''),
	Column(u'lastupdated', TIMESTAMP(timezone=False), nullable=False, key=u'lastUpdated', doc=''),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'overallworkprogresscache_taskid_fkey'),
)
#Index('overallworkprogresscache_pkey', t_overallworkprogresscache.c.taskid, unique=True)


t_streams =  Table('streams', metadata,
	Column(u'streamid', INTEGER, primary_key=True, nullable=False, key=u'streamId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'created', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'created', doc=''),
	Column(u'open', BOOLEAN, nullable=False, server_default=text(u'true'), key=u'open', doc=''),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'streams_taskid_fkey'),
)
Index(u'streams_taskid_key', t_streams.c.taskId, t_streams.c.name, unique=True)


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
	ForeignKeyConstraint([u'workTypeId'], [u'worktypes.workTypeId'], name=u'subtasks_worktypeid_fkey'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'subtasks_taskid_fkey'),
	ForeignKeyConstraint([u'modeId'], [u'batchingmodes.modeId'], name=u'subtasks_modeid_fkey'),
)
Index(None, t_subtasks.c.taskId, t_subtasks.c.workTypeId, t_subtasks.c.name, unique=True)
Index('ix_subtasks_taskid_subtaskid', t_subtasks.c.taskId, t_subtasks.c.subTaskId, unique=True)
Index('ix_subtasks_subtaskid', t_subtasks.c.taskId, unique=False)


t_taskerrortypes =  Table('taskerrortypes', metadata,
	Column(u'taskid', INTEGER, primary_key=True, nullable=False, key=u'taskId', doc=''),
	Column(u'errortypeid', INTEGER, primary_key=True, nullable=False, key=u'errorTypeId', doc=''),
	Column(u'severity', DOUBLE_PRECISION, nullable=False, server_default=text(u'1'), key=u'severity', doc=''),
	Column(u'disabled', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'disabled', doc=''),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'taskerrortypes_taskid_fkey'),
	ForeignKeyConstraint([u'errorTypeId'], [u'errortypes.errorTypeId'], name=u'taskerrortypes_errortypeid_fkey'),
)
#Index('taskerrortypes_pkey', t_taskerrortypes.c.taskid, t_taskerrortypes.c.errorTypeId, unique=True)


t_taskreports =  Table('taskreports', metadata,
	Column(u'taskreportid', INTEGER, primary_key=True, nullable=False, key=u'taskReportId', doc=''),
	Column(u'reporttypeid', INTEGER, nullable=False, key=u'reportTypeId', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'filename', TEXT, key=u'filename', doc=''),
	Column(u'title', TEXT, key=u'title', doc=''),
	Column(u'usergroupid', INTEGER, key=u'userGroupId', doc=''),
	ForeignKeyConstraint([u'reportTypeId'], [u'taskreporttypes.reportTypeId'], name=u'taskreports_reporttypeid_fkey'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'taskreports_taskid_fkey'),
)
Index(u'taskreportsbytaskid', t_taskreports.c.taskId, unique=False)


t_tasksupervisors =  Table('tasksupervisors', metadata,
	Column(u'taskid', INTEGER, primary_key=True, nullable=False, key=u'taskId', doc=''),
	Column(u'userid', INTEGER, primary_key=True, nullable=False, key=u'userId', doc=''),
	Column(u'receivesfeedback', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'receivesFeedback', doc=''),
	Column(u'informloads', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'informLoads', doc=''),
	ForeignKeyConstraint([u'userId'], [u'users.userId'], name=u'tasksupervisors_userid_fkey'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'tasksupervisors_taskid_fkey'),
)
#Index('tasksupervisors_pkey', t_tasksupervisors.c.taskid, t_tasksupervisors.c.userid, unique=True)


# Level 130

t_dailysubtasktotals =  Table('dailysubtasktotals', metadata,
	Column(u'totalid', INTEGER, primary_key=True, nullable=False, key=u'totalId', doc=''),
	Column(u'totaldate', DATE(), nullable=False, key=u'totalDate', doc=''),
	Column(u'subtaskid', INTEGER, nullable=False, key=u'subTaskId', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userId', doc=''),
	Column(u'amount', INTEGER, nullable=False, key=u'amount', doc=''),
	Column(u'words', INTEGER, key=u'words', doc=''),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId'], name=u'dailysubtasktotals_subtaskid_fkey'),
	ForeignKeyConstraint([u'userId'], [u'users.userId'], name=u'dailysubtasktotals_userid_fkey'),
)
Index(u'dailysubtasktotals_totaldate_key', t_dailysubtasktotals.c.totalDate, t_dailysubtasktotals.c.subTaskId, t_dailysubtasktotals.c.userId, unique=True)
Index(u'dailysubtasktotalsbysubtaskid', t_dailysubtasktotals.c.subTaskId, unique=False)
Index(u'dailysubtasktotalsbyuserid', t_dailysubtasktotals.c.userId, unique=False)
Index(u'dailysubtasktotalsbytotaldate', t_dailysubtasktotals.c.totalDate, unique=False)


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
	ForeignKeyConstraint([u'workSubTaskId'], [u'subtasks.subTaskId'], name=u'defaultqaconfiguration_worksubtaskid_fkey'),
	ForeignKeyConstraint([u'qaSubTaskId'], [u'subtasks.subTaskId'], name=u'defaultqaconfiguration_qasubtaskid_fkey'),
)
#Index('defaultqaconfiguration_pkey', t_defaultqaconfiguration.c.worksubtaskid, unique=True)


t_qaconfigurationentries =  Table('qaconfigurationentries', metadata,
	Column(u'entryid', INTEGER, primary_key=True, nullable=False, key=u'entryId', doc=''),
	Column(u'worksubtaskid', INTEGER, nullable=False, key=u'workSubTaskId', doc=''),
	Column(u'orderindex', INTEGER, nullable=False, key=u'orderIndex', doc=''),
	Column(u'qasubtaskid', INTEGER, nullable=False, key=u'qaSubTaskId', doc=''),
	Column(u'samplingerror', DOUBLE_PRECISION, nullable=False, key=u'samplingError', doc=''),
	Column(u'defaultexpectedaccuracy', DOUBLE_PRECISION, nullable=False, key=u'defaultExpectedAccuracy', doc=''),
	Column(u'confidenceinterval', DOUBLE_PRECISION, nullable=False, key=u'confidenceInterval', doc=''),
	ForeignKeyConstraint([u'qaSubTaskId'], [u'subtasks.subTaskId'], name=u'qaconfigurationentries_qasubtaskid_fkey'),
	ForeignKeyConstraint([u'workSubTaskId'], [u'subtasks.subTaskId'], name=u'qaconfigurationentries_worksubtaskid_fkey'),
)
Index(u'qaconfigurationentries_worksubtaskid_key', t_qaconfigurationentries.c.workSubTaskId, t_qaconfigurationentries.c.orderIndex, unique=True)


t_subtaskrates =  Table('subtaskrates', metadata,
	Column(u'subtaskrateid', INTEGER, primary_key=True, nullable=False, key=u'subTaskRateId', doc=''),
	Column(u'subtaskid', INTEGER, nullable=False, key=u'subTaskId', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'rateid', INTEGER, nullable=False, key=u'rateId', doc=''),
	Column(u'validfrom', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'validFrom', doc=''),
	Column(u'multiplier', DOUBLE_PRECISION, nullable=False, server_default=text(u'1'), key=u'multiplier', doc=''),
	Column(u'updatedby', INTEGER, nullable=False, key=u'updatedBy', doc=''),
	Column(u'updatedat', TIMESTAMP(timezone=False), server_default=text(u'now()'), key=u'updatedAt', doc=''),
	ForeignKeyConstraint([u'rateId'], [u'rates.rateId'], name=u'subtaskrates_rateid_fkey'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'subtaskrates_taskid_fkey'),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId'], name=u'subtaskrates_subtaskid_fkey'),
)
#Index('subtaskrates_pkey', t_subtaskrates.c.subtaskrateid, unique=True)


t_taskusers =  Table('taskusers', metadata,
	Column(u'userid', INTEGER, primary_key=True, nullable=False, key=u'userId', doc=''),
	Column(u'taskid', INTEGER, primary_key=True, nullable=False, key=u'taskId', doc=''),
	Column(u'subtaskid', INTEGER, primary_key=True, nullable=False, key=u'subTaskId', doc=''),
	Column(u'isnew', BOOLEAN, nullable=False, server_default=text(u'true'), key=u'isNew', doc=''),
	Column(u'removed', BOOLEAN, nullable=False, server_default=text(u'false'), key=u'removed', doc=''),
	Column(u'paymentfactor', DOUBLE_PRECISION, nullable=False, server_default=text(u'1'), key=u'paymentFactor', doc=''),
	Column(u'hasreadinstructions', BOOLEAN, nullable=False, server_default=text(u'FALSE'), key=u'hasReadInstructions', doc=''),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'taskusers_taskid_fkey'),
	ForeignKeyConstraint([u'userId'], [u'users.userId'], name=u'taskusers_userid_fkey'),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId'], name=u'taskusers_subtaskid_fkey'),
)
#Index('taskusers_pkey', t_taskusers.c.userid, t_taskusers.c.taskid, t_taskusers.c.subtaskid, unique=True)


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
	ForeignKeyConstraint([u'userId'], [u'users.userId'], name=u'utteranceselections_userid_fkey'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'utteranceselections_taskid_fkey'),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId'], name=u'utteranceselections_subtaskid_fkey'),
)
#Index('utteranceselections_pkey', t_utteranceselections.c.selectionid, unique=True)


t_workintervals =  Table('workintervals', metadata,
	Column(u'workintervalid', INTEGER, primary_key=True, nullable=False, key=u'workIntervalId', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'subtaskid', INTEGER, nullable=False, key=u'subTaskId', doc=''),
	Column(u'starttime', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'startTime', doc=''),
	Column(u'endtime', TIMESTAMP(timezone=False), key=u'endTime', doc=''),
	Column(u'intervalstatus', TEXT, nullable=False, server_default=text(u"'current'::text"), key=u'status', doc=''),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId'], name=u'workintervals_subtaskid_fkey'),
	ForeignKeyConstraint([u'taskId', u'subTaskId'], [u'subtasks.taskId', u'subtasks.subTaskId'], name=u'workintervals_taskid_fkey1'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'workintervals_taskid_fkey'),
)
#Index('workintervals_pkey', t_workintervals.c.workintervalid, unique=True)


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
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId'], name=u'batches_subtaskid_fkey'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'batches_taskid_fkey'),
	ForeignKeyConstraint([u'userId'], [u'users.userId'], name=u'batches_userid_fkey'),
)
Index(u'batchesbysubtaskid', t_batches.c.subTaskId, unique=False)
Index(u'batchesbytaskid', t_batches.c.taskId, unique=False)
Index(u'batchesbyuserid', t_batches.c.userId, unique=False)


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
	ForeignKeyConstraint([u'userId'], [u'users.userId'], name=u'calculatedpayments_userid_fkey'),
	ForeignKeyConstraint([u'workIntervalId'], [u'workintervals.workIntervalId'], name=u'calculatedpayments_workintervalid_fkey'),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId'], name=u'calculatedpayments_subtaskid_fkey'),
	ForeignKeyConstraint([u'payrollId'], [u'payrolls.payrollId'], name=u'calculatedpayments_payrollid_fkey'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'calculatedpayments_taskid_fkey'),
)
#Index('calculatedpayments_pkey', t_calculatedpayments.c.calculatedpaymentid, unique=True)


t_customutterancegroups =  Table('customutterancegroups', metadata,
	Column(u'groupid', INTEGER, primary_key=True, nullable=False, key=u'groupId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'created', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'created', doc=''),
	Column(u'utterances', INTEGER, nullable=False, key=u'utterances', doc=''),
	Column(u'selectionid', INTEGER, nullable=False, key=u'selectionId', doc=''),
	ForeignKeyConstraint([u'selectionId'], [u'utteranceselections.selectionId'], name=u'customutterancegroups_selectionid_fkey'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'customutterancegroups_taskid_fkey'),
)
Index(u'customutterancegroups_taskid_key', t_customutterancegroups.c.taskId, t_customutterancegroups.c.name, unique=True)


t_postprocessingutterancegroups =  Table('postprocessingutterancegroups', metadata,
	Column(u'groupid', INTEGER, primary_key=True, nullable=False, key=u'groupId', doc=''),
	Column(u'name', TEXT, nullable=False, key=u'name', doc=''),
	Column(u'taskid', INTEGER, nullable=False, key=u'taskId', doc=''),
	Column(u'streamid', INTEGER, key=u'streamId', doc=''),
	Column(u'created', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'created', doc=''),
	Column(u'utterances', INTEGER, nullable=False, key=u'utterances', doc=''),
	Column(u'selectionid', INTEGER, nullable=False, key=u'selectionId', doc=''),
	ForeignKeyConstraint([u'selectionId'], [u'utteranceselections.selectionId'], name=u'postprocessingutterancegroups_selectionid_fkey'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'postprocessingutterancegroups_taskid_fkey'),
)
Index(u'postprocessingutterancegroups_taskid_key', t_postprocessingutterancegroups.c.taskId, t_postprocessingutterancegroups.c.name, unique=True)


t_reworkcontenthistory =  Table('reworkcontenthistory', metadata,
	Column(u'subtaskid', INTEGER, nullable=False, key=u'subTaskId', doc=''),
	Column(u'selectionid', INTEGER, key=u'selectionId', doc=''),
	Column(u'amount', INTEGER, nullable=False, key=u'amount', doc=''),
	Column(u'populating', BOOLEAN, server_default=text(u'true'), key=u'populating', doc=''),
	Column(u't_processed_at', TIMESTAMP(timezone=True), key=u'tProcessedAt', doc=''),
	Column(u'operator', INTEGER, key=u'operator', doc=''),
	ForeignKeyConstraint([u'selectionId'], [u'utteranceselections.selectionId'], name=u'reworkcontenthistory_selectionid_fkey'),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId'], name=u'reworkcontenthistory_subtaskid_fkey'),
)


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
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId'], name=u'subtaskmetrics_subtaskid_fkey'),
	ForeignKeyConstraint([u'userId'], [u'users.userId'], name=u'subtaskmetrics_userid_fkey'),
	ForeignKeyConstraint([u'workIntervalId'], [u'workintervals.workIntervalId'], name=u'subtaskmetrics_workintervalid_fkey'),
)
Index(u'subtaskmetricsbysubtaskid', t_subtaskmetrics.c.subTaskId, unique=False)
Index(u'subtaskmetricsbyuserid', t_subtaskmetrics.c.userId, unique=False)
Index(u'subtaskmetricsbyworkintervalid', t_subtaskmetrics.c.workIntervalId, unique=False)


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
	ForeignKeyConstraint([u'userid'], [u'users.userId'], name=u'userworkstats_userid_fkey'),
	ForeignKeyConstraint([u'workintervalid'], [u'workintervals.workIntervalId'], name=u'userworkstats_workintervalid_fkey'),
)


t_utteranceselectionfilters =  Table('utteranceselectionfilters', metadata,
	Column(u'filterid', INTEGER, primary_key=True, nullable=False, key=u'filterId', doc=''),
	Column(u'selectionid', INTEGER, nullable=False, key=u'selectionId', doc=''),
	Column(u'include', BOOLEAN, nullable=False, key=u'isInclusive', doc=''),
	Column(u'description', TEXT, nullable=False, key=u'description', doc=''),
	Column(u'filtertype', TEXT, nullable=False, key=u'filterType', doc=''),
	Column(u'mandatory', BOOLEAN, nullable=False, key=u'isMandatory', doc=''),
	ForeignKeyConstraint([u'selectionId'], [u'utteranceselections.selectionId'], name=u'utteranceselectionfilters_selectionid_fkey'),
)
#Index('utteranceselectionfilters_pkey', t_utteranceselectionfilters.c.filterid, unique=True)


# Level 150


t_abnormalusage =  Table('abnormalusage', metadata,
	Column(u'metricid', INTEGER, nullable=False, key=u'metricId', doc=''),
	Column(u'tagid', INTEGER, key=u'tagId', doc=''),
	Column(u'labelid', INTEGER, key=u'labelId', doc=''),
	Column(u'degree', INTEGER, nullable=False, key=u'degree', doc=''),
	ForeignKeyConstraint([u'labelId'], [u'labels.labelId'], name=u'abnormalusage_labelid_fkey'),
	ForeignKeyConstraint([u'metricId'], [u'subtaskmetrics.metricId'], name=u'abnormalusage_metricid_fkey'),
	ForeignKeyConstraint([u'tagId'], [u'tags.tagId'], name=u'abnormalusage_tagid_fkey'),
)
Index(u'abnormalusagebymetricid', t_abnormalusage.c.metricId, unique=False)


t_batchhistory =  Table('batchhistory', metadata,
	Column(u'batchid', INTEGER, nullable=False, key=u'batchId', doc=''),
	Column(u'userid', INTEGER, nullable=False, key=u'userId', doc=''),
	Column(u'event', TEXT, nullable=False, key=u'event', doc=''),
	Column(u'when', TIMESTAMP(timezone=False), nullable=False, server_default=text(u'now()'), key=u'when', doc=''),
	ForeignKeyConstraint([u'userId'], [u'users.userId'], name=u'batchhistory_userid_fkey'),
)
Index(u'batchhistorybyuserid', t_batchhistory.c.userId, unique=False)


t_customutterancegroupmembers =  Table('customutterancegroupmembers', metadata,
	Column(u'groupid', INTEGER, nullable=False, key=u'groupId', doc=''),
	Column(u'rawpieceid', INTEGER, nullable=False, key=u'rawPieceId', doc=''),
	PrimaryKeyConstraint(u'groupId', u'rawPieceId'),
	ForeignKeyConstraint([u'groupId'], [u'customutterancegroups.groupId'], name=u'customutterancegroupmembers_groupid_fkey'),
	ForeignKeyConstraint([u'rawPieceId'], [u'rawpieces.rawPieceId'], name=u'customutterancegroupmembers_rawpieceid_fkey'),
)
Index(u'customutterancegroupmember_by_rawpieceid', t_customutterancegroupmembers.c.rawPieceId, unique=False)


t_pages =  Table('pages', metadata,
	Column(u'pageid', INTEGER, primary_key=True, nullable=False, key=u'pageId', doc=''),
	Column(u'batchid', INTEGER, nullable=False, key=u'batchId', doc=''),
	Column(u'pageindex', INTEGER, nullable=False, key=u'pageIndex', doc=''),
	ForeignKeyConstraint([u'batchId'], [u'batches.batchId'], name=u'pages_batchid_fkey'),
)
Index(u'pages_batchid_key', t_pages.c.batchId, t_pages.c.pageIndex, unique=True)
Index(u'pagesbybatchid', t_pages.c.batchId, unique=False)


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
	Column(u'loadid', INTEGER, nullable=False, key='loadId', doc=''),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'rawpieces_taskid_fkey'),
	ForeignKeyConstraint([u'groupId'], [u'postprocessingutterancegroups.groupId'], name=u'rawpieces_groupid_fkey'),
	ForeignKeyConstraint([u'taskId', u'loadId'], [u'loads.taskId', u'loads.loadId'], name=None),#u'rawpieces_taskid_fkey'),
)
#Index(u'rawpiecesbygroupid', t_rawpieces.c.groupId, unique=False)
Index(None, t_rawpieces.c.taskId, unique=False)
Index(None, t_rawpieces.c.taskId, t_rawpieces.c.assemblyContext, unique=True)


t_subtaskmetricerrors =  Table('subtaskmetricerrors', metadata,
	Column(u'metricid', INTEGER, primary_key=True, nullable=False, key=u'metricId', doc=''),
	Column(u'errortypeid', INTEGER, primary_key=True, nullable=False, key=u'errorTypeId', doc=''),
	Column(u'occurences', INTEGER, nullable=False, key=u'occurences', doc=''),
	ForeignKeyConstraint([u'errorTypeId'], [u'errortypes.errorTypeId'], name=u'subtaskmetricerrors_errortypeid_fkey'),
	ForeignKeyConstraint([u'metricId'], [u'subtaskmetrics.metricId'], name=u'subtaskmetricerrors_metricid_fkey'),
)
Index(u'subtaskmetricerrorsbymetricid', t_subtaskmetricerrors.c.metricId, unique=False)


t_utteranceselectionfilterpieces =  Table('utteranceselectionfilterpieces', metadata,
	Column(u'filterid', INTEGER, primary_key=True, nullable=False, key=u'filterId', doc=''),
	Column(u'pieceindex', INTEGER, primary_key=True, autoincrement=False, nullable=False, key=u'index', doc=''),
	Column(u'data', TEXT, nullable=False, key=u'data', doc=''),
	ForeignKeyConstraint([u'filterId'], [u'utteranceselectionfilters.filterId'], name=u'utteranceselectionfilterpieces_filterid_fkey'),
)
#Index('utteranceselectionfilterpieces_pkey', t_utteranceselectionfilterpieces.c.filterid, t_utteranceselectionfilterpieces.c.pieceindex, unique=True)


# Level 160


t_batchcheckincache =  Table('batchcheckincache', metadata,
	Column(u'batchid', INTEGER, nullable=False, key=u'batchId', doc=''),
	Column(u'rawpieceid', INTEGER, nullable=False, key=u'rawPieceId', doc=''),
	Column(u'result', TEXT, nullable=False, key=u'result', doc=''),
	Column(u'pageid', INTEGER, nullable=False, key=u'pageId', doc=''),
)
Index(u'batchcheckincache_batchid_key', t_batchcheckincache.c.batchId, t_batchcheckincache.c.rawPieceId, unique=True)
Index(u'checkindatabybatchid', t_batchcheckincache.c.batchId, unique=False)
Index(u'checkindatabyrawpiecehid', t_batchcheckincache.c.rawPieceId, unique=False)


t_utteranceselectioncache =  Table('utteranceselectioncache', metadata,
	Column(u'selectionid', INTEGER, primary_key=True, nullable=False, key=u'selectionId', doc=''),
	Column(u'rawpieceid', INTEGER, primary_key=True, nullable=False, key=u'rawPieceId', doc=''),
	ForeignKeyConstraint([u'rawPieceId'], [u'rawpieces.rawPieceId'], name=u'utteranceselectioncache_rawpieceid_fkey'),
	ForeignKeyConstraint([u'selectionId'], [u'utteranceselections.selectionId'], name=u'utteranceselectioncache_selectionid_fkey'),
)
#Index('utteranceselectioncache_pkey', t_utteranceselectioncache.c.selectionid, t_utteranceselectioncache.c.rawpieceid, unique=True)


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
	ForeignKeyConstraint([u'rawPieceId'], [u'rawpieces.rawPieceId'], name=u'workentries_rawpieceid_fkey'),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId'], name=u'workentries_subtaskid_fkey'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'workentries_taskid_fkey'),
	ForeignKeyConstraint([u'workTypeId'], [u'worktypes.workTypeId'], name=u'workentries_worktypeid_fkey'),
	ForeignKeyConstraint([u'userId'], [u'users.userId'], name=u'workentries_userid_fkey'),
)
Index(u'workentriesbypageid', t_workentries.c.pageId, unique=False)
Index(u'workentriesbyqaedentryid', t_workentries.c.qaedEntryId, unique=False)
Index(u'workentriesbyrawpieceid', t_workentries.c.rawPieceId, unique=False)
Index(u'workentriesbysubtaskid', t_workentries.c.subTaskId, unique=False)
Index(u'workentriesbytaskid', t_workentries.c.taskId, unique=False)
Index(u'workentriesbybatchid', t_workentries.c.batchId, unique=False)
Index(u'workentriesbyuserid', t_workentries.c.userId, unique=False)


# Level 170


t_pagemembers =  Table('pagemembers', metadata,
	Column(u'pageid', INTEGER, primary_key=True, nullable=False, key=u'pageId', doc=''),
	Column(u'memberindex', INTEGER, primary_key=True, autoincrement=False, nullable=False, key=u'memberIndex', doc=''),
	Column(u'rawpieceid', INTEGER, key=u'rawPieceId', doc=''),
	Column(u'workentryid', INTEGER, key=u'workEntryId', doc=''),
	ForeignKeyConstraint([u'pageId'], [u'pages.pageId'], name=u'pagemembers_pageid_fkey'),
	ForeignKeyConstraint([u'rawPieceId'], [u'rawpieces.rawPieceId'], name=u'pagemembers_rawpieceid_fkey'),
	ForeignKeyConstraint([u'workEntryId'], [u'workentries.entryId'], name=u'pagemembers_workentryid_fkey'),
)
Index(u'pagememberbyrawpiecid', t_pagemembers.c.rawPieceId, unique=False)


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
	Column(u'ipaddress', CIDR(), key=u'ipaddress', doc=''),
	Column(u'ratio', DOUBLE_PRECISION, nullable=False, server_default=text(u'1.0'), key=u'ratio', doc=''),
	ForeignKeyConstraint([u'subTaskId'], [u'subtasks.subTaskId'], name=u'payableevents_subtaskid_fkey'),
	ForeignKeyConstraint([u'taskId'], [u'tasks.taskId'], name=u'payableevents_taskid_fkey'),
	ForeignKeyConstraint([u'calculatedPaymentId'], [u'calculatedpayments.calculatedPaymentId'], name=u'payableevents_calculatedpaymentid_fkey'),
	ForeignKeyConstraint([u'userId'], [u'users.userId'], name=u'payableevents_userid_fkey'),
)
Index(u'payableeventsbycalculatedpaymentid', t_payableevents.c.calculatedPaymentId, unique=False)
Index(u'payableeventsbypageid', t_payableevents.c.pageId, unique=False)
Index(u'payableeventsbyrawpieceid', t_payableevents.c.rawPieceId, unique=False)
Index(u'payableeventsbysubtaskid', t_payableevents.c.subTaskId, unique=False)
Index(u'payableeventsbybatchid', t_payableevents.c.batchId, unique=False)
Index(u'payableeventsbytaskid', t_payableevents.c.taskId, unique=False)
Index(u'payableeventsbyuserid', t_payableevents.c.userId, unique=False)
Index(u'payableeventsbyworkentryid', t_payableevents.c.workEntryId, unique=False)


t_workentryerrors =  Table('workentryerrors', metadata,
	Column(u'entryid', INTEGER, primary_key=True, nullable=False, key=u'entryId', doc=''),
	Column(u'errortypeid', INTEGER, primary_key=True, nullable=False, key=u'errorTypeId', doc=''),
	Column(u'severity', DOUBLE_PRECISION, nullable=False, key=u'severity', doc=''),
	ForeignKeyConstraint([u'entryId'], [u'workentries.entryId'], name=u'workentryerrors_entryid_fkey'),
	ForeignKeyConstraint([u'errorTypeId'], [u'errortypes.errorTypeId'], name=u'workentryerrors_errortypeid_fkey'),
)
Index(u'workentryerrorsbyentryid', t_workentryerrors.c.entryId, unique=False)


t_workentrylabels =  Table('workentrylabels', metadata,
	Column(u'entryid', INTEGER, primary_key=True, nullable=False, key=u'entryId', doc=''),
	Column(u'labelid', INTEGER, primary_key=True, nullable=False, key=u'labelId', doc=''),
	ForeignKeyConstraint([u'entryId'], [u'workentries.entryId'], name=u'workentrylabels_entryid_fkey'),
	ForeignKeyConstraint([u'labelId'], [u'labels.labelId'], name=u'workentrylabels_labelid_fkey'),
)
Index(u'workentrylabelsbyentryid', t_workentrylabels.c.entryId, unique=False)
Index(u'workentrylabelsbylabelid', t_workentrylabels.c.labelId, unique=False)


# Level 200

t_pools =  Table('pools', metadata,
	Column(u'pool_id', INTEGER, primary_key=True, nullable=False, key='poolId', doc=''),
	Column(u'name', TEXT, nullable=False, unique=True, key='name', doc=''),
	Column(u'meta', MutableDict.as_mutable(JsonString), nullable=False, ),
	Column(u'task_type_id', INTEGER, nullable=False, key='taskTypeId', doc=''),
	Column(u'auto_scoring', BOOLEAN, nullable=False, server_default=text('FALSE'), key='autoScoring', doc=''),
	Column(u'tag_set_id', INTEGER, key='tagSetId', doc=''),
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
	Column(u'point', DOUBLE_PRECISION, nullable=False, server_default=text('1.0'), key='point', doc=''),
	Column(u'type', TEXT, nullable=False, server_default=text(u"'text'::bpchar"), key='type', doc=''),
	ForeignKeyConstraint([u'poolId'], [u'q.pools.poolId'], name=None),
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
	Column(u'pool_id', INTEGER, nullable=False, key='poolId', doc=''),
	Column(u'message_success', TEXT, key=u'messageSuccess', doc=''),
	Column(u'message_failure', TEXT, key='messageFailure', doc=''),
	ForeignKeyConstraint([u'tagSetId'], [u'tagsets.tagSetId'], name=u'q_tests_tagsetid_fkey'),
	ForeignKeyConstraint([u'taskTypeId'], [u'tasktypes.taskTypeId'], name=u'q_tests__tasktypeid_fkey'),
	ForeignKeyConstraint([u'poolId'], [u'q.pools.poolId'], name=u'q_tests_poolid_fkey'),
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
	Column(u'more_attempts', BOOLEAN, nullable=False, server_default=text(u'false'), key='moreAttempts', doc=''),
	ForeignKeyConstraint([u'testId'], [u'q.tests.testId'], name=u'q_answer_sheets_testid_fkey'),
	schema='q',
)
# Index(u'answer_sheet_by_testid', t_answer_sheets.c.testId, unique=False)
# Index(u'answer_sheet_by_testid_userid', t_answer_sheets.c.testId, t_answer_sheets.c.userId, unique=False)
# Index(u'answer_sheet_by_userid', t_answer_sheets.c.userId, unique=False)
# Index(u'q_answer_sheets_testid_userid_n_times_key', t_answer_sheets.c.testId, t_answer_sheets.c.userId, t_answer_sheets.c.nTimes, unique=True)


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
	ForeignKeyConstraint([u'sheetEntryId'], [t_sheet_entries.c.sheetEntryId], name=None),
	schema='q',
)
Index(u'answer_by_sheet_entry_id', t_answers.c.sheetEntryId, unique=False)


t_markings =  Table('markings', metadata,
	Column(u'marking_id', INTEGER, primary_key=True, nullable=False, key=u'markingId', doc=''),
	Column(u'sheet_entry_id', INTEGER, nullable=False, key=u'sheetEntryId', doc=''),
	Column(u't_created_at', TIMESTAMP(timezone=True), nullable=False, server_default=text(u'now()'), key=u'tCreatedAt', doc=''),
	Column(u'scorer_id', INTEGER, primary_key=True, autoincrement=False, nullable=False, key=u'scorerId', doc=''),
	Column(u'score', DOUBLE_PRECISION, nullable=False, key=u'score', doc=''),
	Column(u'comment', TEXT, key=u'comment', doc=''),
	ForeignKeyConstraint([u'sheetEntryId'], [u'q.sheet_entries.sheetEntryId'], name=None),
	ForeignKeyConstraint([u'scorerId'], [u'users.userId'], name=u'q_markings_userid_fkey'),
	schema='q',
)
Index(u'marking_by_sheet_entry_id', t_markings.c.sheetEntryId, unique=False)


j_users = join(t_users, t_ao_users, t_users.c.userId == t_ao_users.c.userId)

j_pagemembers = select([t_batches.c.batchId, t_batches.c.userId, t_subtasks.c.subTaskId,
	t_worktypes.c.name.label('workType'), t_pagemembers]).select_from(
	join(t_batches, t_subtasks).join(t_worktypes).join(t_pages).join(t_pagemembers)).alias('j_pm')

j_workentries = select([t_worktypes.c.name.label('workType'), t_worktypes.c.modifiesTranscription, t_workentries]).select_from(
	join(t_workentries, t_worktypes)).alias('j_we')

__all__ = [name for name in locals().keys() if name.startswith('t_')]
__all__.insert(0, 'metadata')
__all__.append('j_users')
__all__.append('j_pagemembers')
__all__.append('j_workentries')
