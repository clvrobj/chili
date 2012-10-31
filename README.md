Chili
=====
Chili is a Dropbox powered static site generator.

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
* [Create an app](https://www.dropbox.com/developers/apps), `Access level` → `App folder`, `Name of app folder` → `Chili`, Dropbox will generate `App key` and `App secret` for you.
* In your dropbox folder `~user/Dropbox/Apps/Chili`, write articles in Markdown and save with `.md` suffix.

## Settings
`config.py` is to config Chili, but it's better to create a new file `local_config.py`, it can overwrite the settings in `config,py`.

* `DROPBOX_APP_KEY`: `App key` of your app in Dropbox
* `DROPBOX_APP_SECRET`: `App secret` of your app in Dropbox
* `DROPBOX_ACCOUNT_EMAIL`: Dropbox account email address (bind to this account , other account will not be sync)
* `APP_SECRET_KEY`: for using flask session, this value can be get by

		>>> import os
		>>> os.urandom(24)

## Start Chili on server
* `sh restartapp.sh`

Then you can sync your app folder follow [Routine use](#routine-use) part.

# Routine use
* request `http://your-domain/sync` in browser to sync Dropbox app folder, download all posts, all posts will be generated,     first time you will be asked for the permission for operate Dropbox Chili folder.
* request `http://your-domain/regen` in browser to generate posts without sync.

All these links are list in`http://your-domain/tools`.

# About Markdown meta data
* Title: title of the post
* Date: the create time of the post
* Public: public switch
* Comment: Chili using Disqus to support comments, comments will not shown if set to off.
* Keywords: the tags of the post

Example:

		Title: This is title
		Date:  2012-09-24 09:26:00
		Public: Yes
		Comment: Yes
		Keywords: markdown
                  dropbox
                  blog


# Sample
My personal blog in Chinese: [http://zhangchi.de/](http://zhangchi.de/)