Chili
=====
Chili is a Dropbox powered static site generator.

# Install
`git clone git@github.com:clvrobj/chili.git`

## Dependencies
* [Flask](http://flask.pocoo.org/) - chili is based on Flask framework
* [Flask-Mako](http://packages.python.org/Flask-Mako/) - for Mako templating support
* [Flask-Actions](http://packages.python.org/Flask-Actions/) - for running fastcgi daemon on server
* [Dropbox Python SDK](https://www.dropbox.com/developers/reference/sdk)
* [Markdown](http://pypi.python.org/pypi/Markdown) - for supporting Markdown
* [PyRSS2Gen](http://pypi.python.org/pypi/PyRSS2Gen) - to generate RSS feeds

# How to Start

## Dropbox configuration
* [Create an Dropbox app](https://www.dropbox.com/developers/apps), `Access level` → `App folder`, `Name of app folder` → `Chili`, Dropbox will generate `App key` and `App secret` for you.
* In your dropbox folder `~user/Dropbox/Apps/Chili`, write articles in Markdown and save with `.md` suffix.

## Settings
`/config.py` is to config Chili, but it's better to create a new file `/local_config.py`, it can overwrite the settings in `/config,py`.

* `DROPBOX_APP_KEY`: `App key` of your app in Dropbox
* `DROPBOX_APP_SECRET`: `App secret` of your app in Dropbox
* `DROPBOX_ACCOUNT_EMAIL`: Dropbox account email address (bind to this account , other account will not be sync)
* `APP_SECRET_KEY`: for using flask session, this value can be get by

		>>> import os
		>>> os.urandom(24)

## Nginx config
    upstream chili {
	   server 127.0.0.1:7777;
   	}

	server {
		listen 8080;
		server_name  127.0.0.0;
	location / {
	  fastcgi_pass  chili;
	  fastcgi_param REQUEST_METHOD    $request_method;
	  fastcgi_param QUERY_STRING      $query_string;
	  fastcgi_param CONTENT_TYPE      $content_type;
	  fastcgi_param CONTENT_LENGTH    $content_length;
	  fastcgi_param SERVER_ADDR       $server_addr;
	  fastcgi_param SERVER_PORT       $server_port;
	  fastcgi_param SERVER_NAME       $server_name;
	  fastcgi_param SERVER_PROTOCOL   $server_protocol;
	  fastcgi_param PATH_INFO         $fastcgi_script_name;
	  fastcgi_param REMOTE_ADDR       $remote_addr;
	  fastcgi_param REMOTE_PORT       $remote_port;
	  fastcgi_pass_header Authorization;
	  fastcgi_intercept_errors off;
	}

## Start Chili on server
* `sh restartapp.sh`

# How to sync new post?
* Just request `http://your-domaindotcom/sync` in browser,  this will sync Dropbox app folder and download all posts, all your posts will be generated,  you will be asked for the permission for accessing Dropbox Chili folder for the first time.
* If request `http://your-domaindotcom/regen` in browser, this will generate all your posts without sync, this is useful when you just make some customize on the template.

All these links are list in`http://your-domaindotcom/tools`.

# About Markdown meta data
You can control the post by using the meta data:
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