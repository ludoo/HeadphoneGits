#!/usr/bin/env python
'Download locally and replace GitHub CDN images in Markdown files.'

import collections
import glob
import logging
import os
import re
import requests
import sys

IMG_URL = 'https://headphonegits.org'
IMGDIR_PATH = 'assets'
R = re.compile(r'(?sm)https://github.com/ludoo/HeadphoneGits/assets/[^\s\)"]+')

Document = collections.namedtuple('Document', 'path image_basepath text')
Image = collections.namedtuple('Image', 'url path')


class Error(Exception):
  pass


def _get_image_from_fs(abspath):
  'Return first fylesystem glob match for path.'
  results = glob.glob(f'{abspath}*')
  if results:
    return results[0]


def _get_image_from_cdn(abspath, url):
  'Fetch image from GitHub CDN and store it locally returning its path.'
  response = requests.get(url, stream=True)
  if not response.ok:
    raise Error(f'{response.code} {response.reason} for url {url}')
  content_type = response.headers['Content-Type']
  if not content_type.startswith('image/'):
    raise Error(f'Incorrect content type {content_type} for URL {url}')
  abspath = '.'.join([abspath, content_type.split('/')[1]])
  try:
    open(abspath, 'wb').write(response.raw.read())
  except (IOError, OSError) as e:
    logging.critical(abspath)
    raise Error(f'Cannot write image to filesystem. {e.args[0]}')
  return abspath


def get_docs(root_path):
  'Get list of markdown documents in the root tree.'
  for dirpath, _, filenames in os.walk(root_path):
    for filename in filenames:
      if not filename.endswith('.md') or filename.endswith('.html'):
        continue
      abspath = os.path.join(dirpath, filename)
      relpath = os.path.relpath(abspath, root_path)
      image_basepath = os.path.join(IMGDIR_PATH, os.path.splitext(relpath)[0])
      yield Document(relpath, image_basepath, open(abspath).read())


def get_image(url, basepath, rootpath):
  'Get image from filesystem or download and store.'
  name = url.split('/')[-1]
  abspath = os.path.join(rootpath, basepath, name)
  result = _get_image_from_fs(abspath)
  if not result:
    logging.info(f'--- fetching {url}')
    result = _get_image_from_cdn(abspath, url)
  return Image(url, os.path.relpath(result, rootpath))


def main(root_path):
  'Program entry point.'
  logging.basicConfig(level=logging.INFO)
  logging.info(f'starting in {os.getcwd()}')
  for doc in get_docs(root_path):
    logging.info(f'doc {doc.path}')
    text = doc.text
    for m in R.finditer(doc.text):
      url = m.group(0)
      logging.info(f'--- url {url}')
      try:
        image = get_image(url, doc.image_basepath, root_path)
      except Error as e:
        logging.critical(e.args[0])
        continue
      text = text.replace(image.url, f'{IMG_URL}/{image.path}')
    open(os.path.join(root_path, doc.path), 'w').write(text)


if __name__ == '__main__':
  main(sys.argv[1])
