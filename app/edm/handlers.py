
import json
import urllib
import base64
import cStringIO
import traceback
from collections import OrderedDict

from flask import request, current_app, make_response
from sqlalchemy import func
from M2Crypto import X509

import db.model as m
from db.db import SS
from app.i18n import get_text as _
from . import edm as bp


class MessageError(Exception):
	pass


class SnsMessage(object):
	_KEYS = {
		'': [
			'Message',
			'MessageId',
			'Signature',
			'SignatureVersion',
			'SigningCertURL',
			'Timestamp',
			'TopicArn',
			'Type',
		],
		'SubscriptionConfirmation': [
			#'Message',
			#'MessageId',
			#'Signature',
			#'SignatureVersion',
			#'SigningCertURL',
			'SubscribeURL',
			#'Timestamp',
			'Token',
			#'TopicArn',
			#'Type',
		],
		'Notification': [
			#'Message',
			#'MessageId',
			#'Signature',
			#'SignatureVersion',
			#'SigningCertURL',
			'Subject',
			#'Timestamp',
			#'TopicArn',
			#'Type',
			'UnsubscribeURL',
		],
		'UnsubscribeConfirmation': [
			#'Message',
			#'MessageId',
			#'Signature',
			#'SignatureVersion',
			#'SigningCertURL',
			'SubscribeURL',
			#'Timestamp',
			'Token',
			#'TopicArn',
			#'Type',
		],
	}
	_HANDLERS = OrderedDict()

	@classmethod
	def message_handler(cls, *args, **kwargs):
		try:
			if len(args):
				if len(args) != 1 or not isinstance(args[0], dict):
					raise ValueError
				data = args[0]
			else:
				data = kwargs
		except:
			raise ValueError('predicates must either use dict or keyword arguments')
		predicates = tuple((k, v) for k, v in sorted(data.iteritems()))
		if not len(predicates):
			raise ValueError('predicates must not be empty')
		if predicates in cls._HANDLERS:
			raise RuntimeError('predicates already registered: {}'.format(predicates))
		def registration_decorator(fn):
			cls._HANDLERS[predicates] = fn
			return fn
		return registration_decorator

	@classmethod
	def load(cls, body):
		try:
			data = json.loads(body)
		except (ValueError, TypeError):
			raise MessageError(_('message not well-formed: {}').format(body))
		msg = super(SnsMessage, cls).__new__(cls)
		msg.body = body
		msg._data = data
		return msg

	@classmethod
	def processMessage(cls, request, topics=[]):
		try:
			messageType = request.headers['x-amz-sns-message-type']
			messageId = request.headers['x-amz-sns-message-id']
			topic = request.headers['x-amz-sns-topic-arn']
		except Exception, e:
			raise MessageError(_('message header corrupted: {}').format(e))

		if topic not in topics:
			current_app.logger.debug('skipped unknown topic {}'.format(topic))
			return make_response()

		if cls.get_record(messageId):
			return make_response()

		msg = SnsMessage.load(request.get_data())
		msg.validate()
		if current_app.config['SNS_AUTHENTICATE_REQUEST']:
			msg.authenticate()
		else:
			current_app.logger.info('skipping SNS request authentication')

		handler = None
		for predicates, func in cls._HANDLERS.iteritems():
			if msg.test(predicates):
				handler = func
				break
		if not handler:
			return make_response()
		try:
			resp = handler(msg) or make_response()
		except:
			raise
		else:
			msg.save_record()
			return resp

	@staticmethod
	def get_record(messageId):
		return m.SnsMessageRecord.query.get(messageId)

	def __init__(self):
		raise RuntimeError('must use SnsMessage.load() to instantiate')
	def __getattr__(self, key):
		if key in self._data:
			return self._data[key]
		raise AttributeError(key)
	def validate(self):
		# check if all mandatory keys are present
		for key in self._KEYS['']:
			if key not in self._data:
				raise MessageError(_('invalid message: key missing: {}'
						.format(key)))
		for key in self._KEYS[self.Type]:
			if key not in self._data:
				raise MessageError(_('invalid message: key missing: {}'
						.format(key)))
		return True
	def get_canonical_message(self):
		if self.Type == 'Notification':
			keys = 'Message MessageId Subject Timestamp TopicArn Type'.split()
		else:
			keys = 'Message MessageId SubscribeURL Timestamp Token TopicArn Type'.split()
		buf = []
		for k in sorted(keys):
			buf.append(k)
			buf.append(self._data[k])
		return '\n'.join(buf)
	def get_decoded_signature(self):
		return base64.b64decode(self.Signature)
	def authenticate(self):
		cert = X509.load_cert_string(str(urllib.urlopen(
			self.SigningCertURL).read()))
		pubkey = cert.get_pubkey()
		pubkey.reset_context(md='sha1')
		pubkey.verify_init()
		pubkey.verify_update(self.get_canonical_message())
		result = pubkey.verify_final(self.get_decoded_signature())
		if result != 1:
			raise MessageError(_('message authentication failed: {}'
				).format(self.MessageId))
		return True
	def save_record(self):
		if m.SnsMessageRecord.query.get(self.MessageId):
			raise RuntimeError(_('message {} has been saved already'
				).format(self.MessageId))
		record = m.SnsMessageRecord(messageId=self.MessageId,
			messageType=self.Type, body=self.body)
		SS.add(record)
		SS.flush()
		current_app.logger.debug('record of message {} has been saved'.format(self.MessageId))
	def test(self, predicates):
		for k, v in predicates:
			if k not in self._data:
				return False
			if callable(v):
				if not v(self._data[k]):
					return False
			elif self._data[k] != v:
				return False
		return True


@bp.route('/process', methods=['POST'])
def edm_callback():
	try:
		return SnsMessage.processMessage(request,
			topics=current_app.config['EDM_TOPICS'])
	except MessageError, e:
		return make_response('%s' % e, 400)
	except Exception, e:
		out = cStringIO.StringIO()
		traceback.print_exc(file=out)
		current_app.logger.error(
			'\033[1;31mERROR caught inside api:\033[0m\n%s\n' %
			out.getvalue())
		# TODO: hide debug information for production deployment
		return make_response(_('internal server error: {}'
			).format(e), 500)


@SnsMessage.message_handler(Type='SubscriptionConfirmation')
def confirm_subscription(self):
	resp = urllib.urlopen(self.SubscribeURL)
	return make_response(resp.read(), resp.getcode(),
			dict(resp.info().items()))


ATTR_MAP = {
	'Person': {
		'primary_email_address': 'emailAddress',
		'family_name': 'familyName',
		'given_name': 'givenName',
		# 'mobile_phone_phone_number': None,
		# 'street_address_address1': None,
		# 'street_address_country': None,
		# 'nationality_country_id': None,
		# 'salutation': None,
		# 'street_address_city': None,
	},
	'Country': {
		'name_eng': 'name',
		'iso2': None,
		'iso3': None,
	}
}

def decode_changes(json_encoded, attr_map):
	desc = json.loads(json_encoded)
	lookup = attr_map
	data = {}
	for i in desc['changes']:
		key = lookup.get(i['attribute_name'])
		if not key:
			continue
		data[key] = i['after_value']
	return data

@SnsMessage.message_handler(Type='Notification', Subject='Person_Create')
def create_person(self):
	data = decode_changes(self.Message, ATTR_MAP['Person'])
	user = m.User(**data)
	newId = SS.query(func.max(m.User.userId)).one()[0] + 1
	user.userId = newId
	SS.add(user)
	SS.flush()
	current_app.logger.info('user {0} was created using {1}'.format(user.userId, data))
	return

@SnsMessage.message_handler(Type='Notification', Subject='Person_Update')
def update_person(self):
	data = decode_changes(self.Message, ATTR_MAP['Person'])
	current_app.logger.info('a person is being updated using {}'.format(data))
	return

@SnsMessage.message_handler(Type='Notification', Subject='Country_Create')
def create_country(self):
	data = decode_changes(self.Message, ATTR_MAP['Country'])
	current_app.logger.info('a country is being created using {}'.format(data))
	return

@SnsMessage.message_handler(Type='Notification', Subject='Country_Update')
def update_country(self):
	data = decode_changes(self.Message, ATTR_MAP['Country'])
	current_app.logger.info('a country is being updated using {}'.format(data))
	return
