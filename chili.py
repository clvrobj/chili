#-*- coding:utf-8 -*-
from werkzeug.exceptions import Forbidden
from flask import Flask, request, redirect, url_for, send_from_directory, abort, session as flask_session
from flask.ext.mako import MakoTemplates, render_template
from dropbox.rest import ErrorResponse
from utils import Dropbox, DropboxSync
from global_config import LOCAL_DEV, APP_SECRET_KEY, MAKO_DIR, DROPBOX_REQUEST_TOKEN_KEY,\
    ENTRY_LINK_PATTERN, IMAGE_LINK_PATTERN, TAG_LINK_PATTERN,\
    PUBLIC_DIR, LOCAL_ENTRIES_DIR, LOCAL_IMAGE_DIR, LOCAL_TAGS_DIR, DOMAIN, DOMAIN2,\
    PAGE_LINK_PATTERN

app = Flask(__name__)
app.config['MAKO_DIR'] = MAKO_DIR
mako = MakoTemplates(app)
app.secret_key = APP_SECRET_KEY
app.debug = True
dropbox = Dropbox()


@app.route('/sync')
def sync():
    if not dropbox.is_authenticated:
        return redirect('/login')

    client = dropbox.client
    if client:
        sync = DropboxSync(client)
        sync.sync_folder()
        return sync.gen_pages() + ' <a href="/">Back to home</a>'
    else:
        print 'Can not auth to dropbox'

@app.route('/regen')
def regen_pages():
    if not dropbox.is_authenticated:
        return redirect('/login')

    client = dropbox.client
    if client:
        DropboxSync(client).gen_pages()
        return redirect('/')
    else:
        print 'Can not auth to dropbox'

@app.route('/tools')
def tools():
    return render_template('tools.html', **locals())

@app.route('/')
def home():
    return send_from_directory(PUBLIC_DIR, 'home-1.html')

@app.route(PAGE_LINK_PATTERN % '<path:page_id>')
def page(page_id):
    return send_from_directory(PUBLIC_DIR, 'home-%s.html' % page_id)

@app.route(ENTRY_LINK_PATTERN % '<path:filename>')
def post(filename):
    return send_from_directory(LOCAL_ENTRIES_DIR, filename)

@app.route(TAG_LINK_PATTERN % '<path:filename>')
def tag(filename):
    return send_from_directory(LOCAL_TAGS_DIR, filename)

@app.route(IMAGE_LINK_PATTERN % '<path:filename>')
def image(filename):
    if not LOCAL_DEV:
        r = request.referrer.split('/')[2]
        if r != DOMAIN and r != DOMAIN2:
            abort(403)
    return send_from_directory(LOCAL_IMAGE_DIR, filename)

@app.route('/<path:filename>')
def public(filename):
    return send_from_directory('public', filename)

@app.route('/login')
def login():
    url = dropbox.login_url
    return 'Click <a href="%s">here</a> to login with Dropbox.' % url

@app.route('/logout')
def logout():
    dropbox.logout()
    return redirect('/')

@app.route('/login_success')
def login_success():
    oauth_token = request.args.get('oauth_token')
    uid = request.args.get('uid')
    if not oauth_token:
        return 'oauth token error'

    # oAuth token **should** be equal to stored request token
    request_token = flask_session.get(DROPBOX_REQUEST_TOKEN_KEY)

    if not request_token or oauth_token != request_token['key']:
        return 'token not equal'

    try:
        dropbox.login(request_token)
    except (ErrorResponse, Forbidden):
        return 'Login error!'
    return redirect('/')

@app.route('/logout')
def logout():
    dropbox.logout()
    return redirect('/')

@app.errorhandler(404)
def page_not_found(error):
    from config import DOMAIN, BLOG_NAME, TWITTER_NAME
    return render_template('page_not_found.html', **locals()), 404


if __name__ == '__main__':
    app.run(port=7777)
