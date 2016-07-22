import logging
import sys

from flask import current_app
from flask.ext.script import Manager
from sqlalchemy import func

from db import database as db
from db.model import Batch, Task

log = logging.getLogger(__name__)


JobCommand = Manager(usage="Runs housekeeping jobs")


@JobCommand.option("-t", "--task_id", default=None, help="reclaim expires batches for this task only")
def reclaim_expired_batches(task_id=None):

	if task_id:
		task = Task.query.get(task_id)

		if not task:
			log.error("task {0} does not exist".format(task_id))
			sys.exit(-1)

		tasks = [task_id]

	else:
		tasks = Task.query.all()

	for task in tasks:

		# get batches that have expired
		expired_batches = Batch.query\
			.filter(Batch.taskId==task.taskId)\
			.filter(Batch.leaseExpires<=func.now())\
			.all()
		
		if expired_batches:
			log.debug("found {0} expired batches for task {1}".format(len(expired_batches), task.taskId))

			for batch in expired_batches:
				batch.expire()

		else:
			log.debug("no expired batches found for task {0}".format(task.taskId))
