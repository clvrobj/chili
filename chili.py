#-*- coding:utf-8 -*-
import os
from os.path import isfile, join
from markdown import markdown
from flask import Flask, redirect, url_for
from flaskext.mako import init_mako, render_template

APP_KEY = 'bmkh1yhg71eu9dt'
APP_SECRET = 'ao1ejlaaymwyopa'
ACCESS_TYPE = 'app_folder'

RAWS_DIR = 'raw_entries'
ENTRIES_DIR = 'public/entries'
MAKO_DIR = 'templates'

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
        raw.write(f)
    print 'Sync folder done.'

def gen_html(file_name):
    raw = open(join(RAWS_DIR, file_name), 'r')
    gen = open(join(ENTRIES_DIR, '%s.html' % file_name.rstrip('.md')), 'wb')
    gen.write(markdown(raw.read()))

def sync_all():
    client = auth_dropbox()
    if client:
        sync_folder(client)
        print 'Sync folder OK.'
        print 'Gen html now...'
        try:
            for f in os.listdir(RAWS_DIR):
                if isfile(join(RAWS_DIR, f)):
                    gen_html(f)
            return 'Done!'
        except OSError:
            return 'Woops! File operations error ...'
    else:
        print 'Can not auth to dropbox'

@app.route('/')
def show_entries():
    return render_template('home.html', c=locals())

@app.route('/<path:name>')
def show_entry(name=None):
    try:
        with open(join(ENTRIES_DIR, '%s.html' % name)) as f:
            file_content = f.read()
            return render_template('entry.html', c=locals())
    except IOError as e:
        return 'No such entry.'
    return 'name: %s' % name.rstrip('/')


if __name__ == '__main__':
    app.config['MAKO_DIR'] = MAKO_DIR
    init_mako(app)
    app.debug = True
    app.run()
