
from flask import request, abort, session, jsonify

import db.model as m
from db.db import SS
from app.api import api, caps
from app.i18n import get_text as _
from . import api_1_0 as bp, InvalidUsage

_name = __file__.split('/')[-1].split('.')[0]

@bp.route(_name + '/', methods=['GET'])
@api
@caps()
def get_projects():
	'''
	returns a list of matched projects
	'''
	if request.args.get('t', '') == 'candidate':
		# TODO: check for capability
		if True:
			projects = m.PdbProject.query.filter(m.PdbProject.projectId.notin_(
				SS.query(m.Project.projectId))).all()
		else:
			projects = []
		rs = m.PdbProject.dump(projects)
	else:
		projects = m.Project.query.all()
		# TODO: filter-out projects that user doesn't manage
		rs = m.Project.dump(projects)
	return jsonify({
		'projects': rs,
	})


@bp.route(_name + '/<int:projectId>', methods=['GET'])
@api
@caps()
def get_project(projectId):
	'''
	returns specified project
	'''
	project = m.Project.query.get(projectId)
	if not project:
		raise InvalidUsage(_('project {0} not found').format(projectId), 404)
	return jsonify({
		'project': m.Project.dump(project),
	})


@bp.route(_name + '/<int:projectId>', methods=['PUT'])
@api
@caps()
def migrate_project(projectId):
	'''
	migrates project from pdb database
	'''
	candidate = m.PdbProject.query.get(projectId)
	if not candidate:
		raise InvalidUsage(_('project {0} not found').format(projectId), 404)
	project = m.Project.query.get(projectId)
	if project:
		raise InvalidUsage(_('project {0} already migrated').format(projectId))
	project = m.Project(projectId=candidate.projectId, name=candidate.name,
			_migratedByUser=session['current_user'])
	SS.add(project)
	SS.flush()
	# as an alternative, we do following to trigger flush()
	#project = m.Project.query.get(projectId)
	return jsonify({
		'status': _('project {0} successfully migrated').format(projectId),
		'project': m.Project.dump(project),
	})
