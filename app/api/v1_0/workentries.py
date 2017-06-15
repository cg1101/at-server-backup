
from flask import request, jsonify

import db.model as m
from db.db import SS
from app.api import api, caps, MyForm, Field, validators
from app.i18n import get_text as _
from . import api_1_0 as bp, InvalidUsage

_name = __file__.split('/')[-1].split('.')[0]


@bp.route(_name + '/', methods=['GET'])
@api
@caps()
def get_work_entries():
	data = MyForm(
		Field('rawPieceId', is_mandatory=True,
			normalizer=lambda data, key, value: int(value[-1]
				) if isinstance(value, list) else int(value),
			validators=[
				validators.is_number,
		]),
	).get_data(use_args=True)
	rawPieceId = data['rawPieceId']
	workEntries = []
	rawPiece = m.RawPiece.query.get(rawPieceId)
	if rawPiece:
		rs = m.WorkEntry.query.filter(
			m.WorkEntry.taskId==rawPiece.taskId
			).filter(m.WorkEntry.rawPieceId==rawPieceId
			).filter(m.WorkEntry.workType!=m.WorkType.QA
			).distinct(m.WorkEntry.batchId, m.WorkEntry.rawPieceId
			).order_by(m.WorkEntry.batchId, m.WorkEntry.rawPieceId,
				m.WorkEntry.created.desc()
			).all()
		for w in rs:
			workEntries.append(w.dump(w))
	return jsonify(workEntries=workEntries)

