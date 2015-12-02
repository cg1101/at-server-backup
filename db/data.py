#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, text

import schema as s
import model as m
from db import SS

class DataConfig:
	PDB_URL = 'postgresql://dbserver/admin'
	AO_URL = 'postgresql://dbserver/appenonline'
	AT_URL = 'postgresql://dbserver/appentext'
	TODO = {
		'pdb_projects': False,
		'pdb_tasks': False,

		'ao_payment_classes': False,
		'ao_payment_types': False,
		'ao_payrolls': False,
		'ao_users': False,

		'batchingmodes': False,
		'tasktypes': False,
		'worktypes': False,
		'rates': False,
		'taskreporttypes': False,
		'errorclasses': False,
		'errortypes': False,
		'filehandlers': False,
	}


def init_db(engine, config):

	#s.metadata.create_all(engine)

	def load(x):
		return config.TODO.get(x, False)

	# copy from project database

	pdb_engine = create_engine(config.PDB_URL)

	if load('pdb_projects'):
		todo = []
		for i in pdb_engine.execute('''SELECT id AS "projectId",
				codename AS name
				FROM pdb_project
				ORDER BY "projectId"'''):
			todo.append(dict(i))
		engine.execute(s.t_pdb_projects.insert(), todo)


	if load('pdb_tasks'):
		todo = []
		for i in pdb_engine.execute('''SELECT a.projno AS "taskId",
				b.project AS "projectId", a.type AS "workArea", a.description AS "name"
				FROM projects AS a JOIN pdb_map_project2tasks AS b ON (a.projno=b.task)
				ORDER BY "taskId"'''):
			todo.append(dict(i))
		engine.execute(s.t_pdb_tasks.insert(), todo)

	# copy from appenonline database

	ao_engine = create_engine(config.AO_URL)

	if load('ao_payment_types'):
		todo = []
		for i in ao_engine.execute('''SELECT paymentclassid AS "paymentClassId",
				name, created
				FROM paymentclasses
				ORDER BY paymentclassid'''):
			todo.append(dict(i))
		engine.execute(s.t_ao_payment_classes.insert(), todo)

	if load('ao_payment_classes'):
		todo = []
		for i in ao_engine.execute('''SELECT paymenttypeid AS "paymentTypeId",
				name, created
				FROM paymenttypes
				ORDER BY paymenttypeid'''):
			todo.append(dict(i))
		engine.execute(s.t_ao_payment_types.insert(), todo)

	if load('ao_payrolls'):
		todo = []
		for i in ao_engine.execute('''SELECT payrollid AS "payrollId",
				startdate AS "startDate", enddate AS "endDate"
				FROM payrolls
				ORDER BY payrollid'''):
			todo.append(dict(i))
		engine.execute(s.t_ao_payrolls.insert(), todo)

	if load('ao_users'):
		todo = []
		for i in ao_engine.execute('''SELECT userid AS "userId",
				emailaddress AS "emailAddress", active, familyname AS "familyName", givenname AS "givenName"
				FROM users
				ORDER BY "userId"'''):
			todo.append(dict(i))
		engine.execute(s.t_ao_users.insert(), todo)


	# copy from appentext database

	at_engine = create_engine(config.AT_URL)

	if False:# or True: # only do this in office
		from sqlalchemy.orm import sessionmaker
		src = sessionmaker(bind=at_engine)()
		dst = SS()

		for klass in [
				#m.BatchingMode, m.TaskType, m.WorkType,
				#m.ErrorClass, m.ErrorType, m.Rate, m.RatePoint,
				#m.TaskType, m.WorkType, m.FileHandler,
				#m.TagSet, m.Tag, m.LabelSet, m.LabelGroup, m.Label,
				#m.User,
				#m.Project, m.Task,
				#m.TaskSupervisor,
				#m.SubTask, m.TaskWorker, m.SubTaskRate,
				#m.Pool, m.Question, m.Test, m.Sheet, m.SheetEntry,
				#m.Answer, m.Marking, 
			]:
			for i in src.query(klass).all():
				src.expunge(i)
				dst.merge(i)

		dst.commit()

	# populate data directly

	if load('fileoptions'):
		engine.execute(s.t_filehandleroptions.delete())
		engine.execute(s.t_filehandlers.delete())
		engine.execute(s.t_filehandlers.insert(), [
			{'handlerId': 1, 'name': 'plaintext', 'description': None},
			{'handlerId': 2, 'name': 'tdf', 'description': None},
		])
		engine.execute(text("SELECT pg_catalog.setval('filehandlers_handlerid_seq', 2, true)"))
		engine.execute(s.t_filehandleroptions.insert(), [
			{'handlerId': 1, 'optionId': 1, 'name': 'split', 'label': 'Split line', 'dataType': 'bool', 'widgetType': 'radiobuttons', 'params': {"default":False}},
			{'handlerId': 1, 'optionId': 2, 'name': 'escape', 'label': 'Escape for html', 'dataType': 'bool', 'widgetType': 'radiobuttons', 'params': {"default":True}},
			{'handlerId': 1, 'optionId': 3, 'name': 'skip header line', 'label': 'Skip header lines', 'dataType': 'int', 'widgetType': 'input', 'params': {"default": 0}},
			{'handlerId': 1, 'optionId': 4, 'name': 'data column', 'label': 'Data column', 'dataType': 'int', 'widgetType': 'input', 'params': {"default":1}},
			{'handlerId': 1, 'optionId': 5, 'name': 'delimiter', 'label': 'Delimiter', 'dataType': 'string', 'widgetType': 'input', 'params': {"default":None}},
		])
		engine.execute(text("SELECT pg_catalog.setval('filehandleroptions_optionid_seq', 5, true)"))

	if load('tasktypes'):
		engine.execute(s.t_tasktypes.delete())
		engine.execute(s.t_tasktypes.insert(), [
			{'taskTypeId': 1, 'name': 'translation', 'description': 'free editing: yes, use of tag/label: optional, payment counted by: words'},
			{'taskTypeId': 2, 'name': 'text collection', 'description': 'free editing: yes, use of tag/label: optional, payment counted by: item'},
			{'taskTypeId': 3, 'name': 'markup', 'description': 'free editing: no, use of tag/label: yes, payment counted by: item'},
			{'taskTypeId': 4, 'name': '3-way translation', 'description': 'free editing: yes, use of tag/label: optional, payment counted by: words'},
			{'taskTypeId': 5, 'name': 'DEFT like', 'description': 'free editing: no, use of tag/label: yes, payment counted by: item'},
		])
		engine.execute(text("SELECT pg_catalog.setval('tasktypes_tasktypeid_seq', 5, true)"))

	# engine.execute(s.t_users.insert(), [
	# 	{'userId': 699}
	# ])

	# engine.execute(t_projects.delete())
	# engine.execute(t_projects.insert(), [
	# 	{'projectId': 10000, 'name': 'test project', 'description': 'for testing purposes', 'migratedBy': 699},
	# ])

	# engine.execute(t_tasks.delete())
	# engine.execute(t_tasks.insert(), [
	# 	{'projectid': 10000, 'taskid': 999999, 'name': 'fake task', 'tasktypeid': 1, 'status': 'active'},
	# ])

	# engine.execute(t_utteranceselections.delete());
	# engine.execute(t_utteranceselections.delete())
	# engine.execute(t_utteranceselections.insert(), [
	# 	{'selectionId': 1, 'taskId': 999999, 'userId': 699, 'limit': None},
	# ])

	# engine.execute(t_utteranceselectionfilters.delete())
	# engine.execute(t_utteranceselectionfilters.insert(), [
	# 	{'selectionId': 1, 'filterId': 1, 'isInclusive': True, 'isMandatory': False, 'filterType': 'qaseverity', 'description': 'Utterance less than 100.0% correct'},
	# ])

	# engine.execute(t_utteranceselectionfilterpieces.delete())
	# engine.execute(t_utteranceselectionfilterpieces.insert(), [
	# 	{'filterId': 1, 'index': 0, 'data': 'false'},
	# 	{'filterId': 1, 'index': 1, 'data': '1'},
	# 	{'filterId': 1, 'index': 2, 'data': 'true'},
	# ])

if __name__ == "__main__":
	import argparse
	uri = 'postgresql://localhost/atdb'
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('uri', metavar='URI', nargs='?', default=uri, help='URI of database, default: %s' % uri)
	args = parser.parse_args()
	engine = create_engine(args.uri)
	init_db(engine, DataConfig)
