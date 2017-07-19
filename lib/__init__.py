import datetime
import pytz
import re

from functools import wraps


class GetConstantsMixin(object):
	"""
	Class mixin for use of the
	get_constants function.
	"""

	@classmethod
	def get_constants(cls):
		"""
		Returns the constants defined on the
		class. Constants are assumed to be
		variables with names consisting of
		uppercase letters or underscores only.
		"""
		constants = {}

		for attr in dir(cls):
			if re.match("[A-Z_]+$", attr):
				value = getattr(cls, attr)
				constants[attr] = value

		return constants


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
