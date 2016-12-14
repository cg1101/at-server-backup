import datetime
import pytz

from marshmallow import fields


def utcnow():
	return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

