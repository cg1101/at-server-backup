#!/usr/bin/python

import fileinput

class PlainRecord:
	"""A group of non-blank lines from the same file."""
	def __init__(self, file, start, lines):
		if not isinstance(file, str):
			raise TypeError, \
				"file: expected string, '%s' found" \
				% type(file).__name__
		elif file == "":
			raise ValueError, "invalid filename: '%s'" % file
		if not isinstance(start, int):
			raise TypeError, \
				"start: expected integer, '%s' found" \
				% type(start).__name__
		elif start < 0:
			raise ValueError, "invalid line number: %d" % start
		try:
			it = enumerate(lines)
		except TypeError:
			raise TypeError, \
				"lines: expected sequence, '%s' found" \
				% type(lines).__name__
		for i, l in it:
			if not isinstance(l, basestring):
				raise TypeError, "lines: sequence %d: "\
						"expected string, '%s' found" \
						% (i, type(l).__name__)
		self.file  = file
		self.start = start
		self.lines = lines
		# append an empty line if there isn't one
		# this could happen at the end of a file
		if self.lines[-1].strip():
			self.lines.append("")
	def __str__(self):
		return "\n".join(self.lines)
	def __repr__(self):
		msg = "File '%s', line %d-%d\n" % (self.file,
			self.start, self.start + len(self.lines) - 1)
		return repr(msg + self.__str__())
	def __cmp__(self, other):
		if self.file < other.file:
			return -1
		elif self.file > other.file:
			return 1
		elif self.start < other.start:
			return -1
		elif self.start > other.start:
			return 1
		elif self.lines == self.lines:
			return 0
		else:
			# something really bad happens
			raise ValueError, "inconsistent records in '%s'" \
				% self.file
	def __len__(self):
		return len(self.lines)
# end of class PlainRecord

def iter_recs(files, encoding="utf-8"):
	filename = ""
	start = 0
	buf = []
	print ('input file spec files is', files)
	if isinstance(files, file) or True:
		line_no = 0
		filename = getattr(files, 'name', '<unknown>')
		for l in files:
			line_no += 1
			l = l.rstrip("\r\n")
			if l.strip():
				if not buf:
					start = line_no
				buf.append(unicode(l, encoding))
			else:
				if buf:
					buf.append(l)
					yield PlainRecord(filename, start, buf)
					buf = []
	# else:
	# 	for l in fileinput.input(files, openhook=fileinput.hook_compressed):
	# 		line_no = fileinput.filelineno()
	# 		if line_no == 1:
	# 			if buf:
	# 				yield PlainRecord(filename, start, buf)
	# 				buf = []
	# 			filename = fileinput.filename()
	# 		l = l.rstrip("\r\n")
	# 		if l.strip():
	# 			if not buf:
	# 				start = line_no
	# 			buf.append(unicode(l, encoding))
	# 		else:
	# 			if buf:
	# 				buf.append(l)
	# 				yield PlainRecord(filename, start, buf)
	# 				buf = []
	if buf:
		yield PlainRecord(filename, start, buf)
	fileinput.close()
# end of iter_recs
