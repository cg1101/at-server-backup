
from flask import Blueprint

webservices = bp = Blueprint('webservices', __name__)

@bp.route('/apply_user_search_action', methods=['GET', 'POST'])
def apply_user_search_action():
	return 'apply_user_search_action'

@bp.route('/apply_user_search_filters', methods=['GET', 'POST'])
def apply_user_search_filters():
	return 'apply_user_search_filters'

@bp.route('/available_qualifications', methods=['GET', 'POST'])
def get_available_qualification_tests():
	return 'qualification tests'

@bp.route('/available_work', methods=['GET', 'POST'])
def get_available_work_entries():
	return 'available_work'

@bp.route('/get_user_search_actions', methods=['GET', 'POST'])
def get_user_search_actions():
	return 'user_search_actions'

@bp.route('/get_user_search_filters', methods=['GET', 'POST'])
def get_user_search_filters():
	return 'user_search_filters'

@bp.route('/get_user_details_css', methods=['GET', 'POST'])
def get_user_details_css():
	return 'get_user_details_css'

@bp.route('/get_user_details_js', methods=['GET', 'POST'])
def get_user_details_js():
	return 'get_user_details_js'

@bp.route('/recent_work', methods=['GET', 'POST'])
def get_recent_work_entries():
	return 'recent_work'

@bp.route('/update_payments', methods=['GET', 'POST'])
def update_payments():
	return 'update_payments'

@bp.route('/user_details', methods=['GET', 'POST'])
def get_user_details():
	return 'user_details'
