#-*- coding:utf-8 -*-

DROPBOX_APP_KEY = ''
DROPBOX_APP_SECRET = ''
DROPBOX_ACCESS_TYPE = ''
APP_SECRET_KEY = '' # for use flask session

try:
    from local_config import *
except ImportError:
    pass

DROPBOX_REQUEST_TOKEN_KEY = 'dropbox_request_token'
DROPBOX_REQUEST_TOKEN_SECRET_KEY = 'dropbox_request_token_secret'
DROPBOX_ACCESS_TOKEN_KEY = 'dropbox_access_token'

RAW_ENTRY_FILE_FORMAT = 'md'
RAWS_DIR = 'raw_entries'
REMOTE_IMAGE_DIR = '/image'
LOCAL_ENTRIES_DIR = 'public/entries'
LOCAL_IMAGE_DIR = 'public/image'
MAKO_DIR = 'templates'
ENTRY_LINK_PATTERN = '/entry/%s'
IMAGE_LINK_PATTERN = '/img/%s'

TIMEZONE = 'Asia/Shanghai'
