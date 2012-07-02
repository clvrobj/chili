#-*- coding:utf-8 -*-
import os
from os.path import isfile, join
import urllib
from markdown import markdown
from flask import Flask, redirect, url_for, send_from_directory
from flaskext.mako import init_mako, render_template

APP_KEY = ''
APP_SECRET = ''
ACCESS_TYPE = ''

try:
    from local_config import *
except ImportError:
    pass


RAWS_DIR = 'raw_entries'
ENTRIES_DIR = 'public/entries'
MAKO_DIR = 'templates'
ENTRY_LINK_PATTERN = '/entry/%s'

app = Flask(__name__)


def auth_dropbox():
    # Include the Dropbox SDK libraries
    from dropbox import client, rest, session

    sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
    request_token = sess.obtain_request_token()
    url = sess.build_authorize_url(request_token)
    # Make the user sign in and authorize this token
    print "url:", url
    print "Please visit this website and press the 'Allow' button, then hit 'Enter' here."
    raw_input()

    # This will fail if the user didn't visit the above URL and hit 'Allow'
    access_token = sess.obtain_access_token(request_token)
    
    client = client.DropboxClient(sess)
    print "linked account:", client.account_info()
    return client

def sync_folder(client):
    """
    download all files in the app folder into raws folder
    """
    folder_meta = client.metadata('/')
    for f in folder_meta['contents']:
        p = f['path']
        print 'Downloading %s' % p
        f, meta = client.get_file_and_metadata(p)
        name = p.rsplit('.', 1)[0].lstrip('/')
        raw = open(join(RAWS_DIR, name), 'w')
        raw.write(f.read())
    print 'Sync folder done.'

def gen_entry(file_name):
    raw = open(join(RAWS_DIR, file_name), 'r')
    title = file_name.rstrip('.md')
    path = urllib.quote_plus(title) + '.html'
    gen = open(join(ENTRIES_DIR, path), 'wb')
    content = markdown(raw.read())
    html_content = render_template('entry.html', c={'file_content':content})
    gen.write(html_content)
    gen.close()
    raw.close()
    return dict(title=title, path=path, content=content)

def gen_home(files):
    entries = []
    for f in files:
        entries.append(dict(link=ENTRY_LINK_PATTERN % f['path'], title=f['title'], content=f['content']))
    gen = open(join(ENTRIES_DIR, 'home.html'), 'wb')
    gen.write(render_template('home.html', c={'entries':entries}))
    gen.close()

@app.route('/sync')
def sync_all():
    client = auth_dropbox()
    if client:
        sync_folder(client)
        print 'Sync folder OK.'
        print 'Gen html now...'
        try:
            files = []
            for f in os.listdir(RAWS_DIR):
                if isfile(join(RAWS_DIR, f)):
                    files.append(gen_entry(f))
                    print 'Gen %s OK.' % f
            # gen home
            gen_home(files)
            print 'Gen home page OK.'
            return 'Done!'
        except OSError:
            return 'Woops! File operations error ...'
    else:
        print 'Can not auth to dropbox'

@app.route('/')
def home():
    return send_from_directory(ENTRIES_DIR, 'home.html')

@app.route(ENTRY_LINK_PATTERN % '<path:filename>')
def entry(filename):
    return send_from_directory(ENTRIES_DIR, filename)


if __name__ == '__main__':
    app.config['MAKO_DIR'] = MAKO_DIR
    init_mako(app)
    app.debug = True
    app.run()
