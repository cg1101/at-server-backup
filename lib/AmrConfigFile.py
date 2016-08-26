#TODO move to lr_utilities when migrated to Python 3

# TODO
# name -> <title>
# extractor -> {"key": <id>}
# type should be mapped to validator, code to create the validator (to be saved)

import logging

from collections import OrderedDict
from lxml import etree

log = logging.getLogger(__name__)


class AmrConfigFileError(Exception): pass


class AmrConfigFile(object):

	DEMOGRAPHICS = "demographics"

	def __init__(self, demographics, other_nodes):
		self.demographics = demographics
		self.other_nodes = other_nodes

	@classmethod
	def load(cls, fp):
		xml = fp.read()
		root = etree.fromstring(xml)
		return cls.create(root)

	@classmethod
	def create(cls, node):

		demographics = []
		other_nodes = []

		for child in node:

			if child.tag == cls.DEMOGRAPHICS:
				demographics = cls.parse_demographics(child)

			else:
				other_nodes.append(child)

		return cls(demographics, other_nodes)

	@classmethod
	def parse_demographics(cls, demographics_node):
		categories = []

		for category_node in demographics_node:
			category = DemographicCategory.create(category_node)
			categories.append(category)

		return categories


class DemographicCategory(object):

	TYPE = None

	def __init__(self, id, title, **extra):
		self.id = id
		self.title = title

		for attr, value in extra.items():
			setattr(self, attr, value)

	@classmethod
	def create(cls, node):
		if node.tag != "category":
			raise AmrConfigFileError("Expected 'category' tag, got {0}".format(node.tag))

		type = None
		
		try:
			type = node.attrib["type"]
		except KeyError:
			raise AmrConfigFileError("Missing type for demographic category: {0}".format(node.attrib))

		category_types = {
			"select": SelectDemographicCategory,
			"integer": IntegerDemographicCategory
		}

		try:
			category_cls = category_types[type]
		except KeyError:
			raise AmrConfigFileError("Unknown demographic category: {0}".format(type))
		
		args = OrderedDict([("id", None), ("title", None)])

		for key in args:
			try:
				value = node.attrib[key]
			except KeyError:
				raise AmrConfigFileError("Missing {0} for demographic category: {1}".format(key, node.attrib))

			args[key] = value

		extra_attrs = category_cls.get_extra_attrs(node)
		return category_cls(*args.values(), **extra_attrs)

	@classmethod
	def get_extra_attrs(cls, node):
		return {}


class IntegerDemographicCategory(DemographicCategory):
	TYPE = "integer"


class SelectDemographicCategory(DemographicCategory):
	TYPE = "select"
	
	@classmethod
	def get_extra_attrs(cls, node):
		options = []
		ids = set()

		for option_node in node:

			if option_node.tag != "categoryselect":
				raise AmrConfigFileError("Expected 'category' tag, got {0}".format(option_node.tag))

			try:
				id = option_node.attrib["id"]
			except KeyError:
				raise AmrConfigFileError("Missing id attribute: {0}".format(option_node.attrib))

			value = option_node.text

			if id in ids:
				raise AmrConfigFileError("Duplicate categoryselect id: {0}".format(id))

			options.append((id, value))
		
		return {"options": options}
