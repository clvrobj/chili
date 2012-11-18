#-*- coding:utf-8 -*-

DROPBOX_APP_KEY = ''
DROPBOX_APP_SECRET = ''
DROPBOX_ACCOUNT_EMAIL = ''
APP_SECRET_KEY = '' # for flask session

DROPBOX_ACCESS_TYPE = 'app_folder'
DROPBOX_REQUEST_TOKEN_KEY = 'dropbox_request_token'
DROPBOX_REQUEST_TOKEN_SECRET_KEY = 'dropbox_request_token_secret'
DROPBOX_ACCESS_TOKEN_KEY = 'dropbox_access_token'

RAW_ENTRY_FILE_SUFFIX = ('.md', '.markdown')
NAV_ITEMS = () # items shown in nav menu. e.g. ('about', 'work')
RAWS_DIR = 'raw_entries'
REMOTE_IMAGE_DIR = '/image'
PUBLIC_DIR = 'public'
LOCAL_ENTRIES_DIR = PUBLIC_DIR + '/entries'
LOCAL_IMAGE_DIR = PUBLIC_DIR + '/image'
LOCAL_TAGS_DIR = PUBLIC_DIR + '/tags'
MAKO_DIR = 'templates'
ENTRY_LINK_PATTERN = '/post/%s'
TAG_LINK_PATTERN = '/tag/%s'
IMAGE_LINK_PATTERN = '/img/%s'
PAGE_LINK_PATTERN = '/page/%s'

TIMEZONE = 'Asia/Shanghai'

PAGE_POSTS_COUNT = 5

DOMAIN = ''
DOMAIN2 = ''
DOMAIN_URL = 'http://' + DOMAIN
DOMAIN_URL2 = 'http://' + DOMAIN2

BLOG_NAME = '博客'
TWITTER_NAME = ''
DISQUS_SHORTNAME = ''
TRACKING_CODE = ''''''

LOCAL_DEV = False

try:
    from config import *
except ImportError:
    pass
