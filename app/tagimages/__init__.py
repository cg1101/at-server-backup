
import os
import cStringIO
import base64

from flask import Blueprint, request, make_response, jsonify
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageOps
import psycopg2

import db.model as m
from db.db import SS


bp = tagimages = Blueprint('tagimages', __name__, template_folder='../templates')


def generate_tag_image(text):
	_dir = os.path.dirname(__file__)
	canvas_file = os.path.join(_dir, 'event.png')
	font_file = os.path.join(_dir, 'Code2000b2.ttf')

	img = Image.open(canvas_file)
	w, h = img.size
	draw = ImageDraw.Draw(img)
	font_size = 16
	while font_size >= 13:
		font = ImageFont.truetype(font_file, font_size)
		tw, th = draw.textsize(text, font=font)
		if tw + 6 <= w:
			break
		font_size -= 1
	if font_size < 13:
		raise ValueError('The text is too long to fit in tag image.')

	x = int(float(w - tw) / 2)
	y = int(float(h - th) / 2)
	draw.text((x, y), text, fill=(68, 68, 68), font=font)

	f = cStringIO.StringIO()
	img.save(f, format='png')
	f.seek(0)
	data = f.read()
	return data


@bp.route('/', methods=['POST'])
def create_tag_image_preview():
	try:
		text = request.get_json(force=True)['text']
		text = text.strip()
		if not text:
			raise ValueError('tag label text must not be blank')
		image = generate_tag_image(text)
	except ValueError, e:
		return make_response(jsonify(error='{}'.format(e)), 400)
	except Exception, e:
		return make_response(jsonify(error='{}'.format(e)), 500)

	preview = m.TagImage(image=image)
	# preview = m.TagImage(image=psycopg2.Binary(image))
	SS.add(preview)
	SS.flush()

	url = 'image/png;base64,' + base64.b64encode(image)
	return make_response(jsonify(
		previewId=preview.previewId,
		imageUrl=url,
	))


@bp.route('/<int:tagId>.png')
def get_tag_image(tagId):
	tag = m.Tag.query.get(tagId)
	if (not tag and tag.tagType == m.Tag.EVENT):
		return make_response(('tag image not found', 404,
			{'Content-Type': 'text/plain'}))
	return make_response((tag.image, 200,
			{'Content-Type': 'image/png'}))

