class MetaValue(object):
	"""
	Saved format of a metadata value.
	Used to save to the database as JSON.
	"""

	def __init__(self, value, invalid=False):
		self.value = value
		self.invalid = invalid

	@classmethod
	def load(cls, json_dict):
		"""
		Loads the meta value from JSON.
		"""
		return cls(**json_dict)

	def to_dict(self):
		d = {"value": self.value}
		
		if self.invalid:
			d.update({"invalid": self.invalid})
		
		return d


class MetaValidator(object):
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
			allowed_values = dict(demographic_category.options)
			return EnumValidator(**allowed_values)

		# string
		elif demographic_category.TYPE == "string":
			return StringValidator()
		
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
		return MetaValue(int(value))


class FloatValidator(SimpleValidator):
	"""
	Validates float metadata.
	"""
	VALIDATOR_TYPE = "float"
	
	def __call__(self, value):
		return MetaValue(float(value))


class StringValidator(SimpleValidator):
	"""
	Validates string metadata
	"""
	VALIDATOR_TYPE = "string"
	
	def __call__(self, value):
		return MetaValue(str(value))


class EnumValidator(MetaValidator):
	"""
	Validates enumerated-type metadata
	i.e. a finite list of allowed values
	"""
	VALIDATOR_TYPE = "enum"
	
	def __init__(self, **allowed_values):
		"""
		Expects a dictionary of allowed values.
		"""
		if not allowed_values:
			raise ValueError("No allowed values given")
		
		# organise allowed values by key
		self.allowed_values = allowed_values


	@classmethod
	def load(cls, json_dict):
		return cls(**json_dict["allowed"])

	def to_dict(self):
		return {
			"type": self.VALIDATOR_TYPE,
			"allowed": self.allowed_values,
		}

	def __call__(self, value):
		if value not in self.allowed_values:
			raise ValueError("Unknown meta value: %s" %value)
		
		return MetaValue(value)


def process_received_metadata(received_value_dict, meta_categories, expect_saved_value=False):
	"""
	Processes metadata received from the field. Returns
	a list of two item tuples: (meta_category, meta_value or
	invalid_meta_value)
	"""

	# the received_value_dict was probably transferred as JSON
	# which doesn't allow integer object keys - convert them
	# back to integers
	received_value_dict = dict([(int(meta_category_id), value) for meta_category_id, value in received_value_dict.items()])

	if expect_saved_value:
		for meta_category_id, value in received_value_dict.items():
			received_value_dict[meta_category_id] = value["value"]

	meta_values = []

	for meta_category in meta_categories:
		
		# if received value for this category
		if meta_category.meta_category_id in received_value_dict:
			received_value = received_value_dict[meta_category.meta_category_id]
			
			# validate
			try:
				meta_value = meta_category.validator(received_value)
			except ValueError:
				meta_value = MetaValue(received_value, invalid=True)
			
			meta_values.append((meta_category, meta_value.to_dict()))

	return meta_values


def resolve_new_metadata(meta_entity, new_meta_values, user=None, change_method_name=None, add_change_requests=False, add_log_entries=True):
	"""
	Resolves new metadata for a meta entity according to
	any existing values. If the entity has:

	 * no existing value for the category, a new value is
	 added
	 * a differing existing value for the category, the
	 value is updated or a change request is added
	
	All other cases are ignored.
	"""

	if (add_log_entries or add_change_requests) and (user is None or change_method_name is None):
		raise RuntimeError("expecting user and change method when adding log entries or change requests")

	# organise existing values by category
	existing_meta_values = dict([(value.meta_category.meta_category_id, value) for value in meta_entity.meta_values])
	
	for meta_category, new_value in new_meta_values:
	
		# if category has existing value
		if meta_category.meta_category_id in existing_meta_values:
			existing_value = existing_meta_values[meta_category.meta_category_id]

			# if existing value is different
			if existing_value.value["value"] != new_value["value"]:

				# add change request
				if add_change_requests:
					meta_entity.add_meta_change_request(meta_category, new_value)

				# update value
				else:

					if add_log_entries:
						meta_entity.add_change_log_entry(
							meta_category,
							existing_value.value,
							new_value,
							user,
							change_method_name
						)

					existing_value.value = new_value

		# no existing value
		else:
			meta_entity.add_meta_value(meta_category, new_value)
