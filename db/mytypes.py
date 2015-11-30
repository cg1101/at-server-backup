#!/usr/bin/env python

import json

from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy.ext.mutable import Mutable

class JsonString(TypeDecorator):
	impl = TEXT
	def process_bind_param(self, value, dialect):
		if value is not None:
			value = json.dumps(value)
		return value
	def process_result_value(self, value, dialect):
		if value is not None:
			value = json.loads(value)
		return value

class MutableDict(Mutable, dict):
	@classmethod
	def coerce(klass, key, value):
		if not isinstance(value, MutableDict):
			if isinstance(value, dict):
				return MutableDict(value)
			return Mutable.coerce(key, value)
		else:
			return value
	def __setitem__(self, key, value):
		dict.__setitem__(self, key, value)
		self.changed()
	def __delitem__(self, key):
		dict.__delitem__(self, key)
		self.changed()

