
from flask import request, abort, session

import db.model as m
from db.db import SS
from app.api import ajax, caps, get_text as _
from . import api_1_0 as bp

_name = __file__.split('/')[-1].split('.')[0]

@bp.route(_name + '/', methods=['GET'])
@ajax
@caps()
def get_projects():
	'''
	returns a list of matched projects
	'''
	if request.args.get('t', '') == 'candidate':
		if True: # and user has capability
			projects = m.PdbProject.query.filter(m.PdbProject.projectId.notin_(
				SS.query(m.Project.projectId))).all()
		else:
			projects = []
		rs = m.PdbProject.dump(projects)
	else:
		projects = m.Project.query.all()
		# TODO: filter-out projects that user doesn't manage
		rs = m.Project.dump(projects)
	return {
		'projects': rs,
	}


@bp.route(_name + '/<int:projectId>', methods=['GET'])
@ajax
@caps()
def get_project(projectId):
	'''
	returns specified project
	'''
	project = m.Project.query.get(projectId)
	if not project:
		abort(404)
	return {
		'project': m.Project.dump(project),
	}


@bp.route(_name + '/<int:projectId>', methods=['PUT'])
@ajax
@caps()
def migrate_project(projectId):
	'''
	migrates project from pdb database
	'''
	candidate = m.PdbProject.query.get(projectId)
	if not candidate:
		raise RuntimeError, _('project {0} not found').format(projectId)
	project = m.Project.query.get(projectId)
	if project:
		raise RuntimeError, _('project {0} already migrated').format(projectId)
	project = m.Project(projectId=candidate.projectId, name=candidate.name, _migratedByUser=session['current_user'])
	SS.add(project)
 	project = m.Project.query.get(projectId)
	s = m.ProjectSchema()
	return {
		'status': _('project {0} successfully migrated').format(projectId),
		'project': m.Project.dump(project),
	}
