
import re
import functools
import cgi
import json

from app.i18n import get_text as _

class FileHandler(object):
	_registry = {}
	@classmethod
	def get_handler(cls, name):
		try:
			handler = cls._registry[name]
		except KeyError, e:
			raise RuntimeError(_('file handler {0} not found').format(name))
		return handler
	@classmethod
	def register_handler(cls, name, func):
		if cls._registry.has_key(name):
			raise RuntimeError(_('file handler {0} already registered').format(name))
		if not callable(func):
			raise RuntimeError(_('\'func\' must be a callable'))
		handler = super(FileHandler, cls).__new__(cls)
		handler.name = name
		handler.func = func
		cls._registry[name] = handler
		return handler
	def __init__(self, *args, **kwargs):
		raise RuntimeError(_('FileHandler must not be directly instanitated,',
			'please call factory method `register_handler`.'))
	def load_data(self, file, **options):
		return self.func(file, **options)


def count_words(text):
	return len(text.split())


def smart(fn):
	@functools.wraps(fn)
	def smart_loader(file, *args, **kwargs):
		close_on_exit = False
		if isinstance(file, basestring):
			fname = file
			file = open(fname)
			close_on_exit = True
		try:
			return fn(file, *args, **kwargs)
		finally:
			if close_on_exit:
				file.close()
	return smart_loader


@smart
def load_generic_text_file(file, split=False, escape=True, skip_header_line=0, data_column=1, delimiter=None, **kwargs):
	# normalize/validate options
	split = bool(split)
	escape = bool(escape)
	try:
		skip_header_line = int(skip_header_line)
		if skip_header_line < 0:
			skip_header_line = 0
	except ValueError:
		skip_header_line = 0
	try:
		data_column = int(data_column)
		if data_column < 1:
			data_column = 1
	except:
		data_column = 1
	if not isinstance(delimiter, basestring) or delimiter == '':
		delimiter = '\t'
	else:
		delimiter = re.escape(delimiter)

	def get_field(line, delimiter='\t', data_column=1):
		return re.split(delimiter, line)[data_column-1]

	if split:
		get_data = functools.partial(get_field, delimiter=delimiter, data_column=data_column)
	else:
		get_data = lambda (x): x

	if escape:
		html_safe = lambda (x): cgi.escape(x)
	else:
		html_safe = lambda (x): x

	itemDicts = []
	for i, l in enumerate(file):
		if i < skip_header_line:
			continue
		l = unicode(l.rstrip('\r\n'), 'utf-8')
		data = get_data(l)
		itemDicts.append({
			'rawText': html_safe(data),
			'words': count_words(data),
		})
	return itemDicts


@smart
def load_tdf_file(file):
	itemDicts = []
	for i, l in enumerate(file):
		if i == 0 and l.startswith('file\t'):
			continue
		fields = l.split('\t')
		if len(fields) != 14:
			raise ValueError(_('invalid format of input tdf file'))
		data = fields[7]
		itemDicts.append({
			'rawText': cgi.escape(data),
			'words': count_words(data),
		})
	return itemDicts


@smart
def load_utt_file(file):
	itemDicts = []
	jsonDict = json.load(file)
	# jsonDict['taskId']
	utts = jsonDict['utterances']
	for utt in utts:
		meta = {}
		for key in ('filePath', 'audioSpec', 'audioDataLocation'):
			meta[key] = utt[key]
		itemDicts.append(dict(
			rawText='',
			hypothesis=utt['hypothesis'],
			assemblyContext=utt['url'],
			meta=json.dumps(meta),
		))
	return itemDicts


FileHandler.register_handler('plaintext', load_generic_text_file)
FileHandler.register_handler('tdf', load_tdf_file)
FileHandler.register_handler('utts', load_utt_file)


def get_handler(name):
	return FileHandler.get_handler(name)

