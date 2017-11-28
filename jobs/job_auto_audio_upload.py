import logging
import time

from flask import current_app
from sqlalchemy import or_

from LRUtilities.Misc import get_traceback_str
from db.db import SS as session
from db.model import Task, TaskType


log = logging.getLogger(__name__)


def main(taskId=None):
	logging.basicConfig(level=logging.DEBUG)

	from app import audio_server
	from application import application as app
	
	with app.app_context():

		tasks = Task.query\
			.filter_by(status=Task.STATUS_ACTIVE)\
			.filter_by(auto_loading=True)\
			.filter(or_(Task.taskType == TaskType.TRANSCRIPTION, Task.taskType == TaskType.AUDIO_CHECKING))\
			.all()

		log.info("tasks found: {0}".format(len(tasks)))
		log.debug("api class:{0}".format(current_app.config["AUDIO_SERVER_API_CLS"]))

		for task in tasks:
			log.info("uploading audio for {0}".format(task.display_name))

			try:
				audio_server.api.start_load(task.task_id, current_app.config["ENV"])
				
				# wait so that the audio server staggers requests slightly
				time.sleep(10)
			
			except Exception, e:
				log.error("error starting upload for {0}".format(task.task_id))
				log.error(get_traceback_str())
				continue
