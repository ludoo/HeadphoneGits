#!/usr/bin/env python

import collections
import glob
import logging
import os
import re
import requests
import sys

R = re.compile(r'https://github.com/ludoo/HeadphoneGits/assets/[^\s\)"]+')

Image = collections.namedtuple('Image', 'source dest_base dest_name')
ImageData = collections.namedtuple('ImageData', 'ext data')


class Error(Exception):
  pass


def fetch(url):
  response = requests.get(url, stream=True)
  if not response.ok:
    logging.critical(f'{response.code} {response.reason} for url {url}')
  content_type = response.headers['Content-Type']
  if not content_type.startswith('image/'):
    logging.critical(f'content type {content_type} for url {url}')
    return
  return ImageData(content_type.split('/')[1], response.raw.read())


def get_images(path):
  for dirpath, _, filenames in os.walk(path):
    for filename in filenames:
      if not filename.endswith('.md') or filename.endswith('.html'):
        continue
      filepath = os.path.join(dirpath, filename)
      logging.info(f'parsing {filepath}')
      image_base = os.path.join('assets', path, os.path.splitext(filename)[0])
      with open(filepath) as f:
        text = f.read()
        for m in R.findall(text):
          yield Image(m, image_base, m.split('/')[-1])


def main(path):
  logging.basicConfig(level=logging.INFO)
  _done = set()
  for image in get_images(path):
    if image.source in _done:
      continue
    image_path = os.path.join(image.dest_base, image.dest_name)
    image_files = glob.glob(f'{image_path}*')
    if image_files:
      logging.info(f'[-] image {image_files[0]} in {image.dest_base}')
      _done.add(image.source)
      continue
    logging.info(f'[+] image {image.source} to {image.dest_base}')
    try:
      image_data = fetch(image.source)
    except Error as e:
      logging.critical(e.args[0])
    else:
      if not os.path.isdir(image.dest_base):
        os.makedirs(image.dest_base)
      with open(f'{image_path}.{image_data.ext}', 'wb') as dest:
        dest.write(image_data.data)
      logging.info(f'[+] downloaded to {image_path}.{image_data.ext}')
      pass
    _done.add(image.source)


if __name__ == '__main__':
  main(sys.argv[1])
