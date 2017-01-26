#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
.. module: tx
.. versionadded:: 1.0

The :mod:`tx` module contains a number of constants, classes and functions
that facilitate transcription extract manipulation.

.. moduleauthor:: CHENG Gang <gcheng@appen.com.au>

"""

import fileinput, os, re

from recordfile import PlainRecord, iter_recs

CALL_ID = "Call ID"
UTT_ID = "Utterance ID"
QUEUE_NAME = "Queue Name"
CALL_COMMENT = "Call Comment"
DATA_TYPE = "Data Type"
FILE = "FILE"
TRANSCRIPTION = "TRANSCRIPTION"
LABELS = "LABELS"
USERS = "USERS"
INTERVAL = "INTERVAL"

LEVEL_MINIMAL = (TRANSCRIPTION,)
LEVEL_BASIC = (FILE, TRANSCRIPTION,)
LEVEL_STANDARD = (FILE, TRANSCRIPTION, LABELS,)
LEVEL_S2DUMP = (CALL_ID, UTT_ID, QUEUE_NAME, CALL_COMMENT,
		DATA_TYPE, FILE, TRANSCRIPTION, LABELS, USERS)
LEVEL_APPENSCRIBE = (FILE, INTERVAL, TRANSCRIPTION, LABELS,)

KEY_SET1 = ("FILE", "TRANSCRIPTION", "LABELS")
KEY_SET2 = ("Call ID", "Utterance ID", "Queue Name",
			"Call Comment", "Data Type",
			"FILE", "TRANSCRIPTION", "LABELS", "USERS")

TIMESTAMP = re.compile("\[(\d+\.\d{3})\]$")
"""
.. data: TIMESTAMP

Regular expression pattern that matches time stamps.
"""

TIMEDELTA = re.compile(r"""(?P<hour>\d+):
		(?P<min>[0-5][0-9]):
		(?P<sec>[0-5][0-9](?:\.\d+)?)$""", re.VERBOSE)
"""
.. data: TIMEDELTA

Regular expression pattern that matches interval literals.
"""

DUMMYFILE = re.compile("dudWavReplacement")	# do not add '$' here

JOINABLE  = re.compile(r"""
		(?P<key_p1>.*)_
		(?P<rate>\d+)_
		(?P<ordinal>\d+)_
		(?P<start>\d+)_
		(?P<end>\d+)
		(?P<key_p2>\.[^/]*)$""", re.VERBOSE)
"""
.. data: JOINABLE

Regular expression pattern that matches file names of cut-up audios for scrivener 2.

.. warning::
	Since scrivener 2 is no longer used, such audio file names should not be used anymore.

"""

P_SPLITTER  = re.compile(r"(\[\d+\.\d+\]|<(?:[^>]*?at_)\d+\.\d+>|\s+)")
P_TIMESTAMP = re.compile(r"""(\[(?P<v1>\d+\.\d+)\]|
		<(?P<prefix>.*at_)(?P<v2>\d+\.\d+)>)$""", re.VERBOSE)

def interval_to_ts(interval):
	"""
	.. func: interval_to_ts(interval)

	Convert interval literal to seconds in a float.

	.. note::
		*interval* must match the pattern :data:`tx.TIMEDELTA`.

	Here is an example:

	>>> from tx import interval_to_ts
	>>> interval_to_ts("0:03:30.384999")
	210.38499899999999

	"""

	m = TIMEDELTA.match(interval)
	if not m:
		raise ValueError, "%s: invalid interval literal" % interval
	ts_value = int(m.group("hour")) * 3600 + \
			int(m.group("min")) * 60 + float(m.group("sec"))
	return ts_value
# end of interval_to_ts

def ts_to_interval(ts_value):
	"""
	.. func: ts_to_interval(ts_value)

	Convert time stamp value to interval literal.

	.. note::
		*ts_value* should be a non-negative float representing time in seconds.

	Here is an example:

	>>> from tx import ts_to_interval
	>>> ts_to_interval(73.328)
	'0:01:13.328000'

	"""

	if ts_value < 0:
		raise ValueError, "%f: time stamp must not be negative" % ts_value
	hour = int(ts_value / 3600)
	ts_value -= 3600 * hour
	minute = int(ts_value / 60)
	second = ts_value - 60 * minute
	return "%d:%02d:%09.6f" % (hour, minute, second)
# end of ts_to_interval

class UttRecord(PlainRecord):
	"""
	.. class: UttRecord

	Class that holds data from utterance records, data can be accessed via keyword
	just like using a regular dictionary.
	"""
	def __init__(self, file, start, lines):
		PlainRecord.__init__(self, file, start, lines)
		# self.indice should be used internally to track
		# offsets of valid keyword lines
		self.indice = {}.fromkeys(KEY_SET2, -1)
		try:
			for i, l in enumerate(self.lines):
				kw = l.split(":")[0]
				if kw in self.indice:
					if self.indice[kw] >= 0:
						raise ValueError, "duplicate key '%s'" % kw
				self.indice[kw] = i
			for k in KEY_SET1:
				if self.indice[k] < 0:
					raise ValueError, "key '%s' missing" % k
		except ValueError, e:
			raise UttError("%s" % e, self)
	def __getitem__(self, key):
		if key not in self.indice:
			raise KeyError, key
		index = self.indice[key]
		if index < 0:
			raise KeyError, key
		return self.lines[index][len(key)+1:].strip()
	def __setitem__(self, key, value):
		index = self.indice[key]
		if index < 0:
			raise KeyError, key
		if isinstance(value, str):
			self.lines[index] = key + ": " + unicode(value, "utf-8")
		elif isinstance(value, unicode):
			self.lines[index] = key + ": " + value
		else:
			raise TypeError, "value must be str or unicode"
	def getCriticalLines(self):
		return [self.lines[self.indice[k]] for k in KEY_SET1]
	def brief(self):
		return "\n".join(self.getCriticalLines()) + "\n"
# end of class UttRecord

def iter_utts(files, encoding="utf-8", errhdlr=None):
	"""
	.. func: iter_utts(files, encoding="utf-8", errhdlr=None)

	`iter_utts` enumerate utterances from given file(s). Input files are
	transcription extract files, either in plain text format or compressed
	by gzip (\*.gz) or bzip2 (\*.bz2).

	*files* specifies a list of input extract files. A single filename is also allowed.

	*encoding* specifies the encoding of input files.

	*errhdlr* specifies a callable which takes

	The typical use is::

		from tx import iter_utts

		for utt in iter_utts(["a.tx", "b.gz", "c.bz2"]):
			print utt

	"""
	if errhdlr and not callable(errhdlr):
		raise TypeError, "errhdlr must be callable"
	for rec in iter_recs(files, encoding):
		try:
			utt = UttRecord(rec.file, rec.start, rec.lines)
			yield utt
		except UttError, e:
			if errhdlr:
				errhdlr(e)
			else:
				raise
# end of iter_utts

def load_utts(files, encoding="utf-8", errhdlr=None):
	utts = [utt for utt in iter_utts(files, encoding, errhdlr)]
	return utts
# end of load_utts

class UttManipulator:
	"""Defines some useful methods to manipulate utterance data."""
	def isJoinable(self, utt):
		assert isinstance(utt, UttRecord)
		return JOINABLE.match(utt["FILE"])
	def isDummy(self, utt):
		assert isinstance(utt, UttRecord)
		return DUMMYFILE.match(os.path.basename(utt["FILE"]))
	def splitJoinable(self, utt):
		"""Returns join root and utterance details."""
		assert isinstance(utt, UttRecord)
		m = JOINABLE.match(utt["FILE"])
		if not m:
			raise ValueError, "not a joinable utterance."
		root  = m.group("key_p1")
		rate  = int(m.group("rate"))
		seq   = int(m.group("ordinal"))
		start = int(m.group("start"))
		stop  = int(m.group("end"))
		return (root, rate, seq, start, stop)
	def splitCallPath(self, utt):
		assert isinstance(utt, UttRecord)
		m = JOINABLE.match(utt["FILE"])
		if m:
			root = m.group("key_p1")
		else:
			root = utt["FILE"]
		return os.path.split(root)
	def checkTS(self, utt, absolute=False):
		"""Check timestamps of joinable utterance."""
		assert isinstance(utt, UttRecord)

		todo = utt["TRANSCRIPTION"].split()
		lastTS = 0
		lastWasTS = True
		for tk in todo:
			m = TIMESTAMP.match(tk)
			if m:
				currTS = float(m.group(1))
				if currTS < lastTS:
					raise ValueError, "non-sequential timestamp '%s'"\
						% tk
				elif currTS == lastTS and not lastWasTS:
					raise ValueError, "non-sequential timestamp '%s'"\
						% tk
			else:
				lastWasTS = False
# end of class UttInspector

class TxExtract:
	"""
	Class that similuates transcription extract file.
	"""
	def __init__(self, filename="", encoding="utf-8"):
		self.utts = []
		self.loaded = False
		self.filename = filename
		self.encoding = encoding
		# load tx extract file if filename is provided
		# do not call _load_utt() for it is a generator function.
		# when it is called, it simply returns a generator
		# iterator but will not actually load the file.
		# we need a driver to make it work
		# this could be either _load(), or xread()
		if self.filename:
			self._load(filename)
	def xread(self, filename):
		"""UttRecord generator function."""
		if self.filename:
			raise RuntimeError, "TxExtract already loaded"
		self.generator = True
		self.filename  = filename
		for utt in self._load_utt(filename):
			yield utt
	def _load(self, filename):
		"""Drives utterance generator to work."""
		for utt in self._load_utt(filename):
			pass
	def _load_utt(self, filename):
		"""Utterance generator that is used inside a wrapper."""
		for utt in iter_utts(filename, self.encoding):
			self.utts.append(utt)
			if getattr(self, "generator", False):
				yield utt
		self.loaded = True
		if getattr(self, "generator", False):
			del self.generator
	def __len__(self):
		if not self.loaded:
			raise RuntimeError, "TxExtract loading not complete"
		return len(self.utts)
	def __str__(self):
		return "\n".join(map(str, self.utts))
	def __iter__(self):
		return self.utts.__iter__()
	def brief(self):
		return "\n".join(map(UttRecord.brief, self.utts))
# end of TxExtract

class UttError(Exception):
	"""
	.. exception: UttError

	"""
	def __init__(self, msg, utt):
		Exception.__init__(self, msg)
		if not isinstance(utt, UttRecord):
			raise TypeError, "utt: expected UttRecord, %s found" % \
					type(utt).__name__
		self.utt = utt
	def __str__(self):
		return self.message + "\n" + eval(repr(self.utt))
# end of class UttError

class UttRefError(Exception):
	"""
	.. exception: UttRefError
	"""
	def __init__(self, msg, utts):
		Exception.__init__(self, msg)
		for i, utt in enumerate(utts):
			if not isinstance(utt, UttRecord):
				raise TypeError, "utt: expected UttRecord, %s found" % \
						type(utt).__name__
		self.utts = utts[:]
	def __str__(self):
		return self.message + "\n" + "\n".join([eval(repr(utt))
				for utt in self.utts])
# end of class UttRefError

class TxInputError(Exception):
	"""
	.. exception: TxInputError
	"""
	def __init__(self, utterrs):
		for i, e in enumerate(utterrs):
			if not isinstance(e, UttError):
				raise TypeError, "sequence item %d: " % i + \
						"expected UttError, %s found" % \
						type(e).__name__
		self.errors = utterrs[:]
		self.message = "\n".join(["%s" % e for e in self.errors])
	def __str__(self):
		return self.message
# end of class TxInputError

def iter_joinable_utts(files, panic=False, durationSlack = 0.170):
	errors = []
	for utt in iter_utts(files, errhdlr=errors.append):
		try:
			m = JOINABLE.match(utt["FILE"])
			if m:
				joinkey = m.group("key_p1") + m.group("key_p2")
				rate = float(m.group("rate"))
				start = float(m.group("start")) / rate
				end = float(m.group("end")) / rate
			else:
				try:
					tmp = utt["INTERVAL"]
				except KeyError, e:
					raise UttError("not a joinable utterance", utt)
				joinkey = utt["FILE"]
				try:
					start, end = map(interval_to_ts, tmp.split())
				except ValueError, e:
					raise UttError("interval corrupted", utt)
			duration = end - start + 0.0005
			if duration <= 0:
				raise UttError("bad duration: " + \
						"start: %.3f, end: %.3f" % \
						(start, end), utt)
			tks = []            # buffer to store tokens
			ts0 = False         # start with a time stamp
			ts1 = False         # end with a time stamp
			last_v = -0.001     # last time stamp value to compare
			for tk in P_SPLITTER.split(utt["TRANSCRIPTION"]):
				if not tk.strip(): continue
				m = P_TIMESTAMP.match(tk)
				if not m:
					ts1 = False
					tks.append(tk)
					continue
				if not tks:
					ts0 = True
				ts1 = True
				v = m.group("v1")
				if v:
					prefix = ""
					v = float(v)
				else:
					prefix = m.group("prefix")
					v = float(m.group("v2"))
				if v > duration:
					if v - duration <= durationSlack:
						v = duration
					else:
						raise UttError("time stamp out of range: " + \
							"duration: %.3f, time stamp: %.3f" % \
							(duration, v), utt)
				if prefix:
					tks.append("[###" + prefix + "###]")
				if v < last_v:
					raise UttError("non-sequential time stamp: " + \
							"was: %.3f, now: %.3f" % \
							(last_v, v), utt)
				else:
					last_v = v
				tks.append("[%.3f]" % (v + start))
			yield (joinkey, start, end, ts0, ts1, tks, utt)
		except UttError, e:
			if panic: raise e
			errors.append(e)
	if errors:
		raise TxInputError(errors)
# end of iter_joinable_utts

# end of $URL: file:///local/svnroot/template/tx.py $

