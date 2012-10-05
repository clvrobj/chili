Chili
=====
Chili is a static site generator sync with Dropbox folder.

# Install
`git clone git@github.com:clvrobj/chili.git`

## Dependencies
* [Flask](http://flask.pocoo.org/), chili is based on Flask framework
* [Flask-Mako](http://packages.python.org/Flask-Mako/), for templating support
* [Dropbox Python SDK](https://www.dropbox.com/developers/reference/sdk)
* [Markdown](http://pypi.python.org/pypi/Markdown), for supporting Markdown
* [PyRSS2Gen](http://pypi.python.org/pypi/PyRSS2Gen), to generate RSS feeds

# How to Start

## Dropbox configuration
* [Create an app in Dropbox](https://www.dropbox.com/developers/apps), `Access level` set to `App folder`, `Name of app folder` set to `Chili`, and record the `App key` and `App secret` value.
* in `~user/Dropbox/Apps/Chili` directory, write articles and save in `.md` format.

## Settings
`config.py` is to config Chili, but it's better to create a new file `local_config.py`, it can overwrite the settings in `config,py`.

* `DROPBOX_APP_KEY`: `App key` of your app in Dropbox
* `DROPBOX_APP_SECRET`: `App secret` of your app in Dropbox
* `DROPBOX_ACCOUNT_EMAIL`: Dropbox account email address
* `APP_SECRET_KEY`: for using flask session, this value can be get by

		>>> import os
		>>> os.urandom(24)

## Start Chili on server side
* `sh restartapp.sh`

Then you can sync your app folder follow the Routine use part.

# Routine use
* request `http://your-domain/sync` in browser to sync Dropbox app folder, all posts will be generated.
* request `http://your-domain/regen` in browser to generate posts without sync.

All these links are list in`http://your-domain/tools`.

# Sample
[zhangchi.de blog](http://zhangchi.de/)