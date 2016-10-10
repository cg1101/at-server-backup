class MetaValueMixin:
	
	def to_dict(self):
		"""
		Converts to a JSON serializable dict.
		"""
		raise NotImplementedError


class MetaValue(MetaValueMixin):
	"""
	The value of a metadata category for
	some entity. Contains the raw value
	and the display value.
	"""

	def __init__(self, raw=None, display=None):
		self.raw = raw
		self.display = display

	@classmethod
	def load(cls, json_dict):
		"""
		Loads the meta value from JSON.
		"""
		return cls(**json_dict)

	def to_dict(self):
		return {
			"raw" : self.raw,
			"display" : self.display
		}


class InvalidMetaValue(MetaValueMixin):
	"""
	A submitted meta value that is
	considered invalid by the validator.
	"""

	def __init__(self, value):
		self.value = value

	def to_dict(self):
		return {
			"raw" : self.value,
			"invalid" : True
		}


class MetaValidator:
	"""
	Validates raw metadata values.
	"""
	VALIDATOR_TYPE = None

	@staticmethod
	def get_validator(json_dict):
		"""
		Returns the corresponding MetaValidator 
		object for the given JSON definition.
		"""
		validators = [
			IntValidator,
			FloatValidator,
			StringValidator,
			EnumValidator,
			RangeValidator,
		]

		# organise by type
		validators = dict([(validator_cls.VALIDATOR_TYPE, validator_cls) for validator_cls in validators])

		meta_type = json_dict.get("type")

		if meta_type is None:
			raise ValueError("No meta type specified")

		try:
			validator_cls = validators[meta_type]
		except KeyError:
			raise ValueError("Unknown meta type: %s" %meta_type)
	
		return validator_cls.load(json_dict)

	@classmethod
	def from_amr_demographic_category(cls, demographic_category):
		"""
		Returns the corresponding MetaValidator
		object for an AMR demographic category.
		"""

		# integer
		if demographic_category.TYPE == "integer":
			return IntValidator()

		# select
		elif demographic_category.TYPE == "select":
			allowed_values = [MetaValue(id, value) for id, value in demographic_category.options]
			return EnumValidator(allowed_values, "str")

		else:
			raise ValueError("Unhandled demographic category type: {0}".format(demographic_category.TYPE))
		
	@classmethod
	def load(cls, json_dict):
		raise NotImplementedError

	def to_dict(self):
		"""
		Converts to a JSON serializable dict.
		"""
		raise NotImplementedError

	def __call__(self, value):
		"""
		Validates the given metadata value. If
		successful, a MetaValue object will
		be returned.
		"""
		raise NotImplementedError


class SimpleValidator(MetaValidator):
	
	@classmethod
	def load(cls, json_dict):
		return cls()

	def to_dict(self):
		"""
		Converts to a JSON serializable dict.
		"""
		return {"type": self.VALIDATOR_TYPE}


class IntValidator(SimpleValidator):
	"""
	Validates integer metadata.
	"""
	VALIDATOR_TYPE = "int"

	def __call__(self, value):
		value = int(value)
		return MetaValue(raw=value, display=value)


class FloatValidator(SimpleValidator):
	"""
	Validates float metadata.
	"""
	VALIDATOR_TYPE = "float"
	
	def __call__(self, value):
		value = float(value)
		return MetaValue(raw=value, display=value)


class StringValidator(SimpleValidator):
	"""
	Validates string metadata
	"""
	VALIDATOR_TYPE = "string"
	
	def __call__(self, value):
		value = str(value)
		return MetaValue(raw=value, display=value)


class CastedValidatorMixin:
	"""
	Adds functionality for casting the 
	value being validated.
	Each subclass should set a 'cast'
	attribute which is the name of
	the cast function.
	"""

	def cast_value(self, value):
		"""
		Casts the value using the configured cast function.
		"""
		cast_func = eval(self.cast)
		return cast_func(value)


class EnumValidator(MetaValidator, CastedValidatorMixin):
	"""
	Validates enumerated-type metadata
	i.e. a finite list of allowed values
	"""
	VALIDATOR_TYPE = "enum"
	
	def __init__(self, allowed_values, cast):
		"""
		Expects a list of allowed MetaValue objects.
		"""
		if not allowed_values:
			raise ValueError("No allowed values given")
		
		# organise allowed values by key
		self.allowed_values = dict([(meta_value.raw, meta_value) for meta_value in allowed_values])
		self.cast = cast


	@classmethod
	def load(cls, json_dict):
		allowed_values = [MetaValue.load(value) for value in json_dict["allowed"]]
		cast = json_dict["cast"]
		return cls(allowed_values, cast)

	def to_dict(self):
		allowed_values = [meta_value.to_dict() for meta_value in self.allowed_values.values()]
		return {
			"type": self.VALIDATOR_TYPE,
			"allowed": allowed_values,
			"cast": self.cast,
		}
	
	def __call__(self, value):
		value = self.cast_value(value)
		
		if value not in self.allowed_values:
			raise ValueError("Unknown meta value: %s" %value)
		
		return self.allowed_values[value]
	

class RangeValidator(MetaValidator, CastedValidatorMixin):
	"""
	Validates ranged metadata
	i.e. a list of min/max bins
	"""
	VALIDATOR_TYPE = "range"
	
	class Range:
		def __init__(self, minimum=None, maximum=None):
			self.minimum = minimum
			self.maximum = maximum
			assert self.minimum is not None or self.maximum is not None

		def is_within(self, value):
			"""
			Checks if the given value is
			within the range.
			"""
			if self.minimum is not None and value < self.minimum:
				return False

			if self.maximum is not None and value > self.maximum:
				return False

			return True

		@classmethod
		def load(cls, json_dict):
			return cls(
				minimum=json_dict.get("minimum"),
				maximum=json_dict.get("maximum")
			)

		def to_dict(self):
			"""
			Converts to a JSON serializable dict.
			"""
			d = {}

			if self.minimum is not None:
				d["minimum"] = self.minimum

			if self.maximum is not None:
				d["maximum"] = self.maximum

			return d				

	def __init__(self, ranges, cast):
		"""
		Expects a list of Range objects.
		"""
		if not ranges:
			raise ValueError("No ranges given")

		self.ranges = ranges
		self.cast = cast

	@classmethod
	def load(cls, json_dict):
		ranges = [cls.Range.load(range) for range in json_dict["ranges"]]
		cast = json_dict["cast"]
		return cls(ranges, cast)

	def to_dict(self):
		ranges = [range.to_dict() for range in self.ranges]
		return {
			"type": self.VALIDATOR_TYPE,
			"cast": self.cast,
			"ranges": ranges,
		}
	
	def __call__(self, value):
		value = self.cast_value(value)
		for r in self.ranges:
			if r.is_within(value):
				return MetaValue(raw=value, display=value)
		raise ValueError("Value %s is not within any range" %value)


def process_received_metadata(received_value_dict, meta_categories):
	"""
	Processes metadata received from the field. Returns
	a list of two item tuples: (meta_category, meta_value or
	invalid_meta_value)
	"""

	# the received_value_dict was probably transferred as JSON
	# which doesn't allow integer object keys - convert them
	# back to integers
	received_value_dict = dict([(int(meta_category_id), value) for meta_category_id, value in received_value_dict.items()])

	meta_values = []

	for meta_category in meta_categories:
		
		# if received value for this category
		if meta_category.meta_category_id in received_value_dict:
			received_value = received_value_dict[meta_category.meta_category_id]
			validator = MetaValidator.get_validator(meta_category.validator)
			
			# validate
			try:
				meta_value = validator(received_value)
			except ValueError:
				meta_value = InvalidMetaValue(received_value)
			
			meta_values.append((meta_category, meta_value.to_dict()))

	return meta_values


def resolve_new_metadata(meta_entity, new_meta_values):
	"""
	Resolves new metadata for a meta entity according to
	any existing values. If the entity has:

	 * no existing value for the category, a new value is
	 added
	 * a differing existing value for the category, a
	 change request is added
	
	All other cases are ignored.
	"""

	# organise existing values by category
	existing_meta_values = dict([(value.meta_category.meta_category_id, value) for value in meta_entity.meta_values])
	
	for meta_category, new_value in new_meta_values:
		
		# if category has existing value
		if meta_category.meta_category_id in existing_meta_values:
			existing_value = existing_meta_values[meta_category.meta_category_id]

			# if existing value is different
			if existing_value.value["raw"] != new_value["raw"]:
				meta_entity.add_meta_change_request(meta_category, new_value)

		# no existing value
		else:
			meta_entity.add_meta_value(meta_category, new_value)
