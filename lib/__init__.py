import datetime
import pytz

from marshmallow import fields

# TODO use lr_utilities version
class DurationField(fields.Field):
	"""
	Marshmallow field to serialise a duration
	timedelta field.
	"""
	def _serialize(self, value, attr, obj):
		if value is None:
			return None
		return value.total_seconds()

	def _deserialize(self, value, attr, data):
		return datetime.timedelta(seconds=value)


def utcnow():
	return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

