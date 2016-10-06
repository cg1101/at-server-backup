
import json
import urllib
import base64
import cStringIO
import traceback
from collections import OrderedDict

import sqlalchemy.orm.exc
from flask import request, current_app, make_response
from M2Crypto import X509

import db.model as m
from db.db import SS
from app.i18n import get_text as _
import app.util as util
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
			raise MessageError(_('message not well-formed: \'{}\'').format(body))
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
	current_app.logger.debug('received incoming message {}'.format(request.data));
	try:
		return SnsMessage.processMessage(request,\
			topics=current_app.config['EDM_TOPICS'])
	except MessageError, e:
		return make_response('%s' % e, 400)
	except Exception, e:
		out = cStringIO.StringIO()
		traceback.print_exc(file=out)
		current_app.logger.error(
			'ERROR caught inside api:\n%s\n' %
			out.getvalue())
		# TODO: hide debug information for production deployment
		return make_response(_('internal server error: {}'
			).format(e), 500)


@SnsMessage.message_handler(Type='SubscriptionConfirmation')
def confirm_subscription(self):
	current_app.logger.debug('confirming subscription from %s' % self.SubscribeURL)
	resp = urllib.urlopen(self.SubscribeURL)
	return make_response(resp.read(), 200, #resp.getcode(),
			dict(resp.info().items()))


@SnsMessage.message_handler(Type='Notification', Subject='Person_Create')
def create_person(self):
	desc = json.loads(self.Message)
	globalId = desc['global_id']
	data = util.edm.decode_changes('Person', desc['changes'])
	try:
		user = m.User.query.filter_by(emailAddress=data['emailAddress']).one()
		for k, v in data.items():
			if k == 'emailAddress':
				continue
			setattr(user, k, v)
		user.globalId = globalId
		SS.flush()
		current_app.logger.info('user {0} was updated using {1}'.format(user.userId, data))
	except sqlalchemy.orm.exc.NoResultFound:
		SS.rollback()
		user = m.User(**data)
		user.globalId = globalId
		SS.add(user)
		SS.flush()
		SS.commit()
		current_app.logger.info('user {0} was created using {1}'.format(user.userId, data))
	return

@SnsMessage.message_handler(Type='Notification', Subject='Person_Update')
def update_person(self):
	desc = json.loads(self.Message)
	globalId = desc['global_id']
	try:
		user = m.User.query.filter(m.User.globalId==globalId).one()
		data = util.edm.decode_changes('Person', desc['changes'])
		current_app.logger.info('found user {}, applying changes {}'.format(globalId, data))
		changes = {}
		for k, v in data.items():
			try:
				if getattr(user, k) != v:
					setattr(user, k, v)
					changes[k] = v
			except AttributeError:
				continue
		current_app.logger.debug('actual changes {}'.format(changes))
		SS.flush()
		SS.commit()
	except sqlalchemy.orm.exc.NoResultFound:
		SS.rollback()
		current_app.logger.info('user {} not found, get user from edm'.format(globalId))
		user = edm.make_new_user(globalId)
		SS.add(user)
		SS.flush()
		SS.commit()
		current_app.logger.info('user {} is added locally'.format(globalId))
	return

@SnsMessage.message_handler(Type='Notification', Subject='Country_Create')
def create_country(self):
	desc = json.loads(self.Message)
	data = util.edm.decode_changes('Country', desc['changes'])
	current_app.logger.info('a country is being created using {}'.format(data))
	try:
		country = m.Country.query.filter(m.Country.name==data['name']).one()
		current_app.logger.info('found country {}, applying changes {}'.format(country.name, data))
		changes = {}
		for k, v in data.iteritems():
			try:
				if getattr(country, k) != v:
					setattr(country, k, v)
					changes[k] = v
			except AttributeError:
				continue
		current_app.logger.debug('actual changes {}'.format(changes))
		SS.flush()
		SS.commit()
	except sqlalchemy.orm.exc.NoResultFound:
		SS.rollback()
		country = m.Country(**data)
		SS.add(country)
		SS.flush()
		SS.commit()
	return

@SnsMessage.message_handler(Type='Notification', Subject='Country_Update')
def update_country(self):
	desc = json.loads(self.Message)
	iso3 = desc['iso3']
	try:
		country = m.Country.query.filter(m.Country.iso3==iso3).one()
		data = util.edm.decode_changes('Country', desc['changes'])
		current_app.logger.info('found country {}, applying changes {}'.format(country.name, data))
		changes = {}
		for k, v in data.items():
			try:
				if getattr(country, k) != v:
					setattr(country, k, v)
					changes[k] = v
			except AttributeError:
				continue
		current_app.logger.debug('actual changes {}'.format(changes))
		SS.flush()
		SS.commit()
	except sqlalchemy.orm.exc.NoResultFound:
		SS.rollback()
		current_app.logger.info('country {} not found, get country from edm'.format(iso3))
		result = util.edm.get_country(iso3)
		data = dict(
			name=result['name_eng'],
			iso2=result['iso2'],
			iso3=iso3,
			isoNum=result['iso_num'],
			internet=result['internet'],
			active=result['active'],
		)
		country = m.Country(**data)
		SS.add(country)
		SS.flush()
		SS.commit()
		current_app.logger.info('country {} is added locally'.format(country.name))
	return

@SnsMessage.message_handler(Type='Notification', Subject='Language_Create')
def create_language(self):
	desc = json.loads(self.Message)
	data = util.edm.decode_changes('Language', desc['changes'])
	current_app.logger.info('a language is being created using {}'.format(data))
	try:
		lang = m.Language.query.filter(m.Language.name==data['name']).one()
		current_app.logger.info('found language {}, applying changes {}'.format(lang.name, data))
		changes = {}
		for k, v in data.iteritems():
			try:
				if getattr(lang, k) != v:
					setattr(lang, k, v)
					changes[k] = v
			except AttributeError:
				continue
		current_app.logger.debug('actual changes {}'.format(changes))
		SS.flush()
		SS.commit()
	except sqlalchemy.orm.exc.NoResultFound:
		SS.rollback()
		lang = m.Language(**data)
		SS.add(lang)
		SS.flush()
		SS.commit()

@SnsMessage.message_handler(Type='Notification', Subject='Language_Update')
def update_language(self):
	desc = json.loads(self.Message)
	iso3 = desc['iso3']
	try:
		lang = m.Language.query.filter(m.Language.iso3==iso3).one()
		data = util.edm.decode_changes('Language', desc['changes'])
		current_app.logger.info('found language {}, applying changes {}'.format(lang.name, data))
		changes = {}
		for k, v in data.items():
			try:
				if getattr(lang, k) != v:
					setattr(lang, k, v)
					changes[k] = v
			except AttributeError:
				continue
		current_app.logger.debug('actual changes {}'.format(changes))
		SS.flush()
		SS.commit()
	except sqlalchemy.orm.exc.NoResultFound:
		SS.rollback()
		current_app.logger.info('language {} not found, get language from edm'.format(iso3))
		result = util.edm.get_language(iso3)
		data = dict(
			name=result['name_eng'],
			iso2=result['iso2'],
			iso3=iso3,
			active=result['active'],
		)
		lang = m.Language(**data)
		SS.add(lang)
		SS.flush()
		SS.commit()
		current_app.logger.info('language {} is added locally'.format(lang.name))
	return
