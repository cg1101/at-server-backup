import time


# TODO move to lr utilities
def to_timestamp(dt):
	"""
	Converts datetime object to timestamp.
	"""
	return time.mktime(dt.timetuple())
