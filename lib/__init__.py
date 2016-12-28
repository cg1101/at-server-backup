import datetime
import pytz

from functools import wraps


def utcnow():
	return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)


def validator(fn):
	"""
	Decorator for wrapping a function that returns a MyForm
	validator which does not require any external context.
	The function itself can be passed to the validator list,
	rather than the validator that is returned e.g.

	def get_validator():
		return validator_fn

	validators = [
		get_validator(),	# function is called
	]

	becomes:

	@validator
	def get_validator():
		return validator_fn

	validators = [
		get_validator,		# function is called later
	]
	"""

	@wraps(fn)
	def decorated(self_or_cls, *args, **kwargs):
		validator_fn = fn(self_or_cls)
		return validator_fn(*args, **kwargs)

	return decorated
