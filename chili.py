#-*- coding:utf-8 -*-
from __future__ import print_function

from dropbox.client import DropboxOAuth2Flow
from flask import session as flask_session
from flask import (Flask, abort, flash, redirect, request, send_from_directory,
                   url_for)
from flask.ext.mako import MakoTemplates, render_template
from werkzeug.exceptions import Forbidden

from global_config import (APP_SECRET_KEY, DOMAIN, DOMAIN2,
                           DROPBOX_REQUEST_TOKEN_KEY, ENTRY_LINK_PATTERN,
                           IMAGE_LINK_PATTERN, LOCAL_DEV, LOCAL_ENTRIES_DIR,
                           LOCAL_IMAGE_DIR, LOCAL_TAGS_DIR, MAKO_DIR,
                           PAGE_LINK_PATTERN, PUBLIC_DIR, TAG_LINK_PATTERN)
from utils import Dropbox, DropboxSync

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
        print('Can not auth to dropbox')

@app.route('/regen')
def regen_pages():
    if not dropbox.is_authenticated:
        return redirect('/login')

    client = dropbox.client
    if client:
        DropboxSync(client).gen_pages()
        return redirect('/')
    else:
        print('Can not auth to dropbox')

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

@app.route('/dropbox-auth-finish')
def dropbox_auth_finish():
    try:
        access_token, user_id, url_state = dropbox.get_auth_flow().finish(request.args)
    except DropboxOAuth2Flow.BadRequestException, e:
        abort(400)
    except DropboxOAuth2Flow.BadStateException, e:
        abort(400)
    except DropboxOAuth2Flow.CsrfException, e:
        abort(403)
    except DropboxOAuth2Flow.NotApprovedException, e:
        flash('Not approved?  Why not')
        return redirect('/')
    except DropboxOAuth2Flow.ProviderException, e:
        app.logger.exception("Auth error" + e)
        abort(403)
    dropbox.login_success(access_token)
    return redirect('/')

@app.route('/login')
def dropbox_auth_start():
    return redirect(dropbox.login_url)

@app.route('/logout')
def logout():
    dropbox.logout()
    return redirect('/')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html', **locals()), 404

@app.route('/.well-known/<path:filename>')
def for_certbot(filename):
    return send_from_directory('.well-known', filename)


if __name__ == '__main__':
    app.run(port=7777)
