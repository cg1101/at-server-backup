
import os

import boto3

s3 = boto3.resource('s3')
bucket_name = os.environ.get('BUCKET_NAME', '')
use_s3 = bool(bucket_name)

class LogisticsManager(object):
	DOCUMENT_ROOT = '/tmp'
	def __init__(self, access_key_id, secret_access_key):
		self.access_key_id = access_key_id
		self.secret_access_key = secret_access_key
		self.client = boto3.client(service_name='ses',
			region_name='us-west-2',
			aws_access_key_id=access_key_id,
			aws_secret_access_key=secret_access_key)
		self.me = 'do-not-reply@appen.com'
	def send_email(self, to, subject, data, html=True):
		message = {
			'Subject': {'Data': subject},
			'Body': {'Html' if html else 'Text': {'Data': data}}
		}
		if isinstance(to, basestring):
			receipients = [to]
		elif not isinstance(to, list):
			receipients = list(to)
		else:
			receipients = to
		destination = {
			'ToAddresses': receipients,
			'CcAddresses': [],
			'BccAddresses': [],
		}
		result = self.client.send_email(
			Source=self.me,
			Destination=destination,
			Message=message,
		)
		return result if 'ErrorResponse' in result else ''
	def save_file(self, relpath, data):
		if use_s3:
			key = relpath
			s3.Object(bucket_name, key).put(Body=data)
		else:
			filepath = os.path.join(self.DOCUMENT_ROOT, relpath)
			file_dir = os.path.dirname(filepath)
			# print file_dir, 'path', filepath
			if not os.path.exists(file_dir):
				os.makedirs(file_dir)
			with open(filepath, 'w') as f:
				f.write(data)
	def list_guidelines(self, taskId):
		bucket = s3.Bucket(bucket_name)
		files = []
		key_prefix = 'tasks/{0}/guidelines/'.format(taskId)
		for obj in bucket.objects.all():
			if not obj.key.startswith(key_prefix):
				continue
			path = obj.key[len(key_prefix):]
			if path and path == os.path.basename(path):
				files.append({'name': path, 'updatedAt': obj.last_modified})
		return files


logistics = LogisticsManager(os.environ['AWS_ACCESS_KEY_ID'], os.environ['AWS_SECRET_ACCESS_KEY'])
