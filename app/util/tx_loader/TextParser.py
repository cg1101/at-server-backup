#!/usr/bin/env python

import re
import cgi
import logging
import logging.handlers
import cStringIO
from xml.dom.minidom import getDOMImplementation

log = logging.getLogger(__name__)
logging.basicConfig(format="%(message)s", level=logging.DEBUG)

DEBUG_MODE = False

TOKEN_LITERAL = "TOKEN_LITERAL"
TOKEN_BLANK = "TOKEN_BLANK"
TOKEN_EVENT = "TOKEN_EVENT"
TOKEN_PREFIX = "TOKEN_PREFIX"
TOKEN_MARKUP_OPEN = "TOKEN_MARKUP_OPEN"
TOKEN_MARKUP_CLOSE = "TOKEN_MARKUP_CLOSE"
TOKEN_EMBEDDABLE_OPEN = "TOKEN_EMBEDDABLE_OPEN"
TOKEN_EMBEDDABLE_CLOSE = "TOKEN_EMBEDDABLE_CLOSE"
TOKEN_END = 'TOKEN_END'

PO_MARKUP = 'PO_MARKUP'
PO_PREFIX = 'PO_PREFIX'
PO_EVENT = 'PO_EVENT'
PO_EMBEDDABLE = 'PO_EMBEDDABLE'

class TokenType(object):
	def __init__(self, name, regex, escape=True, tagid=None):
		self.name = name
		self.text = regex
		self.regex = re.compile(re.escape(regex) if escape else regex)
		self.length = len(regex)
		self.tagid = tagid

TOKEN_TYPE_LITERAL = TokenType(TOKEN_LITERAL, r'\S+', False)
TOKEN_TYPE_BLANK = TokenType(TOKEN_BLANK, r'\s+', False)
TOKEN_TYPE_END = TokenType(TOKEN_END, '^$', False)

class Tokenizer(object):
	def __init__(self, tokenTypes):
		self.tokenTypes = tokenTypes[:]
	def __call__(self, s):
		toTry = sorted(self.tokenTypes, key=lambda x: x.length, reverse=True)
		for i in toTry:
			#print i.regex.pattern
			pass
		pos = 0
		while s[pos:]:
			#print "\n" + s
			#print " " * pos + "^"
			candidate = None
			# try tokenTypes defined from tags first
			for tt in toTry:
				if s[pos:].startswith(tt.text):
					yield (tt.text, tt.length, tt)
					pos += tt.length
					break
			else:
				m = TOKEN_TYPE_BLANK.regex.match(s[pos:])
				if m:
					yield (m.group(0), m.end(), TOKEN_TYPE_BLANK)
					pos += len(m.group(0))
					continue
				candidate = None
				for tt in toTry:
					offset = s[pos:].find(tt.text)
					if offset > 0:
						if not candidate:
							candidate = (offset, tt.text, tt.length, tt)
						elif offset < candidate[0]:
							candidate = (offset, tt.text, tt.length, tt)
				m = TOKEN_TYPE_LITERAL.regex.match(s[pos:])
				matchedText = m.group(0)
				if candidate and m.end() >= candidate[0]:
					# shorten it
					yield (s[pos:][:candidate[0]], candidate[0], TOKEN_TYPE_LITERAL)
					yield tuple(candidate[1:])
					pos += candidate[0] + candidate[2]
					continue
				else:
					yield (m.group(0), m.end(), TOKEN_TYPE_LITERAL)
					pos += m.end()

		assert not s[pos:]
		yield ('', 0, TOKEN_TYPE_END)

class ParserBase(object):
	pass

class Token(ParserBase, unicode):
	def __new__(cls, value, type, tagid=None):
		self = super(Token, cls).__new__(cls, value)
		self.type = type
		self.tagid = tagid
		return self
	def __repr__(self):
		return '<%s(%s), tagid:%s>' % (self.type, super(Token, self.__class__).__repr__(self), self.tagid)

class ParsedObject(ParserBase):
	def __init__(self, type, items, tagid=None):
		self.type = type
		self.items = items[:]
		self.tagid = tagid
	def __repr__(self):
		return '<%s:[%s], tagid:%s>' % (self.type, (','.join(['%r' % i for i in self.items])), self.tagid)

# grammar
'''
1 PO_SEQ = (TOKEN_LITERAL | TOKEN_BLANK | TOKEN_EVENT | PO_PREFIX | PO_MARKUP | PO_EMBEDDABLE)*
2 PO_PREFIX := TOKEN_PREFIX TOKEN_LITERAL
3 PO_MARKUP := TOKEN_MARKUP_OPEN (TOKEN_LITERAL | TOKEN_BLANK)* TOKEN_MARKUP_CLOSE
4 PO_EMBEDDABLE := TOKEN_EMBEDDABLE_OPEN PO_EMBEDDABLE_CONTENT TOKEN_EMBEDDABLE_CLOSE;
5 PO_EMBEDDABLE_CONTENT := (TOKEN_LITERAL|TOKEN_BLANK|PO_EMBEDDABLE)*
'''

STATES = {
	# input, action, next state
	# state 0
	0: {
		TOKEN_END: ('accept',),
		TOKEN_LITERAL: ('add',),
		TOKEN_BLANK: ('add',),
		PO_EVENT: ('add',),
		PO_PREFIX: ('add',),
		PO_MARKUP: ('add',),
		PO_EMBEDDABLE: ('add',),
		TOKEN_EVENT: ('push', 1),
		TOKEN_PREFIX: ('push', 2),
		TOKEN_MARKUP_OPEN: ('push', 3),
		TOKEN_EMBEDDABLE_OPEN: ('push', 4),
	},
	# state 1 inside event
	1: {
		None: ('reduce', 'PO_EVENT')
	},
	# state 2 inside prefix
	2: {
		TOKEN_LITERAL: ('reduce', 'PO_PREFIX'),
	},
	# state 3 inside markup
	3: {
		TOKEN_LITERAL: ('add',),
		TOKEN_BLANK: ('add',),
		TOKEN_MARKUP_CLOSE: ('reduce', 'PO_MARKUP'),
	},
	# state 4 inside embeddable
	4: {
		TOKEN_LITERAL: ('add',),
		TOKEN_BLANK: ('add',),
		TOKEN_EMBEDDABLE_OPEN: ('push', 4),
		TOKEN_EMBEDDABLE_CLOSE: ('reduce', 'PO_EMBEDDABLE'),
		PO_EMBEDDABLE: ('add',),
	},
}

import pprint
class Parser(object):
	def __init__(self, tokenizer, tags):
		self.tokenizer = tokenizer
		self.tags = tags
		self.tagById = {}
		for t in tags:
			assert t.tagId not in self.tagById
			self.tagById[t.tagId] = t
	def __call__(self, text):
		'''
		first parse input text into a tree,
		then dump this parse result tree as html
		'''
		tokens = [Token(matchedText, tokenType.name, tagid=tokenType.tagid) for
			(matchedText, matchedLength, tokenType) in self.tokenizer(text)]

		if DEBUG_MODE:
			f = cStringIO.StringIO()
			f.write("\nTokens:\n")
			for token in tokens:
				f.write("%s:\t'%s', %d, tagid: %s\n" % (token.type, token, len(token), token.tagid))
			log.debug('\033[1;32m%s\033[0m' % f.getvalue())
			f.close()

		parsing_stack = []
		parsing_stack.append((0, []))

		def do_reduce(po_type, items):
			#log.debug('reducing to %s using %s' % (po_type, items))
			if items[0].type == TOKEN_MARKUP_OPEN:
				assert items[-1].type == TOKEN_MARKUP_CLOSE and items[0].tagid == items[-1].tagid
			elif items[0].type == TOKEN_EMBEDDABLE_OPEN:
				assert items[-1].type == TOKEN_EMBEDDABLE_CLOSE and items[0].tagid == items[-1].tagid
			po = ParsedObject(po_type, items, tagid=items[0].tagid)
			parsing_stack.pop()
			tokens.insert(0, po)

		def dump_item(item, doc, parentNode):
			if item.type in (TOKEN_BLANK, TOKEN_LITERAL):
				node = doc.createTextNode(item)
				parentNode.appendChild(node)
			elif item.type in (PO_EVENT,):
				node = doc.createElement("IMG")
				node.setAttribute('tagid', str(item.tagid))
				node.setAttribute('tagtype', self.tagById[item.tagid].tagType)
				assert len(item.items) == 1
				parentNode.appendChild(node)
			elif item.type in (PO_PREFIX,):
				assert len(item.items) == 2
				tag = self.tagById[item.tagid]
				node = doc.createElement('SPAN')
				node.setAttribute('tagid', str(item.tagid))
				node.setAttribute('tagtype', self.tagById[item.tagid].tagType)
				node.setAttribute('style', tag.style)
				dump_item(item.items[1], doc, node)
				parentNode.appendChild(node)
			elif item.type in (PO_MARKUP, PO_EMBEDDABLE):
				opening = item.items[0]
				closing = item.items[-1]
				try:
					assert opening.tagid == closing.tagid == item.tagid
				except:
					print opening, closing, item
				tag = self.tagById[opening.tagid]
				node = doc.createElement('SPAN')
				node.setAttribute('tagid', str(item.tagid))
				node.setAttribute('tagtype', tag.tagType)
				node.setAttribute('style', tag.style)
				for j in item.items[1:-1]:
					dump_item(j, doc, node)
				parentNode.appendChild(node)
			else:
				raise RuntimeError, "unexpected token: %s" % item

		def dump(parsed_items):
			impl = getDOMImplementation()
			doc = impl.createDocument(None, 'div', None)
			root = doc.documentElement
			for item in parsed_items:
				dump_item(item, doc, root)
			result = doc.toxml()
			result = result.replace('<?xml version="1.0" ?>', '').replace('<div>', '').replace('</div>', '')
			return result
		while tokens:
			# print '=' * 70
			# pprint.pprint(parsing_stack)

			statusTuple = parsing_stack[-1]
			currentState = statusTuple[0]
			items = statusTuple[1]

			if None in STATES[currentState]:
				# default action, no need to fetch lookAheadToken
				t = STATES[currentState][None]
				action = t[0]
				if action == 'reduce':
					# TODO: we need to check to make sure tagid matches
					do_reduce(t[1], items)
			else:
				lookAheadToken = tokens.pop(0)
				if isinstance(lookAheadToken, Token):
					key = lookAheadToken.type
				elif isinstance(lookAheadToken, ParsedObject):
					key = lookAheadToken.type
				else:
					raise RuntimeError, 'expecting Token/ParsedObject only'
				t = STATES[currentState].get(key, None)
				if t == None:
					raise RuntimeError, 'paring error detected'
				action = t[0]
				# print 'lookAheadToken: ==>%s<==' % lookAheadToken
				# print 'key: ==>%s<==' % key
				# print 'tuple: ==>%r<==' % (t,)
				# print 'action=%s' % action
				if action == 'add':
					items.append(lookAheadToken)
					continue
				elif action == 'push':
					nextState = t[1]
					parsing_stack.append((nextState, [lookAheadToken]))
				elif action == 'accept':
					assert len(parsing_stack) == 1
					assert currentState == 0
					assert len(tokens) == 0
					break
				elif action == 'reduce':
					items.append(lookAheadToken)
					do_reduce(t[1], items)

		text = dump(parsing_stack[-1][1])
		return text

def get_token_types(tags):
	tokenTypes = []
	regs = {}
	for t in tags:
		s = t.extractStart
		assert s and s == s.strip()
		if s in regs:
			raise ValueError, 'ambiguous tag configuration: %s' % s
		regs[s] = t
		if t.tagType == 'Event':
			assert not t.extractEnd
			tt = TokenType(TOKEN_EVENT, t.extractStart, tagid=t.tagId)
			tokenTypes.append(tt)
		elif t.tagType in ('Span', 'Substitution', 'Footnote', 'Entity'):
			if t.extractEnd:
				tt = TokenType(TOKEN_MARKUP_OPEN, t.extractStart, tagid=t.tagId)
				tokenTypes.append(tt)
				tt = TokenType(TOKEN_MARKUP_CLOSE, t.extractEnd, tagid=t.tagId)
				tokenTypes.append(tt)
			else:
				tt = TokenType(TOKEN_PREFIX, t.extractStart, tagid=t.tagId)
				tokenTypes.append(tt)
		elif t.tagType == 'SpanB':
			tt = TokenType(TOKEN_EMBEDDABLE_OPEN, t.extractStart, tagid=t.tagId)
			tokenTypes.append(tt)
			assert t.extractEnd
			tt = TokenType(TOKEN_EMBEDDABLE_CLOSE, t.extractEnd, tagid=t.tagId)
			tokenTypes.append(tt)
	return tokenTypes

class TxParser(object):
	def __init__(self, tags):
		tokenTypes = get_token_types(tags)
		if not tokenTypes:
			self.parser = lambda x: cgi.escape(x)
		else:
			tokenizer = Tokenizer(tokenTypes)
			self.parser = Parser(tokenizer, tags)

	def parse(self, text):
		"""
		parse input text, convert text into html format
		"""
		return self.parser(text)

def main():
	import argparse
	import fileinput
	import database.utilities as dbutil
	from database.pool import getCursor

	global log
	log = logging.getLogger('TextParser')
	# handler = logging.StreamHandler()
	# handler.setFormatter(logging.Formatter('\033[1;31m%(message)s\033[0m'))
	# log.setLevel(logging.DEBUG)
	# log.addHandler(handler)

	parser = argparse.ArgumentParser(__doc__)
	parser.add_argument('--taskID', metavar='TASK_ID', help='Task to use')
	parser.add_argument('--tagSetID', metavar='TAG_SET_ID', help='Tag set id to use')
	parser.add_argument('input', nargs='*', help='Input files')
	parser.add_argument('-D', '--debug', action='store_true', default=False, help='Turn on debug mode')

	args = parser.parse_args()
	cursor = getCursor()
	if args.tagSetID:
		tags = dbutil.getTags(cursor, tagSetID=args.tagSetID)
	elif args.taskID:
		try:
			task = dbutil.getTasks(cursor, taskID=args.taskID)[0]
		except:
			parser.error('cannot find task %s' % args.taskID)
		tags = [] if task.tagsetid == None else dbutil.getTags(cursor, tagSetID=task.tagsetid)
	else:
		parser.error('must specify either taskID or tagSetID')

	if args.debug:
		global DEBUG_MODE
		DEBUG_MODE = True

	if DEBUG_MODE:
		f = cStringIO.StringIO()
		f.write('\nfound %d tags\n' % len(tags))
		for t in tags:
			f.write('tag #%d: %s, %s %s\n' % (t.tagid, t.tagtype, t.extractstart, t.extractend or ''))
		log.info('\033[1;34m%s\033[0m' % f.getvalue())
		f.close()

	txParser = TxParser(tags)
	for l in map(lambda x: x.rstrip('\r\n'), fileinput.input(args.input)):
		print txParser.parse(l)


if __name__ == "__main__":
	main()
