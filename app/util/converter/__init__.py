
import os
import re
import unicodedata

from lxml import etree

import db.model as m


_dir = os.path.dirname(__file__)

class ConversionError(Exception):
	pass

class HtmlTextFormatError(ConversionError):
	pass

class XmlTextFormatError(ConversionError):
	pass

class Converter(object):
	HTML2XML = etree.XSLT(etree.parse(os.path.join(_dir, 'html2xml.xsl')))
	XML2HTML = etree.XSLT(etree.parse(os.path.join(_dir, 'xml2html.xsl')))

	NO_BREAK_SPACE = unicodedata.lookup("NO-BREAK SPACE") # &nbsp;

	tags = {}


	@classmethod
	def htmlText2HtmlDoc(cls, htmlText, nullable=True):
		if htmlText is None:
			if nullable:
				htmlText = ''
			else:
				raise ValueError('htmlText must not be None')
		if not isinstance(htmlText, basestring):
			raise TypeError('htmlText must be a string')
		if not isinstance(htmlText, unicode):
			htmlText = unicode(htmlText, 'utf-8')
		try:
			htmlDoc = etree.XML(u'<body>{}</body>'.format(htmlText), etree.HTMLParser())
		except:
			raise HtmlTextFormatError('invalid html text: {}'.format(htmlText))
		return htmlDoc

	@classmethod
	def htmlDoc2XmlDoc(cls, htmlDoc):
		xmlDoc = cls.HTML2XML(htmlDoc)
		return xmlDoc

	@classmethod
	def xmlDoc2XmlText(cls, xmlDoc):
		xmlText = etree.tostring(xmlDoc, encoding=unicode)
		xmlText = xmlText.replace(cls.NO_BREAK_SPACE, ' ')
		xmlText = ' '.join(xmlText.split())
		return xmlText

	@classmethod
	def xmlText2XmlDoc(cls, xmlText):
		try:
			xmlDoc = etree.XML(xmlText)
		except:
			raise XmlTextFormatError('invalid xml text: {}'.format(xmlText))
		return xmlDoc

	@classmethod
	def xmlDoc2htmlDoc(cls, xmlDoc):
		htmlDoc = cls.XML2HTML(xmlDoc)
		return htmlDoc

	@classmethod
	def htmlDoc2HtmlText(cls, htmlDoc):
		return etree.tostring(htmlDoc, encoding=unicode)

	@classmethod
	def xmlDoc2ExtractText(cls, xmlDoc):
		def _getText(element):
			if element == None:
				return ''

			if element.tag.lower() == 'br':
				return '\n' + (element.tail or '')

			if element.tag.lower() == 'timestamp':
				try:
					tagId = int(element.attrib['tagid'])
					tag = cls.tags.setdefault(tagId, m.Tag.query.get(tagId))
					extractStart = re.sub(r'\s+', '_', (tag.extractStart or ''))
					extractEnd = re.sub(r'\s+', '_', (tag.extractEnd or ''))
				except Exception, e:
					raise
				return (' %s%.3f%s ' % (extractStart, float(element.attrib['value']), extractEnd)) + (element.tail or '')

			extractStart = ''
			extractEnd = ''

			# TODO: flag when tag is not found and/or not in configured set
			if element.attrib.has_key('tagid'):
				try:
					tagId = int(element.attrib['tagid'])
					tag = cls.tags.setdefault(tagId, m.Tag.query.get(tagId))
					extractStart = tag.extractStart or ''
					extractEnd = tag.extractEnd or ''
				except Exception, e:
					pass

			if element.attrib.has_key('tagtype') and\
					element.attrib['tagtype'] == 'Event':
				extractStart = ' ' + extractStart
				extractEnd = extractEnd + ' '

			buf = [element.text or '']
			for ch in element:
				if isinstance(ch, etree._Comment):
					continue
				if not isinstance(ch, etree._Element):
					continue
				if ch.tag.lower() in ('script', 'style'):
					continue
				buf.append(_getText(ch))
			return extractStart + ''.join(buf) + extractEnd + (element.tail or '')

		txt = _getText(xmlDoc.getroot())
		txt = txt.replace(u'\xa0', ' ')
		txt = ' '.join(txt.split())
		return txt

	@classmethod
	def extractText2XmlDoc(cls, extractText):
		raise NotImplementedError

	@classmethod
	def asExtract(cls, htmlText):
		htmlDoc = cls.htmlText2HtmlDoc(htmlText)
		xmlDoc = cls.htmlDoc2XmlDoc(htmlDoc)
		extractText = cls.xmlDoc2ExtractText(xmlDoc)
		return extractText
