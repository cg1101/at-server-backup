from db.model import Project, Task, TaskType, User


class keys(object):
	
	# projects
	project_id_1 = 101
	project_id_2 = 102

	# tasks
	task_id_1 = 1001

	# users
	test_user_appen_id = 1


def add_sample_data(session):
	adders = [
		add_users,
		add_projects,
		add_tasks,
	]
		
	for adder in adders:
		adder(session)


def add_projects(session):
	session.add(Project(
		project_id=keys.project_id_1,
		name="Sample Project 1",
		migrated_by=keys.test_user_appen_id,
	))

	session.add(Project(
		project_id=keys.project_id_2,
		name="Sample Project 2",
		migrated_by=keys.test_user_appen_id,
	))


def add_tasks(session):
	session.add(Task(
		task_id=keys.task_id_1,
		name="Sample Task 1",
		project_id=keys.project_id_1,
		_taskType=session.query(TaskType).filter_by(name="Audio Checking").one(),
	))


def add_users(session):
	session.add(User(
		appen_id=keys.test_user_appen_id,
		email_address="test-user@appen.com",
		given_name="Test",
		family_name="User",
	))
