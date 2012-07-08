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
RAWS_DIR = 'raw_entries'
ENTRIES_DIR = 'public/entries'
MAKO_DIR = 'templates'
ENTRY_LINK_PATTERN = '/entry/%s'
