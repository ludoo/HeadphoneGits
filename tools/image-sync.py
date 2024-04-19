#!/usr/bin/env python

import collections
import logging
import os
import re
import requests
import sys

IMGDIR_PATH = 'assets'
R = re.compile(r'(?sm)https://github.com/ludoo/HeadphoneGits/assets/[^\s\)"]+')

Document = collections.namedtuple('Document',
                                  'abspath relpath imgdir_path text')
Image = collections.namedtuple('Image', 'name data')


class Error(Exception):
  pass


def get_docs(root_path):
  for dirpath, _, filenames in os.walk(root_path):
    for filename in filenames:
      if not filename.endswith('.md') or filename.endswith('.html'):
        continue
      abspath = os.path.join(dirpath, filename)
      relpath = os.path.relpath(abspath, root_path)
      imgdir_path = os.path.join(IMGDIR_PATH, os.path.splitext(relpath)[0])
      yield Document(abspath, relpath, imgdir_path, open(abspath).read())


def get_image(url):
  response = requests.get(url, stream=True)
  if not response.ok:
    raise Error(f'{response.code} {response.reason} for url {url}')
  content_type = response.headers['Content-Type']
  if not content_type.startswith('image/'):
    raise Error(f'content type {content_type} for url {url}')
  name = '.'.join([url.split('/')[-1], content_type.split('/')[1]])
  return Image(name, response.raw.read())


def store_image(path, data):
  if os.path.isfile(path):
    return
  open(path, 'wb').write(data)
  return True


def main(root_path):
  logging.basicConfig(level=logging.INFO)
  for doc in get_docs(root_path):
    logging.info(f'doc {doc.relpath}')
    for m in reversed(list(R.finditer(doc.text))):
      span, url = m.span(), m.group(0)
      logging.info(f'--- found {url}')
      try:
        image = get_image(url)
        logging.info(f'--- downloaded {image.name}')
        result = store_image(
            os.path.join(root_path, doc.imgdir_path, image.name), image.data)
        logging.info(f'--- {"existing" if not result else "written"}')
      except Error as e:
        logging.critical(e.args[0])
        continue


if __name__ == '__main__':
  main(sys.argv[1])
